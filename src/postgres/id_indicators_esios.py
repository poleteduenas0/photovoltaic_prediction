"""
Script creado por: Pablo Dueñas Fernández.
Este script trata de localizar los indicadores de la API de ESIOS.
Para ello lanza una request a la API que da la información de los indicadores.
El resultado lo introduce en un archivo .csv y también en una tabla PostgreSQL
para facilitar la consulta y selección de indicadores relevantes.
"""

import os
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración
ESIOS_TOKEN = os.getenv('ESIOS_TOKEN')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Tabla y archivos de salida
TABLE_INDICATORS = "esios_indicators"  # Nombre de la tabla en PostgreSQL
CSV_FILENAME = "esios_indicators.csv"  # Archivo CSV para guardar los indicadores

# Verificar que el token esté disponible
if not ESIOS_TOKEN:
    raise RuntimeError("No se encontró el token ESIOS en el archivo .env")

def get_esios_indicators():
    """Obtiene lista completa de indicadores de ESIOS"""
    url = "https://api.esios.ree.es/indicators"
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v2+json',
        'Content-Type': 'application/json',
        'x-api-key': ESIOS_TOKEN.strip()  # Eliminar espacios en blanco
    }
    
    print(f"Solicitando indicadores ESIOS desde: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Código de estado: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error en la respuesta: {response.text[:500]}...")
            response.raise_for_status()
            
        data = response.json()
        
        if 'indicators' not in data:
            print(f"Estructura de respuesta inesperada. Claves disponibles: {list(data.keys())}")
            raise RuntimeError("No se encontró la lista de indicadores en la respuesta")
            
        indicators = data['indicators']
        print(f"Se encontraron {len(indicators)} indicadores")
        return indicators
        
    except Exception as e:
        print(f"Error al hacer la petición HTTP: {str(e)}")
        raise

def save_to_csv(indicators, filename):
    """Guarda los indicadores en un archivo CSV"""
    df = pd.DataFrame(indicators)
    
    # Mostrar información del DataFrame
    print(f"Columnas disponibles: {df.columns.tolist()}")
    print(f"Total indicadores: {len(df)}")
    
    # Guardar todos los datos
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"CSV generado con todos los datos: {filename}")
    
    # También crear un CSV simplificado con sólo id, nombre y unidad
    if all(col in df.columns for col in ['id', 'name', 'short_name', 'unit']):
        df_simple = df[['id', 'name', 'short_name', 'unit']]
        simple_filename = "esios_indicators_simple.csv"
        df_simple.to_csv(simple_filename, index=False, encoding='utf-8')
        print(f"CSV simplificado generado: {simple_filename}")
        
    return df

def save_to_postgres(df, table_name):
    """Guarda los indicadores en PostgreSQL"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Eliminar la tabla si existe
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        print(f"Tabla {table_name} eliminada (si existía)")
        
        # Crear tabla con las columnas adecuadas
        columns = []
        for col in df.columns:
            # Determinar el tipo de columna
            if df[col].dtype == 'object':
                if col == 'id':
                    columns.append(f"{col} INTEGER PRIMARY KEY")
                else:
                    columns.append(f"{col} TEXT")
            elif df[col].dtype == 'float64':
                columns.append(f"{col} FLOAT")
            elif df[col].dtype == 'int64':
                if col == 'id':
                    columns.append(f"{col} INTEGER PRIMARY KEY")
                else:
                    columns.append(f"{col} INTEGER")
            elif 'datetime' in str(df[col].dtype).lower():
                columns.append(f"{col} TIMESTAMP")
            else:
                columns.append(f"{col} TEXT")  # Tipo por defecto
                
        # Crear la tabla
        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
        print(f"Creando tabla con estructura: {create_table_sql}")
        cur.execute(create_table_sql)
        
        # Preparar datos para inserción
        records = df.replace({pd.NA: None}).to_records(index=False)
        values = list(records)
        
        # Construir consulta de inserción
        columns_str = ", ".join(df.columns)
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES %s"
        
        # Insertar datos
        try:
            execute_values(cur, insert_query, values)
            print(f"{len(values)} registros insertados en la tabla '{table_name}'.")
        except Exception as e:
            print(f"Error al insertar datos en lote: {e}")
            print("Intentando inserción fila por fila...")
            
            # Reintentar fila por fila
            conn.rollback()
            successful_inserts = 0
            
            for i, row in df.iterrows():
                try:
                    placeholders = ", ".join(["%s"] * len(row))
                    row_insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cur.execute(row_insert_query, tuple(row))
                    conn.commit()
                    successful_inserts += 1
                    if i % 50 == 0:
                        print(f"Procesadas {i+1} filas...")
                except Exception as row_error:
                    print(f"Error al insertar fila {i} (id={row.get('id', 'N/A')}): {row_error}")
                    conn.rollback()
            
            print(f"Inserción completa: {successful_inserts} de {len(df)} registros insertados.")
            
        # Cerrar conexión
        cur.close()
        conn.close()
        print("Conexión a PostgreSQL cerrada.")
        
    except Exception as db_error:
        print(f"Error con la base de datos: {db_error}")

def main():
    print("Obteniendo indicadores ESIOS...")
    try:
        # Obtener indicadores
        indicators = get_esios_indicators()
        
        # Guardar en CSV
        df = save_to_csv(indicators, CSV_FILENAME)
        
        # Guardar en PostgreSQL
        save_to_postgres(df, TABLE_INDICATORS)
        
        # Mostrar algunos indicadores populares
        try:
            df_simple = df[['id', 'name']]
            popular_ids = [1001, 600, 1739, 10211, 10076]  
            print("\nIndicadores populares para usar en ESIOS:")
            for pid in popular_ids:
                indicator = df_simple[df_simple['id'] == pid]
                if not indicator.empty:
                    print(f"- ID {pid}: {indicator['name'].values[0]}")
            print("\nConsulta la tabla completa para más indicadores.")
        except Exception as e:
            print(f"Error al mostrar indicadores populares: {e}")
        
        print("\nProceso completado.")
        
    except Exception as e:
        print(f"Error en el proceso: {e}")

if __name__ == "__main__":
    main()
