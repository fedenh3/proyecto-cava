import sqlite3
import os

DB_CONFIG = {
    "database": "cava_stats_v2.db",
    "schema_file": "cava_schema.sql"
}

def get_connection():
    """Conecta a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_CONFIG["database"])
        # Habilitar Foreign Keys en SQLite (por defecto desactivadas)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def init_db():
    """Inicializa la base de datos leyendo el archivo SQL."""
    if not os.path.exists(DB_CONFIG["schema_file"]):
        print(f"❌ Error: No se encontró el archivo de esquema {DB_CONFIG['schema_file']}")
        return

    try:
        conn = get_connection()
        if conn:
            with open(DB_CONFIG["schema_file"], 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Ejecutar script SQL (sqlite3 soporta executescript para múltiples sentencias)
            conn.executescript(schema_sql)
            conn.commit()
            print("✅ Base de datos inicializada correctamente (Tablas creadas/verificadas).")
            conn.close()
    except sqlite3.Error as e:
        print(f"❌ Error inicializando la base de datos: {e}")
