import pandas as pd
import sqlite3
import re
import os
from datetime import datetime
from db_config import get_connection, get_placeholder, get_ignore_clause, get_conflict_clause, is_postgres

# Nombre del archivo Excel principal de donde se extraen los datos
EXCEL_FILE = "Estadísticas CAVA_v3_original.xlsx"

def date_converter(val):
    """
    Convierte diferentes formatos de fecha del Excel a un formato estándar YYYY-MM-DD.
    Si el valor no es una fecha válida, lo devuelve como string o None.
    """
    if pd.isna(val): return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    # Lista de valores inválidos conocidos
    if s in ['--------', '-', 'nan', 'NaT']: return None
    
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except: pass
    # Si no coincide con ningún formato, retornamos None para que se guarde como NULL en la DB
    return None

def clean_database():
    """
    Borra todo el contenido de las tablas de la base de datos para realizar una
    carga limpia desde cero. También reinicia los contadores de ID.
    """
    conn = get_connection()
    c = conn.cursor()
    tables = ["stats", "partidos", "jugadores", "rivales", "torneos", "arbitros", "tecnicos", "posiciones"]
    
    if is_postgres(conn):
        # Postgres: TRUNCATE vacía tablas y reinicia secuencias en cascada
        try:
            # Desactivar constraints temporalmente si fuera necesario, pero CASCADE suele bastar
            for table in tables:
                try:
                    c.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                except Exception as e:
                    print(f"Error truncating {table}: {e}")
            conn.commit()
        except Exception as e:
            print(f"Error general limpiando DB Postgres: {e}")
            conn.rollback()
    else:
        # SQLite: DELETE FROM + sqlite_sequence
        for table in tables:
            try:
                c.execute(f"DELETE FROM {table}")
                c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            except: pass
        conn.commit()
        
    conn.close()
    print("Base de datos limpia para carga desde V3.")

def migrate_posiciones(conn):
    print("Migrando Posiciones...")
    df = pd.read_excel(EXCEL_FILE, sheet_name="Jugadores", header=1)
    df = df[df['APELLIDO'].notna() & (df['APELLIDO'] != 'APELLIDO')]
    posiciones = df['POS'].dropna().unique()
    
    c = conn.cursor()
    ph = get_placeholder(conn)
    ignore = get_ignore_clause(conn)
    conflict = get_conflict_clause(conn)
    
    for pos in posiciones:
        c.execute(f"INSERT {ignore} INTO posiciones (nombre) VALUES ({ph}) {conflict}", (str(pos).strip().upper(),))
    conn.commit()

def migrate_jugadores(conn):
    print("Migrando Jugadores desde V3...")
    df = pd.read_excel(EXCEL_FILE, sheet_name="Jugadores", header=1)
    df = df[df['APELLIDO'].notna()]
    
    c = conn.cursor()
    ph = get_placeholder(conn)
    
    c.execute("SELECT id, nombre FROM posiciones")
    pos_map = {name: id for id, name in c.fetchall()}
    
    for _, row in df.iterrows():
        id_excel = str(row.get('ID_Jugador', '')).strip()
        ap = str(row['APELLIDO']).strip()
        nom = str(row['NOMBRE']).strip() if pd.notna(row['NOMBRE']) else ""
        pos_str = str(row['POS']).strip().upper() if pd.notna(row['POS']) else None
        if pos_str == 'NAN': pos_str = None
        id_pos = pos_map.get(pos_str)
        
        f_debut = date_converter(row.get('fecha debut'))
        r_debut = str(row.get('RIVAL debut', '')).strip()
        res_debut = str(row.get('RESULTADO debut', '')).strip()
        nota = str(row.get('nota', '')).strip()
        comentarios = str(row.get('comentarios guido franck', '')).strip()
        
        com_final = comentarios
        if nota and nota != 'nan' and nota != '-':
            com_final = f"{comentarios} | Nota: {nota}".strip(" | ")
        
        g_val = row.get('GOLES', 0)
        if pd.isna(g_val): g_val = 0
        try:
            g_int = int(float(g_val))
            g_marcados = g_int if g_int > 0 else 0
            g_recibidos = abs(g_int) if g_int < 0 else 0
        except:
            g_marcados, g_recibidos = 0, 0
        
        def to_i(v): 
            try: return int(float(v)) if pd.notna(v) else 0
            except: return 0

        # Para Postgres, id_excel es UNIQUE, podríamos tener conflicto si re-corremos
        # pero clean_database() ya limpió todo.
        c.execute(f"""
            INSERT INTO jugadores (
                id_excel, nombre, apellido, id_posicion, 
                pj_inicial, goles_marcados_inicial, goles_recibidos_inicial, 
                asistencias_inicial, amarillas_inicial, rojas_inicial,
                titular_inicial, suplente_inicial,
                fecha_debut, rival_debut, resultado_debut, comentarios_gf
            ) VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
        """, (
            id_excel, nom, ap, id_pos,
            to_i(row.get('PJ')), g_marcados, g_recibidos,
            to_i(row.get('ASISTENCIAS')), to_i(row.get('AMARILLAS')), to_i(row.get('ROJAS')),
            to_i(row.get('TITULAR')), to_i(row.get('SUPLENTE')),
            f_debut, r_debut, res_debut, com_final
        ))
    conn.commit()

