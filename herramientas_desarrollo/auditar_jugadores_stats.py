import sqlite3
import pandas as pd

def audit_jugadores_completo():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    # Consulta incluyendo las columnas de saldos iniciales (amarillas, rojas, asistencias, suplente)
    query = """
        SELECT j.id_excel, j.apellido, j.nombre, p.nombre as posicion,
               j.asistencias_inicial as Asist, 
               j.amarillas_inicial as Amar, 
               j.rojas_inicial as Roj, 
               j.titular_inicial as Tit,
               j.suplente_inicial as Sup
        FROM jugadores j
        LEFT JOIN posiciones p ON j.id_posicion = p.id
        ORDER BY j.id_excel ASC
        LIMIT 20
    """
    
    df = pd.read_sql(query, conn)
    
    print("=== AUDITORÍA: SALDOS INICIALES (Amarillas, Asistencias, Rojas, Suplente) ===")
    print(df.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    audit_jugadores_completo()
