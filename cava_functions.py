import sqlite3
import pandas as pd
import streamlit as st
from db_config import get_connection, get_placeholder, close_connection

def load_torneos():
    """
    Carga la lista completa de torneos registrados en la base de datos.
    Retorna un DataFrame de Pandas.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM torneos ORDER BY temporada DESC, nombre", conn)
    finally:
        close_connection(conn)

@st.cache_data(ttl=600, show_spinner=False)
def load_partidos(torneo_id=None):
    """
    Carga los partidos de la base de datos, opcionalmente filtrados por torneo.
    Retorna los datos unidos con los nombres de los rivales y torneos.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        ph = get_placeholder(conn)
        query = """
            SELECT p.*, r.nombre as rival_nombre, t.nombre as torneo_nombre 
            FROM partidos p
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
        """
        params = []
        if torneo_id:
            query += f" WHERE p.id_torneo = {torneo_id}" # ID numérico, seguro
        query += " ORDER BY p.id DESC"
        
        # Para read_sql con psycopg2, a veces es mejor pasar params vacíos si no se usan
        return pd.read_sql(query, conn)
    finally:
        close_connection(conn)

@st.cache_data(ttl=3600, show_spinner=False)
def load_jugadores():
    """
    Carga la ficha de todos los jugadores unidos con su nombre de posición.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT j.*, p.nombre as posicion_nombre 
            FROM jugadores j
            LEFT JOIN posiciones p ON j.id_posicion = p.id
            ORDER BY j.apellido, j.nombre
        """
        return pd.read_sql(query, conn)
    finally:
        close_connection(conn)

@st.cache_data(ttl=3600, show_spinner=False)
def load_rivales():
    """
    Retorna la lista de todos los rivales únicos.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM rivales ORDER BY nombre", conn)
    finally:
        close_connection(conn)

@st.cache_data(ttl=60, show_spinner=False)
def get_player_stats(jugador_id):
    """
    Calcula las estadísticas totales de un jugador sumando detalle y estático.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        ph = get_placeholder(conn)
        # Obtenemos los saldos iniciales del jugador
        df_j = pd.read_sql(f"SELECT * FROM jugadores WHERE id = {ph}", conn, params=(jugador_id,))
        if df_j.empty: return pd.DataFrame()
        j = df_j.iloc[0]

        # Sumamos el rendimiento detallado de la tabla stats
        query = f"""
            SELECT COUNT(*) as pj, 
                   SUM(CASE WHEN es_titular THEN 1 ELSE 0 END) as titular,
                   SUM(minutos_jugados) as minutos,
                   SUM(goles_marcados) as goles,
                   SUM(goles_recibidos) as recibidos,
                   SUM(amarillas) as amarillas,
                   SUM(rojas) as rojas
            FROM stats
            WHERE id_jugador = {ph}
        """
        df_stats = pd.read_sql(query, conn, params=(jugador_id,))
        
        # Combinamos historial con detalle actual
        res = df_stats.iloc[0].to_dict()
        def clean_val(val): return val if val is not None else 0
        
        res['pj'] = clean_val(res.get('pj')) + j['pj_inicial']
        res['titular'] = clean_val(res.get('titular')) + j['titular_inicial']
        res['goles'] = clean_val(res.get('goles')) + j['goles_marcados_inicial']
        res['recibidos'] = clean_val(res.get('recibidos')) + j['goles_recibidos_inicial']
        res['amarillas'] = clean_val(res.get('amarillas')) + j['amarillas_inicial']
        res['rojas'] = clean_val(res.get('rojas')) + j['rojas_inicial']
        res['minutos'] = clean_val(res.get('minutos'))
        
        return pd.DataFrame([res])
    finally:
        close_connection(conn)