def migrate_resultados(conn):
    print("Migrando Resultados (Partidos detallados)...")
    df = pd.read_excel(EXCEL_FILE, sheet_name="Resultados", header=1)
    
    c = conn.cursor()
    ph = get_placeholder(conn)
    ignore = get_ignore_clause(conn)
    conflict = get_conflict_clause(conn)

    for _, row in df.iterrows():
        rival_str = str(row.get('EQUIPO', '')).strip().upper()
        if not rival_str or rival_str == 'NAN' or rival_str == 'EQUIPO': continue
        
        c.execute(f"INSERT {ignore} INTO rivales (nombre) VALUES ({ph}) {conflict}", (rival_str,))
        c.execute(f"SELECT id FROM rivales WHERE nombre={ph}", (rival_str,))
        rid = c.fetchone()[0]
        
        t_nombre = str(row.get('TORNEO', 'Campeonato')).strip()
        m4 = re.search(r"(\d{4})", t_nombre)
        m2 = re.search(r"\b(\d{2})$| (\d{2})\b", t_nombre)
        
        if m4: t_temp = m4.group(1)
        elif m2:
            año_corto = m2.group(1) or m2.group(2)
            t_temp = "20" + año_corto
        else: t_temp = "Desconocida"
        
        # Insertamos Torneo
        c.execute(f"INSERT {ignore} INTO torneos (nombre, temporada) VALUES ({ph},{ph}) {conflict}", (t_nombre, t_temp))
        c.execute(f"SELECT id FROM torneos WHERE nombre={ph} AND temporada={ph}", (t_nombre, t_temp))
        tid = c.fetchone()[0]
        
        # Árbitros
        arb_nom = str(row.get('ÁRBITRO', '')).strip()
        aid = None
        if arb_nom and arb_nom != 'nan' and arb_nom != '--------':
            c.execute(f"INSERT {ignore} INTO arbitros (nombre) VALUES ({ph}) {conflict}", (arb_nom,))
            c.execute(f"SELECT id FROM arbitros WHERE nombre={ph}", (arb_nom,))
            try: aid = c.fetchone()[0]
            except: pass

        # DTs
        dt_nom = str(row.get('DT', '')).strip()
        tecid = None
        if dt_nom and dt_nom != 'nan' and dt_nom != '--------':
            c.execute(f"INSERT {ignore} INTO tecnicos (nombre) VALUES ({ph}) {conflict}", (dt_nom,))
            c.execute(f"SELECT id FROM tecnicos WHERE nombre={ph}", (dt_nom,))
            try: tecid = c.fetchone()[0]
            except: pass

        res_str = str(row.get('RESULTADO', '0-0'))
        match = re.search(r"(\d+)-(\d+)", res_str)
        gf, gc = (int(match.group(1)), int(match.group(2))) if match else (0,0)
        
        cond = str(row.get('local/visitante', 'L')).strip().upper()
        nro_fecha = str(row.get('nro_fecha', row.get('fecha', ''))).strip()
        if nro_fecha == 'nan': nro_fecha = ''
        
        def clean_val(v): return int(v) if pd.notna(v) and str(v).replace('.','').isdigit() else 0
        def clean_txt(v): return str(v).strip() if pd.notna(v) and str(v) != '--------' else None

        c.execute(f"""
            INSERT INTO partidos (
                nro_fecha, id_torneo, id_rival, id_arbitro, id_tecnico, 
                condicion, goles_favor, goles_contra, goles_detalle,
                rojas_cava, rojas_rival, expulsados_nombres,
                penales_favor, penales_favor_detalle,
                penales_contra, penales_contra_detalle
            ) VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
        """, (
            nro_fecha, tid, rid, aid, tecid,
            cond[0] if cond else 'L', gf, gc, clean_txt(row.get('GOLES')),
            clean_val(row.get('ROJAS VICTORIANO')), clean_val(row.get('ROJAS RIVALES')), 
            clean_txt(row.get('ROJAS')),
            clean_val(row.get('PENALES A FAVOR')), clean_txt(row.get('DESCRIPCIÓN PENALES A/F')),
            clean_val(row.get('PENALES EN CONTRA')), clean_txt(row.get('DESCRIPCIÓN PENALES E/C'))
        ))
    conn.commit()

