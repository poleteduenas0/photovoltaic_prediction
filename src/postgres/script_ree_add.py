"""
Script creado por: Pablo Dueñas Fernández.
Este script obtiene datos del balance eléctrico y demanda energética desde la API de REE.
Descarga información sobre generación renovable y no renovable, además de datos de demanda,
organizando los datos por intervalos temporales y guardándolos en formato DataFrame para
su posterior procesamiento y análisis.
"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# ——————————————————————————————
# Configuración
# ——————————————————————————————
load_dotenv()
START = os.getenv('ESIOS_START_DATE') + "T00:00"   # ej. '2023-01-01T00:00'
END   = os.getenv('ESIOS_END_DATE')   + "T23:59"   # ej. '2023-04-30T23:59'
BASE    = "https://apidatos.ree.es/es/datos"
TIME_TRUNC = "day"
GEO_LIMIT  = "peninsular"
GEO_IDS    = "8741"

# Mapeo de columnas para balance
REN_MAP = {
    'Hidráulica':          'Hidráulica',
    'Eólica':              'Eólica',
    'Solar fotovoltaica':  'Solar_fotovoltaica',
    'Solar térmica':       'Solar_térmica',
    'Otras renovables':    'Otras_renovables',
    'Generación renovable':'Generación_renovable'
}
NONREN_MAP = {
    'Nuclear':                   'Nuclear',
    'Ciclo combinado':           'Ciclo_combinado',
    'Carbón':                    'Carbón',
    'Cogeneración':              'Cogeneración',
    'Residuos no renovables':    'Residuos_no_renovables',
    'Generación no renovable':   'Generación_no_renovable'
}

# Endpoints relativos
ENDPOINTS = {
    'balance': "/balance/balance-electrico",
    'demanda': "/demanda/evolucion"
}

def chunk_ranges(start_str, end_str, max_months=6):
    """Divide el rango en trozos de hasta max_months meses."""
    start = datetime.fromisoformat(start_str)
    end   = datetime.fromisoformat(end_str)
    out = []
    cur = start
    while cur < end:
        nxt = cur + relativedelta(months=max_months) - timedelta(seconds=1)
        chunk_end = min(nxt, end)
        out.append((cur, chunk_end))
        cur = chunk_end + timedelta(seconds=1)
    return out

def fetch_and_parse_balance(start_dt, end_dt):
    """Descarga un chunk de balance y extrae valores por tipo."""
    params = {
        'start_date': start_dt.strftime("%Y-%m-%dT%H:%M"),
        'end_date':   end_dt.strftime("%Y-%m-%dT%H:%M"),
        'time_trunc': TIME_TRUNC,
        'geo_limit':  GEO_LIMIT,
        'geo_ids':    GEO_IDS
    }
    url = BASE + ENDPOINTS['balance']
    resp = requests.get(url, params=params, headers={'Accept':'application/json'})
    resp.raise_for_status()
    inc = resp.json().get('included', [])
    
    records = []
    for section in inc:
        for content in section['attributes']['content']:
            title = content['attributes']['title']
            # decidir si es renovable o no renovable
            if title in REN_MAP:
                key = REN_MAP[title]
            elif title in NONREN_MAP:
                key = NONREN_MAP[title]
            else:
                continue
            for v in content['attributes']['values']:
                dt = datetime.fromisoformat(v['datetime'][:19])
                records.append({'fecha': dt, key: v['value']})
    return pd.DataFrame(records)

def fetch_and_parse_demanda(start_dt, end_dt):
    """Descarga un chunk de demanda y extrae valores."""
    params = {
        'start_date': start_dt.strftime("%Y-%m-%dT%H:%M"),
        'end_date':   end_dt.strftime("%Y-%m-%dT%H:%M"),
        'time_trunc': TIME_TRUNC,
        'geo_trunc':  'electric_system',
        'geo_limit':  GEO_LIMIT,
        'geo_ids':    GEO_IDS
    }
    url = BASE + ENDPOINTS['demanda']
    resp = requests.get(url, params=params, headers={'Accept':'application/json'})
    resp.raise_for_status()
    inc = resp.json().get('included', [])
    
    records = []
    for section in inc:
        for v in section['attributes']['values']:
            dt = datetime.fromisoformat(v['datetime'][:19])
            records.append({'fecha': dt, 'Demanda': v['value']})
    return pd.DataFrame(records)

def main():
    # 1) Calculamos los intervalos
    ranges = chunk_ranges(START, END, max_months=6)
    print("Chunks a solicitar:")
    for s,e in ranges:
        print(f"  • {s} → {e}")
    
    # 2) Recolectamos y parseamos
    dfs_bal = []
    dfs_dem = []
    for s,e in ranges:
        dfs_bal.append(fetch_and_parse_balance(s, e))
        dfs_dem.append(fetch_and_parse_demanda(s, e))
    
    # 3) Concatenar todos los trozos
    df_balance = pd.concat(dfs_bal, ignore_index=True)
    df_demanda = pd.concat(dfs_dem, ignore_index=True)

    # 4) Pivotar balance a formato ancho
    df_bal_wide = df_balance.pivot_table(
        index='fecha',
        aggfunc='first'  # cada fecha es única en cada chunk
    )
    
    # 5) Preparar demanda
    df_dem_wide = df_demanda.set_index('fecha')
    
    # 6) Unir en un solo DataFrame
    df_all = pd.concat([df_bal_wide, df_dem_wide], axis=1).sort_index()

    # 7) Mostrar resultado
    print(df_all.info())
    return df_all

if __name__ == "__main__":
    df_final = main()
