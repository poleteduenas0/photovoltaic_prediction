"""
ESIOS Data Fetcher
Obtiene datos del mercado eléctrico español (ESIOS/REE) y los inserta en SQLite
"""
import os
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()


class ESIOSFetcher:
    """Fetcher para datos del mercado eléctrico (ESIOS)"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Args:
            api_url: URL base de la API FastAPI
        """
        self.api_url = api_url
        self.esios_token = os.getenv("ESIOS_TOKEN")
        self.region_id = os.getenv("ESIOS_REGION_ID", "3")  # Península
        
        # Indicadores a descargar
        self.indicators = {
            '1739': 'precio_excedente',
            # Puedes añadir más indicadores aquí:
            # '10148': 'demanda_peninsular',
            # '600': 'precio_spot',
            # '12': 'generacion_eolica',
            # '14': 'generacion_solar'
        }
        
        if not self.esios_token:
            raise ValueError("ESIOS_TOKEN no encontrado en .env")
    
    def fetch_indicator(
        self, 
        indicator_id: str, 
        col_name: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Obtener datos de un indicador específico de ESIOS
        
        Args:
            indicator_id: ID del indicador ESIOS
            col_name: Nombre de la columna para este indicador
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
        
        Returns:
            DataFrame con fecha y valor del indicador
        """
        url = f"https://api.esios.ree.es/indicators/{indicator_id}"
        params = {
            'start_date': f"{start_date}T00:00:00",
            'end_date': f"{end_date}T23:59:59",
            'geo_ids[]': self.region_id,
            'time_trunc': 'hour'
        }
        headers = {
            'Accept': 'application/json; application/vnd.esios-api-v2+json',
            'x-api-key': self.esios_token.strip()
        }
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json().get('indicator', {}).get('values', [])
            
            if not data:
                print(f"⚠️  No hay datos para el indicador {indicator_id}")
                return None
            
            df = pd.DataFrame(data)
            
            # Debug: mostrar columnas disponibles
            print(f"   Columnas recibidas: {list(df.columns)}")
            
            # Identificar columnas de fecha y valor
            # La API puede devolver diferentes nombres de columnas
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            value_cols = [col for col in df.columns if 'value' in col.lower()]
            
            if not date_cols or not value_cols:
                print(f"⚠️  No se encontraron columnas de fecha/valor en {list(df.columns)}")
                return None
            
            # Renombrar usando las columnas detectadas
            df = df.rename(columns={date_cols[0]: 'fecha', value_cols[0]: col_name})
            # Convertir fecha a UTC para evitar problemas con zonas horarias mixtas
            df['fecha'] = pd.to_datetime(df['fecha'], utc=True)
            
            print(f"   ✅ Indicador {indicator_id} ({col_name}): {len(df)} registros")
            
            return df[['fecha', col_name]]
            
        except Exception as e:
            print(f"❌ Error obteniendo indicador {indicator_id}: {e}")
            return None
    
    def process_esios_data(self, dfs: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Combinar múltiples indicadores en un único DataFrame
        
        Args:
            dfs: Lista de DataFrames con indicadores individuales
        
        Returns:
            DataFrame combinado con todos los indicadores
        """
        if not dfs:
            return None
        
        # Merge de todos los DataFrames sobre la columna fecha
        df_all = dfs[0]
        for df_next in dfs[1:]:
            df_all = df_all.merge(df_next, on='fecha', how='outer')
        
        # Ordenar por fecha
        df_all = df_all.sort_values('fecha').reset_index(drop=True)
        
        # Forward-fill para rellenar valores faltantes (usando nueva sintaxis)
        df_all = df_all.ffill()
        
        return df_all
    
    def send_to_api(self, df: pd.DataFrame) -> Dict:
        """
        Enviar datos a la API FastAPI
        
        Args:
            df: DataFrame con datos procesados
        
        Returns:
            Diccionario con resultado de la operación
        """
        # Asegurar que fecha es datetime y convertir a UTC sin timezone info
        df['fecha'] = pd.to_datetime(df['fecha'], utc=True).dt.tz_localize(None)
        
        # Convertir a formato JSON compatible con la API
        records = []
        for _, row in df.iterrows():
            record = {
                'fecha': row['fecha'].isoformat(),
                'precio_excedente': float(row['precio_excedente']) if pd.notna(row.get('precio_excedente')) else None,
                'solar_fotovoltaica': float(row['solar_fotovoltaica']) if pd.notna(row.get('solar_fotovoltaica')) else None,
                'eolica': float(row['eolica']) if pd.notna(row.get('eolica')) else None,
                'hidraulica': float(row['hidraulica']) if pd.notna(row.get('hidraulica')) else None,
                'generacion_renovable': float(row['generacion_renovable']) if pd.notna(row.get('generacion_renovable')) else None,
                'nuclear': float(row['nuclear']) if pd.notna(row.get('nuclear')) else None,
                'ciclo_combinado': float(row['ciclo_combinado']) if pd.notna(row.get('ciclo_combinado')) else None,
                'generacion_no_renovable': float(row['generacion_no_renovable']) if pd.notna(row.get('generacion_no_renovable')) else None,
                'demanda': float(row['demanda']) if pd.notna(row.get('demanda')) else None
            }
            records.append(record)
        
        # Enviar a API (bulk insert)
        try:
            response = requests.post(
                f"{self.api_url}/esios/bulk",
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
        start_date: str,
        end_date: str,
        progress_callback=None
    ) -> Dict:
        """
        Proceso completo: fetch desde ESIOS y store en SQLite
        
        Args:
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            progress_callback: Función callback para reportar progreso
        
        Returns:
            Diccionario con estadísticas de la operación
        """
        print(f"\n{'='*60}")
        print(f"⚡ Obteniendo datos ESIOS")
        print(f"{'='*60}")
        print(f"Fecha inicio: {start_date}")
        print(f"Fecha fin: {end_date}")
        print(f"Indicadores: {len(self.indicators)}\n")
        
        dfs = []
        total_indicators = len(self.indicators)
        
        for i, (ind_id, col_name) in enumerate(self.indicators.items(), 1):
            print(f"📊 [{i}/{total_indicators}] Descargando indicador {ind_id} → '{col_name}'")
            
            df_ind = self.fetch_indicator(ind_id, col_name, start_date, end_date)
            
            if df_ind is not None:
                dfs.append(df_ind)
            
            if progress_callback:
                progress_callback(i, total_indicators)
        
        if not dfs:
            return {"error": "No se obtuvieron datos", "total_records": 0}
        
        # Combinar todos los indicadores
        print(f"\n🔄 Combinando indicadores...")
        df_final = self.process_esios_data(dfs)
        
        if df_final is None:
            return {"error": "Error procesando datos", "total_records": 0}
        
        print(f"📦 Total de registros a insertar: {len(df_final)}")
        
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
    start_date = os.getenv("ESIOS_START_DATE", "2023-01-01")
    end_date = os.getenv("ESIOS_END_DATE", "2024-12-31")
    
    fetcher = ESIOSFetcher()
    result = fetcher.fetch_and_store(start_date, end_date)
    
    return result


if __name__ == "__main__":
    main()
