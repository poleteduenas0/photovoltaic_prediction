import psycopg2
import pandas as pd
from datetime import datetime
import sys
import os

# Añadir el directorio padre al path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.database import get_db_connection
except ImportError:
    # Configuración alternativa si no existe el módulo config
    def get_db_connection():
        return psycopg2.connect(
            host="localhost",
            database="db_tfm",
            user="tfm_user", 
            password="tfm_password"  # Cambia por tu password
        )

def mostrar_forecast_por_tipo(cursor, tipo_modelo):
    """
    Mostrar forecast agrupadas por tipo de modelo
    """
    print(f"\n{'='*80}")
    print(f"forecast - MODELO {tipo_modelo.upper()}")
    print(f"{'='*80}")
    
    # Obtener variables únicas para este tipo de modelo
    cursor.execute("""
        SELECT DISTINCT variable_objetivo 
        FROM forecast 
        WHERE tipo_modelo = %s 
        ORDER BY variable_objetivo
    """, (tipo_modelo,))
    
    variables = cursor.fetchall()
    
    if not variables:
        print(f"No se encontraron forecast para el modelo {tipo_modelo}")
        return
    
    for (variable,) in variables:
        print(f"\n{'-'*60}")
        print(f"Variable: {variable}")
        print(f"{'-'*60}")
        
        # Obtener forecast más recientes para esta variable y modelo
        cursor.execute("""
            SELECT fecha_prediccion, valor_prediccion, fecha_creacion
            FROM forecast 
            WHERE tipo_modelo = %s AND variable_objetivo = %s
            ORDER BY fecha_creacion DESC, fecha_prediccion ASC
            LIMIT 7
        """, (tipo_modelo, variable))
        
        forecast = cursor.fetchall()
        
        if forecast:
            print(f"{'Fecha Predicción':<20} {'Valor':<15} {'Fecha Creación':<20}")
            print(f"{'-'*55}")
            
            for fecha_pred, valor, fecha_creacion in forecast:
                fecha_pred_str = fecha_pred.strftime("%Y-%m-%d") if fecha_pred else "N/A"
                fecha_creacion_str = fecha_creacion.strftime("%Y-%m-%d %H:%M") if fecha_creacion else "N/A"
                print(f"{fecha_pred_str:<20} {valor:<15.4f} {fecha_creacion_str:<20}")
        else:
            print("No hay forecast disponibles")

def mostrar_resumen_general(cursor):
    """
    Mostrar resumen general de todas las forecast
    """
    print(f"\n{'='*80}")
    print("RESUMEN GENERAL DE forecast")
    print(f"{'='*80}")
    
    # Resumen por tipo de modelo y variable
    cursor.execute("""
        SELECT 
            tipo_modelo,
            variable_objetivo,
            COUNT(*) as total_forecast,
            MIN(fecha_prediccion) as fecha_min,
            MAX(fecha_prediccion) as fecha_max,
            AVG(valor_prediccion) as valor_promedio,
            MAX(fecha_creacion) as ultima_actualizacion
        FROM forecast 
        GROUP BY tipo_modelo, variable_objetivo
        ORDER BY tipo_modelo, variable_objetivo
    """)
    
    resultados = cursor.fetchall()
    
    if resultados:
        print(f"{'Modelo':<12} {'Variable':<20} {'Total':<8} {'Fecha Min':<12} {'Fecha Max':<12} {'Promedio':<12} {'Última Act.':<12}")
        print(f"{'-'*100}")
        
        for row in resultados:
            tipo_modelo, variable, total, fecha_min, fecha_max, promedio, ultima_act = row
            fecha_min_str = fecha_min.strftime("%Y-%m-%d") if fecha_min else "N/A"
            fecha_max_str = fecha_max.strftime("%Y-%m-%d") if fecha_max else "N/A"
            ultima_act_str = ultima_act.strftime("%m-%d %H:%M") if ultima_act else "N/A"
            
            print(f"{tipo_modelo:<12} {variable:<20} {total:<8} {fecha_min_str:<12} {fecha_max_str:<12} {promedio:<12.2f} {ultima_act_str:<12}")
    else:
        print("No se encontraron forecast en la base de datos")

def mostrar_forecast_recientes(cursor, limite=10):
    """
    Mostrar las forecast más recientes de todos los modelos
    """
    print(f"\n{'='*80}")
    print(f"ÚLTIMAS {limite} forecast CREADAS")
    print(f"{'='*80}")
    
    cursor.execute("""
        SELECT 
            tipo_modelo,
            variable_objetivo,
            fecha_prediccion,
            valor_prediccion,
            fecha_creacion
        FROM forecast 
        ORDER BY fecha_creacion DESC
        LIMIT %s
    """, (limite,))
    
    forecast = cursor.fetchall()
    
    if forecast:
        print(f"{'Modelo':<12} {'Variable':<20} {'Fecha Pred.':<12} {'Valor':<12} {'Creación':<16}")
        print(f"{'-'*80}")
        
        for row in forecast:
            tipo_modelo, variable, fecha_pred, valor, fecha_creacion = row
            fecha_pred_str = fecha_pred.strftime("%Y-%m-%d") if fecha_pred else "N/A"
            fecha_creacion_str = fecha_creacion.strftime("%m-%d %H:%M") if fecha_creacion else "N/A"
            
            print(f"{tipo_modelo:<12} {variable:<20} {fecha_pred_str:<12} {valor:<12.4f} {fecha_creacion_str:<16}")
    else:
        print("No se encontraron forecast recientes")

def main():
    """
    Función principal para mostrar todas las forecast
    """
    try:
        # Conectar a la base de datos
        print("Conectando a la base de datos...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que existe la tabla forecast
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'forecast'
            )
        """)
        
        if not cursor.fetchone()[0]:
            print("Error: La tabla 'forecast' no existe en la base de datos")
            return
        
        # Obtener tipos de modelo únicos
        cursor.execute("SELECT DISTINCT tipo_modelo FROM forecast ORDER BY tipo_modelo")
        tipos_modelo = cursor.fetchall()
        
        if not tipos_modelo:
            print("No se encontraron forecast en la base de datos")
            return
        
        print(f"Fecha y hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar resumen general
        mostrar_resumen_general(cursor)
        
        # Mostrar forecast por cada tipo de modelo
        for (tipo_modelo,) in tipos_modelo:
            mostrar_forecast_por_tipo(cursor, tipo_modelo)
        
        # Mostrar forecast más recientes
        mostrar_forecast_recientes(cursor, 15)
        
        print(f"\n{'='*80}")
        print("VISUALIZACIÓN COMPLETADA")
        print(f"{'='*80}")
        
    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()