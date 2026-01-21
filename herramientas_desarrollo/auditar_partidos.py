import sqlite3
import pandas as pd

def audit_partidos():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    query = """
        SELECT p.nro_fecha as Fecha, r.nombre as Rival, 
               p.goles_favor || '-' || p.goles_contra as Resultado,
               p.goles_detalle, 
               p.penales_favor as P_AF, p.penales_favor_detalle as P_AF_Det,
               p.penales_contra as P_EC, p.penales_contra_detalle as P_EC_Det,
               t.nombre as DT, a.nombre as Arb
        FROM partidos p
        JOIN rivales r ON p.id_rival = r.id
        LEFT JOIN tecnicos t ON p.id_tecnico = t.id
        LEFT JOIN arbitros a ON p.id_arbitro = a.id
        LIMIT 10
    """
    
    df = pd.read_sql(query, conn)
    
    print("=== AUDITORÍA: TABLA PARTIDOS (DETALLADA) ===")
    print(df.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    audit_partidos()
