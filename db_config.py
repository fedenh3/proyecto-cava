import sqlite3
import os

# Nombre del archivo de la base de datos SQLite
DB_NAME = "cava_stats_v2.db"
# Nombre del archivo que contiene las sentencias SQL para crear las tablas
SCHEMA_FILE = "cava_schema.sql"

def get_connection():
    """
    Establece y retorna una conexión a la base de datos SQLite.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def init_db():
    """
    Lee el archivo .sql y ejecuta las sentencias para crear la estructura
    de tablas si estas no existen.
    """
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: No se encuentra el archivo {SCHEMA_FILE}")
        return
    
    conn = get_connection()
    if conn:
        try:
            with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            print("✅ Base de datos inicializada correctamente (Tablas creadas/verificadas).")
        except Exception as e:
            print(f"Error inicializando la estructura: {e}")
        finally:
            conn.close()
