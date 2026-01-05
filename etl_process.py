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
        # Determine Year from Date if Temporada missing
        # If 'FECHA' is still missing (not mapped), try to find a date-like column?
        # For now assume rename worked.
        
        fecha_raw = row.get("FECHA", None)
        # Verify if fecha_raw is really a date or something else
        # Sometimes UNNAMED: 1 is empty?
        
        fecha_str = parse_date(fecha_raw)
        
        # Infer Season from Torneo if available
        torneo_val = row.get("TORNEO", "Torneo Regular")
        if pd.isna(torneo_val): torneo_val = "Torneo Regular"
        
        temp_val = row.get("TEMPORADA", None)
        if pd.isna(temp_val):
            # Try to use Torneo as Season if it looks like year (e.g. 2018/2019)
            if re.search(r"\d{4}", str(torneo_val)):
                 temp_val = str(torneo_val)
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
        # Extract DT and Arbitro
        dt_val = row.get("DT", None)
        id_dt = get_or_create_tecnico(conn, dt_val)
        
        arb_val = row.get("ÁRBITRO", None) 
        # Excel column has accent 'ÁRBITRO'
        # If not found, try without accent or other variations if rename failed?
        if arb_val is None: arb_val = row.get("ARBITRO", None)
        id_arb = get_or_create_arbitro(conn, arb_val)
        
        c = conn.cursor()
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

def find_match_id(conn, rival_name_partial, year_hint, match_date_hint=None):
    """
    Finds a match ID based on Rival name similar match and Year.
    This is the semantic linking part.
    """
    if not rival_name_partial: return None
    
    rival_clean = rival_name_partial.strip().upper()
    c = conn.cursor()
    
    # 1. Try to find Rival ID first
    # We select all rivals and check string inclusion because headers might be "CLAYPOLE" and DB "CLUB CLAYPOLE"
    c.execute("SELECT id, nombre FROM rivales")
    all_rivals = c.fetchall()
    
    param_rival_ids = []
    
    for rid, rname in all_rivals:
        # Simple fuzzy: check if one contains the other
        if rival_clean in rname or rname in rival_clean:
            param_rival_ids.append(rid)
            
    if not param_rival_ids:
        return None
        
    # 2. Find match with these rivals in the given year/season
    # We join with torneos to check season
    placeholders = ','.join('?' for _ in param_rival_ids)
    query = f"""
        SELECT p.id, t.temporada 
        FROM partidos p
        JOIN torneos t ON p.id_torneo = t.id
        WHERE p.id_rival IN ({placeholders})
    """
    c.execute(query, param_rival_ids)
    matches = c.fetchall()
    
    # Filter by year hint
    for mid, season in matches:
        if str(year_hint) in str(season):
            return mid
            
    return None

