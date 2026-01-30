"""
Script creado por: Pablo Dueñas Fernández.
Este script obtiene múltiples indicadores del mercado eléctrico desde la API de ESIOS.
Descarga datos de precio de excedente, demanda peninsular, precio spot, generación eólica
y solar, unificando toda la información en un DataFrame común y guardándolo en PostgreSQL
para análisis posterior.
"""

import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


load_dotenv()
ESIOS_TOKEN        = os.getenv('ESIOS_TOKEN')
ESIOS_START_DATE   = os.getenv('ESIOS_START_DATE')
ESIOS_END_DATE     = os.getenv('ESIOS_END_DATE')
ESIOS_REGION_ID    = os.getenv('ESIOS_REGION_ID', '3')  # península

# Indicadores a descargar
INDICATORS = {
    '1739': 'precio_excedente',
    # '10148': 'demanda_peninsular',
    # '600' : 'precio_spot',
    # '12'  : 'generacion_eolica',
    # '14'  : 'generacion_solar'
}

ESIOS_POSTGRES_TABLE = os.getenv('ESIOS_POSTGRES_TABLE', 'esios_autoconsumo')
DB_HOST   = os.getenv('DB_HOST')
DB_PORT   = os.getenv('DB_PORT')
DB_NAME   = os.getenv('DB_NAME')
DB_USER   = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

if not all([ESIOS_TOKEN, ESIOS_START_DATE, ESIOS_END_DATE]):
    raise RuntimeError('Faltan variables ESIOS en .env')
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError('Faltan credenciales de base de datos en .env')


def fetch_indicator(indicator_id, col_name):
    url = f"https://api.esios.ree.es/indicators/{indicator_id}"
    params = {
        'start_date': f"{ESIOS_START_DATE}T00:00:00",
        'end_date'  : f"{ESIOS_END_DATE}T23:59:59",
        'geo_ids[]' : ESIOS_REGION_ID,
        'time_trunc': 'hour'
    }
    headers = {
        'Accept'    : 'application/json; application/vnd.esios-api-v2+json',
        'x-api-key' : ESIOS_TOKEN.strip()
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json().get('indicator', {}).get('values', [])
    if not data:
        raise RuntimeError(f"No hay datos para el indicador {indicator_id}")
    df = pd.DataFrame(data)
    # Tomamos la primera columna datetime y la segunda value (por si cambia el API)
    df = df.rename(columns={df.columns[0]: 'fecha', df.columns[1]: col_name})
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df[['fecha', col_name]]

#  Guardado en SQL
def save_to_sql(df):
    conn_str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_str)
    df.to_sql(ESIOS_POSTGRES_TABLE, engine, if_exists='replace', index=False)
    print(f"✔ Datos guardados en '{ESIOS_POSTGRES_TABLE}' (n={len(df)})")


def main():
    dfs = []
    for ind_id, col_name in INDICATORS.items():
        print(f"→ Descargando indicador {ind_id} → columna '{col_name}'")
        df_ind = fetch_indicator(ind_id, col_name)
        dfs.append(df_ind)
    # Merge de todos sobre la columna fecha
    df_all = dfs[0]
    for df_next in dfs[1:]:
        df_all = df_all.merge(df_next, on='fecha', how='outer')
    # Ordenamos y rellenamos huecos si hay
    df_all = df_all.sort_values('fecha').reset_index(drop=True)
    
    # Opcional: imputar valores faltantes (ej. forward-fill)
    df_all.fillna(method='ffill', inplace=True)
    
    print("Primeros registros resultantes:")
    print(df_all.head())
    
    save_to_sql(df_all)
    return df_all

if __name__ == '__main__':
    df_final = main()
