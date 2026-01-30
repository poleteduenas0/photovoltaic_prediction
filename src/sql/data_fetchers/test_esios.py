"""
Script para probar ESIOS con rango corto de fechas
"""
import sys
from pathlib import Path
import time

root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.data_fetchers.esios_fetcher import ESIOSFetcher

def main():
    print("\n⏳ Esperando 3 segundos para que la API esté lista...")
    time.sleep(3)
    
    # Probar con solo 1 mes para verificar que funciona
    fetcher = ESIOSFetcher()
    result = fetcher.fetch_and_store(
        start_date="2024-12-01",
        end_date="2024-12-07"  # Solo 1 semana
    )
    
    if "error" not in result.get("api_response", {}):
        print(f"\n🎉 ¡ÉXITO! {result['total_records']} registros insertados")
        return 0
    else:
        print(f"\n❌ Error: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