def migrate_plantel(conn):
    print("--- Migrando Plantel y Presencias ---")
    xls = pd.ExcelFile(EXCEL_FILE)
    
    plantel_sheets = [s for s in xls.sheet_names if "PLANTEL" in s.upper()]
    
    total_presencias = 0
    
    for sheet in plantel_sheets:
        print(f"Procesando hoja: {sheet}")
        year_match = re.search(r"(\d{4})", sheet)
        sheet_year = year_match.group(1) if year_match else "2024"
        
        # 1. Read first few rows to understand structure
        # We suspect Row 0 has Match Names (Fecha 1...) and Row 1 has Column Names (Apellido...)
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
        print(f"DEBUG HEADERS ({sheet}):\n{df_headers.iloc[:data_header_idx+1].to_string()}")
        
        # The row with match names is likely the one above data_header_idx, or the same if mixed.
        # Usually it is data_header_idx - 1
        match_info_row_idx = data_header_idx - 1 if data_header_idx > 0 else 0
        
        # Load the Match Info Row to parse match names
        match_row_values = df_headers.iloc[match_info_row_idx].values
        
        # Load main data
        df = pd.read_excel(xls, sheet_name=sheet, header=data_header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        
        col_apellido = next((c for c in df.columns if "APELLIDO" in c.upper()), None)
        col_nombre = next((c for c in df.columns if "NOMBRE" in c.upper()), None)
        
        if not col_apellido: continue
        
        # Map DataFrame Column Index -> Match ID
        # We iterate over columns by integer location to align with match_row_values
        col_map = {}
        
        # Align match_row_values (which might include empty cells due to merge) with df columns
        # Note: pandas read_excel with header=X might drop empty leading cols or shift? 
        # Usually checking columns by index is safer if we trust the alignment.
        
        # We assume df.shape[1] == len(match_row_values) approximately.
        # Actually, standard behavior: yes.
        
        match_cnt = 0
        for col_idx in range(len(df.columns)):
            # Get the header from the row above
            if col_idx < len(match_row_values):
                header_val = str(match_row_values[col_idx]).strip()
                
                # Check if this header looks like a match
                if "FECHA" in header_val.upper() or "VS" in header_val.upper():
                    # Parse Match
                    parts = header_val.upper().split("VS")
                    rival_part = parts[1].strip() if len(parts) > 1 else header_val
                    
                    # Clean Rival Part: remove (L), (V), results like 1-2
                    rival_part = re.sub(r"\(\s*[LVN]\s*\)", "", rival_part) # Remove (L), (V)
                    rival_part = re.sub(r"\d+-\d+", "", rival_part) # Remove score 1-2
                    rival_part = re.sub(r"FECHA\s*\d+[:\s]*", "", rival_part) # Remove "FECHA 1:"
                    rival_part = rival_part.strip()
        # Try to find match in DB
        rival_norm = rival_part.upper()
        year_val = sheet_year
        
        # --- CUSTOM MAPPING FOR TYPOS/ABBREVIATIONS ---
        RIVAL_MAPPING = {
            "CTRAL. BALLESTER": "CENTRAL BALLESTER",
            "CTRO ESPAÑOL": "CENTRO ESPAÑOL",
            "JUV. UNIDA": "JUVENTUD UNIDA",
            "ARG ROSARIO": "ARGENTINO ROSARIO",
            "ARG. DE QUILMES": "ARG. DE QUILMES", # db might be ARG.. or ARGENTINO
            "DEP. PARAGUAYO": "DEP. PARAGUAYO",
            "CAMIONEROS": "CAMIONEROS",
            "YUPANQUI": "YUPANQUI",
            "LUJÁN": "LUJÁN",
            "ATLAS": "ATLAS",
            "CAÑUELAS": "CAÑUELAS",
            "ESTRELLA DEL SUR": "ESTRELLA DEL SUR",
            "SP. BARRACAS": "SP. BARRACAS"
        }
        
        if rival_norm in RIVAL_MAPPING:
             rival_norm = RIVAL_MAPPING[rival_norm]
        
        # Also try simpler fuzzy normalization (remove periods)
        rival_norm_clean = rival_norm.replace(".", "").replace("  ", " ")

        match_id = None
        
        # 1. Exact Name + Year
        # We need a helper to search ID by Name+Year efficiently.
        # Ideally we loaded a catalog. For now, run query.
        
        # Try finding by name in DB
        # Warning: "temporada" in DB is usually "2024" or inferred. 
        # Match might belong to Torneo
        # Helper to normalize for DB search
        def db_norm(s): return re.sub(r'[^A-Z0-9]', '', str(s).upper())
        # Helper to normalize for DB search
        def db_norm(s): return re.sub(r'[^A-Z0-9]', '', str(s).upper())
        
        cand_clean = db_norm(rival_norm)
        
        # DEBUG: Specific check for Col 14 (Dep Paraguayo)
        if col_idx == 14:
             print(f"    [DEBUG COL 14] Header='{header_val}' Clean='{rival_norm}' Norm='{cand_clean}'")

        # We fetch ALL matches involving a rival that looks like this
        c = conn.cursor()
        c.execute("SELECT id, nombre FROM rivales")
        all_rivals = c.fetchall()
        
        target_rival_ids = []
        for rid, rname in all_rivals:
             if cand_clean in db_norm(rname) or db_norm(rname) in cand_clean:
                 target_rival_ids.append(rid)
        
        if target_rival_ids:
             placeholders = ','.join('?' for _ in target_rival_ids)
             q = f"""
                SELECT p.id, t.temporada, r.nombre
                FROM partidos p
                JOIN torneos t ON p.id_torneo = t.id
                JOIN rivales r ON p.id_rival = r.id
                WHERE p.id_rival IN ({placeholders})
             """
             c.execute(q, target_rival_ids)
             potential_matches = c.fetchall()
             
             # Filter by Year
             for mid, mseason, mname in potential_matches:
                 if str(year_val) in str(mseason):
                     match_id = mid
                     # print(f"    -> Linked {rival_norm} to Match {mid} ({mname}) in {mseason}")
                     break
        
        if match_id:
            col_map[col_idx] = match_id
    
    print(f"  > Vinculadas {len(col_map)} columnas de stats a partidos.")
    
    # --- GOALS EXTRACTION (Summary Column) ---
    # Find "GOLES" column idx
    goles_col_idx = None
    for c in df.columns:
        if str(c).upper().strip() in ["GOLES", "GOL", "G"]:
            goles_col_idx = c
            print(f"  > Columna de Goles detectda: {c}")
            break

    count_presencias = 0
    for index, row in df.iterrows():
        nombre = row.get("NOMBRE")
        apellido = row.get("APELLIDO")
        
        if pd.isna(nombre) and pd.isna(apellido):
             # print(f"Skipping row {index}: No Name/Surname")
             continue
             
        # Debug Abalos
        if "BALOS" in str(apellido).upper():
             print(f"    [DEBUG ROW] Processing {apellido} {nombre}. PID found? {get_or_create_jugador(conn, nombre, apellido)}")
        
        if pd.notna(nombre) or pd.notna(apellido): # Relax: allow one missing? No, user said name is there.
            pid = get_or_create_jugador(conn, nombre, apellido)
            pid = get_or_create_jugador(conn, nombre, apellido)
            
            # --- Update Initial Goals ---
            if goles_col_idx:
                try:
                    gval = row[goles_col_idx]
                    if pd.notna(gval):
                        ival = int(float(gval))
                        # Update player logic: accumulating or setting?
                        # Since we process multiple sheets, we should ADD.
                        # But wait, one player might be in multiple sheets.
                        # We should simple add `ival`.
                        cur = conn.cursor()
                        cur.execute("UPDATE jugadores SET goles_iniciales = goles_iniciales + ? WHERE id = ?", (ival, pid))
                except: pass

            # Iterate columns for matches
            for col_idx, mid in col_map.items():
                # Get value from row by integer index
                # data dataframe `df` has columns. `col_map` keys are integer indices of the original excel row (0-based)
                # We need to map `col_idx` to `df` column name or location.
                # `df` was created with `header=header_row`. 
                # The columns in `df` correspond to Excel columns.
                # `col_idx` comes from `df_headers` (raw top rows).
                # If header_row was e.g. 1, then df column 0 is Excel column 0.
                
                # Careful: Pandas generic column names if duplicate.
                # Let's use `iloc`.
                val = row.iloc[col_idx]
                
                minutes = 0
                titular = 0
                
                # Logic for values
                val_str = str(val).strip().upper()
                if val_str in ["NAN", "NONE", ""]:
                    continue
                
                if val_str.isdigit():
                    minutes = int(val_str)
                    if minutes > 45: titular = 1 # Heuristic
                    # If minutes is small (e.g. 16), likely substitute.
                    # Or maybe started and injured. Titular status is hard to know 100% without explicit marker.
                    # Usually "X" = 90 titular. Number = minutes played.
                    # If < 90, could be subbed in OR subbed out.
                    # Let's assume Titular implies started?
                    # The excel sometimes has "S" column or similar? User didn't specify.
                    # For now: > 0 minutes = played.
                    
                elif val_str == 'X':
                    minutes = 90
                    titular = 1
                else:
                    # Maybe "45'" or similar
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
                        print(f"Error insertando stats {pid} en partido {mid}: {e}")
            
            conn.commit()
            
    print(f"--- Hoja procesada. Total presencias cargadas: {count_presencias} ---")

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
