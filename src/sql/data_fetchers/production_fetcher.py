"""
Production Data Fetcher
Lee datos de producción fotovoltaica desde CSV y los inserta en SQLite
"""
import os
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class ProductionFetcher:
    """Fetcher para datos de producción fotovoltaica"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Args:
            api_url: URL base de la API FastAPI
        """
        self.api_url = api_url
        self.csv_path = os.getenv(
            "PRODUCTION_CSV_PATH",
            "data/CDGVSP_01012023-31122024.csv"
        )
    
    def load_production_csv(self, csv_path: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Cargar datos de producción desde CSV
        
        Args:
            csv_path: Ruta al archivo CSV (opcional, usa default si no se proporciona)
        
        Returns:
            DataFrame con datos de producción
        """
        path = csv_path or self.csv_path
        
        if not os.path.exists(path):
            print(f"❌ Error: Archivo no encontrado: {path}")
            return None
        
        try:
            print(f"📂 Leyendo archivo: {path}")
            
            # Intentar con diferentes encodings y separadores
            try:
                df = pd.read_csv(path, sep=";", encoding="latin1")
            except:
                try:
                    df = pd.read_csv(path, sep=",", encoding="utf-8")
                except:
                    df = pd.read_csv(path, sep=";", encoding="utf-8")
            
            print(f"   ✅ Archivo leído: {len(df)} registros")
            print(f"   Columnas: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error leyendo CSV: {e}")
            return None
    
    def process_production_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Procesar datos de producción para formato de la API
        
        Args:
            df: DataFrame crudo desde CSV
        
        Returns:
            DataFrame procesado
        """
        try:
            # Normalizar nombres de columnas
            df.columns = df.columns.str.replace(" ", "_").str.replace(".", "_").str.lower()
            
            print(f"🔄 Procesando datos de producción...")
            print(f"   Columnas normalizadas: {list(df.columns)}")
            
            # Buscar columnas de fecha y producción (adaptar según tu CSV)
            date_col = None
            production_col = None
            
            # Buscar columna de fecha
            for col in df.columns:
                if any(word in col.lower() for word in ['fecha', 'date', 'time', 'timestamp']):
                    date_col = col
                    break
            
            # Buscar columna de producción
            for col in df.columns:
                if any(word in col.lower() for word in ['produccion', 'production', 'total', 'generation', 'generacion']):
                    production_col = col
                    break
            
            if not date_col:
                print("⚠️  No se encontró columna de fecha. Usando primera columna.")
                date_col = df.columns[0]
            
            if not production_col:
                print("⚠️  No se encontró columna de producción. Usando segunda columna.")
                production_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
            print(f"   📅 Columna fecha: {date_col}")
            print(f"   ⚡ Columna producción: {production_col}")
            
            # Crear DataFrame limpio
            df_clean = pd.DataFrame()
            
            # Convertir fecha (especificar dayfirst=True para formato DD.MM.YYYY)
            df_clean['fecha'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
            
            # Convertir producción a numérico
            if df[production_col].dtype == 'object':
                df_clean['totalproduction'] = df[production_col].str.replace(',', '.').astype(float)
            else:
                df_clean['totalproduction'] = df[production_col].astype(float)
            
            # Eliminar filas con valores nulos
            df_clean = df_clean.dropna()
            
            # Ordenar por fecha
            df_clean = df_clean.sort_values('fecha').reset_index(drop=True)
            
            print(f"   ✅ Datos procesados: {len(df_clean)} registros válidos")
            
            return df_clean
            
        except Exception as e:
            print(f"❌ Error procesando datos: {e}")
            return None
    
    def send_to_api(self, df: pd.DataFrame) -> Dict:
        """
        Enviar datos a la API FastAPI
        
        Args:
            df: DataFrame con datos procesados
        
        Returns:
            Diccionario con resultado de la operación
        """
        # Convertir a formato JSON compatible con la API
        records = []
        for _, row in df.iterrows():
            record = {
                'fecha': row['fecha'].isoformat(),
                'totalproduction': float(row['totalproduction'])
            }
            records.append(record)
        
        # Enviar a API (bulk insert)
        try:
            response = requests.post(
                f"{self.api_url}/production/bulk",
                json=records,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error enviando datos a API: {e}")
            return {"error": str(e)}
    
    def fetch_and_store(
        self,
        csv_path: Optional[str] = None,
        progress_callback=None
    ) -> Dict:
        """
        Proceso completo: leer CSV y store en SQLite
        
        Args:
            csv_path: Ruta al archivo CSV (opcional)
            progress_callback: Función callback para reportar progreso
        
        Returns:
            Diccionario con estadísticas de la operación
        """
        print(f"\n{'='*60}")
        print(f"📊 Procesando datos de producción fotovoltaica")
        print(f"{'='*60}\n")
        
        # Cargar CSV
        df = self.load_production_csv(csv_path)
        
        if df is None:
            return {"error": "Error cargando CSV", "total_records": 0}
        
        if progress_callback:
            progress_callback(1, 3)
        
        # Procesar datos
        df_processed = self.process_production_data(df)
        
        if df_processed is None:
            return {"error": "Error procesando datos", "total_records": 0}
        
        if progress_callback:
            progress_callback(2, 3)
        
        print(f"\n📦 Total de registros a insertar: {len(df_processed)}")
        
        # Enviar a API
        print(f"🚀 Enviando datos a la API...\n")
        result = self.send_to_api(df_processed)
        
        if "error" not in result:
            print(f"✅ Datos insertados correctamente: {result.get('count', 0)} registros")
        else:
            print(f"❌ Error: {result['error']}")
        
        if progress_callback:
            progress_callback(3, 3)
        
        print(f"\n{'='*60}\n")
        
        return {
            "total_records": len(df_processed),
            "api_response": result
        }


def main():
    """Función principal para ejecutar el fetcher"""
    csv_path = os.getenv("PRODUCTION_CSV_PATH")
    
    fetcher = ProductionFetcher()
    result = fetcher.fetch_and_store(csv_path)
    
    return result


if __name__ == "__main__":
    main()
