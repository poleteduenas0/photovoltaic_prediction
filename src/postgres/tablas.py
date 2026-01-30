"""
Script creado por: Pablo Dueñas Fernández.
Este script integra datos de múltiples fuentes (AEMET, ESIOS, REE y producción) 
y los almacena en tablas de PostgreSQL. Ejecuta los scripts de obtención de datos
de cada fuente, procesa los DataFrames y los guarda en la base de datos con 
nombres de tabla específicos para su posterior análisis.
"""
from script_aemet import main as get_aemet_data
from script_esios_newfeatures import main as get_esios_data
from script_production import main as get_production_data
from script_ree_add import main as get_ree_data
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Obtener credenciales de base de datos desde variables de entorno
AEMET_START_DATE = os.getenv('AEMET_START_DATE')
AEMET_END_DATE = os.getenv('AEMET_END_DATE')
AEMET_STATION_ID = os.getenv('AEMET_STATION_ID')
ESIOS_START_DATE = os.getenv('ESIOS_START_DATE')
ESIOS_END_DATE = os.getenv('ESIOS_END_DATE')
ESIOS_INDICATOR_ID = os.getenv('ESIOS_INDICATOR_ID')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
ESIOS_INDICATOR_ID = '1739'

# Crear cadena de conexión a base de datos
connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

# Obtener datos de AEMET
df_aemet = get_aemet_data(start_date=AEMET_START_DATE, end_date=AEMET_END_DATE, station_id=AEMET_STATION_ID)

# Obtener datos de ESIOS (reemplaza a REE)
df_esios = get_esios_data()
df_ree = get_ree_data()
df_esios = df_esios.sort_values(by='fecha')
df_ree = df_ree.sort_values(by='fecha')

# quitamos fecha de esios
df_esios = df_esios.drop(columns=['fecha'])

# juntar los DataFrames de ESIOS y REE sin tener en cuenta fecha puesto que ya están ordenados
df_esios = pd.concat([df_ree, df_esios], axis=1)

# Obtener datos de la base de datos
df_database = get_production_data()

# Crear tablas en PostgreSQL e insertar datos
df_aemet.to_sql('aemet_data', engine, if_exists='replace', index=False)
df_esios.to_sql('esios_data', engine, if_exists='replace', index=False)
df_database.to_sql('production_data', engine, if_exists='replace', index=False)

print("Datos guardados exitosamente en PostgreSQL:")
print("- aemet_data")
print("- production_data")
print("- esios_data")


