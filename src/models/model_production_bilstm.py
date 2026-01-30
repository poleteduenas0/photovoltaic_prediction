"""
Script creado por: Pablo Dueñas Fernández.
Este script implementa un modelo LSTM bidireccional para la predicción de producción
fotovoltaica utilizando datos históricos y variables meteorológicas. Incluye
evaluación de métricas y guardado de resultados en base de datos.
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error
from dotenv import load_dotenv
from sqlalchemy import create_engine
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import pickle

# ——————————————————————————————————————————————
#   (Mantenemos tu código de obtención y preprocesado casi igual)
# ——————————————————————————————————————————————

def data_obtention():
    load_dotenv()
    conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"\
               f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(conn_str)
    df = pd.read_sql(f"SELECT * FROM {os.getenv('PRODUCTION_POSTGRES_TABLE_TREATED')} ORDER BY fecha", engine)
    df['fecha'] = pd.to_datetime(df['fecha'], utc=True)
    df.set_index('fecha', inplace=True)
    return df, engine

def data_preprocessing(df, feature_cols):
    scaler_all = MinMaxScaler()
    df_scaled = df.copy()
    df_scaled[feature_cols] = scaler_all.fit_transform(df[feature_cols])
    scaler_prod = MinMaxScaler().fit(df[['Totalproduction']])
    return df_scaled, scaler_all, scaler_prod

def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length, :])
        y.append(data[i+seq_length, 0])  # 0 = Totalproduction
    return np.array(X), np.array(y)

# ——————————————————————————————————————————————
#   Modelo mejorado: Bidirectional + ReduceLROnPlateau
# ——————————————————————————————————————————————

def build_model(input_shape):
    model = Sequential([
        Bidirectional(LSTM(128, return_sequences=True), input_shape=input_shape),
        Dropout(0.3),
        Bidirectional(LSTM(64, return_sequences=False)),
        Dropout(0.3),
        Dense(32, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(1e-4)),
        Dropout(0.3),
        Dense(1)
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  loss='mse', metrics=['mae'])
    return model

# ——————————————————————————————————————————————
#   Forecast a 7 días
# ——————————————————————————————————————————————

def forecast_future(model, df_scaled, seq_length, scaler_prod, n_days=7):
    last_seq = df_scaled.values[-seq_length:]
    future_preds_scaled = []
    seq = last_seq.copy()
    for _ in range(n_days):
        # tomamos los últimos seq_length filas como input
        x_input = seq.reshape(1, seq_length, -1)
        yhat = model.predict(x_input)[0,0]
        future_preds_scaled.append(yhat)
        # construimos la siguiente ventana: desplazamos y añadimos predicción
        next_row = np.zeros((1, df_scaled.shape[1]))
        next_row[0, 0] = yhat  # Totalproduction predicha
        seq = np.vstack([seq[1:], next_row])
    # invertimos escala
    future_preds = scaler_prod.inverse_transform(np.array(future_preds_scaled).reshape(-1,1))
    return future_preds.flatten()

def evaluate_model_and_save_metrics(y_true, y_pred, model_name, engine):
    """Evaluar modelo y guardar métricas en base de datos y CSV"""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    
    metrics = {
        'model': model_name,
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'data_type': 'production',
        'target_variable': 'Totalproduction',
        'timestamp': pd.Timestamp.now()
    }
    
    print(f"\n{model_name} - Métricas de evaluación:")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    
    # Guardar en base de datos
    try:
        df_metrics = pd.DataFrame([metrics])
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
        csv_filename = f'models/metrics_results/production_bilstm_metrics_{timestamp_str}.csv'
        
        # Guardar métricas actuales
        df_metrics = pd.DataFrame([metrics])
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
    
    return metrics

# ——————————————————————————————————————————————
#   Función principal
# ——————————————————————————————————————————————

def main(n_days=5):
    # 1) Datos
    df, engine = data_obtention()
    feature_cols = ['Totalproduction','tmed','prec','tmin','tmax','velmedia',
                    'racha','sol','presmax','presmin','hrmedia','hrmax','hrmin','precio_excedente','Solar_fotovoltaica']
    df_scaled, scaler_all, scaler_prod = data_preprocessing(df, feature_cols)

    # 2) Secuencias
    seq_length = n_days  # ventana de 14 días
    X, y = create_sequences(df_scaled.values, seq_length)

    # 3) Split entrenamiento/test con TimeSeriesSplit
    tss = TimeSeriesSplit(n_splits=3)
    # Tomamos el último split para evaluar
    for train_idx, test_idx in tss.split(X):
        pass
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # 4) Entrenamiento
    model = build_model(input_shape=(seq_length, len(feature_cols)))
    es = EarlyStopping(monitor='val_loss', patience=100, restore_best_weights=True)
    rlp = ReduceLROnPlateau(monitor='val_loss', patience=10, factor=0.5, min_lr=1e-5)
    model.fit(X_train, y_train, epochs=200, batch_size=32,
              validation_split=0.2, callbacks=[es, rlp])

    # 5) Predicción test y métricas
    preds_test = model.predict(X_test)
    y_test_inv  = scaler_prod.inverse_transform(y_test.reshape(-1,1)).flatten()
    preds_test_inv = scaler_prod.inverse_transform(preds_test).flatten()

    # Evaluar y guardar métricas
    evaluate_model_and_save_metrics(y_test_inv, preds_test_inv, 'BiLSTM', engine)

    # 6) Forecast 7 días
    future_preds = forecast_future(model, df_scaled, seq_length, scaler_prod, n_days=7)
    last_date = df.index[-1]
    future_idx = pd.date_range(start=last_date + pd.Timedelta(days=1),
                               periods=len(future_preds), freq='D')

    # 7) Gráfico combinado
    plt.figure(figsize=(14,6))
    # a) test real vs predicha
    test_idx = df.index[seq_length + test_idx]  # alineamos índices
    plt.plot(test_idx, y_test_inv,  label='Real (test)', color='blue', alpha=0.6)
    plt.plot(test_idx, preds_test_inv, label='Predicha (test)', color='red',  alpha=0.6)
    # b) forecasting
    plt.plot(future_idx, future_preds, label='Predicción +7 días', color='green', linestyle='--')
    plt.title('Producción real vs predicha y forecast 7 días - BiLSTM')
    plt.xlabel('Fecha')
    plt.ylabel('Total Production')
    plt.legend()
    plt.tight_layout()
    plt.savefig('models/visualizations/production/bilstm_forecast_7d.png')
    plt.close()

    # 8) Guardar modelo y scalers
    os.makedirs('models/saved_models/production', exist_ok=True)
    model.save('models/saved_models/production/bilstm_model_prod.h5')
    with open('models/saved_models/production/scaler_all_bilstm.pkl','wb') as f: pickle.dump(scaler_all, f)
    with open('models/saved_models/production/scaler_prod_bilstm.pkl','wb') as f: pickle.dump(scaler_prod, f)

    # 11) put predicted data into new postgres table
    future_df = pd.DataFrame({
        'fecha': future_idx,
        'Totalproduction': future_preds
    })
    future_df.set_index('fecha', inplace=True)
    future_df.to_sql('production_forecast_totalproduction_bilstm', engine, if_exists='replace', index=True)

if __name__ == "__main__":
    main()
