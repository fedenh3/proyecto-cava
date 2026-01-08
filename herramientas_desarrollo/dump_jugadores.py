import pandas as pd

FILE = "Estadísticas CAVA_v2_original.xlsx"
SHEET = "Jugadores"

print(f"--- DUMP DETALLADO DE HOJA: {SHEET} ---")

try:
    # Leer raw total sin headers para no asumir nada
    df = pd.read_excel(FILE, sheet_name=SHEET, header=None).head(20)
    
    # Imprimir fila por fila
    for i, row in df.iterrows():
        # Reemplazar NaNs por "-" para ver limpio
        vals = [str(v) if pd.notna(v) else "-" for v in row.values]
        print(f"Fila {i:02d} | {' | '.join(vals)}")

except Exception as e:
    print(f"Error: {e}")
