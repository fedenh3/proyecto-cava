import pandas as pd

FILE = "Estadísticas CAVA_v3_original.xlsx"
df = pd.read_excel(FILE, sheet_name="Jugadores", header=1)
print("Columnas detectadas en Jugadores (header=1):")
print(df.columns.tolist())

print("\nPrimeras 2 filas de datos:")
print(df.head(2).to_string())
