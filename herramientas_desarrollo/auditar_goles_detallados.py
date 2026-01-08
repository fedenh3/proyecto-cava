import sqlite3
import pandas as pd

def audit_goles_detallados():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    # Auditamos a Coselli para ver si sus goles están en el detalle
    query = """
        SELECT j.apellido, p.nro_fecha, t.nombre as torneo, s.goles_marcados 
        FROM stats s
        JOIN jugadores j ON s.id_jugador = j.id
        JOIN partidos p ON s.id_partido = p.id
        JOIN torneos t ON p.id_torneo = t.id
        WHERE j.apellido LIKE '%COSELLI%' AND s.goles_marcados > 0
    """
    
    df = pd.read_sql(query, conn)
    
    print("=== AUDITORÍA: GOLES DETALLADOS (COSELLI) ===")
    if df.empty:
        print("No se encontraron goles detallados.")
    else:
        print(df.to_string(index=False))
        print(f"\nTotal Goles en detalle: {df['goles_marcados'].sum()}")
        
    conn.close()

if __name__ == "__main__":
    audit_goles_detallados()
