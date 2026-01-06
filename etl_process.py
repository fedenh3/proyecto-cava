import pandas as pd
import sqlite3
import re
import os
from datetime import datetime

from db_config import get_connection

# DB_NAME is now handled in db_config
EXCEL_FILE = "Estadísticas CAVA_v2_original.xlsx"

def get_db_connection():
    return get_connection()

def clean_database():
    """Clears data to allow re-running ETL without duplicates"""
    conn = get_db_connection()
    c = conn.cursor()
    # Orden inverso de dependencias para borrar
    tables = ["stats", "partidos", "jugadores", "rivales", "torneos", "arbitros", "tecnicos"]
    for table in tables:
        c.execute(f"DELETE FROM {table}") # Delete data, keep schema
        c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'") # Reset autoincrement
    conn.commit()
    conn.close()
    print("Base de datos limpiada preliminarmente.")

def extract_result(score_str):
    if not isinstance(score_str, str): return None, None
    score_str = score_str.strip()
    match = re.search(r"(\d+)\s*-\s*(\d+)", score_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def remove_accents(input_str):
    """Normalize string by removing accents"""
    if not input_str: return ""
    s = str(input_str)
    replacements = (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"),
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ñ", "N"),
        ("Ü", "U"), ("ü", "u")
    )
    for a, b in replacements:
        s = s.replace(a, b)
    return s

def db_norm(s): 
    """Normalize for DB search comparison"""
    return re.sub(r'[^A-Z0-9]', '', remove_accents(str(s)).upper())

def get_or_create_rival(conn, rival_name):
    if not rival_name or pd.isna(rival_name): return None
    rival_name = str(rival_name).strip().upper()
    c = conn.cursor()
    c.execute("SELECT id FROM rivales WHERE nombre = ?", (rival_name,))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO rivales (nombre) VALUES (?)", (rival_name,))
    conn.commit()
    return c.lastrowid

def get_or_create_torneo(conn, nombre_torneo, temporada):
    nombre_torneo = str(nombre_torneo).strip()
    temporada = str(temporada).strip()
    c = conn.cursor()
    c.execute("SELECT id FROM torneos WHERE nombre = ? AND temporada = ?", (nombre_torneo, temporada))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO torneos (nombre, temporada) VALUES (?, ?)", (nombre_torneo, temporada))
    conn.commit()
    return c.lastrowid

def get_or_create_jugador(conn, nombre, apellido, posicion=None):
    if not apellido or pd.isna(apellido): return None
    nombre = str(nombre).strip() if nombre and not pd.isna(nombre) else ""
    apellido = str(apellido).strip()
    posicion = str(posicion).strip() if posicion and not pd.isna(posicion) else "Desconocido"

    c = conn.cursor()
    # Check by Name + Surname
    c.execute("SELECT id FROM jugadores WHERE nombre = ? AND apellido = ?", (nombre, apellido))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO jugadores (nombre, apellido, posicion) VALUES (?, ?, ?)", (nombre, apellido, posicion))
    conn.commit()
    return c.lastrowid

def get_or_create_arbitro(conn, nombre):
    if not nombre or pd.isna(nombre): return None
    nombre = str(nombre).strip().upper()
    c = conn.cursor()
    c.execute("SELECT id FROM arbitros WHERE nombre = ?", (nombre,))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO arbitros (nombre) VALUES (?)", (nombre,))
    conn.commit()
    return c.lastrowid

def get_or_create_tecnico(conn, nombre):
    if not nombre or pd.isna(nombre): return None
    nombre = str(nombre).strip().upper()
    c = conn.cursor()
    c.execute("SELECT id FROM tecnicos WHERE nombre = ?", (nombre,))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO tecnicos (nombre) VALUES (?)", (nombre,))
    conn.commit()
    return c.lastrowid

def parse_date(date_val):
    """Try to parse date from various formats"""
    if pd.isna(date_val): return None
    # If it's already datetime
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    # If string
    s = str(date_val).strip()
    # Try formats
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except:
            pass
    return s # Return as string if fail

def migrate_matches(conn):
    print("--- Migrando Partidos ---")
    try:
        df_raw = pd.read_excel(EXCEL_FILE, sheet_name="Resultados", header=None, nrows=10)
    except:
        print("No se encontró hoja 'Resultados'")
        return

    header_idx = None
    for i, row in df_raw.iterrows():
        row_str = " ".join([str(x).upper() for x in row.values])
        if "RIVAL" in row_str or "RESULTADO" in row_str or "FECHA" in row_str:
            header_idx = i
            break
            
    if header_idx is None:
        print("No se encontró fila de encabezado en Resultados")
        return
        
    print(f"Encabezado de Resultados detectado en fila {header_idx}")
    df = pd.read_excel(EXCEL_FILE, sheet_name="Resultados", header=header_idx)

    # Clean headers
    df.columns = [str(c).upper().strip() for c in df.columns]
    
    # Rename standard columns if found
    rename_map = {}
    if "EQUIPO" in df.columns: rename_map["EQUIPO"] = "RIVAL"
    if "UNNAMED: 1" in df.columns: rename_map["UNNAMED: 1"] = "FECHA"
    
    df.rename(columns=rename_map, inplace=True)
    
    print(f"DEBUG RESULTADOS FINAL COLS: {df.columns.tolist()}")
    
    count = 0
    for index, row in df.iterrows():
        fecha_raw = row.get("FECHA", None)
        fecha_str = parse_date(fecha_raw)
        
        # Infer Season from Torneo if available
        torneo_val = row.get("TORNEO", "Torneo Regular")
        if pd.isna(torneo_val): torneo_val = "Torneo Regular"
        
        temp_val = row.get("TEMPORADA", None)
        if pd.isna(temp_val):
            # Try to use Torneo as Season
            # 1. Look for 4 digits (e.g. 2019)
            m4 = re.search(r"\d{4}", str(torneo_val))
            
            # 2. Look for 2 digits at end or preceded by space (e.g. APERTURA 19, CLAUSURA 20)
            m2 = re.search(r"\b(1[5-9]|2[0-9])\b", str(torneo_val))
            
            if m4:
                 temp_val = m4.group(0)
            elif m2:
                 # Infer 20xx
                 temp_val = "20" + m2.group(1)
            else:
                 habitual_year = "2024"
                 if fecha_str:
                     try:
                         habitual_year = str(datetime.strptime(fecha_str, "%Y-%m-%d").year)
                     except: pass
                 temp_val = habitual_year

        id_torneo = get_or_create_torneo(conn, torneo_val, temp_val)
        
        rival_val = row.get("RIVAL", "Libre")
        id_rival = get_or_create_rival(conn, rival_val)
        
        resultado_val = row.get("RESULTADO", "")
        gf, gc = extract_result(str(resultado_val))
        
        cond_val = row.get("CONDICION", "L")
        if cond_val not in ['L', 'V', 'N']: cond_val = 'L'
        
        c = conn.cursor()
        dt_val = row.get("DT", None)
        id_dt = get_or_create_tecnico(conn, dt_val)
        
        arb_val = row.get("ÁRBITRO", None) 
        if arb_val is None: arb_val = row.get("ARBITRO", None)
        id_arb = get_or_create_arbitro(conn, arb_val)
        
        try:
            c.execute("""
                INSERT OR IGNORE INTO partidos (fecha, id_torneo, id_rival, condicion, goles_favor, goles_contra, id_arbitro, id_tecnico)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, id_torneo, id_rival, cond_val, gf, gc, id_arb, id_dt))
            count += 1
        except sqlite3.Error as e:
            print(f"Error insertando partido {fecha_str} vs {rival_val}: {e}")
    
    conn.commit()
    print(f"Migrados {count} partidos.")

def migrate_plantel(conn):
    print("--- Migrando Plantel y Presencias ---")
    xls = pd.ExcelFile(EXCEL_FILE)
    
    plantel_sheets = [s for s in xls.sheet_names if "PLANTEL" in s.upper()]
    
    total_presencias = 0
    
    RIVAL_MAPPING = {
        "CTRAL. BALLESTER": "CENTRAL BALLESTER",
        "CTRO ESPAÑOL": "CENTRO ESPAÑOL",
        "JUV. UNIDA": "JUVENTUD UNIDA",
        "ARG ROSARIO": "ARGENTINO ROSARIO",
        "ARG. DE QUILMES": "ARG. DE QUILMES",
        "DEP. PARAGUAYO": "DEP. PARAGUAYO",
        "CAMIONEROS": "CAMIONEROS",
        "YUPANQUI": "YUPANQUI",
        "LUJÁN": "LUJÁN",
        "ATLAS": "ATLAS",
        "CAÑUELAS": "CAÑUELAS",
        "ESTRELLA DEL SUR": "ESTRELLA DEL SUR",
        "SP. BARRACAS": "SP. BARRACAS"
    }
    
    for sheet in plantel_sheets:
        print(f"Procesando hoja: {sheet}")
        year_match = re.search(r"(\d{4})", sheet)
        sheet_year = year_match.group(1) if year_match else "2024"
        
        # 1. Read first few rows to understand structure
        df_headers = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=5)
        
        # Find the row with "APELLIDO" to serve as the Data Header
        data_header_idx = None
        for i, row in df_headers.iterrows():
            row_str = " ".join([str(x).upper() for x in row.values])
            if "APELLIDO" in row_str and "NOMBRE" in row_str:
                data_header_idx = i
                break
        
        if data_header_idx is None:
            print(f"Skipping {sheet}, no header row found.")
            continue
            
        print(f"  > Data Header found at row {data_header_idx}")
        # print(f"DEBUG HEADERS ({sheet}):\n{df_headers.iloc[:data_header_idx+1].to_string()}")
        
        match_info_row_idx = data_header_idx - 1 if data_header_idx > 0 else 0
        match_row_values = df_headers.iloc[match_info_row_idx].values
        
        # Load main data
        df = pd.read_excel(xls, sheet_name=sheet, header=data_header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        
        col_apellido = next((c for c in df.columns if "APELLIDO" in c.upper()), None)
        col_nombre = next((c for c in df.columns if "NOMBRE" in c.upper()), None)
        
        if not col_apellido: continue
        
        # Map DataFrame Column Index -> Match ID
        col_map = {}
        
        # Forward Fill match headers to handle merged cells
        filled_headers = []
        last_header = None
        for i, val in enumerate(match_row_values):
            val_str = str(val).strip()
            if val_str not in ["nan", "None", ""] and ("FECHA" in val_str.upper() or "VS" in val_str.upper()):
                last_header = val_str
                filled_headers.append(val_str)
            elif last_header:
                 filled_headers.append(last_header)
            else:
                 filled_headers.append(val_str)

        match_cnt = 0
        c = conn.cursor()
        
        # Cache Rivals from DB
        c.execute("SELECT id, nombre FROM rivales")
        all_rivals = c.fetchall()

        for col_idx in range(len(df.columns)):
            if col_idx < len(filled_headers):
                header_val = str(filled_headers[col_idx]).strip()
                
                # Check match header
                if "FECHA" in header_val.upper() or "VS" in header_val.upper():
                    # Parse Match
                    parts = header_val.upper().split("VS")
                    rival_part = parts[1].strip() if len(parts) > 1 else header_val
                    
                     # Extract Score if present (e.g. 2-1)
                    score_match = re.search(r"(\d+)-(\d+)", header_val)
                    gf_header, gc_header = None, None
                    if score_match:
                        try:
                            gf_header = int(score_match.group(1))
                            gc_header = int(score_match.group(2))
                        except: pass

                    # Clean Rival Part
                    rival_part = re.sub(r"\(\s*[LVN]\s*\)", "", rival_part) # Remove (L), (V)
                    rival_part = re.sub(r"\d+-\d+", "", rival_part) # Remove score 1-2
                    rival_part = re.sub(r"FECHA\s*\d+[:\s]*", "", rival_part) # Remove "FECHA 1:"
                    rival_part = rival_part.strip()
                    
                    if rival_part in RIVAL_MAPPING:
                         rival_part = RIVAL_MAPPING[rival_part]

                    rival_norm_clean = remove_accents(rival_part).replace(".", "").replace("  ", " ")
                    cand_clean = db_norm(rival_part)
                    
                    match_id = None
                    
                    target_rival_ids = []
                    for rid, rname in all_rivals:
                         if cand_clean in db_norm(rname) or db_norm(rname) in cand_clean:
                             target_rival_ids.append(rid)
                    
                    if target_rival_ids:
                         placeholders = ','.join('?' for _ in target_rival_ids)
                         q = f"""
                            SELECT p.id, t.temporada, r.nombre, p.goles_favor, p.goles_contra
                            FROM partidos p
                            JOIN torneos t ON p.id_torneo = t.id
                            JOIN rivales r ON p.id_rival = r.id
                            WHERE p.id_rival IN ({placeholders})
                         """
                         c.execute(q, target_rival_ids)
                         potential_matches = c.fetchall()
                         
                         for mid, mseason, mname, mgf, mgc in potential_matches:
                             # Strategy 1: Match by Score (Strong signal)
                             if gf_header is not None and gc_header is not None:
                                 if mgf == gf_header and mgc == gc_header:
                                      match_id = mid
                                      break
                             
                             # Strategy 2: Match by Year (Fallback)
                             if str(sheet_year) in str(mseason):
                                 match_id = mid
                                 break
                    
                    if match_id:
                        col_map[col_idx] = match_id
    
        print(f"  > Vinculadas {len(set(col_map.values()))} columnas de stats a partidos distintos: {len(col_map)} columnas totales mapped.")
        
        # --- GOALS EXTRACTION ---
        goles_col_idx = None
        for c in df.columns:
            if str(c).upper().strip() in ["GOLES", "GOL", "G"]:
                goles_col_idx = c
                # print(f"  > Columna de Goles detectda: {c}")
                break

        count_presencias = 0
        for index, row in df.iterrows():
            nombre = row.get("NOMBRE")
            apellido = row.get("APELLIDO")
            
            if pd.isna(nombre) and pd.isna(apellido):
                 continue
            
            if pd.notna(nombre) or pd.notna(apellido):
                pid = get_or_create_jugador(conn, nombre, apellido)
                
                # --- Update Initial Goals ---
                if goles_col_idx:
                    try:
                        gval = row[goles_col_idx]
                        if pd.notna(gval):
                            ival = int(float(gval))
                            cur = conn.cursor()
                            cur.execute("UPDATE jugadores SET goles_iniciales = goles_iniciales + ? WHERE id = ?", (ival, pid))
                    except: pass

                # Iterate columns for matches
                for col_idx, mid in col_map.items():
                    val = row.iloc[col_idx]
                    
                    minutes = 0
                    titular = 0
                    
                    val_str = str(val).strip().upper()
                    if val_str in ["NAN", "NONE", ""]:
                        continue
                    
                    if val_str.isdigit():
                        minutes = int(val_str)
                        if minutes > 45: titular = 1
                    elif val_str == 'X':
                        minutes = 90
                        titular = 1
                    else:
                        continue
                    
                    if minutes > 0:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                INSERT OR REPLACE INTO stats (id_partido, id_jugador, minutos_jugados, es_titular, goles_marcados, goles_recibidos, amarillas, rojas)
                                VALUES (?, ?, ?, ?, 0, 0, 0, 0)
                            """, (mid, pid, minutes, titular))
                            count_presencias += 1
                        except sqlite3.Error as e:
                            pass
                
                conn.commit()
            
        print(f"--- Hoja procesada. Total stats cargadas: {count_presencias} ---")

def main():
    clean_database()
    conn = get_db_connection()
    try:
        migrate_matches(conn)
        migrate_plantel(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
