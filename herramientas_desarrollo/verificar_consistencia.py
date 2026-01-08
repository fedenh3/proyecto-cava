import pandas as pd
import re

FILE = "Estadísticas CAVA_v3_original.xlsx"

def check_consistency():
    # 1. Traer totales de la hoja Jugadores
    df_jug = pd.read_excel(FILE, sheet_name="Jugadores", header=1)
    # Buscamos a Coselli 
    coselli_row = df_jug[df_jug['APELLIDO'].str.contains('COSELLI', na=False, case=False)].iloc[0]
    total_pj_excel = coselli_row['PJ']
    total_goles_excel = coselli_row['GOLES']
    
    print(f"--- DATOS DE COSELLI EN HOJA 'JUGADORES' ---")
    print(f"PJ Totales: {total_pj_excel}")
    print(f"Goles Totales: {total_goles_excel}")
    
    # 2. Contar presencias en todas las hojas de PLANTEL
    xls = pd.ExcelFile(FILE)
    sheets = [s for s in xls.sheet_names if "PLANTEL" in s.upper()]
    count_pj = 0
    
    for s in sheets:
        df_p = pd.read_excel(FILE, sheet_name=s, header=None)
        # Buscar la fila de Coselli
        for i, row in df_p.iterrows():
            if 'COSELLI' in str(row.values).upper():
                # Contar cuántas 'X' o números hay en esa fila (empezando desde la columna E aprox)
                vals = [v for v in row.values[4:] if pd.notna(v) and str(v).strip() != ""]
                count_pj += len(vals)
                break
                
    print(f"\n--- DATOS CALCULADOS DESDE HOJAS 'PLANTEL' ---")
    print(f"Suma de presencias (X/Minutos): {count_pj}")
    
    # 3. Analizar goles en Hoja Resultados
    df_res = pd.read_excel(FILE, sheet_name="Resultados", header=1)
    count_goles = 0
    for val in df_res['GOLES'].dropna():
        if 'COSELLI' in str(val).upper():
            # Buscar patrones tipo (x2), (x3)
            m = re.search(r"COSELLI\s*\(X(\d+)\)", str(val).upper())
            if m:
                count_goles += int(m.group(1))
            else:
                # Si solo aparece el nombre, es 1 gol (o 2 si aparece dos veces en la frase)
                count_goles += str(val).upper().count('COSELLI')
                
    print(f"\n--- DATOS CALCULADOS DESDE HOJA 'RESULTADOS' ---")
    print(f"Suma de goles detectados en texto: {count_goles}")

if __name__ == "__main__":
    check_consistency()
