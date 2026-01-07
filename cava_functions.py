import sqlite3
import pandas as pd
from db_config import get_connection

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
        conn.close()

def load_partidos(torneo_id=None):
    """
    Carga los partidos de la base de datos, opcionalmente filtrados por torneo.
    Retorna los datos unidos con los nombres de los rivales y torneos.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT p.*, r.nombre as rival_nombre, t.nombre as torneo_nombre 
            FROM partidos p
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
        """
        if torneo_id:
            query += f" WHERE p.id_torneo = {torneo_id}"
        query += " ORDER BY p.id DESC"
        return pd.read_sql(query, conn)
    finally:
        conn.close()

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
        conn.close()

def load_rivales():
    """
    Retorna la lista de todos los rivales únicos.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM rivales ORDER BY nombre", conn)
    finally:
        conn.close()

def get_player_stats(jugador_id):
    """
    Calcula las estadísticas totales de un jugador sumando:
    1. Lo que tiene en la tabla 'stats' (detalle partido a partido).
    2. Lo que tiene en sus campos '_inicial' (historial del Excel anterior).
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        # Obtenemos los saldos iniciales del jugador
        df_j = pd.read_sql("SELECT * FROM jugadores WHERE id = ?", conn, params=(jugador_id,))
        if df_j.empty: return pd.DataFrame()
        j = df_j.iloc[0]

        # Sumamos el rendimiento detallado de la tabla stats
        query = """
            SELECT COUNT(*) as pj, 
                   SUM(CASE WHEN es_titular=1 THEN 1 ELSE 0 END) as titular,
                   SUM(minutos_jugados) as minutos,
                   SUM(goles_marcados) as goles,
                   SUM(goles_recibidos) as recibidos,
                   SUM(amarillas) as amarillas,
                   SUM(rojas) as rojas
            FROM stats
            WHERE id_jugador = ?
        """
        df_stats = pd.read_sql(query, conn, params=(jugador_id,))
        
        # Combinamos historial con detalle actual
        res = df_stats.iloc[0].to_dict()
        res['pj'] = (res['pj'] or 0) + j['pj_inicial']
        res['titular'] = (res['titular'] or 0) + j['titular_inicial']
        res['goles'] = (res['goles'] or 0) + j['goles_marcados_inicial']
        res['recibidos'] = (res['recibidos'] or 0) + j['goles_recibidos_inicial']
        res['amarillas'] = (res['amarillas'] or 0) + j['amarillas_inicial']
        res['rojas'] = (res['rojas'] or 0) + j['rojas_inicial']
        res['minutos'] = (res['minutos'] or 0)
        
        return pd.DataFrame([res])
    finally:
        conn.close()

def get_player_matches(jugador_id):
    """
    Retorna la lista detallada de todos los partidos donde participó un jugador.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT p.nro_fecha, r.nombre as rival, t.nombre as torneo,
                   s.minutos_jugados, s.es_titular, s.goles_marcados as goles, 
                   s.goles_recibidos, s.amarillas, s.rojas
            FROM stats s
            JOIN partidos p ON s.id_partido = p.id
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
            WHERE s.id_jugador = ?
            ORDER BY p.id DESC
        """
        return pd.read_sql(query, conn, params=(jugador_id,))
    finally:
        conn.close()

def login_user(username, password):
    """
    Verifica las credenciales de un usuario para el sistema de gestión.
    """
    conn = get_connection()
    if not conn: return False, "Error de conexión"
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        if not user: return False, "Usuario o contraseña incorrectos"
        return True, {
            'id': user[0],
            'username': user[1],
            'rol': user[3],
            'nombre': user[4]
        }
    finally:
        conn.close()

# ========================================
# FUNCIONES DE ANALÍTICA PARA EL DASHBOARD
# ========================================

def get_global_stats(torneo_id=None, temporada=None):
    """
    Calcula el récord global (Ganados, Empatados, Perdidos) y goles totales
    del equipo, permitiendo filtrar por torneo o año.
    """
    conn = get_connection()
    if not conn: return {}
    try:
        query = "SELECT goles_favor, goles_contra FROM partidos p JOIN torneos t ON p.id_torneo = t.id WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            query += " AND t.id = ?"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            query += " AND t.temporada = ?"
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
        conn.close()

