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

def get_top_stat(stat_col="goles_marcados", limit=10, sum_initial=True):
    """
    Retorna el ranking de los mejores jugadores en una estadística específica
    (ej: Goleadores). Suma automáticamente los valores históricos del Excel.
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        if stat_col == "goles_marcados" and sum_initial:
            query = f"""
                SELECT j.nombre || ' ' || j.apellido as Jugador,
                       IFNULL(SUM(s.{stat_col}), 0) + IFNULL(j.goles_marcados_inicial, 0) as Total
                FROM jugadores j
                LEFT JOIN stats s ON j.id = s.id_jugador
                GROUP BY j.id
                ORDER BY Total DESC
                LIMIT ?
            """
        elif stat_col == "goles_recibidos" and sum_initial:
            query = f"""
                SELECT j.nombre || ' ' || j.apellido as Jugador,
                       IFNULL(SUM(s.{stat_col}), 0) + IFNULL(j.goles_recibidos_inicial, 0) as Total
                FROM jugadores j
                LEFT JOIN stats s ON j.id = s.id_jugador
                GROUP BY j.id
                ORDER BY Total DESC
                LIMIT ?
            """
        else:
            query = f"""
                SELECT j.nombre || ' ' || j.apellido as Jugador,
                       IFNULL(SUM(s.{stat_col}), 0) as Total
                FROM jugadores j
                LEFT JOIN stats s ON j.id = s.id_jugador
                GROUP BY j.id
                ORDER BY Total DESC
                LIMIT ?
            """
        return pd.read_sql(query, conn, params=(limit,))
    finally:
        conn.close()

def get_dt_stats():
    """
    Calcula la efectividad de cada Director Técnico basándose en los partidos dirigidos.
    Efectividad = (Puntos Obtenidos / Puntos Posibles) * 100
    """
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT t.nombre as Tecnico,
                   COUNT(p.id) as PJ,
                   SUM(CASE WHEN p.goles_favor > p.goles_contra THEN 1 ELSE 0 END) as PG,
                   SUM(CASE WHEN p.goles_favor = p.goles_contra THEN 1 ELSE 0 END) as PE,
                   SUM(CASE WHEN p.goles_favor < p.goles_contra THEN 1 ELSE 0 END) as PP,
                   SUM(p.goles_favor) as GF,
                   SUM(p.goles_contra) as GC
            FROM partidos p
            JOIN tecnicos t ON p.id_tecnico = t.id
            GROUP BY t.id
            HAVING PJ > 0
            ORDER BY PJ DESC
        """
        df = pd.read_sql(query, conn)
        
        # Calcular Puntos y Efectividad
        df['PTS'] = (df['PG'] * 3) + (df['PE'] * 1)
        df['Efectividad'] = (df['PTS'] / (df['PJ'] * 3) * 100).round(1)
        
        return df.sort_values(by='Efectividad', ascending=False)
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
