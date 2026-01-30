"""
Script creado por: Pablo Dueñas Fernández.
Este script obtiene el inventario completo de estaciones meteorológicas de AEMET.
Realiza una consulta a la API para obtener todas las estaciones disponibles,
guarda la información completa en CSV y crea una tabla en PostgreSQL con
todos los datos de las estaciones para referencia posterior.
"""

import os
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

API_KEY = os.getenv('API_KEY_OPENDATA')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Tabla y archivos
TABLE_STATIONS = os.getenv('AEMET_POSTGRES_TABLE_ID')  # nombre tabla de IDs
CSV_FILENAME = "aemet_station_ids.csv"

# 1. Solicitud inventario completo de estaciones
inventory_url = (
    f"https://opendata.aemet.es/opendata/api/valores/climatologicos/"
    f"inventarioestaciones/todasestaciones/?api_key={API_KEY}"
)
resp = requests.get(inventory_url, headers={'accept': 'application/json'})
resp.raise_for_status()
data_url = resp.json().get('datos')
if not data_url:
    raise RuntimeError("No se encontró la URL de datos en la respuesta de inventario.")

# 2. Descargar datos de inventario
data_resp = requests.get(data_url, headers={'accept': 'application/json'})
data_resp.raise_for_status()
stations = data_resp.json()

# 3. Crear DataFrame con todos los datos de estaciones
df_stations = pd.DataFrame(stations)
print(f"Columnas disponibles: {df_stations.columns.tolist()}")

# Guardar CSV con todos los datos de estaciones
csv_all_data = "aemet_stations_complete.csv"
df_stations.to_csv(csv_all_data, index=False, encoding='utf-8')
print(f"CSV generado con datos completos: {csv_all_data}")

# También guardar CSV solo con IDs para compatibilidad
df_ids = pd.DataFrame({'station_id': df_stations['indicativo'].tolist()})
df_ids.to_csv(CSV_FILENAME, index=False, encoding='utf-8')
print(f"CSV generado con {len(df_ids)} estaciones: {CSV_FILENAME}")

# 4. Crear y poblar tabla en PostgreSQL con todos los datos
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
conn.autocommit = True  # Para poder crear la tabla
cur = conn.cursor()

# Primero eliminamos la tabla si existe
try:
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_STATIONS}")
    print(f"Tabla {TABLE_STATIONS} eliminada")
except Exception as e:
    print(f"Error al eliminar tabla: {e}")

# Crear la tabla con las columnas adecuadas basadas en el DataFrame
columns = []
for col in df_stations.columns:
    if df_stations[col].dtype == 'object':
        columns.append(f"{col} TEXT")
    elif df_stations[col].dtype == 'float64':
        columns.append(f"{col} FLOAT")
    elif df_stations[col].dtype == 'int64':
        columns.append(f"{col} INTEGER")
    else:
        columns.append(f"{col} TEXT")  # Por defecto usamos TEXT para tipos desconocidos

# Crear tabla
create_table_sql = f"CREATE TABLE {TABLE_STATIONS} ({', '.join(columns)})"
print(f"Creando tabla con la siguiente estructura: {create_table_sql}")
cur.execute(create_table_sql)
print(f"Tabla {TABLE_STATIONS} creada con éxito")

# Preparar datos para inserción
# Convertir DataFrame a lista de tuplas para insertarlas
records = df_stations.replace({pd.NA: None}).to_records(index=False)
values = list(records)

# Construir consulta de inserción
columns_str = ", ".join(df_stations.columns)
placeholders = ", ".join(["%s"] * len(df_stations.columns))
insert_query = f"INSERT INTO {TABLE_STATIONS} ({columns_str}) VALUES %s"

# Insertar datos
try:
    execute_values(cur, insert_query, values)
    print(f"{len(values)} registros insertados en la tabla '{TABLE_STATIONS}'.")
except Exception as e:
    print(f"Error al insertar datos: {e}")
    print("Intente examinar los datos para ver si hay valores problemáticos.")
    # Intentamos con una inserción fila por fila para mayor detalle
    conn.rollback()
    for i, row in df_stations.iterrows():
        try:
            placeholders = ", ".join(["%s"] * len(row))
            row_insert_query = f"INSERT INTO {TABLE_STATIONS} ({columns_str}) VALUES ({placeholders})"
            cur.execute(row_insert_query, tuple(row))
            if i % 100 == 0:
                print(f"Procesadas {i+1} filas...")
            conn.commit()
        except Exception as row_error:
            print(f"Error al insertar fila {i}: {row_error}")
            conn.rollback()

# Cerrar conexión
cur.close()
conn.close()
print("Proceso completado.")
