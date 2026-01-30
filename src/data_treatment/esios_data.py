"""
Script creado por: Pablo Dueñas Fernández.
Este script procesa y analiza datos del mercado eléctrico obtenidos de ESIOS.
Realiza análisis exploratorio de precios y variables del mercado, genera
visualizaciones estadísticas y guarda los datos procesados para modelado predictivo.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine
import numpy as np
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# ESIOS parameters
ESIOS_TOKEN = os.getenv("ESIOS_TOKEN")
ESIOS_START_DATE = os.getenv("ESIOS_START_DATE")
ESIOS_END_DATE = os.getenv("ESIOS_END_DATE")
ESIOS_INDICATOR_ID = os.getenv("ESIOS_INDICATOR_ID")
ESIOS_POSTGRES_TABLE = os.getenv("ESIOS_POSTGRES_TABLE")
ESIOS_POSTGRES_TABLE_TREATED = os.getenv("ESIOS_POSTGRES_TABLE_TREATED")


def connect_to_db():
    """Create a connection to the PostgreSQL database"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    return engine

def fetch_esios_data(engine):
    """Fetch ESIOS data from PostgreSQL"""
    query = f"SELECT * FROM {ESIOS_POSTGRES_TABLE}"
    df = pd.read_sql(query, engine)
    return df

def analyze_esios_data(df):
    """Perform analysis on ESIOS data"""
    # Basic information
    print("\nBasic Information:")
    print(f"Total records: {len(df)}")
    print(f"Data columns: {df.columns.tolist()}")
    print("\nData types:")
    print(df.dtypes)
    
    # Check for missing values
    print("\nMissing values:")
    print(df.isnull().sum())
    
    # Convert datetime columns if necessary
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values('fecha').reset_index(drop=True)
    
    # Basic statistics
    print("\nBasic statistics:")
    print(df.describe())
    
    # Visualizations
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('ESIOS Data Analysis', fontsize=16, fontweight='bold')
    
    # 1. Time series plot for precio_excedente
    if 'precio_excedente' in df.columns and 'fecha' in df.columns:
        axes[0, 0].plot(df['fecha'], df['precio_excedente'], linewidth=0.8, color='blue', alpha=0.7)
        axes[0, 0].set_title('Evolución del Precio Excedente', fontweight='bold')
        axes[0, 0].set_xlabel('Fecha')
        axes[0, 0].set_ylabel('Precio Excedente (€/MWh)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Distribution of precio_excedente
    if 'precio_excedente' in df.columns:
        axes[0, 1].hist(df['precio_excedente'].dropna(), bins=50, alpha=0.7, color='green', edgecolor='black')
        axes[0, 1].set_title('Distribución del Precio Excedente', fontweight='bold')
        axes[0, 1].set_xlabel('Precio Excedente (€/MWh)')
        axes[0, 1].set_ylabel('Frecuencia')
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Correlation matrix
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 1:
        correlation_matrix = df[numeric_columns].corr()
        
        # Create correlation heatmap
        im = axes[1, 0].imshow(correlation_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        axes[1, 0].set_title('Matriz de Correlación', fontweight='bold')
        axes[1, 0].set_xticks(range(len(numeric_columns)))
        axes[1, 0].set_yticks(range(len(numeric_columns)))
        axes[1, 0].set_xticklabels(numeric_columns, rotation=45, ha='right')
        axes[1, 0].set_yticklabels(numeric_columns)
        
        # Add correlation values to the heatmap
        for i in range(len(numeric_columns)):
            for j in range(len(numeric_columns)):
                text = axes[1, 0].text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                     ha="center", va="center", color="black", fontsize=8)
        
        # Add colorbar
        plt.colorbar(im, ax=axes[1, 0], shrink=0.8)
    
    # 4. Energy generation comparison (renewable vs non-renewable)
    if 'Generación_renovable' in df.columns and 'Generación_no_renovable' in df.columns:
        renewable_avg = df['Generación_renovable'].mean()
        non_renewable_avg = df['Generación_no_renovable'].mean()
        
        categories = ['Renovable', 'No Renovable']
        values = [renewable_avg, non_renewable_avg]
        colors = ['green', 'red']
        
        bars = axes[1, 1].bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('Generación Promedio: Renovable vs No Renovable', fontweight='bold')
        axes[1, 1].set_ylabel('Generación Promedio (MWh)')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.0f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('esios_analysis.png', dpi=300, bbox_inches='tight')

    
    # Additional correlation analysis
    if 'precio_excedente' in df.columns and len(numeric_columns) > 1:
        print("\nCorrelación con precio_excedente:")
        price_correlations = df[numeric_columns].corr()['precio_excedente'].sort_values(ascending=False)
        for var, corr in price_correlations.items():
            if var != 'precio_excedente':
                print(f"{var}: {corr:.3f}")
    
    return df

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
    """Main function to run the analysis"""
    print(f"Analyzing ESIOS data from {ESIOS_START_DATE} to {ESIOS_END_DATE}")
    print(f"Using indicator ID: {ESIOS_INDICATOR_ID}")
    
    try:
        # Connect to database
        engine = connect_to_db()
        print("Successfully connected to PostgreSQL database")
        
        # Fetch data
        df = fetch_esios_data(engine)
        print(f"Retrieved {len(df)} records from {ESIOS_POSTGRES_TABLE}")
        
        # Analyze data
        df_analyzed = analyze_esios_data(df)
        
        # Clean data before saving
        df_analyzed.drop(columns=['fecha_date'], inplace=True, errors='ignore')
        
        # Save data back to PostgreSQL
        save_to_database(df_analyzed, engine, ESIOS_POSTGRES_TABLE_TREATED)
        
        return df_analyzed

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    main()
