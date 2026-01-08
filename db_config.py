import sqlite3
import os
import streamlit as st

# Nombre del archivo de la base de datos SQLite (Fallback local)
DB_NAME = "cava_stats_v2.db"
SCHEMA_FILE_SQLITE = "cava_schema.sql"
SCHEMA_FILE_POSTGRES = "cava_schema_postgres.sql"

@st.cache_resource
def _get_cached_connection():
    """Retorna una conexión única cacheada."""
    # 1. Intentar conexión a Supabase (Postgres)
    if "supabase" in st.secrets:
        try:
            import psycopg2
            secrets = st.secrets["supabase"]
            conn = psycopg2.connect(
                host=secrets["host"],
                database=secrets["dbname"],
                user=secrets["user"],
                password=secrets["password"],
                port=secrets["port"]
            )
            return conn
        except Exception as e:
            print(f"⚠️ Error conectando a Supabase: {e}. Usando SQLite local.")
            return None
    return None

def get_connection():
    """
    Wrapper que gestiona la conexión cacheada.
    Verifica si está cerrada y reconecta si es necesario.
    """
    # 1. Intentar obtener conexión Postgres cacheada
    conn = _get_cached_connection()
    
    # Si existe y está abierta, retornarla
    if conn and not conn.closed:
        return conn
        
    # Si está cerrada (o es None y falló cache), limpiamos cache y reintentamos
    if conn and conn.closed:
        st.cache_resource.clear()
        conn = _get_cached_connection()
        if conn and not conn.closed:
            return conn

    # 2. Fallback a SQLite (No cacheamos SQLite local porque es rápido)
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except Exception as e:
        print(f"Error conectando a SQLite: {e}")
        return None

def is_postgres(conn):
    return hasattr(conn, 'dsn') # psycopg2 objects have 'dsn' attribute

def get_placeholder(conn):
    if is_postgres(conn):
        return "%s"
    return "?"

def get_ignore_clause(conn):
    """Retorna 'OR IGNORE' para SQLite, vacío para Postgres"""
    if is_postgres(conn):
        return ""
    return "OR IGNORE"

def get_conflict_clause(conn):
    """Retorna vacío para SQLite, 'ON CONFLICT DO NOTHING' para Postgres"""
    if is_postgres(conn):
        return "ON CONFLICT DO NOTHING"
    return ""

def init_db():
    """
    Inicializa la base de datos.
    Nota: Para Supabase, se recomienda correr el script SQL manualmente o adaptar este script.
    Aquí mantenemos la lógica de SQLite por compatibilidad.
    """
    conn = get_connection()
    # Identificar si es SQLite o Postgres para saber cómo ejecutar el script
    is_postgres = hasattr(conn, 'dsn') # psycopg2 tiene dsn
    
    schema_to_load = SCHEMA_FILE_POSTGRES if is_postgres else SCHEMA_FILE_SQLITE
    
    if not os.path.exists(schema_to_load):
        print(f"Error: No se encuentra el archivo {schema_to_load}")
        return

    if conn:
        try:
            with open(schema_to_load, 'r', encoding='utf-8') as f:
                script = f.read()
                
            if is_postgres:
                # Postgres requiere cursor y commit explícito
                cur = conn.cursor()
                cur.execute(script)
                conn.commit()
                cur.close()
            else:
                # SQLite tiene executescript
                conn.executescript(script)
                
            print("✅ Base de datos inicializada correctamente.")
        except Exception as e:
            print(f"Error inicializando la estructura: {e}")
            print("✅ Base de datos inicializada correctamente.")
        except Exception as e:
            print(f"Error inicializando la estructura: {e}")
        finally:
            close_connection(conn)

def close_connection(conn):
    """
    Cierra la conexión SOLO si es SQLite (local).
    Si es Postgres (Supabase), la dejamos abierta porque está cacheada por Streamlit.
    """
    if conn:
        if not is_postgres(conn):
            conn.close()
