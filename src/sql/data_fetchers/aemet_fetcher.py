"""
AEMET Data Fetcher
Obtiene datos meteorológicos de AEMET y los inserta en SQLite vía FastAPI
"""
import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()


class AEMETFetcher:
    """Fetcher para datos meteorológicos de AEMET"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Args:
            api_url: URL base de la API FastAPI
        """
        self.api_url = api_url
        self.aemet_api_key = os.getenv("API_KEY_OPENDATA")
        self.station_id = os.getenv("AEMET_STATION_ID")
        
        if not self.aemet_api_key:
            raise ValueError("API_KEY_OPENDATA no encontrada en .env")
        if not self.station_id:
            raise ValueError("AEMET_STATION_ID no encontrada en .env")
    
    def format_aemet_date(self, date_str: str) -> str:
        """Convertir fecha a formato AEMET"""
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return dt_obj.strftime("%Y-%m-%dT00:00:00UTC")
    
    def get_aemet_daily_climatology(
        self, 
        start_date_str: str, 
        end_date_str: str,
        max_retries: int = 3
    ) -> Optional[List[Dict]]:
        """
        Obtener datos diarios de AEMET con reintentos
        
        Args:
            start_date_str: Fecha inicio (YYYY-MM-DD)
            end_date_str: Fecha fin (YYYY-MM-DD)
            max_retries: Número máximo de reintentos
        
        Returns:
            Lista de diccionarios con datos meteorológicos
        """
        base_url = "https://opendata.aemet.es/opendata"
        fecha_ini = self.format_aemet_date(start_date_str)
        fecha_fin = self.format_aemet_date(end_date_str)
        endpoint = f"/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{self.station_id}"
        url_meta = base_url + endpoint
        headers = {'api_key': self.aemet_api_key, 'Accept': 'application/json'}
        
        for attempt in range(max_retries):
            try:
                # Primera petición para obtener URL de datos
                resp = requests.get(url_meta, headers=headers, timeout=30)
                
                # Si es 429 (Too Many Requests), esperar y reintentar
                if resp.status_code == 429:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 segundos
                    print(f"   ⏳ Rate limit alcanzado. Esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                resp.raise_for_status()
                meta = resp.json()
                
                if meta.get('estado') != 200:
                    print(f"   ⚠️  Error AEMET: {meta.get('descripcion')}")
                    return None
                
                data_url = meta.get('datos')
                
                # Pequeño delay antes de segunda petición
                time.sleep(1)
                
                # Segunda petición para obtener datos reales
                resp2 = requests.get(data_url, headers=headers, timeout=30)
                resp2.raise_for_status()
                return resp2.json()
                
            except requests.exceptions.HTTPError as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"   ⚠️  Error HTTP {e.response.status_code}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Error obteniendo datos AEMET: {e}")
                    return None
            except Exception as e:
                print(f"   ❌ Error obteniendo datos AEMET: {e}")
                return None
        
        return None
    
    def process_aemet_data(
        self, 
        datos: List[Dict], 
        start_date_str: str, 
        end_date_str: str
    ) -> Optional[pd.DataFrame]:
        """
        Procesar datos AEMET y asegurar continuidad temporal
        
        Args:
            datos: Lista de datos crudos de AEMET
            start_date_str: Fecha inicio
            end_date_str: Fecha fin
        
        Returns:
            DataFrame procesado con todas las fechas del rango
        """
        if not datos:
            return None
        
        df = pd.DataFrame(datos)
        
        # Convertir columnas numéricas
        cols_to_convert = [
            'tmed', 'prec', 'tmin', 'tmax', 'velmedia', 'racha', 
            'presMax', 'presMin', 'hrMedia', 'hrMax', 'hrMin', 'sol'
        ]
        
        for col in cols_to_convert:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = df[col].str.replace('Ip', '0.0', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convertir fecha
        df['fecha'] = pd.to_datetime(df['fecha'], format="%Y-%m-%d", errors='coerce')
        
        # Generar rango completo de fechas
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        full_dates = pd.date_range(start=start, end=end)
        df_full = pd.DataFrame({'fecha': full_dates})
        
        # Merge con rango completo
        df_merged = df_full.merge(df, on='fecha', how='left')
        
        # Añadir características temporales
        df_merged['mes'] = df_merged['fecha'].dt.month
        df_merged['dia'] = df_merged['fecha'].dt.day
        df_merged['dia_semana'] = df_merged['fecha'].dt.dayofweek
        df_merged['es_fin_semana'] = df_merged['dia_semana'].isin([5, 6])
        
        # Estación del año
        def get_season(month):
            if month in [12, 1, 2]:
                return 1  # Invierno
            elif month in [3, 4, 5]:
                return 2  # Primavera
            elif month in [6, 7, 8]:
                return 3  # Verano
            else:
                return 4  # Otoño
        
        df_merged['estacion'] = df_merged['mes'].apply(get_season)
        
        return df_merged
    
    def split_date_range(
        self, 
        start_date_str: str, 
        end_date_str: str, 
        max_months: int = 6
    ) -> List[tuple]:
        """
        Dividir rango de fechas en segmentos (API AEMET tiene límites)
        
        Args:
            start_date_str: Fecha inicio
            end_date_str: Fecha fin
            max_months: Máximo de meses por segmento
        
        Returns:
            Lista de tuplas (fecha_inicio, fecha_fin)
        """
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        max_days = max_months * 30
        segments = []
        current = start
        
        while current < end:
            next_date = min(current + timedelta(days=max_days), end)
            segments.append((
                current.strftime("%Y-%m-%d"),
                next_date.strftime("%Y-%m-%d")
            ))
            current = next_date + timedelta(days=1)
        
        return segments
    
    def send_to_api(self, df: pd.DataFrame) -> Dict:
        """
        Enviar datos a la API FastAPI
        
        Args:
            df: DataFrame con datos procesados
        
        Returns:
            Diccionario con resultado de la operación
        """
        # Renombrar columnas para coincidir con schema
        df_renamed = df.rename(columns={
            'presMax': 'presmax',
            'presMin': 'presmin',
            'hrMedia': 'hrmedia',
            'hrMax': 'hrmax',
            'hrMin': 'hrmin'
        })
        
        # Convertir a formato JSON compatible con la API
        records = []
        for _, row in df_renamed.iterrows():
            record = {
                'fecha': row['fecha'].isoformat(),
                'tmed': float(row['tmed']) if pd.notna(row['tmed']) else None,
                'tmin': float(row['tmin']) if pd.notna(row['tmin']) else None,
                'tmax': float(row['tmax']) if pd.notna(row['tmax']) else None,
                'prec': float(row['prec']) if pd.notna(row['prec']) else None,
                'velmedia': float(row['velmedia']) if pd.notna(row['velmedia']) else None,
                'racha': float(row['racha']) if pd.notna(row['racha']) else None,
                'presmax': float(row['presmax']) if pd.notna(row['presmax']) else None,
                'presmin': float(row['presmin']) if pd.notna(row['presmin']) else None,
                'hrmedia': float(row['hrmedia']) if pd.notna(row['hrmedia']) else None,
                'hrmax': float(row['hrmax']) if pd.notna(row['hrmax']) else None,
                'hrmin': float(row['hrmin']) if pd.notna(row['hrmin']) else None,
                'sol': float(row['sol']) if pd.notna(row['sol']) else None,
                'mes': int(row['mes']) if pd.notna(row['mes']) else None,
                'dia': int(row['dia']) if pd.notna(row['dia']) else None,
                'dia_semana': int(row['dia_semana']) if pd.notna(row['dia_semana']) else None,
                'es_fin_semana': bool(row['es_fin_semana']) if pd.notna(row['es_fin_semana']) else False,
                'estacion': int(row['estacion']) if pd.notna(row['estacion']) else None
            }
            records.append(record)
        
        # Enviar a API (bulk insert)
        try:
            response = requests.post(
                f"{self.api_url}/aemet/bulk",
                json=records,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error enviando datos a API: {e}")
            return {"error": str(e)}
    
    def fetch_and_store(
        self, 
        start_date: str, 
        end_date: str,
        progress_callback=None
    ) -> Dict:
        """
        Proceso completo: fetch desde AEMET y store en SQLite
        
        Args:
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            progress_callback: Función callback para reportar progreso
        
        Returns:
            Diccionario con estadísticas de la operación
        """
        print(f"\n{'='*60}")
        print(f"🌤️  Obteniendo datos AEMET")
        print(f"{'='*60}")
        print(f"Fecha inicio: {start_date}")
        print(f"Fecha fin: {end_date}")
        print(f"Estación: {self.station_id}\n")
        
        # Dividir en segmentos
        segments = self.split_date_range(start_date, end_date)
        print(f"📊 Total de segmentos: {len(segments)}\n")
        
        all_data = []
        
        for i, (seg_start, seg_end) in enumerate(segments, 1):
            print(f"⏳ Segmento {i}/{len(segments)}: {seg_start} a {seg_end}")
            
            # Delay entre segmentos para evitar rate limits (excepto el primero)
            if i > 1:
                time.sleep(3)
            
            # Obtener datos de AEMET
            datos = self.get_aemet_daily_climatology(seg_start, seg_end)
            
            if datos:
                # Procesar datos
                df_processed = self.process_aemet_data(datos, seg_start, seg_end)
                
                if df_processed is not None:
                    all_data.append(df_processed)
                    print(f"   ✅ {len(df_processed)} registros procesados")
                else:
                    print(f"   ⚠️  No se pudieron procesar los datos")
            else:
                print(f"   ⚠️  No se obtuvieron datos")
            
            if progress_callback:
                progress_callback(i, len(segments))
        
        # Concatenar todos los datos
        if not all_data:
            return {"error": "No se obtuvieron datos", "total_records": 0}
        
        df_final = pd.concat(all_data, ignore_index=True)
        print(f"\n📦 Total de registros a insertar: {len(df_final)}")
        
        # Enviar a API
        print(f"🚀 Enviando datos a la API...\n")
        result = self.send_to_api(df_final)
        
        if "error" not in result:
            print(f"✅ Datos insertados correctamente: {result.get('count', 0)} registros")
        else:
            print(f"❌ Error: {result['error']}")
        
        print(f"\n{'='*60}\n")
        
        return {
            "total_records": len(df_final),
            "api_response": result
        }


def main():
    """Función principal para ejecutar el fetcher"""
    # Obtener fechas desde .env o usar defaults
    start_date = os.getenv("AEMET_START_DATE", "2023-01-01")
    end_date = os.getenv("AEMET_END_DATE", "2024-12-31")
    
    fetcher = AEMETFetcher()
    result = fetcher.fetch_and_store(start_date, end_date)
    
    return result


if __name__ == "__main__":
    main()
