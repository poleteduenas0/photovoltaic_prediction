"""
Script creado por: Pablo Dueñas Fernández.
Este script procesa y analiza datos meteorológicos de AEMET almacenados en PostgreSQL.
Realiza limpieza de datos, imputación de valores faltantes, tratamiento de outliers,
creación de características temporales y análisis exploratorio con visualizaciones
para preparar los datos meteorológicos para modelos predictivos.
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
AEMET_POSTGRES_TABLE = os.getenv('AEMET_POSTGRES_TABLE')
AEMET_POSTGRES_TABLE_TREATED = os.getenv('AEMET_POSTGRES_TABLE_TREATED')

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
    """Explora y visualiza los datos de AEMET."""
    print("\n=== Análisis Exploratorio de Datos AEMET ===")
    
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
    
    # Crear directorio para visualizaciones si no existe
    os.makedirs('data_treatment/aemet_visualizations', exist_ok=True)
    
    # Visualizaciones específicas para sol, presmax y presmin
    plt.figure(figsize=(18, 12))
    
    # Sol (Horas de sol)
    if 'sol' in df.columns:
        plt.subplot(3, 3, 1)
        sns.histplot(df['sol'].dropna(), kde=True, color='orange')
        plt.title('Distribución de Horas de Sol')
        plt.xlabel('Horas')
        
        plt.subplot(3, 3, 2)
        if 'fecha' in df.columns:
            # Asegúrate de que 'fecha' esté en formato datetime
            if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
                df['fecha'] = pd.to_datetime(df['fecha'])
            plt.plot(df['fecha'], df['sol'], color='orange')
            plt.title('Evolución Temporal de Horas de Sol')
            plt.xlabel('Fecha')
            plt.ylabel('Horas')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(3, 3, 3)
        if 'mes' in df.columns:
            sol_by_month = df.groupby('mes')['sol'].mean()
            sns.barplot(x=sol_by_month.index, y=sol_by_month.values, color='orange')
            plt.title('Promedio de Horas de Sol por Mes')
            plt.xlabel('Mes')
            plt.ylabel('Horas (promedio)')
        
    # Presión máxima
    if 'presmax' in df.columns:
        plt.subplot(3, 3, 4)
        sns.histplot(df['presmax'].dropna(), kde=True, color='blue')
        plt.title('Distribución de Presión Máxima')
        plt.xlabel('hPa')
        
        plt.subplot(3, 3, 5)
        if 'fecha' in df.columns:
            plt.plot(df['fecha'], df['presmax'], color='blue')
            plt.title('Evolución Temporal de Presión Máxima')
            plt.xlabel('Fecha')
            plt.ylabel('hPa')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(3, 3, 6)
        if 'mes' in df.columns:
            presmax_by_month = df.groupby('mes')['presmax'].mean()
            sns.barplot(x=presmax_by_month.index, y=presmax_by_month.values, color='blue')
            plt.title('Promedio de Presión Máxima por Mes')
            plt.xlabel('Mes')
            plt.ylabel('hPa (promedio)')
    
    # Presión mínima
    if 'presmin' in df.columns:
        plt.subplot(3, 3, 7)
        sns.histplot(df['presmin'].dropna(), kde=True, color='green')
        plt.title('Distribución de Presión Mínima')
        plt.xlabel('hPa')
        
        plt.subplot(3, 3, 8)
        if 'fecha' in df.columns:
            plt.plot(df['fecha'], df['presmin'], color='green')
            plt.title('Evolución Temporal de Presión Mínima')
            plt.xlabel('Fecha')
            plt.ylabel('hPa')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(3, 3, 9)
        if 'mes' in df.columns:
            presmin_by_month = df.groupby('mes')['presmin'].mean()
            sns.barplot(x=presmin_by_month.index, y=presmin_by_month.values, color='green')
            plt.title('Promedio de Presión Mínima por Mes')
            plt.xlabel('Mes')
            plt.ylabel('hPa (promedio)')
    
    plt.tight_layout()
    plt.savefig('data_treatment/aemet_visualizations/sol_presion_analysis.png')
    plt.close()
    
    # Correlación entre sol, presmax, presmin y temperatura
    if all(col in df.columns for col in ['sol', 'presmax', 'presmin', 'tmed']):
        selected_cols = ['sol', 'presmax', 'presmin', 'tmed', 'tmax', 'tmin', 'prec']
        selected_cols = [col for col in selected_cols if col in df.columns]
        
        plt.figure(figsize=(10, 8))
        correlation = df[selected_cols].corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title('Matriz de Correlación - Variables Seleccionadas')
        plt.tight_layout()
        plt.savefig('data_treatment/aemet_visualizations/sol_presion_correlation.png')
        plt.close()
    
    # Gráfico de dispersión: Sol vs Presión
    if all(col in df.columns for col in ['sol', 'presmax']):
        plt.figure(figsize=(15, 5))
        
        plt.subplot(1, 2, 1)
        sns.scatterplot(x='presmax', y='sol', data=df, alpha=0.6)
        plt.title('Relación entre Presión Máxima y Horas de Sol')
        plt.xlabel('Presión Máxima (hPa)')
        plt.ylabel('Horas de Sol')
        plt.grid(True, alpha=0.3)
        
        if 'presmin' in df.columns:
            plt.subplot(1, 2, 2)
            sns.scatterplot(x='presmin', y='sol', data=df, alpha=0.6)
            plt.title('Relación entre Presión Mínima y Horas de Sol')
            plt.xlabel('Presión Mínima (hPa)')
            plt.ylabel('Horas de Sol')
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('data_treatment/aemet_visualizations/sol_vs_presion_scatter.png')
        plt.close()
    
    # Análisis estacional de horas de sol
    if all(col in df.columns for col in ['sol', 'estacion']):
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='estacion', y='sol', data=df)
        plt.title('Distribución de Horas de Sol por Estación')
        plt.xlabel('Estación (1=Invierno, 2=Primavera, 3=Verano, 4=Otoño)')
        plt.ylabel('Horas de Sol')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('data_treatment/aemet_visualizations/sol_por_estacion.png')
        plt.close()
    
    print("\nVisualizaciones adicionales para sol, presmax y presmin guardadas en 'data_treatment/aemet_visualizations/'")
    
    # Distribución de temperaturas y precipitaciones (existente)
    plt.figure(figsize=(15, 10))
    
    # Temperatura media
    plt.subplot(2, 2, 1)
    if 'tmed' in df.columns:
        sns.histplot(df['tmed'], kde=True)
        plt.title('Distribución de temperatura media')
    
    # Temperatura máxima
    plt.subplot(2, 2, 2)
    if 'tmax' in df.columns:
        sns.histplot(df['tmax'], kde=True)
        plt.title('Distribución de temperatura máxima')
    
    # Temperatura mínima
    plt.subplot(2, 2, 3)
    if 'tmin' in df.columns:
        sns.histplot(df['tmin'], kde=True)
        plt.title('Distribución de temperatura mínima')
    
    # Precipitaciones
    plt.subplot(2, 2, 4)
    if 'prec' in df.columns:
        # Mostrar solo valores no nulos y menores a cierto umbral para mejor visualización
        prec_data = df['prec'].dropna()
        prec_data = prec_data[prec_data < prec_data.quantile(0.95)]  # Eliminar valores extremos
        sns.histplot(prec_data, kde=True)
        plt.title('Distribución de precipitaciones (sin outliers)')
    
    plt.tight_layout()
    plt.savefig('data_treatment/aemet_visualizations/aemet_distributions.png')
    plt.close()
    
    # Serie temporal de temperaturas
    if 'fecha' in df.columns:
        plt.figure(figsize=(15, 8))
        # Asegúrate de que 'fecha' esté en formato datetime
        if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
            df['fecha'] = pd.to_datetime(df['fecha'])
            
        if 'tmed' in df.columns and 'tmax' in df.columns and 'tmin' in df.columns:
            plt.plot(df['fecha'], df['tmed'], label='Temperatura Media')
            plt.plot(df['fecha'], df['tmax'], label='Temperatura Máxima')
            plt.plot(df['fecha'], df['tmin'], label='Temperatura Mínima')
            plt.title('Evolución de Temperaturas')
            plt.xlabel('Fecha')
            plt.ylabel('Temperatura (°C)')
            plt.legend()
            plt.grid(True)
            plt.savefig('data_treatment/aemet_visualizations/aemet_temperature_time_series.png')
            plt.close()
    
    # Correlación entre variables numéricas
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        plt.figure(figsize=(12, 10))
        correlation = numeric_df.corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title('Matriz de Correlación')
        plt.tight_layout()
        plt.savefig('data_treatment/aemet_visualizations/aemet_correlation_matrix.png')
        plt.close()
    
    print("\nGráficos guardados en el directorio actual.")

def process_data(df):
    """Procesa y transforma los datos de AEMET."""
    print("\n=== Procesamiento de Datos AEMET ===")
    
    processed_df = df.copy()
    
    # 3. Normalizar nombres de columnas y convertir tipos de datos (ANTES DE IMPUTAR)
    print("3. Normalizando nombres de columnas y convirtiendo tipos de datos...")
    processed_df.columns = processed_df.columns.str.lower()
    
    # Asegurar que la columna fecha esté en formato datetime y ordenar
    if 'fecha' in processed_df.columns:
        if not pd.api.types.is_datetime64_any_dtype(processed_df['fecha']):
            processed_df['fecha'] = pd.to_datetime(processed_df['fecha'])
        processed_df.sort_values('fecha', inplace=True) # Asegurar orden cronológico

    # 1. Manejar valores faltantes - Estrategia Específica
    print("1. Manejando valores faltantes...")

    # 1.a. Imputación específica para 'prec' (NaN -> 0)
    if 'prec' in processed_df.columns:
        print("   - Imputando NaNs en 'prec' con 0.")
        processed_df['prec'].fillna(0, inplace=True)

    # 1.b. Imputación para otras columnas numéricas (ej. media o mediana)
    #     Identificar columnas numéricas que aún tienen NaNs (excluyendo 'prec' si ya se trató)
    numeric_cols_with_na = processed_df.select_dtypes(include=[np.number]).isnull().any()
    cols_to_impute = numeric_cols_with_na[numeric_cols_with_na].index.tolist()
    
    # Eliminar 'prec' de esta lista si ya fue imputada
    if 'prec' in cols_to_impute:
        cols_to_impute.remove('prec')

    for col in cols_to_impute:
        # Podrías elegir media o mediana. Mediana es más robusta a outliers.
        # O podrías usar ffill/bfill si la naturaleza temporal es más importante aquí
        # y no hay demasiados NaNs consecutivos.
        median_val = processed_df[col].median()
        processed_df[col].fillna(median_val, inplace=True)
        print(f"   - Imputando NaNs en '{col}' con la mediana ({median_val:.2f}).")


    # 2. Eliminar columnas con demasiados valores faltantes o poco relevantes
    #    (Esto se puede hacer antes si hay columnas que no quieres imputar)
    threshold = 0.5 # 50% de valores faltantes
    # Recalcular columnas a eliminar después de la imputación inicial si es necesario,
    # o ejecutar este paso antes de la imputación general si se prefiere.
    # Por ahora, lo mantenemos como estaba.
    cols_to_drop_post_imputation = [col for col in processed_df.columns if processed_df[col].isnull().mean() > threshold]
    if cols_to_drop_post_imputation:
        print(f"2. Eliminando columnas con más de {threshold*100}% de valores faltantes restantes: {cols_to_drop_post_imputation}")
        processed_df.drop(columns=cols_to_drop_post_imputation, inplace=True, errors='ignore')
    
    # 4. Crear características adicionales basadas en la fecha
    if 'fecha' in processed_df.columns:
        print("4. Creando características basadas en la fecha...")
        processed_df['mes'] = processed_df['fecha'].dt.month
        processed_df['dia'] = processed_df['fecha'].dt.day
        processed_df['dia_semana'] = processed_df['fecha'].dt.dayofweek
        processed_df['es_fin_semana'] = processed_df['dia_semana'].isin([5, 6]).astype(int)
        # Cálculo de estación ajustado para hemisferio norte:
        # (Diciembre, Enero, Febrero = 1 (Invierno))
        # (Marzo, Abril, Mayo = 2 (Primavera))
        # (Junio, Julio, Agosto = 3 (Verano))
        # (Septiembre, Octubre, Noviembre = 4 (Otoño))
        month_to_season = {1:1, 2:1, 3:2, 4:2, 5:2, 6:3, 7:3, 8:3, 9:4, 10:4, 11:4, 12:1}
        processed_df['estacion'] = processed_df['mes'].map(month_to_season)
        print(f"   - Características de fecha creadas: mes, dia, dia_semana, es_fin_semana, estacion")

    # 5. Detección y tratamiento de outliers (después de la imputación)
    print("5. Detectando y tratando valores atípicos...")
    # Asegurarse de que numeric_cols se define después de la posible eliminación de columnas
    # y se aplica solo a las columnas que realmente son numéricas y existen.
    current_numeric_cols = processed_df.select_dtypes(include=[np.number]).columns
    for col in current_numeric_cols:
        # Evitar aplicar a columnas binarias o categóricas codificadas numéricamente
        # si tienen pocos valores únicos, como 'es_fin_semana' o 'estacion'
        if processed_df[col].nunique() < 10: # Umbral ajustable
            continue

        Q1 = processed_df[col].quantile(0.25)
        Q3 = processed_df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        # Solo aplicar si IQR > 0 (evita problemas con columnas constantes)
        if IQR > 0:
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_count = ((processed_df[col] < lower_bound) | (processed_df[col] > upper_bound)).sum()
            outlier_percent = outliers_count / len(processed_df) * 100
            
            if outliers_count > 0:
                print(f"   - {col}: {outliers_count} valores atípicos ({outlier_percent:.2f}%)")
                # Recortar (capping) los outliers a un solo decimal
                processed_df[col] = np.clip(processed_df[col], lower_bound, upper_bound)
                # Redondear a un decimal
                processed_df[col] = processed_df[col].round(1)
                print(f"     - Valores atípicos en '{col}' recortados a los límites [{lower_bound:.2f}, {upper_bound:.2f}]")
        else:
            print(f"   - {col}: IQR es 0, no se aplica tratamiento de outliers.")
            
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

def main():
    """Función principal."""
    # Crear directorio para visualizaciones si no existe
    os.makedirs('data_treatment/aemet_visualizations', exist_ok=True)
    
    engine = connect_to_database()
    if engine is None:
        return
    
    df_aemet = load_data(engine, AEMET_POSTGRES_TABLE)
    if df_aemet is None:
        return
    
    explore_data(df_aemet) # Bueno para un análisis inicial
    
    df_aemet_processed = process_data(df_aemet.copy()) # Pasar copia para no alterar df_aemet original

    # OPCIONAL: Si quieres que la tabla tratada tenga continuidad temporal completa
    # (Este paso es similar al de tu script LSTM)
    # Primero, asegurar que 'fecha' es índice para resample
    if 'fecha' in df_aemet_processed.columns:
        print("\nVerificando y rellenando fechas faltantes para continuidad temporal...")
        df_aemet_processed.set_index('fecha', inplace=True)
        
        # Crear un rango de fechas completo desde min hasta max
        if not df_aemet_processed.empty:
            min_date = df_aemet_processed.index.min()
            max_date = df_aemet_processed.index.max()
            full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
            
            # Remuestrear. Usar mean() es opcional si esperas una fila por día.
            # Si ya tienes una fila por día, reindex puede ser suficiente.
            df_aemet_processed = df_aemet_processed.reindex(full_date_range)
            
            # Rellenar NaNs creados por el reindex (para todas las columnas numéricas)
            # Se podría hacer un ffill/bfill selectivo si algunas columnas no deben rellenarse así
            numeric_cols_for_ffill = df_aemet_processed.select_dtypes(include=np.number).columns
            for col in numeric_cols_for_ffill:
                 # No rellenar 'prec' si ya es 0 y queremos mantenerlo así en días nuevos
                if col == 'prec': # Los días nuevos tendrán NaN en 'prec'
                    df_aemet_processed[col].fillna(0, inplace=True) # Asumir no lluvia en días faltantes
                else:
                    df_aemet_processed[col].fillna(method='ffill', inplace=True)
                    df_aemet_processed[col].fillna(method='bfill', inplace=True)
            print(f"   - Fechas rellenadas. Nuevo shape: {df_aemet_processed.shape}")
        
        df_aemet_processed.reset_index(inplace=True)
        # Renombrar la columna de índice si es necesario (suele ser 'index' o 'fecha')
        if 'index' in df_aemet_processed.columns and 'fecha' not in df_aemet_processed.columns:
             df_aemet_processed.rename(columns={'index': 'fecha'}, inplace=True)

    pd.set_option('display.max_columns', None)
    print("\n=== Datos Procesados (info) ===")
    print(df_aemet_processed.info())
    print("\n=== Primeras filas de Datos Procesados ===")
    print(df_aemet_processed.head())

    # Columnas a eliminar ANTES de guardar en AEMET_POSTGRES_TABLE_TREATED
    # Estas son las que no quieres en tu tabla final "limpia" para la LSTM
    columns_to_remove_final = [
        'indicativo', 'nombre', 'provincia', 'altitud', 
        'latitud', 'longitud', # Geográficas, podrían ser útiles para otros modelos
        'horatmin', 'horatmax', 'horaracha', 'horapresmax', 
        'horapresmin', 'horahrmax', 'horahrmin', # Columnas de hora específicas
    ]
    # Filtrar la lista para solo incluir columnas que existen
    columns_to_remove_final_existing = [col for col in columns_to_remove_final if col in df_aemet_processed.columns]
    df_aemet_to_save = df_aemet_processed.drop(columns=columns_to_remove_final_existing, errors='ignore')
    # cambiamos la columna fecha a tipo datetime si no lo es
    if 'fecha' in df_aemet_to_save.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_aemet_to_save['fecha']):
            df_aemet_to_save['fecha'] = pd.to_datetime(df_aemet_to_save['fecha'])
    print("\n=== Columnas finales para guardar en la tabla tratada: ===")
    print(df_aemet_to_save.columns.tolist())

    save_to_database(df_aemet_to_save, engine, AEMET_POSTGRES_TABLE_TREATED)
    
    print("\n=== Resumen del Procesamiento ===")
    print(f"Dimensiones originales: {df_aemet.shape}")
    print(f"Dimensiones después del procesamiento (antes de eliminar cols finales): {df_aemet_processed.shape}")
    print(f"Dimensiones finales guardadas: {df_aemet_to_save.shape}")
    print(f"Tabla original: {AEMET_POSTGRES_TABLE}")
    print(f"Tabla procesada guardada en: {AEMET_POSTGRES_TABLE_TREATED}")

    # creamos un df sin las fechas, mes, dia, dia_semana, es_fin_semana y estacion
    df_aemet_to_production = df_aemet_to_save.drop(columns=['mes', 'dia', 'dia_semana', 'es_fin_semana', 'estacion'], errors='ignore')

    return df_aemet_to_production

if __name__ == "__main__":
    main()