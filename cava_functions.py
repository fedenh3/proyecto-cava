import pandas as pd
from db_config import get_connection

def load_torneos():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM torneos ORDER BY id DESC", conn)
    finally:
        conn.close()

def load_partidos(torneo_id=None, temporada=None):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        # Join with torneos, rivales, arbitros, tecnicos
        query = """
            SELECT p.id, p.fecha, t.nombre as torneo, t.temporada, 
                   r.nombre as rival, p.condicion, 
                   p.goles_favor, p.goles_contra,
                   a.nombre as arbitro, te.nombre as tecnico
            FROM partidos p
            LEFT JOIN torneos t ON p.id_torneo = t.id
            LEFT JOIN rivales r ON p.id_rival = r.id
            LEFT JOIN arbitros a ON p.id_arbitro = a.id
            LEFT JOIN tecnicos te ON p.id_tecnico = te.id
            WHERE 1=1
        """
        params = []
        if torneo_id and torneo_id != "Todos":
            query += " AND t.id = ?"
            params.append(torneo_id)
        if temporada and temporada != "Todas":
            query += " AND t.temporada = ?"
            params.append(temporada)
            
        query += " ORDER BY p.fecha DESC, p.id DESC"
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

def load_jugadores():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT id, nombre, apellido, posicion, goles_iniciales FROM jugadores ORDER BY apellido, nombre", conn)
    finally:
        conn.close()

def load_rivales():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM rivales ORDER BY nombre", conn)
    finally:
        conn.close()

def get_player_stats(jugador_id, initial_goals=0):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
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
        df = pd.read_sql(query, conn, params=(jugador_id,))
        
        if not df.empty:
            current_goles = df.iloc[0]['goles']
            if pd.isna(current_goles): current_goles = 0
            df.at[0, 'goles'] = current_goles + initial_goals
        
        return df
    finally:
        conn.close()

def get_player_matches(jugador_id):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        query = """
            SELECT p.fecha, r.nombre as rival, t.nombre as torneo,
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

def create_rival(nombre):
    conn = get_connection()
    if not conn: return None
    try:
        c = conn.cursor()
        c.execute("INSERT INTO rivales (nombre) VALUES (?)", (nombre.upper(),))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        print(f"Error creando rival: {e}")
        return None
    finally:
        conn.close()

def get_rival_id_by_name(nombre):
    conn = get_connection()
    if not conn: return None
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM rivales WHERE nombre = ?", (nombre.upper(),))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def save_match(fecha, id_torneo, id_rival, condicion, gf, gc):
    conn = get_connection()
    if not conn: return False
    try:
        c = conn.cursor()
        # Nota: Dejamos id_arbitro y id_tecnico como NULL por ahora desde la UI simple
        c.execute("""
            INSERT INTO partidos (fecha, id_torneo, id_rival, condicion, goles_favor, goles_contra)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fecha, id_torneo, id_rival, condicion, gf, gc))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando partido: {e}")
        return False
    finally:
        conn.close()