def get_top_stat(stat_col="goles_marcados", limit=10, sum_initial=True, torneo_id=None, temporada=None):
    """
    Retorna el ranking de los mejores jugadores. 
    Si hay filtros (torneo/temporada), NO suma los valores históricos iniciales.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        where_clause = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where_clause += " AND p.id_torneo = ?"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where_clause += " AND t.temporada = ?"
            params.append(temporada)
            
        join_clause = "LEFT JOIN stats s ON j.id = s.id_jugador LEFT JOIN partidos p ON s.id_partido = p.id LEFT JOIN torneos t ON p.id_torneo = t.id"
        
        # Si NO hay filtros activos y sum_initial es True, usamos la lógica histórica
        use_initial = sum_initial and (not torneo_id or torneo_id == "Todos") and (not temporada or temporada == "Todas")
        
        initial_col = f"j.{stat_col}_inicial" if stat_col in ["goles_marcados", "goles_recibidos"] and use_initial else "0"
        
        query = f"""
            SELECT j.nombre || ' ' || j.apellido as Jugador,
                   IFNULL(SUM(s.{stat_col}), 0) + IFNULL({initial_col}, 0) as Total
            FROM jugadores j
            {join_clause}
            {where_clause}
            GROUP BY j.id
            HAVING Total > 0
            ORDER BY Total DESC
            LIMIT ?
        """
        params.append(limit)
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

def get_dt_stats(torneo_id=None, temporada=None):
    """
    Calcula la efectividad de los DTs, permitiendo filtrar por torneo/temporada.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        where = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where += " AND t_orn.id = ?"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where += " AND t_orn.temporada = ?"
            params.append(temporada)
            
        query = f"""
            SELECT t.nombre as Tecnico,
                   COUNT(p.id) as PJ,
                   SUM(CASE WHEN p.goles_favor > p.goles_contra THEN 1 ELSE 0 END) as PG,
                   SUM(CASE WHEN p.goles_favor = p.goles_contra THEN 1 ELSE 0 END) as PE,
                   SUM(CASE WHEN p.goles_favor < p.goles_contra THEN 1 ELSE 0 END) as PP,
                   SUM(p.goles_favor) as GF,
                   SUM(p.goles_contra) as GC
            FROM partidos p
            JOIN tecnicos t ON p.id_tecnico = t.id
            JOIN torneos t_orn ON p.id_torneo = t_orn.id
            {where}
            GROUP BY t.id
            HAVING PJ > 0
            ORDER BY PJ DESC
        """
        df = pd.read_sql(query, conn, params=params)
        
        df['PTS'] = (df['PG'] * 3) + (df['PE'] * 1)
        df['Efectividad'] = (df['PTS'] / (df['PJ'] * 3) * 100).round(1)
        
        return df.sort_values(by='Efectividad', ascending=False)
    finally:
        conn.close()

def get_result_distribution(torneo_id=None, temporada=None):
    """
    Retorna el conteo de Victorias, Empates y Derrotas para gráficos de torta.
    """
    stats = get_global_stats(torneo_id, temporada)
    if not stats: return pd.DataFrame()
    
    return pd.DataFrame({
        'Resultado': ['Ganados', 'Empatados', 'Perdidos'],
        'Cantidad': [stats['pg'], stats['pe'], stats['pp']]
    })

def get_recent_form(limit=5, torneo_id=None, temporada=None):
    """
    Retorna los ultimos N partidos con un indicador visual de resultado.
    """
    conn = get_connection()
    try:
        where = "WHERE 1=1"
        params = []
        if torneo_id and torneo_id != "Todos":
            where += " AND p.id_torneo = ?"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            where += " AND t.temporada = ?"
            params.append(temporada)
            
        query = f"""
            SELECT p.goles_favor, p.goles_contra, r.nombre as rival, 
                   p.nro_fecha
            FROM partidos p
            JOIN rivales r ON p.id_rival = r.id
            JOIN torneos t ON p.id_torneo = t.id
            {where}
            ORDER BY p.id DESC
            LIMIT ?
        """
        params.append(limit)
        df = pd.read_sql(query, conn, params=params)
        
        # Agregamos columna de icono
        def get_icon(row):
            if row['goles_favor'] > row['goles_contra']: return "✅" # Ganado
            elif row['goles_favor'] == row['goles_contra']: return "➖" # Empate
            else: return "❌" # Perdido
            
        if not df.empty:
            df['Resultado'] = df.apply(get_icon, axis=1)
            # Ordenamos cronológicamente (antiguo a nuevo) para mostrar la racha
            df = df.sort_values(by='nro_fecha') 
        return df
    finally:
        conn.close()

def get_stats_against_rival(rival_id):
    """
    Obtiene el historial completo (PJ, PG, PE, PP, GF, GC) contra un club específico.
    """
    conn = get_connection()
    if not conn: return {}
    try:
        query = "SELECT goles_favor, goles_contra FROM partidos WHERE id_rival = ?"
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
        conn.close()
