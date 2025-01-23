import pandas as pd
import sqlite3

# Configuración del archivo Excel y la base de datos
EXCEL_FILE = "nomenclador.xlsx"  # Ruta al archivo Excel
SHEET_NAME = "nomenclador"  # Nombre de la hoja en el Excel
DB_FILE = "db.sqlite3"  # Ruta a tu archivo SQLite3

# Campos del modelo Prestacion que corresponden a las columnas del Excel
COLUMN_MAP = {
    "Codigo": "codigo",
    "Descripcion": "descripcion",
    "Honorarios": "honorarios",
    "Ayudante": "ayudante",
    "Gastos": "gastos",
    "Anestesia": "anestesia",
    "Total": "total",
    "Servicio": "servicio",
    "Practica": "practica"
}

def importar_prestaciones():
    conn = None  # Inicializar la variable conn
    try:
        # Leer el archivo Excel y forzar que 'Codigo' sea texto
        print("Leyendo el archivo Excel...")
        df = pd.read_excel(
            EXCEL_FILE,
            sheet_name=SHEET_NAME,
            usecols="C:K",
            skiprows=1  # Saltar la primera fila (títulos)
        )

        # Imprimir columnas reales leídas para diagnóstico
        print("Columnas reales leídas desde el Excel:", df.columns)

        # Validar las columnas leídas y ajustar COLUMN_MAP dinámicamente
        columnas_ajustadas = {col.strip(): COLUMN_MAP.get(col.strip(), col.strip()) for col in df.columns}
        print("Mapa ajustado de columnas:", columnas_ajustadas)

        # Renombrar las columnas del DataFrame según el mapa ajustado
        df.rename(columns=columnas_ajustadas, inplace=True)

        # Verificar que las columnas requeridas están presentes
        columnas_faltantes = set(COLUMN_MAP.values()) - set(df.columns)
        if columnas_faltantes:
            raise ValueError(f"Faltan las columnas requeridas en el Excel: {columnas_faltantes}")

        # Convertir el campo "codigo" a texto y manejar valores vacíos
        print("Convirtiendo código a texto...")
        df["codigo"] = df["codigo"].fillna("SIN_CODIGO").astype(str)

        # Verificar el contenido del DataFrame
        print("Datos leídos del Excel:")
        print(df.head())

        # Reemplazar valores NaN con cadenas vacías
        print("Limpiando datos...")
        df.fillna("", inplace=True)

        # Convertir columnas numéricas a tipo float (o 0 si no son convertibles)
        for col in ["honorarios", "ayudante", "gastos", "anestesia", "total"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Conectar a la base de datos SQLite3
        print(f"Conectando a la base de datos {DB_FILE}...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Insertar los datos en la tabla facturacion_prestacion
        print("Insertando datos en la tabla facturacion_prestacion...")
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO facturacion_prestacion 
                (codigo, descripcion, honorarios, ayudante, gastos, anestesia, total, servicio, practica)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["codigo"],
                row["descripcion"],
                row["honorarios"],
                row["ayudante"],
                row["gastos"],
                row["anestesia"],
                row["total"],
                row["servicio"],
                row["practica"]
            ))

        # Confirmar cambios y cerrar la conexión
        conn.commit()
        print("Importación completada con éxito.")
    except Exception as e:
        print(f"Error durante la importación: {e}")
    finally:
        # Cerrar la conexión si fue abierta
        if conn:
            conn.close()

if __name__ == "__main__":
    importar_prestaciones()






