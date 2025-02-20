import pandas as pd

# Nombre base del archivo
var = 'CSS - 0125'

# Leer el archivo CSV, omitiendo las primeras 2 líneas (que contienen encabezados)
df = pd.read_csv(var + '.csv', skiprows=2)

# Verificar si la columna "id_practica" existe en el DataFrame
if "id_practica" in df.columns:
    # Reemplazar los espacios por cadenas vacías en la columna "id_practica"
    df["id_practica"] = df["id_practica"].str.replace(" ", "", regex=False)

# Guardar el DataFrame en un archivo Excel
df.to_excel(var + '.xlsx', index=False, engine='openpyxl')

print(f"El archivo ha sido guardado como {var}.xlsx")


