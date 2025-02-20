import pandas as pd
import csv
import re

# Nombre del archivo de entrada
input_file = "CSS-0125_.csv"
# Nombre del archivo de salida
output_file = input_file.replace(".csv", ".xlsx")

# Leer el archivo línea por línea para limpiar las comillas incorrectas
cleaned_lines = []
with open(input_file, "r", encoding="utf-8") as file:
    for line in file:
        # Eliminar comillas dobles exteriores solo si la línea entera está entre comillas
        if line.startswith('"') and line.endswith('"\n'):
            line = line[1:-2] + "\n"  # Quita la primera y última comilla

        # Reemplazar comillas dobles internas por comillas simples
        line = re.sub(r'""', '"', line)

        # Agregar la línea limpiada a la lista
        cleaned_lines.append(line)

# Guardar el archivo temporalmente sin comillas incorrectas
temp_file = "temp_cleaned.csv"
with open(temp_file, "w", encoding="utf-8") as file:
    file.writelines(cleaned_lines)

# Detectar delimitador automático
with open(temp_file, "r", encoding="utf-8") as f:
    first_line = f.readline()
    delimiter = ";" if ";" in first_line else ","

# Leer el CSV limpio
df = pd.read_csv(temp_file, delimiter=delimiter, encoding="utf-8", quotechar='"', dtype=str)

# Reemplazar comas en valores numéricos por puntos (sin usar applymap)
df = df.map(lambda x: x.replace(",", ".") if isinstance(x, str) and re.fullmatch(r'\d{1,3}(?:\.\d{3})*,\d{2}', x) else x)

# ✅ Verificar si la columna "id_practica" existe y eliminar espacios en blanco
if "id_practica" in df.columns:
    df["id_practica"] = df["id_practica"].str.replace(" ", "", regex=False)

# Guardar en Excel
df.to_excel(output_file, index=False, engine="openpyxl")

print(f"✅ Archivo convertido correctamente: {output_file}")