def get_player_matches(jugador_id):
    """
    Retorna la lista detallada de todos los partidos donde participó un jugador.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        ph = get_placeholder(conn)
        query = f"""
            SELECT p.nro_fecha, r.nombre as rival, t.nombre as torneo,
                   s.minutos_jugados, s.es_titular, s.goles_marcados as goles, 
                   s.goles_recibidos, s.amarillas, s.rojas
            FROM stats s
            JOIN partidos p ON s.id_partido = p.id
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
            WHERE s.id_jugador = {ph}
            ORDER BY p.id DESC
        """
        return pd.read_sql(query, conn, params=(jugador_id,))
    finally:
        close_connection(conn)

def login_user(username, password):
    """
    Verifica las credenciales de un usuario.
    """
    conn = get_connection()
    if not conn: return False, "Error de conexión"
    try:
        ph = get_placeholder(conn)
        c = conn.cursor()
        c.execute(f"SELECT * FROM usuarios WHERE username = {ph} AND password = {ph}", (username, password))
        user = c.fetchone()
        if not user: return False, "Usuario o contraseña incorrectos"
        return True, {
            'id': user[0],
            'username': user[1],
            'rol': user[3],
            'nombre': user[4]
        }
    finally:
        close_connection(conn)

# ========================================
# FUNCIONES DE ANALÍTICA PARA EL DASHBOARD
# ========================================

@st.cache_data(ttl=60, show_spinner=False)
def get_global_stats(torneo_id=None, temporada=None):
    """
    Calcula el récord global (G/E/P) filtrado.
    """
    conn = get_connection()
    if not conn: return {}
    try:
        ph = get_placeholder(conn)
        query = "SELECT goles_favor, goles_contra FROM partidos p JOIN torneos t ON p.id_torneo = t.id WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            query += f" AND t.id = {ph}"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            query += f" AND t.temporada = {ph}"
            params.append(temporada)
            
        df = pd.read_sql(query, conn, params=params)
        if df.empty: return {"pj":0, "pg":0, "pe":0, "pp":0, "gf":0, "gc":0}
        
        pj = len(df)
        pg = len(df[df['goles_favor'] > df['goles_contra']])
        pp = len(df[df['goles_favor'] < df['goles_contra']])
        pe = len(df[df['goles_favor'] == df['goles_contra']])
        gf = df['goles_favor'].sum()
        gc = df['goles_contra'].sum()
        
        return {"pj":pj, "pg":pg, "pe":pe, "pp":pp, "gf":gf, "gc":gc}
    finally:
        close_connection(conn)

@st.cache_data(ttl=60, show_spinner=False)
def get_top_stat(stat_col="goles_marcados", limit=10, sum_initial=True, torneo_id=None, temporada=None):
    """
    Retorna el ranking de los mejores jugadores filtrado.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        ph = get_placeholder(conn)
        where_clause = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where_clause += f" AND p.id_torneo = {ph}"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where_clause += f" AND t.temporada = {ph}"
            params.append(temporada)
            
        join_clause = "LEFT JOIN stats s ON j.id = s.id_jugador LEFT JOIN partidos p ON s.id_partido = p.id LEFT JOIN torneos t ON p.id_torneo = t.id"
        
        use_initial = sum_initial and (not torneo_id or torneo_id == "Todos") and (not temporada or temporada == "Todas")
        initial_col = f"j.{stat_col}_inicial" if stat_col in ["goles_marcados", "goles_recibidos"] and use_initial else "0"
        
        # Postgres puede tener problemas con IFNULL, usar COALESCE es estándar SQL
        null_func = "COALESCE" 
        
        query = f"""
            SELECT j.nombre || ' ' || j.apellido as "Jugador",
                   {null_func}(SUM(s.{stat_col}), 0) + {null_func}({initial_col}, 0) as "Total"
            FROM jugadores j
            {join_clause}
            {where_clause}
            GROUP BY j.id
            HAVING {null_func}(SUM(s.{stat_col}), 0) + {null_func}({initial_col}, 0) > 0
            ORDER BY "Total" DESC
            LIMIT {ph}
        """
        params.append(limit)
        return pd.read_sql(query, conn, params=params)
    finally:
        close_connection(conn)

