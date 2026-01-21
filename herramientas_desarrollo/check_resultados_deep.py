import pandas as pd

FILE = "Estadísticas CAVA_v3_original.xlsx"
df = pd.read_excel(FILE, sheet_name="Resultados", header=1)

print("--- EXAMEN DE COLUMNAS EN RESULTADOS ---")
for col in df.columns:
    sample = df[col].dropna().head(3).tolist()
    print(f"Columna: {col} | Ejemplo: {sample}")

# Verificar si hay alguna columna que parezca una fecha calendario
for col in df.columns:
    if "fecha" in col.lower() or "date" in col.lower():
        print(f"\nRevisando valores en '{col}':")
        print(df[col].head(10).tolist())
