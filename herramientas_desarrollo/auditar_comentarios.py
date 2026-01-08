import sqlite3
import pandas as pd

def audit_comentarios():
    conn = sqlite3.connect('cava_stats_v2.db')
    
    # Buscar jugadores que tengan comentarios
    query = """
        SELECT id_excel, apellido, nombre, comentarios_gf
        FROM jugadores 
        WHERE comentarios_gf IS NOT NULL AND comentarios_gf != '' AND comentarios_gf != '-'
        LIMIT 10
    """
    
    df = pd.read_sql(query, conn)
    
    print("=== AUDITORÍA: COLUMNA 'comentarios_gf' ===")
    if df.empty:
        print("No se encontraron comentarios cargados.")
    else:
        print(df.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    audit_comentarios()
