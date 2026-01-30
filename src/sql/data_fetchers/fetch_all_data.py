"""
Master Data Fetcher
Script principal para obtener todos los datos (AEMET, ESIOS, Production)
y almacenarlos en SQLite
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Añadir el directorio raíz al path
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.data_fetchers.aemet_fetcher import AEMETFetcher
from src.sql.data_fetchers.esios_fetcher import ESIOSFetcher
from src.sql.data_fetchers.production_fetcher import ProductionFetcher

load_dotenv()


def print_header(title: str):
    """Imprimir header formateado"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def main():
    """Ejecutar todos los fetchers en secuencia"""
    start_time = datetime.now()
    
    print_header("🚀 INICIANDO CARGA DE DATOS")
    print(f"⏰ Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # ================================
    # 1. DATOS AEMET
    # ================================
    try:
        print_header("1️⃣  DATOS METEOROLÓGICOS (AEMET)")
        
        aemet_start = os.getenv("AEMET_START_DATE", "2023-01-01")
        aemet_end = os.getenv("AEMET_END_DATE", "2024-12-31")
        
        aemet_fetcher = AEMETFetcher()
        results['aemet'] = aemet_fetcher.fetch_and_store(aemet_start, aemet_end)
        
    except Exception as e:
        print(f"❌ Error en AEMET fetcher: {e}")
        results['aemet'] = {"error": str(e), "total_records": 0}
    
    # ================================
    # 2. DATOS ESIOS
    # ================================
    try:
        print_header("2️⃣  DATOS DEL MERCADO ELÉCTRICO (ESIOS)")
        
        esios_start = os.getenv("ESIOS_START_DATE", "2023-01-01")
        esios_end = os.getenv("ESIOS_END_DATE", "2024-12-31")
        
        esios_fetcher = ESIOSFetcher()
        results['esios'] = esios_fetcher.fetch_and_store(esios_start, esios_end)
        
    except Exception as e:
        print(f"❌ Error en ESIOS fetcher: {e}")
        results['esios'] = {"error": str(e), "total_records": 0}
    
    # ================================
    # 3. DATOS DE PRODUCCIÓN
    # ================================
    try:
        print_header("3️⃣  DATOS DE PRODUCCIÓN FOTOVOLTAICA")
        
        production_csv = os.getenv("PRODUCTION_CSV_PATH")
        
        production_fetcher = ProductionFetcher()
        results['production'] = production_fetcher.fetch_and_store(production_csv)
        
    except Exception as e:
        print(f"❌ Error en Production fetcher: {e}")
        results['production'] = {"error": str(e), "total_records": 0}
    
    # ================================
    # RESUMEN FINAL
    # ================================
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("📊 RESUMEN DE CARGA DE DATOS")
    
    total_records = 0
    
    print("Resultados por fuente de datos:")
    print(f"\n  {'Fuente':<20} {'Registros':<15} {'Estado'}")
    print(f"  {'-'*20} {'-'*15} {'-'*20}")
    
    for source, result in results.items():
        records = result.get('total_records', 0)
        total_records += records
        status = "✅ OK" if 'error' not in result else f"❌ {result['error'][:30]}"
        print(f"  {source.upper():<20} {records:<15} {status}")
    
    print(f"\n  {'TOTAL':<20} {total_records:<15}")
    
    print(f"\n⏱️  Tiempo total: {duration.total_seconds():.2f} segundos")
    print(f"⏰ Hora de finalización: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n{'='*70}")
    print(f"  ✅ PROCESO COMPLETADO")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    results = main()
