import pandas as pd

# Nombre del archivo de entrada
input_file = "CSS - 0125_.csv"
# Nombre del archivo de salida
output_file = input_file.replace(".csv", ".xlsx")

# Leer el archivo CSV con codificación UTF-8 y separador de comas
df = pd.read_csv(input_file, sep=",", encoding="utf-8", dtype=str, engine="python")

# Guardar en un archivo Excel con el mismo nombre
df.to_excel(output_file, index=False, engine="openpyxl")

print(f"Archivo convertido correctamente: {output_file}")