def migrate_stats(conn):
    print("Migrando Estadísticas (Planteles desde V3)...")
    xls = pd.ExcelFile(EXCEL_FILE)
    sheets = [s for s in xls.sheet_names if "PLANTEL" in s.upper()]
    
    c = conn.cursor()
    ph = get_placeholder(conn)
    ignore = get_ignore_clause(conn)
    conflict = get_conflict_clause(conn)
    
    c.execute("SELECT id, nombre, apellido FROM jugadores")
    jug_db = {(row[1].upper(), row[2].upper()): row[0] for row in c.fetchall()}

    for sheet in sheets:
        print(f"  Procesando {sheet}...")
        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=10)
        header_row = 0
        for i, row in df_raw.iterrows():
            if "APELLIDO" in str(row.values).upper():
                header_row = i
                break
        
        match_headers_row = header_row - 1
        df_matches = pd.read_excel(xls, sheet_name=sheet, header=None, skiprows=match_headers_row, nrows=1)
        df_data = pd.read_excel(xls, sheet_name=sheet, header=header_row)
        
        batch_data = [] # Inicializamos lista para lote
        filled_matches = []
        curr = None
        for val in df_matches.values[0]:
            v_str = str(val).upper()
            if "FECHA" in v_str or "VS" in v_str:
                curr = v_str
            filled_matches.append(curr)
            
        col_to_match = {}
        for idx, m_header in enumerate(filled_matches):
            if not m_header: continue
            
            parts = m_header.split("VS")
            rival_part = parts[1].strip() if len(parts) > 1 else m_header
            rival_part = re.sub(r"\(.*\)", "", rival_part).strip() 
            rival_part = re.sub(r"\d+-\d+", "", rival_part).strip() 
            rival_part = re.sub(r"FECHA\s+\d+", "", rival_part).strip()
            
            score_match = re.search(r"(\d+)-(\d+)", m_header)
            gf_h, gc_h = (int(score_match.group(1)), int(score_match.group(2))) if score_match else (None, None)
            
            c.execute("SELECT p.id, r.nombre, p.goles_favor, p.goles_contra FROM partidos p JOIN rivales r ON p.id_rival = r.id")
            for m_id, r_name, p_gf, p_gc in c.fetchall():
                if rival_part in r_name.upper() or r_name.upper() in rival_part:
                    if gf_h is not None:
                        if p_gf == gf_h and p_gc == gc_h:
                            col_to_match[idx] = m_id
                            break
                    else:
                        col_to_match[idx] = m_id
        
        for _, row in df_data.iterrows():
            nom = str(row.get('NOMBRE', '')).strip().upper()
            ape = str(row.get('APELLIDO', '')).strip().upper()
            jid = jug_db.get((nom, ape))
            if not jid: continue
            
            for col_idx, mid in col_to_match.items():
                if col_idx >= len(row): continue
                val = row.iloc[col_idx]
                if pd.isna(val) or str(val).strip() == "": continue
                
                v_str = str(val).strip().upper()
                mins = 90 if v_str == 'X' else (int(v_str) if v_str.isdigit() else 0)
                if mins >= 0:
                    # Agregamos a la lista para insertar en lote
                    # Postgres requiere True/False para columnas booleanas, no 1/0
                    is_starter = (mins > 45)
                    batch_data.append((mid, jid, mins, is_starter))
        
        if batch_data:
            print(f"    Insertando lote de {len(batch_data)} registros...")
            
            # Determinamos si estamos en Postgres (para ajuste de tipos)
            is_pg = is_postgres(conn)
            if is_pg:
                print("    [DEBUG] Modo Postgres activado para inserción.")
            
            # Ajuste final de tipos para garantizar compatibilidad
            final_batch = []
            for (mid, jid, mins, is_start_bool) in batch_data:
                # Si es Postgres enviamos True/False nativo, si es SQLite enviamos 1/0
                val_titular = bool(is_start_bool) if is_pg else (1 if is_start_bool else 0)
                final_batch.append((mid, jid, mins, val_titular))

            try:
                # Query estándar
                c.executemany(f"""
                    INSERT {ignore} INTO stats (id_partido, id_jugador, minutos_jugados, es_titular)
                    VALUES ({ph},{ph},{ph},{ph}) {conflict}
                """, final_batch)
                conn.commit() 
            except Exception as e:
                print(f"Error en batch insert: {e}")
                conn.rollback() 
        else:
            print(f"    ⚠️ No se encontraron datos para insertar en {sheet} (Batch vacío).")
                
    conn.commit()
    # Verificación final
    try:
        c.execute("SELECT count(*) FROM stats")
        count = c.fetchone()[0]
        print(f"✅ Migración de Stats finalizada. Total registros en DB: {count}")
    except: pass

