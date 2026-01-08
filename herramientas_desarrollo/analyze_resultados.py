import pandas as pd

FILE = "Estadísticas CAVA_v3_original.xlsx"
SHEET = "Resultados"

print(f"--- ANALIZANDO HOJA: {SHEET} ---")

try:
    # 1. Ver qué hay en las primeras filas (incluyendo posibles headers decorativos)
    df_preview = pd.read_excel(FILE, sheet_name=SHEET, header=None).head(10)
    print("Primeras 10 filas (Raw):")
    for i, row in df_preview.iterrows():
        vals = [str(v) if pd.notna(v) else "-" for v in row.values]
        print(f"Fila {i:02d} | {' | '.join(vals)}")

    # 2. Intentar leer con header=1 como hicimos en Jugadores
    df = pd.read_excel(FILE, sheet_name=SHEET, header=1)
    print("\nColumnas detectadas (header=1):")
    print(df.columns.tolist())
    
    print("\nResumen de Atributos:")
    print(f"Total de partidos: {len(df.dropna(subset=['RIVAL']))}")
    
    # 3. Ver calidad de datos
    print("\nTipos de datos detectados:")
    print(df.dtypes)
    
except Exception as e:
    print(f"Error analizando {SHEET}: {e}")
