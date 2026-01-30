"""
Script simplificado para cargar solo datos de producción
"""
import sys
from pathlib import Path
import time

root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.data_fetchers.production_fetcher import ProductionFetcher

def main():
    print("\n⏳ Esperando 3 segundos para que la API esté lista...")
    time.sleep(3)
    
    fetcher = ProductionFetcher()
    result = fetcher.fetch_and_store()
    
    if "error" not in result.get("api_response", {}):
        print(f"\n🎉 ¡ÉXITO! {result['total_records']} registros insertados")
        return 0
    else:
        print(f"\n❌ Error: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
