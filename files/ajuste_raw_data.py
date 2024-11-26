import pandas as pd

def ajustar_raw_data(input_file, output_file):
    """
    Itera sobre df1, procesa los valores de la columna 7 eliminando espacios,
    y guarda el DataFrame ajustado en un archivo Excel.
    
    Parámetros:
    - input_file: Ruta del archivo Excel de entrada (raw_data.xlsx)
    - output_file: Ruta del archivo Excel de salida (ajustado_raw_data.xlsx)
    """
    try:
        # Leer el archivo Excel original
        df1 = pd.read_excel(input_file, sheet_name='raw_data', usecols="A:Q", header=None)
        
        # Iterar sobre df1 y ajustar los valores de la columna H (columna 7)
        for index, row in df1.iterrows():
            # Eliminar espacios en la columna 7 (índice 7)
            df1.at[index, 7] = str(row[7]).replace(" ", "") if not pd.isna(row[7]) else row[7]
        
        # Guardar el DataFrame ajustado en un nuevo archivo Excel
        df1.to_excel(output_file, index=False, header=False)
        
        print(f"El archivo ajustado se ha guardado como '{output_file}'.")
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

# Parámetros
input_file = 'raw_data.xlsx'  # Archivo de entrada
output_file = 'ajustado_raw_data.xlsx'  # Archivo de salida

# Ejecutar la función
ajustar_raw_data(input_file, output_file)


