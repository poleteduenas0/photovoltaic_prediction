"""
Script creado por: Pablo Dueñas Fernández.
Este script realiza consultas de prueba a la API de REE para obtener datos específicos.
Configura parámetros de consulta para diferentes categorías y widgets de datos energéticos,
ejecuta peticiones HTTP y guarda los resultados en formato CSV para análisis exploratorio
de los endpoints disponibles.
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ——————————————————————————————
# Configuración
# ——————————————————————————————
load_dotenv()

# Token opcional para entornos corporativos
REE_KEY   = os.getenv('REE_KEY', None)

# Parámetros de consulta
LANG      = 'es'                    # 'es' o 'en'
CATEGORY  = 'demanda'               # ej. 'demanda', 'generacion', 'balance', 'mercados', …
WIDGET    = 'demanda-tiempo-real'   # ver lista widgets en la documentación
START     = '2023-05-01T00:00'
END       = '2023-05-07T23:59'
TIME_TRUNC = 'hour'                 # 'hour', 'day', 'month', 'year'
GEO_TRUNC = 'electric_system'       # opcional
GEO_LIMIT = 'peninsular'            # opcional
GEO_IDS   = '8741'                  # opcional, id de CC.AA. si corresponde

# Construcción de la URL
BASE_URL = "https://apidatos.ree.es"
endpoint = f"{BASE_URL}/{LANG}/datos/{CATEGORY}/{WIDGET}"
params = {
    'start_date': START,
    'end_date'  : END,
    'time_trunc': TIME_TRUNC,
    'geo_trunc' : GEO_TRUNC,
    'geo_limit' : GEO_LIMIT,
    'geo_ids'   : GEO_IDS
}

headers = {
    'Accept'      : 'application/json',
    'Content-Type': 'application/json'
}
if REE_KEY:
    headers['Authorization'] = f"Token token={REE_KEY.strip()}"

def fetch_widget(endpoint, headers, params):
    """Realiza la petición a la API de REE y devuelve JSON parseado."""
    print(f"→ GET {endpoint}")
    print(f"  Params: {params}")
    resp = requests.get(endpoint, headers=headers, params=params)
    print(f"  Status: {resp.status_code}")
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    try:
        data = fetch_widget(endpoint, headers, params)
        # Extraer valores del JSON: data["included"][0]["attributes"]["values"]
        values = []
        for inc in data.get("included", []):
            attrs = inc.get("attributes", {})
            if "values" in attrs:
                values = attrs["values"]
                break

        if not values:
            print("¡No se han encontrado valores en la respuesta!")
        else:
            df = pd.DataFrame(values)
            print("\nPrimeros registros:")
            print(df.head())
            # Guardar a CSV opcional
            df.to_csv(f"{CATEGORY}_{WIDGET}.csv", index=False, encoding="utf-8")
            print(f"\nDatos guardados en {CATEGORY}_{WIDGET}.csv")

    except Exception as e:
        print("Error al obtener datos de REE:", e)
