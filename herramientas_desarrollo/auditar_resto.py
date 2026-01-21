import sqlite3
import pandas as pd

def audit_maestras():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    print("=== TABLA: POSICIONES ===")
    print(pd.read_sql("SELECT * FROM posiciones", conn).to_string(index=False))
    
    print("\n=== TABLA: TECNICOS ===")
    print(pd.read_sql("SELECT * FROM tecnicos", conn).to_string(index=False))
    
    print("\n=== MUESTRA DE STATS (UNIÓN JUGADOR-PARTIDO) ===")
    # Verificamos si se cargaron minutos correctamente
    query = """
        SELECT j.apellido, p.nro_fecha, p.id_torneo, s.minutos_jugados, s.es_titular
        FROM stats s
        JOIN jugadores j ON s.id_jugador = j.id
        JOIN partidos p ON s.id_partido = p.id
        LIMIT 10
    """
    print(pd.read_sql(query, conn).to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    audit_maestras()
