"""
Script de prueba para verificar que los fetchers funcionan correctamente
"""
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.data_fetchers.production_fetcher import ProductionFetcher

def test_production():
    """Probar el fetcher de producción (más simple)"""
    print("\n" + "="*60)
    print("🧪 TEST: Production Fetcher")
    print("="*60 + "\n")
    
    fetcher = ProductionFetcher()
    
    # Solo cargar y procesar el CSV (sin enviar a API)
    df = fetcher.load_production_csv()
    
    if df is not None:
        print(f"✅ CSV cargado: {len(df)} registros")
        print(f"Columnas: {list(df.columns)}\n")
        print("Primeros 5 registros:")
        print(df.head())
        
        # Procesar datos
        df_processed = fetcher.process_production_data(df)
        
        if df_processed is not None:
            print(f"\n✅ Datos procesados: {len(df_processed)} registros")
            print("\nPrimeros 5 registros procesados:")
            print(df_processed.head())
            return True
    
    return False

if __name__ == "__main__":
    success = test_production()
    sys.exit(0 if success else 1)
