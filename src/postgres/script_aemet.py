"""
Script creado por: Pablo Dueñas Fernández.
Este script obtiene datos meteorológicos diarios desde la API de AEMET.
Descarga información climatológica de estaciones meteorológicas específicas,
procesa los datos para asegurar continuidad temporal y los almacena en PostgreSQL
para su uso en modelos de predicción fotovoltaica.
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd # Importar pandas
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine

# Cargar variables de entorno desde .env
load_dotenv()
AEMET_API_KEY = os.getenv("API_KEY_OPENDATA")
AEMET_START_DATE = os.getenv("AEMET_START_DATE")
AEMET_END_DATE = os.getenv("AEMET_END_DATE")
AEMET_STATION_ID = os.getenv("AEMET_STATION_ID")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
AEMET_POSTGRES_TABLE = os.getenv("AEMET_POSTGRES_TABLE")

if not AEMET_API_KEY:
    print("Error: No se encontró la AEMET_API_KEY en el archivo .env")
    exit()

# Función para formatear fecha a formato AEMET

def format_aemet_date(date_str):
    dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return dt_obj.strftime("%Y-%m-%dT00:00:00UTC")

# Función para obtener datos diarios de AEMET

def get_aemet_daily_climatology(api_key, start_date_str, end_date_str, station_id):
    base_url = "https://opendata.aemet.es/opendata"
    fecha_ini = format_aemet_date(start_date_str)
    fecha_fin = format_aemet_date(end_date_str)
    endpoint = f"/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{station_id}"
    url_meta = base_url + endpoint
    headers = {'api_key': api_key, 'Accept': 'application/json'}

    resp = requests.get(url_meta, headers=headers)
    resp.raise_for_status()
    meta = resp.json()
    if meta.get('estado') != 200:
        raise RuntimeError(f"Error AEMET: {meta.get('descripcion')}")
    data_url = meta.get('datos')

    resp2 = requests.get(data_url, headers=headers)
    resp2.raise_for_status()
    try:
        return resp2.json()
    except ValueError:
        print("Error al decodificar JSON de datos reales:", resp2.text)
        return None

# Procesar datos y asegurar fila por cada día

def process_aemet_data(datos, start_date_str, end_date_str):
    if not datos:
        return None
    df = pd.DataFrame(datos)
    # Convertir columnas numéricas
    cols_to_convert = ['tmed', 'prec', 'tmin', 'tmax', 'velmedia', 'racha', 'presMax', 'presMin', 'hrMedia', 'hrMax', 'hrMin', 'sol']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = df[col].str.replace('Ip', '0.0', regex=False)  # Reemplazar N/A por 0
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Convertir fecha y formatear AAAA-MM-dd
    df['fecha'] = pd.to_datetime(df['fecha'], format="%Y-%m-%d", errors='coerce')
    # Generar rango completo de fechas
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    full_dates = pd.date_range(start=start, end=end)
    df_full = pd.DataFrame({'fecha': full_dates})
    # Unir datos reales con rango completo (left join rango completo)
    df_merged = df_full.merge(df, on='fecha', how='left')
    # Formatear de nuevo fecha como string AAAA-MM-dd
    df_merged['fecha'] = df_merged['fecha'].dt.strftime('%Y-%m-%d')
    return df_merged

# División de rango en segmentos de máximo 6 meses

def split_date_range(start_date_str, end_date_str, max_months=6):
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    max_days = max_months * 30
    segments = []
    current = start
    while current <= end:
        seg_end = min(current + timedelta(days=max_days-1), end)
        segments.append((current.strftime("%Y-%m-%d"), seg_end.strftime("%Y-%m-%d")))
        current = seg_end + timedelta(days=1)
    return segments

# Función para guardar datos en PostgreSQL
def save_to_postgres(df):
    """Guarda el DataFrame en PostgreSQL utilizando SQLAlchemy"""
    if df is None or df.empty:
        print("No hay datos para guardar en PostgreSQL")
        return False
    
    try:
        # Convertir la columna fecha a datetime si es necesario
        if 'fecha' in df.columns and not pd.api.types.is_datetime64_dtype(df['fecha']):
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Crear una conexión SQLAlchemy
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        # Guardar el DataFrame en PostgreSQL
        df.to_sql(AEMET_POSTGRES_TABLE, engine, if_exists='replace', index=False)
        
        print(f"Datos guardados exitosamente en la tabla {AEMET_POSTGRES_TABLE}")
        return True
    except Exception as e:
        print(f"Error al guardar datos en PostgreSQL: {e}")
        return False

# Función principal

def main(start_date, end_date, station_id):
    # Dividir si >6 meses
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    months_diff = (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month
    all_data = []
    if months_diff > 6:
        segments = split_date_range(start_date, end_date)
        for seg_start, seg_end in segments:
            data = get_aemet_daily_climatology(AEMET_API_KEY, seg_start, seg_end, station_id)
            if data:
                all_data.extend(data)
    else:
        data = get_aemet_daily_climatology(AEMET_API_KEY, start_date, end_date, station_id)
        if data:
            all_data = data
    # Procesar y obtener df_final con fila por día
    df_final = process_aemet_data(all_data, start_date, end_date)
    
    # Guardar datos en PostgreSQL
    if df_final is not None:
        save_to_postgres(df_final)
    
    return df_final

if __name__ == '__main__':
    df = main(AEMET_START_DATE, AEMET_END_DATE, AEMET_STATION_ID)
    if df is not None:
        print(df.head())
        print(df.info())
        print(f"Total filas (días): {len(df)}")
        # También guardar como CSV si se desea
        df.to_csv('aemet_daily_full.csv', index=False, encoding='utf-8')
        print("CSV generado: aemet_daily_full.csv")