@st.cache_data(ttl=60, show_spinner=False)
def get_dt_stats(torneo_id=None, temporada=None):
    """
    Calcula la efectividad de los DTs.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        ph = get_placeholder(conn)
        where = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where += f" AND t_orn.id = {ph}"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where += f" AND t_orn.temporada = {ph}"
            params.append(temporada)
            
        query = f"""
            SELECT t.nombre as "Tecnico",
                   COUNT(p.id) as "PJ",
                   SUM(CASE WHEN p.goles_favor > p.goles_contra THEN 1 ELSE 0 END) as "PG",
                   SUM(CASE WHEN p.goles_favor = p.goles_contra THEN 1 ELSE 0 END) as "PE",
                   SUM(CASE WHEN p.goles_favor < p.goles_contra THEN 1 ELSE 0 END) as "PP",
                   SUM(p.goles_favor) as "GF",
                   SUM(p.goles_contra) as "GC"
            FROM partidos p
            JOIN tecnicos t ON p.id_tecnico = t.id
            JOIN torneos t_orn ON p.id_torneo = t_orn.id
            {where}
            GROUP BY t.id
            HAVING COUNT(p.id) > 0
            ORDER BY "PJ" DESC
        """
        df = pd.read_sql(query, conn, params=params)
        
        # Postgres puede retornar Decimal/BigInt como object, forzamos numérico
        cols_to_numeric = ['PJ', 'PG', 'PE', 'PP', 'GF', 'GC']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['PTS'] = (df['PG'] * 3) + (df['PE'] * 1)
        df['Efectividad'] = (df['PTS'] / (df['PJ'] * 3) * 100).round(1)
        
        return df.sort_values(by='Efectividad', ascending=False)
    finally:
        close_connection(conn)

def get_result_distribution(torneo_id=None, temporada=None):
    stats = get_global_stats(torneo_id, temporada)
    if not stats: return pd.DataFrame()
    return pd.DataFrame({
        'Resultado': ['Ganados', 'Empatados', 'Perdidos'],
        'Cantidad': [stats['pg'], stats['pe'], stats['pp']]
    })

@st.cache_data(ttl=60, show_spinner=False)
def get_recent_form(limit=5, torneo_id=None, temporada=None):
    conn = get_connection()
    try:
        ph = get_placeholder(conn)
        where = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where += f" AND p.id_torneo = {ph}"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where += f" AND t.temporada = {ph}"
            params.append(temporada)
            
        query = f"""
            SELECT p.goles_favor, p.goles_contra, r.nombre as rival, 
                   p.nro_fecha
            FROM partidos p
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
            {where}
            ORDER BY p.id DESC
            LIMIT {ph}
        """
        params.append(limit)
        df = pd.read_sql(query, conn, params=params)
        
        def get_icon(row):
            if row['goles_favor'] > row['goles_contra']: return "✅" 
            elif row['goles_favor'] == row['goles_contra']: return "➖" 
            else: return "❌" 
            
        if not df.empty:
            df['Resultado'] = df.apply(get_icon, axis=1)
            df = df.sort_values(by='nro_fecha') 
        return df
    finally:
        close_connection(conn)

@st.cache_data(ttl=600, show_spinner=False)
def get_stats_against_rival(rival_id):
    conn = get_connection()
    if not conn: return {}
    try:
        ph = get_placeholder(conn)
        query = f"SELECT goles_favor, goles_contra FROM partidos WHERE id_rival = {ph}"
        df = pd.read_sql(query, conn, params=(rival_id,))
        
        if df.empty: return {"pj":0, "pg":0, "pe":0, "pp":0, "gf":0, "gc":0}
        
        return {
            "pj": len(df),
            "pg": len(df[df['goles_favor'] > df['goles_contra']]),
            "pe": len(df[df['goles_favor'] == df['goles_contra']]),
            "pp": len(df[df['goles_favor'] < df['goles_contra']]),
            "gf": df['goles_favor'].sum(),
            "gc": df['goles_contra'].sum()
        }
    finally:
        close_connection(conn)

# ==============================================================================
# FUNCIONES DE ESCRITURA (ADMIN)
# ==============================================================================

def create_user(username, password, nombre):
    conn = get_connection()
    if not conn: return False, "Error de conexión"
    try:
        ph = get_placeholder(conn)
        ignore = "OR IGNORE" if "sqlite" in str(conn.__class__).lower() else ""
        conflict = "ON CONFLICT DO NOTHING" if ignore == "" else ""
        
        c = conn.cursor()
        # Verificar si existe
        c.execute(f"SELECT id FROM usuarios WHERE username = {ph}", (username,))
        if c.fetchone():
            return False, "El usuario ya existe"
            
        c.execute(f"INSERT {ignore} INTO usuarios (username, password, rol, nombre) VALUES ({ph}, {ph}, 'admin', {ph}) {conflict}",
                 (username, password, nombre))
        conn.commit()
        return True, "Usuario creado exitosamente"
    except Exception as e:
        conn.rollback()
        return False, f"Error DB: {e}"
    finally:
        close_connection(conn)

def save_match(match_data, df_stats):
    """
    Guarda un partido y sus estadísticas en una transacción atómica.
    match_data: dict con keys (id_torneo, id_rival, fecha, condicion, gf, gc)
    df_stats: DataFrame con cols (id_jugador, minutos, goles, amarillas, rojas)
    """
    conn = get_connection()
    if not conn: return False, "Error de conexión"
    
    try:
        ph = get_placeholder(conn)
        c = conn.cursor()
        
        # 1. Insertar Partido
        query_match = f"""
            INSERT INTO partidos (id_torneo, id_rival, nro_fecha, condicion, goles_favor, goles_contra)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        """
        # Postgres necesita RETURNING para obtener el ID insertado
        if "psycopg2" in str(conn.__class__):
            query_match += " RETURNING id"
            c.execute(query_match, (
                match_data['id_torneo'], match_data['id_rival'], match_data['fecha'],
                match_data['condicion'], match_data['gf'], match_data['gc']
            ))
            match_id = c.fetchone()[0]
        else:
            # SQLite usa lastrowid
            c.execute(query_match, (
                match_data['id_torneo'], match_data['id_rival'], match_data['fecha'],
                match_data['condicion'], match_data['gf'], match_data['gc']
            ))
            match_id = c.lastrowid

        # 2. Preparar Stats
        batch_stats = []
        is_pg = "psycopg2" in str(conn.__class__)
        
        # Iteramos solo los jugadores que jugaron o fueron al banco (pj > 0 o suplente)
        for _, row in df_stats.iterrows():
            mins = int(row['minutos'])
            if mins > 0 or row['rojas'] > 0 or row['amarillas'] > 0 or row['goles'] > 0: 
                is_starter = (mins > 45) # Logica simple para MVP
                
                # Ajuste de tipos para Postgres
                val_titular = bool(is_starter) if is_pg else (1 if is_starter else 0)
                
                batch_stats.append((
                    match_id, 
                    int(row['id']), # id_jugador
                    mins,
                    val_titular,
                    int(row['goles']),
                    int(row['goles_recibidos']) if 'goles_recibidos' in row else 0,
                    int(row['amarillas']),
                    int(row['rojas'])
                ))

        if batch_stats:
            query_stats = f"""
                INSERT INTO stats (id_partido, id_jugador, minutos_jugados, es_titular, goles_marcados, goles_recibidos, amarillas, rojas)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """
            c.executemany(query_stats, batch_stats)
            
        conn.commit()
        # Invalidar cache de Streamlit para que se refresquen los datos
        st.cache_data.clear()
        
        return True, f"Partido guardado con ID {match_id}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error guardando partido: {e}"
    finally:
        conn.close()
