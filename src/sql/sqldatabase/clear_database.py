"""
Script para limpiar la base de datos SQLite
"""
import os
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from src.sql.sqldatabase.database import engine, SQLITE_DB_PATH
from sqlalchemy import text

def main():
    print(f"\n{'='*60}")
    print(f"🗑️  LIMPIANDO BASE DE DATOS")
    print(f"{'='*60}\n")
    print(f"Base de datos: {SQLITE_DB_PATH}\n")
    
    with engine.connect() as conn:
        # Contar registros antes
        aemet_before = conn.execute(text("SELECT COUNT(*) FROM aemet_data")).scalar()
        esios_before = conn.execute(text("SELECT COUNT(*) FROM esios_data")).scalar()
        production_before = conn.execute(text("SELECT COUNT(*) FROM production_data")).scalar()
        
        print(f"Registros actuales:")
        print(f"  - AEMET: {aemet_before}")
        print(f"  - ESIOS: {esios_before}")
        print(f"  - Production: {production_before}")
        
        # Limpiar tablas
        print(f"\n🧹 Limpiando tablas...")
        conn.execute(text("DELETE FROM aemet_data"))
        conn.execute(text("DELETE FROM esios_data"))
        conn.execute(text("DELETE FROM production_data"))
        conn.execute(text("DELETE FROM model_metrics"))
        conn.execute(text("DELETE FROM forecasts"))
        conn.commit()
        
        print(f"✅ Todas las tablas limpiadas")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
