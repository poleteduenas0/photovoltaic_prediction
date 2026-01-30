"""
Script creado por: Pablo Dueñas Fernández.
Este script implementa modelos ARIMA y ARMAX para la predicción de horas de sol
utilizando datos meteorológicos de AEMET. Compara el rendimiento de ambos modelos
y guarda las métricas de evaluación en la base de datos y visualizaciones.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error
from dotenv import load_dotenv
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Librerías para ARIMA
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

def data_obtention():
    """Obtener datos de AEMET desde PostgreSQL"""
    load_dotenv()
    conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"\
               f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(conn_str)
    
    table_name = os.getenv('AEMET_POSTGRES_TABLE_TREATED')
    df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY fecha", engine)
    
    df['fecha'] = pd.to_datetime(df['fecha'])
    df.set_index('fecha', inplace=True)
    
    print(f"Datos cargados desde {table_name}. Forma: {df.shape}")
    return df, engine

def check_stationarity(ts):
    """Verificar estacionariedad de la serie temporal"""
    result = adfuller(ts.dropna())
    print(f'Estadístico ADF: {result[0]:.6f}')
    print(f'p-value: {result[1]:.6f}')
    print(f'Valores críticos:')
    for key, value in result[4].items():
        print(f'\t{key}: {value:.3f}')
    
    if result[1] <= 0.05:
        print("Serie es estacionaria")
        return True
    else:
        print("Serie no es estacionaria")
        return False

def prepare_data(df, target_var='sol'):
    """Preparar datos para modelado"""
    # Verificar si existe la variable objetivo
    if target_var not in df.columns:
        raise ValueError(f"Variable objetivo '{target_var}' no encontrada")
    
    # Eliminar valores nulos
    df_clean = df.dropna()
    
    # Variables exógenas para ARMAX
    exog_vars = ['tmed', 'tmax', 'hrMedia', 'prec','hrMin']
    exog_vars = [var for var in exog_vars if var in df_clean.columns]
    
    print(f"Variables exógenas disponibles: {exog_vars}")
    
    return df_clean, exog_vars

def fit_arima_model(ts, order=(1,1,1)):
    """Ajustar modelo ARIMA"""
    try:
        model = ARIMA(ts, order=order)
        fitted_model = model.fit()
        return fitted_model
    except Exception as e:
        print(f"Error al ajustar modelo ARIMA: {e}")
        return None

def fit_armax_model(ts, exog, order=(1,1,1)):
    """Ajustar modelo ARMAX"""
    try:
        model = ARIMA(ts, exog=exog, order=order)
        fitted_model = model.fit()
        return fitted_model
    except Exception as e:
        print(f"Error al ajustar modelo ARMAX: {e}")
        return None

def evaluate_model(y_true, y_pred, model_name):
    """Evaluar modelo y calcular métricas"""
    # Filtrar valores no nulos
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        print(f"No hay datos válidos para evaluar {model_name}")
        return None
    
    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    mse = mean_squared_error(y_true_clean, y_pred_clean)
    rmse = np.sqrt(mse)
    
    metrics = {
        'model': model_name,
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'data_type': 'aemet',
        'target_variable': 'sol'
    }
    
    print(f"\n{model_name} - Métricas de evaluación:")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    
    return metrics

def save_metrics_to_db(metrics_list, engine):
    """Guardar métricas en la base de datos y CSV"""
    df_metrics = pd.DataFrame(metrics_list)
    df_metrics['timestamp'] = pd.Timestamp.now()
    
    # Guardar en base de datos
    try:
        df_metrics.to_sql('model_performance_metrics', engine, 
                         if_exists='append', index=False)
        print("Métricas guardadas en la base de datos")
    except Exception as e:
        print(f"Error al guardar métricas: {e}")
    
    # Guardar en CSV
    try:
        # Crear directorio si no existe
        os.makedirs('models/metrics_results', exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'models/metrics_results/aemet_arima_metrics_{timestamp_str}.csv'
        
        # Guardar métricas actuales
        df_metrics.to_csv(csv_filename, index=False)
        
        # Append a archivo consolidado
        consolidated_file = 'models/metrics_results/all_models_metrics.csv'
        if os.path.exists(consolidated_file):
            df_existing = pd.read_csv(consolidated_file)
            df_combined = pd.concat([df_existing, df_metrics], ignore_index=True)
        else:
            df_combined = df_metrics
        
        df_combined.to_csv(consolidated_file, index=False)
        print(f"Métricas guardadas en CSV: {csv_filename}")
        print(f"Métricas consolidadas en: {consolidated_file}")
        
    except Exception as e:
        print(f"Error al guardar métricas en CSV: {e}")

def plot_results(y_true, y_pred_arima, y_pred_armax, future_dates, 
                forecast_arima, forecast_armax, target_var='sol'):
    """Crear visualizaciones de los resultados"""
    
    # Crear directorio para visualizaciones
    os.makedirs('models/visualizations/aemet', exist_ok=True)
    
    # Gráfico 1: Comparación de predicciones
    plt.figure(figsize=(15, 10))
    
    # Subplot 1: Comparación de modelos
    plt.subplot(2, 2, 1)
    plt.plot(y_true.index, y_true.values, label='Real', alpha=0.7)
    plt.plot(y_true.index, y_pred_arima, label='ARIMA', alpha=0.7)
    plt.plot(y_true.index, y_pred_armax, label='ARMAX', alpha=0.7)
    plt.title(f'Comparación de Modelos - {target_var}')
    plt.xlabel('Fecha')
    plt.ylabel('Horas de Sol')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Subplot 2: Residuos ARIMA
    plt.subplot(2, 2, 2)
    residuals_arima = y_true.values - y_pred_arima
    plt.plot(y_true.index, residuals_arima)
    plt.title('Residuos ARIMA')
    plt.xlabel('Fecha')
    plt.ylabel('Residuos')
    plt.grid(True, alpha=0.3)
    
    # Subplot 3: Residuos ARMAX
    plt.subplot(2, 2, 3)
    residuals_armax = y_true.values - y_pred_armax
    plt.plot(y_true.index, residuals_armax)
    plt.title('Residuos ARMAX')
    plt.xlabel('Fecha')
    plt.ylabel('Residuos')
    plt.grid(True, alpha=0.3)
    
    # Subplot 4: Predicciones futuras
    plt.subplot(2, 2, 4)
    plt.plot(future_dates, forecast_arima, label='Forecast ARIMA', 
             linestyle='--', marker='o')
    plt.plot(future_dates, forecast_armax, label='Forecast ARMAX', 
             linestyle='--', marker='s')
    plt.title('Predicciones Futuras')
    plt.xlabel('Fecha')
    plt.ylabel('Horas de Sol')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('models/visualizations/aemet/arima_armax_comparison.png', dpi=300)
    plt.close()
    
    # Gráfico 2: Métricas de comparación
    plt.figure(figsize=(12, 6))
    
    # Calcular métricas para visualización
    mae_arima = mean_absolute_error(y_true.values, y_pred_arima)
    mae_armax = mean_absolute_error(y_true.values, y_pred_armax)
    rmse_arima = np.sqrt(mean_squared_error(y_true.values, y_pred_arima))
    rmse_armax = np.sqrt(mean_squared_error(y_true.values, y_pred_armax))
    
    metrics_comparison = pd.DataFrame({
        'Modelo': ['ARIMA', 'ARMAX'],
        'MAE': [mae_arima, mae_armax],
        'RMSE': [rmse_arima, rmse_armax]
    })
    
    plt.subplot(1, 2, 1)
    plt.bar(metrics_comparison['Modelo'], metrics_comparison['MAE'], 
            color=['blue', 'green'], alpha=0.7)
    plt.title('Comparación MAE')
    plt.ylabel('MAE')
    
    plt.subplot(1, 2, 2)
    plt.bar(metrics_comparison['Modelo'], metrics_comparison['RMSE'], 
            color=['blue', 'green'], alpha=0.7)
    plt.title('Comparación RMSE')
    plt.ylabel('RMSE')
    
    plt.tight_layout()
    plt.savefig('models/visualizations/aemet/metrics_comparison.png', dpi=300)
    plt.close()
    
    print("Visualizaciones guardadas en 'models/visualizations/aemet/'")

def save_predictions_and_plot(future_dates, future_preds, target_var='sol'):
    """
    Guardar predicciones en CSV y generar gráfico PNG
    """
    # 1) Guardar predicciones en CSV
    try:
        # Crear directorio si no existe
        os.makedirs('models/metrics_results', exist_ok=True)
        
        # Crear DataFrame con predicciones
        future_df = pd.DataFrame({
            'fecha': future_dates,
            target_var: future_preds
        })
        
        # Nombre del archivo con timestamp
        timestamp_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'models/metrics_results/aemet_arima_predictions_{timestamp_str}.csv'
        
        # Guardar CSV
        future_df.to_csv(csv_filename, index=False)
        print(f"Predicciones guardadas en CSV: {csv_filename}")
        
    except Exception as e:
        print(f"Error al guardar predicciones en CSV: {e}")
    
    # 2) Generar y guardar gráfico PNG
    try:
        # Crear directorio si no existe
        os.makedirs('models/visualizations/aemet', exist_ok=True)
        
        plt.figure(figsize=(12, 6))
        plt.plot(future_dates, future_preds, marker='o', linestyle='-', linewidth=2, markersize=6)
        plt.title(f'Predicción ARIMA - {target_var.capitalize()} (7 días)', fontsize=14)
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel(f'{target_var.capitalize()}', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar PNG
        png_filename = f'models/visualizations/aemet/arima_{target_var}_forecast_7d.png'
        plt.savefig(png_filename, dpi=300, bbox_inches='tight')
        plt.close()  # Cerrar figura para liberar memoria
        print(f"Gráfico guardado en PNG: {png_filename}")
        
    except Exception as e:
        print(f"Error al guardar gráfico en PNG: {e}")

def main(n_days=7):
    """Función principal"""
    target_var = 'sol'
    
    # 1. Obtener datos
    df, engine = data_obtention()
    
    # 2. Preparar datos
    df_clean, exog_vars = prepare_data(df, target_var)
    
    # 3. Verificar estacionariedad
    print(f"\nVerificando estacionariedad de {target_var}:")
    ts = df_clean[target_var]
    is_stationary = check_stationarity(ts)
    
    # 4. Dividir datos en entrenamiento y prueba
    train_size = int(len(df_clean) * 0.8)
    train_data = df_clean[:train_size]
    test_data = df_clean[train_size:]
    
    print(f"\nDatos de entrenamiento: {len(train_data)}")
    print(f"Datos de prueba: {len(test_data)}")
    
    # 5. Ajustar modelo ARIMA
    print("\n=== Ajustando modelo ARIMA ===")
    arima_model = fit_arima_model(train_data[target_var], order=(1,1,1))
    
    # 6. Ajustar modelo ARMAX
    print("\n=== Ajustando modelo ARMAX ===")
    if exog_vars:
        armax_model = fit_armax_model(
            train_data[target_var], 
            train_data[exog_vars], 
            order=(1,1,1)
        )
    else:
        print("No hay variables exógenas disponibles para ARMAX")
        armax_model = None
    
    # 7. Hacer predicciones en conjunto de prueba
    predictions_arima = []
    predictions_armax = []
    
    if arima_model:
        try:
            # Predicciones ARIMA
            forecast_arima = arima_model.forecast(steps=len(test_data))
            predictions_arima = forecast_arima
        except Exception as e:
            print(f"Error en predicciones ARIMA: {e}")
            predictions_arima = np.full(len(test_data), np.nan)
    
    if armax_model and exog_vars:
        try:
            # Predicciones ARMAX
            forecast_armax = armax_model.forecast(
                steps=len(test_data), 
                exog=test_data[exog_vars]
            )
            predictions_armax = forecast_armax
        except Exception as e:
            print(f"Error en predicciones ARMAX: {e}")
            predictions_armax = np.full(len(test_data), np.nan)
    
    # 8. Evaluar modelos
    metrics_list = []
    
    if len(predictions_arima) > 0:
        metrics_arima = evaluate_model(
            test_data[target_var].values, 
            predictions_arima, 
            'ARIMA'
        )
        if metrics_arima:
            metrics_list.append(metrics_arima)
    
    if len(predictions_armax) > 0:
        metrics_armax = evaluate_model(
            test_data[target_var].values, 
            predictions_armax, 
            'ARMAX'
        )
        if metrics_armax:
            metrics_list.append(metrics_armax)
    
    # 9. Predicciones futuras
    future_dates = pd.date_range(
        start=df_clean.index[-1] + pd.Timedelta(days=1),
        periods=n_days,
        freq='D'
    )
    
    future_arima = []
    future_armax = []
    
    if arima_model:
        try:
            future_arima = arima_model.forecast(steps=n_days)
        except Exception as e:
            print(f"Error en predicción futura ARIMA: {e}")
            future_arima = np.full(n_days, np.nan)
    
    if armax_model and exog_vars:
        try:
            # Para ARMAX necesitamos valores futuros de variables exógenas
            # Usamos los últimos valores conocidos
            last_exog = df_clean[exog_vars].iloc[-n_days:].values
            future_armax = armax_model.forecast(steps=n_days, exog=last_exog)
        except Exception as e:
            print(f"Error en predicción futura ARMAX: {e}")
            future_armax = np.full(n_days, np.nan)
    
    # 10. Crear visualizaciones
    if len(predictions_arima) > 0 and len(predictions_armax) > 0:
        plot_results(
            test_data[target_var], 
            predictions_arima, 
            predictions_armax,
            future_dates,
            future_arima,
            future_armax,
            target_var
        )
    
    # 11. Guardar métricas en base de datos
    if metrics_list:
        save_metrics_to_db(metrics_list, engine)
    
    # 12. Guardar predicciones futuras en base de datos
    if len(future_arima) > 0:
        future_df_arima = pd.DataFrame({
            'fecha': future_dates,
            target_var: future_arima
        })
        future_df_arima.to_sql(
            f'aemet_forecast_{target_var}_arima', 
            engine, 
            if_exists='replace', 
            index=False
        )
    
    if len(future_armax) > 0:
        future_df_armax = pd.DataFrame({
            'fecha': future_dates,
            target_var: future_armax
        })
        future_df_armax.to_sql(
            f'aemet_forecast_{target_var}_armax', 
            engine, 
            if_exists='replace', 
            index=False
        )
    
    # Guardar predicciones y gráfico
    save_predictions_and_plot(future_dates, future_arima, target_var)
    save_predictions_and_plot(future_dates, future_armax, target_var)
    
    print(f"\nProceso completado para {target_var}")
    return metrics_list

if __name__ == "__main__":
    main()