def parse_goals_from_results(conn):
    print("Parsing goleadores detallados desde Resultados...")
    c = conn.cursor()
    ph = get_placeholder(conn)
    
    c.execute("SELECT id, goles_favor, goles_detalle FROM partidos WHERE goles_favor > 0")
    matches = c.fetchall()
    
    c.execute("SELECT id, apellido FROM jugadores")
    jugadores = {row[1].upper(): row[0] for row in c.fetchall()}
    
    for mid, gf, detalle in matches:
        if not detalle or detalle == '--------': continue
        
        parts = re.split(r' y |,|\s-\s', detalle)
        for part in parts:
            part = part.strip().upper()
            if not part: continue
            
            count = 1
            m = re.search(r'\(X(\d+)\)', part)
            if m:
                count = int(m.group(1))
                part = re.sub(r'\(X\d+\)', '', part).strip()
            
            found_jid = None
            for apellido, jid in jugadores.items():
                if apellido in part:
                    found_jid = jid
                    break
            
            if found_jid:
                # Actualizamos la estadística del jugador para ese partido
                c.execute(f"SELECT 1 FROM stats WHERE id_partido={ph} AND id_jugador={ph}", (mid, found_jid))
                if not c.fetchone():
                    c.execute(f"INSERT INTO stats (id_partido, id_jugador, goles_marcados) VALUES ({ph},{ph},{ph})", 
                              (mid, found_jid, count))
                else:
                    c.execute(f"UPDATE stats SET goles_marcados = {ph} WHERE id_partido={ph} AND id_jugador={ph}",
                              (count, mid, found_jid))
    conn.commit()

def seed_admin_user(conn):
    """
    Crea un usuario administrador por defecto si no existe.
    """
    print("Creando usuario admin por defecto...")
    c = conn.cursor()
    ph = get_placeholder(conn)
    ignore = get_ignore_clause(conn)
    conflict = get_conflict_clause(conn)
    
    # Usuario: admin, Pass: cava2024
    c.execute(f"INSERT {ignore} INTO usuarios (username, password, rol, nombre) VALUES ({ph},{ph},'admin','Administrador') {conflict}", 
              ('admin', 'cava2024'))
    conn.commit()

def main():
    clean_database()
    conn = get_connection()
    try:
        migrate_posiciones(conn)
        migrate_jugadores(conn)
        migrate_resultados(conn)
        migrate_stats(conn)
        parse_goals_from_results(conn)
        seed_admin_user(conn)
        print("✅ ETL Finalizado con éxito (Goles detallados incluidos).")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
