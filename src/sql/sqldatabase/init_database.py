"""
Script de inicialización de base de datos SQLite
Ejecutar una sola vez para crear todas las tablas
"""
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.sqldatabase.database import init_db, engine, SQLITE_DB_PATH
from src.sql.sqldatabase.models import (
    AEMETData,
    ESIOSData,
    ProductionData,
    ModelMetrics,
    Forecast
)

def main():
    """
    Inicializa la base de datos y crea todas las tablas
    """
    print("=" * 60)
    print("🚀 Inicializando Base de Datos SQLite")
    print("=" * 60)
    print(f"\n📁 Ubicación: {SQLITE_DB_PATH}\n")
    
    # Crear todas las tablas
    init_db()
    
    # Verificar tablas creadas
    print("\n📊 Tablas creadas:")
    print("   ✅ aemet_data")
    print("   ✅ esios_data")
    print("   ✅ production_data")
    print("   ✅ model_metrics")
    print("   ✅ forecasts")
    
    # Verificar conexión
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            
            print(f"\n✔️  Base de datos verificada: {len(tables)} tablas")
            print("\n" + "=" * 60)
            print("✅ Inicialización completada con éxito")
            print("=" * 60)
            print("\n💡 Próximos pasos:")
            print("   1. Ejecutar: uv run uvicorn src.sql.sqldatabase.api:app --reload")
            print("   2. Abrir: http://localhost:8000/docs")
            print("   3. Usar la API para insertar datos\n")
            
    except Exception as e:
        print(f"\n❌ Error verificando base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
