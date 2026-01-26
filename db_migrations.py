import streamlit as st
from db_config import get_connection, close_connection

def run_migration_v4():
    """
    Agrega las columnas de detalle de goles y estadísticas de arquero a la tabla stats.
    """
    conn = get_connection()
    if not conn:
        return False, "No se pudo conectar a la base de datos."
    
    try:
        c = conn.cursor()
        
        # Lista de columnas a agregar y su definición
        new_cols = [
            ("goles_penal", "INTEGER DEFAULT 0 CHECK(goles_penal >= 0)"),
            ("goles_tiro_libre", "INTEGER DEFAULT 0 CHECK(goles_tiro_libre >= 0)"),
            ("goles_cabeza", "INTEGER DEFAULT 0 CHECK(goles_cabeza >= 0)"),
            ("goles_jugada", "INTEGER DEFAULT 0 CHECK(goles_jugada >= 0)"),
            ("goles_recibidos_penal", "INTEGER DEFAULT 0 CHECK(goles_recibidos_penal >= 0)")
        ]
        
        is_sqlite = "sqlite" in str(conn.__class__).lower()
        
        added_count = 0
        for col_name, col_def in new_cols:
            try:
                # Intentamos agregar la columna
                alter_query = f"ALTER TABLE stats ADD COLUMN {col_name} {col_def}"
                c.execute(alter_query)
                added_count += 1
            except Exception as e:
                # Si falla es probable que ya exista, la ignoramos
                pass
                
        conn.commit()
        return True, f"Migración completada. Se agregaron {added_count} columnas nuevas."
        
    except Exception as e:
        conn.rollback()
        return False, f"Error en migración: {e}"
    finally:
        close_connection(conn)
