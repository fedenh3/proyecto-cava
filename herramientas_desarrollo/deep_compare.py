import pandas as pd

v2_file = "Estadísticas CAVA_v2_original.xlsx"
v3_file = "Estadísticas CAVA_v3_original.xlsx"

def deep_compare(file1, file2):
    try:
        xls1 = pd.ExcelFile(file1)
        xls2 = pd.ExcelFile(file2)
        
        common_sheets = set(xls1.sheet_names) & set(xls2.sheet_names)
        
        print(f"--- COMPARACIÓN DE DATOS (V2 vs V3) ---")
        
        for sheet in common_sheets:
            print(f"\nSolapa: {sheet}")
            # Cargamos datos tratando de saltar encabezados decorativos si es Jugadores
            if sheet == "Jugadores":
                df2 = pd.read_excel(file1, sheet_name=sheet, header=1)
                df3 = pd.read_excel(file2, sheet_name=sheet, header=1)
            else:
                df2 = pd.read_excel(file1, sheet_name=sheet)
                df3 = pd.read_excel(file2, sheet_name=sheet)
            
            if len(df2) != len(df3):
                print(f"  AVISO: Diferente cantidad de filas. V2: {len(df2)} | V3: {len(df3)}")
            
            # Comparar Goles de Jugadores específicamente
            if sheet == "Jugadores":
                # Buscamos a Ábalos como muestra
                a2 = df2[df2['APELLIDO'] == 'ÁBALOS']['GOLES'].values
                a3 = df3[df3['APELLIDO'] == 'ÁBALOS']['GOLES'].values
                if len(a2) > 0 and len(a3) > 0:
                    if a2[0] != a3[0]:
                        print(f"  DIFERENCIA: Goles de Ábalos -> V2: {a2[0]} | V3: {a3[0]}")
                    else:
                        print("  Los goles de los jugadores principales coinciden.")
            
            # Comparar última fila de Resultados
            if sheet == "Resultados":
                last2 = df2.iloc[-1].to_dict()
                last3 = df3.iloc[-1].to_dict()
                if last2 != last3:
                    print("  DIFERENCIA en últimos partidos:")
                    print(f"    V2 última fila: {last2.get('RIVAL', 'N/A')} - {last2.get('RESULTADO', 'N/A')}")
                    print(f"    V3 última fila: {last3.get('RIVAL', 'N/A')} - {last3.get('RESULTADO', 'N/A')}")
                else:
                    print("  Los resultados de los últimos partidos coinciden.")

    except Exception as e:
        print(f"Error en comparación profunda: {e}")

deep_compare(v2_file, v3_file)
