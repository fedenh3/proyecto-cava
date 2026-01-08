import sqlite3
import pandas as pd

def audit_jugadores():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    # Consulta detallada uniendo con posiciones
    query = """
        SELECT j.id, j.id_excel, j.apellido, j.nombre, p.nombre as posicion,
               j.pj_inicial as PJ, j.goles_marcados_inicial as G_Marc,
               j.goles_recibidos_inicial as G_Rec, j.fecha_debut, 
               j.rival_debut, j.resultado_debut
        FROM jugadores j
        LEFT JOIN posiciones p ON j.id_posicion = p.id
        LIMIT 15
    """
    
    df = pd.read_sql(query, conn)
    
    print("=== AUDITORÍA TABLA: JUGADORES (Primeras 15 filas) ===")
    print(df.to_string(index=False))
    
    print("\n--- Conteo Total ---")
    count = pd.read_sql("SELECT COUNT(*) as total FROM jugadores", conn).iloc[0]['total']
    print(f"Total de jugadores en base de datos: {count}")
    
    conn.close()

if __name__ == "__main__":
    audit_jugadores()
