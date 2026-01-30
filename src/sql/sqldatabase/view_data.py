"""
Script para visualizar datos de la base de datos SQLite
"""
import sys
from pathlib import Path
import pandas as pd

root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.sqldatabase.database import engine

def print_separator(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def view_aemet_data(limit=10):
    """Ver datos AEMET"""
    query = f"""
    SELECT fecha, tmed, tmin, tmax, sol, prec, hrmedia
    FROM aemet_data 
    ORDER BY fecha DESC 
    LIMIT {limit}
    """
    df = pd.read_sql(query, engine)
    print(f"📊 Últimos {limit} registros AEMET:")
    print(df.to_string(index=False))
    return df

def view_esios_data(limit=10):
    """Ver datos ESIOS"""
    query = f"""
    SELECT fecha, precio_excedente
    FROM esios_data 
    ORDER BY fecha DESC 
    LIMIT {limit}
    """
    df = pd.read_sql(query, engine)
    print(f"⚡ Últimos {limit} registros ESIOS:")
    print(df.to_string(index=False))
    return df

def view_production_data(limit=10):
    """Ver datos de producción"""
    query = f"""
    SELECT fecha, totalproduction
    FROM production_data 
    ORDER BY fecha DESC 
    LIMIT {limit}
    """
    df = pd.read_sql(query, engine)
    print(f"☀️ Últimos {limit} registros de Producción:")
    print(df.to_string(index=False))
    return df

def view_statistics():
    """Ver estadísticas generales"""
    queries = {
        "AEMET": "SELECT COUNT(*) as total, MIN(fecha) as primera_fecha, MAX(fecha) as ultima_fecha FROM aemet_data",
        "ESIOS": "SELECT COUNT(*) as total, MIN(fecha) as primera_fecha, MAX(fecha) as ultima_fecha FROM esios_data",
        "Production": "SELECT COUNT(*) as total, MIN(fecha) as primera_fecha, MAX(fecha) as ultima_fecha FROM production_data"
    }
    
    print("📈 Estadísticas Generales:")
    print(f"\n{'Tabla':<15} {'Total':<10} {'Primera Fecha':<20} {'Última Fecha':<20}")
    print(f"{'-'*15} {'-'*10} {'-'*20} {'-'*20}")
    
    for table, query in queries.items():
        df = pd.read_sql(query, engine)
        if not df.empty:
            row = df.iloc[0]
            print(f"{table:<15} {row['total']:<10} {str(row['primera_fecha'])[:19]:<20} {str(row['ultima_fecha'])[:19]:<20}")

def view_date_range(start_date, end_date, table="aemet_data"):
    """Ver datos en un rango de fechas"""
    query = f"""
    SELECT * FROM {table}
    WHERE fecha BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY fecha
    """
    df = pd.read_sql(query, engine)
    print(f"📅 Datos de {table} entre {start_date} y {end_date}:")
    print(f"Total registros: {len(df)}\n")
    if not df.empty:
        print(df.head(10).to_string(index=False))
        if len(df) > 10:
            print(f"\n... y {len(df) - 10} registros más")
    return df

def main():
    print_separator("🔍 VISUALIZACIÓN DE DATOS - SQLITE")
    
    # 1. Estadísticas generales
    print_separator("1. ESTADÍSTICAS GENERALES")
    view_statistics()
    
    # 2. Últimos registros de cada tabla
    print_separator("2. ÚLTIMOS 5 REGISTROS - AEMET")
    view_aemet_data(limit=5)
    
    print_separator("3. ÚLTIMOS 5 REGISTROS - ESIOS")
    view_esios_data(limit=5)
    
    print_separator("4. ÚLTIMOS 5 REGISTROS - PRODUCCIÓN")
    view_production_data(limit=5)
    
    # 3. Ejemplo de consulta por rango de fechas
    print_separator("5. EJEMPLO: DATOS DE DICIEMBRE 2024")
    view_date_range("2024-12-01", "2024-12-31", "aemet_data")
    
    print(f"\n{'='*70}")
    print("✅ Visualización completada")
    print(f"{'='*70}\n")
    
    print("💡 Tip: Modifica este script para hacer tus propias consultas SQL")

if __name__ == "__main__":
    main()
