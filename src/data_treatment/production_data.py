"""
Script creado por: Pablo Dueñas Fernández.
Este script procesa y analiza datos de producción fotovoltaica almacenados en PostgreSQL.
Realiza análisis exploratorio, limpieza de datos, visualizaciones estadísticas
y guarda los datos procesados en una tabla tratada para su uso en modelos predictivos.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
PRODUCTION_POSTGRES_TABLE = os.getenv('PRODUCTION_POSTGRES_TABLE')
PRODUCTION_POSTGRES_TABLE_TREATED = os.getenv('PRODUCTION_POSTGRES_TABLE_TREATED')

# Definir la ruta para guardar las visualizaciones
VISUALIZATION_DIR = 'data_treatment/production_visualizations'

# Crear el directorio si no existe
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

# creamoos dos dataframes vacios para evitar errores
df_aemet = pd.DataFrame()
df_esios = pd.DataFrame()

def connect_to_database():
    """Establece conexión con la base de datos PostgreSQL."""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    try:
        engine = create_engine(connection_string)
        print("Conexión a la base de datos establecida con éxito.")
        return engine
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def load_data(engine, table_name):
    """Carga los datos desde la tabla especificada en PostgreSQL."""
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        print(f"Datos cargados con éxito. Dimensiones: {df.shape}")
        return df
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

def explore_data(df):
    """Explora y visualiza los datos de producción."""
    print("\n=== Análisis Exploratorio de Datos de Producción ===")
    
    # Información general del DataFrame
    print("\n1. Información general del DataFrame:")
    print(f"Dimensiones: {df.shape}")
    print(f"Columnas: {df.columns.tolist()}")
    
    # Estadísticas descriptivas
    print("\n2. Estadísticas descriptivas:")
    print(df.describe().T)
    
    # Valores faltantes
    print("\n3. Valores faltantes por columna:")
    missing = df.isnull().sum()
    missing_percent = (df.isnull().sum() / len(df) * 100)
    missing_data = pd.concat([missing, missing_percent], axis=1, keys=['Total', 'Porcentaje'])
    print(missing_data[missing_data['Total'] > 0].sort_values('Total', ascending=False))
    
    # Distribución de producción total
    plt.figure(figsize=(12, 6))
    if 'Totalproduction' in df.columns:
        sns.histplot(df['Totalproduction'], kde=True)
        plt.title('Distribución de Producción Total')
        plt.xlabel('Producción Total')
        
        # Guardar con ruta absoluta usando os.path.join
        output_path = os.path.join(VISUALIZATION_DIR, 'production_distribution.png')
        plt.savefig(output_path)
        print(f"Gráfico guardado en: {output_path}")
        plt.close()
    
    # Serie temporal de producción
    if 'date_and_time' in df.columns:
        plt.figure(figsize=(15, 8))
        # Asegúrate de que la fecha esté en formato datetime
        date_col = 'date_and_time'
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col])
            
        if 'Totalproduction' in df.columns:
            plt.plot(df[date_col], df['Totalproduction'])
            plt.title('Evolución de la Producción Total')
            plt.xlabel('Fecha')
            plt.ylabel('Producción Total')
            plt.grid(True)
            
            output_path = os.path.join(VISUALIZATION_DIR, 'production_time_series.png')
            plt.savefig(output_path)
            print(f"Gráfico guardado en: {output_path}")
            plt.close()
    
    # Producción por mes (si hay datos de varios meses)
    if 'date_and_time' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['date_and_time']):
            df['date_and_time'] = pd.to_datetime(df['date_and_time'])
        
        df['month'] = df['date_and_time'].dt.month
        monthly_production = df.groupby('month')['Totalproduction'].mean().reset_index()
        
        plt.figure(figsize=(12, 6))
        sns.barplot(x='month', y='Totalproduction', data=monthly_production)
        plt.title('Producción Media Mensual')
        plt.xlabel('Mes')
        plt.ylabel('Producción Media')
        plt.xticks(range(12), ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
        
        output_path = os.path.join(VISUALIZATION_DIR, 'monthly_production.png')
        plt.savefig(output_path)
        print(f"Gráfico guardado en: {output_path}")
        plt.close()
        
        # Clean up temporary column
        df.drop('month', axis=1, inplace=True)
    
    print(f"\nTodos los gráficos se han guardado en: {os.path.abspath(VISUALIZATION_DIR)}")

def process_data(df):
    """Procesa y transforma los datos de producción."""
    print("\n=== Procesamiento de Datos de Producción ===")
    
    # Crear una copia para no modificar el original
    processed_df = df.copy()
    
    # 2. Convertir tipos de datos
    print("2. Convirtiendo tipos de datos...")
    # Asegurar que la fecha esté en formato datetime
    date_col = 'date_and_time'
    if date_col in processed_df.columns:
        if not pd.api.types.is_datetime64_any_dtype(processed_df[date_col]):
            processed_df[date_col] = pd.to_datetime(processed_df[date_col])
    
    # Asegurar que la producción sea numérica y reemplazar comas por puntos si es necesario
    if 'Totalproduction' in processed_df.columns and processed_df['Totalproduction'].dtype == 'object':
        processed_df['Totalproduction'] = (
            processed_df['Totalproduction']
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )
    
    # Simplificamos el procesamiento para trabajar solo con las dos columnas principales
    print("3. Simplificando dataset a las columnas principales...")
    columns_to_keep = ['date_and_time', 'Totalproduction']
    processed_df = processed_df[columns_to_keep]
    
    print("\nProcesamiento completado.")
    return processed_df

def save_to_database(df, engine, table_name):
    """Guarda el DataFrame procesado en una nueva tabla en PostgreSQL."""
    try:
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Datos guardados exitosamente en la tabla {table_name}.")
        return True
    except Exception as e:
        print(f"Error al guardar los datos en la base de datos: {e}")
        return False



def main(df_aemet, df_esios):
    """Función principal."""
    # Conectar a la base de datos
    engine = connect_to_database()
    if engine is None:
        return
    
    # Cargar datos
    df_production = load_data(engine, PRODUCTION_POSTGRES_TABLE)
    if df_production is None:
        return
    # cambiamos el nombnre de la primera columna por date_and_time
    df_production.rename(columns={df_production.columns[0]: 'date_and_time'}, inplace=True)
    # Asegurarnos de que la columna de fecha esté en el formato correcto
    if not pd.api.types.is_datetime64_any_dtype(df_production['date_and_time']):
        df_production['date_and_time'] = pd.to_datetime(df_production['date_and_time'])
    print(df_production.head())
    # Asegurarnos de que la columna de producción sea numérica
    if df_production['Totalproduction'].dtype == 'object':
        df_production['Totalproduction'] = (
            df_production['Totalproduction']
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )
    # Explorar datos
    explore_data(df_production)
    
    # Procesar datos
    df_production_processed = process_data(df_production)

    
    #sacamos la matriz de correlación con un heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(df_production_processed.corr(), annot=True, fmt=".2f", cmap='coolwarm')
    plt.title('Matriz de Correlación')
    plt.tight_layout()
    correlation_path = os.path.join(VISUALIZATION_DIR, 'correlation_matrix_production.png')
    plt.savefig(correlation_path)
    print(f"Gráfico de matriz de correlación guardado en: {correlation_path}")
    plt.close()
    
    # Guardar datos procesados - No necesitamos renombrar columnas
    save_to_database(df_production_processed, engine, PRODUCTION_POSTGRES_TABLE_TREATED)
    
    # Mostrar resultados finales
    print("\n=== Resumen del Procesamiento ===")
    print(f"Dimensiones originales: {df_production.shape}")
    print(f"Dimensiones después del procesamiento: {df_production_processed.shape}")
    print(f"Tabla original: {PRODUCTION_POSTGRES_TABLE}")
    print(f"Tabla procesada: {PRODUCTION_POSTGRES_TABLE}_treated")
    print(df_production_processed.head())
    print(f"Todos los gráficos se han guardado en: {os.path.abspath(VISUALIZATION_DIR)}")
    return df_production_processed

if __name__ == "__main__":
    main(df_aemet, df_esios)
