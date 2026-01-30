"""
Script creado por: Pablo Dueñas Fernández.
Este script implementa un modelo BiLSTM bidireccional para la predicción de precios
de excedente eléctrico utilizando datos del mercado ESIOS. Incluye evaluación
de métricas y guardado de resultados en base de datos.
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
from dotenv import load_dotenv
from sqlalchemy import create_engine
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import pickle
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ——————————————————————————————————————————————
#   Data acquisition functions 
# ——————————————————————————————————————————————

def data_obtention():
    """
    Obtain ESIOS data from the PostgreSQL database.
    """
    load_dotenv()
    conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"\
               f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(conn_str)
    
    # Get the table name from .env
    table_name = os.getenv('ESIOS_POSTGRES_TABLE_TREATED')
    
    # Read data from PostgreSQL
    df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY fecha", engine)
    
    # Convert date column to datetime and set as index
    df['fecha'] = pd.to_datetime(df['fecha'])
    df.set_index('fecha', inplace=True)
    
    print(f"Data loaded from {table_name}. Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    return df, engine

def data_preprocessing(df, target_var='precio_excedente'):
    """
    Preprocess the ESIOS data for the BiLSTM model.
    
    Args:
        df: DataFrame with ESIOS data
        target_var: Target variable to predict (default: 'precio_excedente')
    
    Returns:
        df_scaled: DataFrame with scaled values
        scaler_all: Scaler for all features
        scaler_target: Scaler for the target variable
    """
    print(f"Preprocessing data for target variable: {target_var}")
    
    # Ensure target variable exists in the dataframe
    if target_var not in df.columns:
        raise ValueError(f"Target variable '{target_var}' not found in dataframe columns")
    
    # Select numeric columns for scaling (excluding categorical features)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove unnecessary columns
    feature_cols = [col for col in numeric_cols]
    
    print(f"Selected features: {feature_cols}")
    
    # Create scalers
    scaler_all = MinMaxScaler()
    df_scaled = df.copy()
    
    # Scale all features
    df_scaled[feature_cols] = scaler_all.fit_transform(df[feature_cols])
    
    # Create separate scaler for target variable
    scaler_target = MinMaxScaler()
    scaler_target.fit(df[[target_var]])
    
    return df_scaled, scaler_all, scaler_target, feature_cols

def create_sequences(data, target_col_idx, seq_length):
    """
    Create sequences for BiLSTM from data.
    
    Args:
        data: NumPy array with scaled data
        target_col_idx: Index of the target column in the data array
        seq_length: Length of input sequences
    
    Returns:
        X: Input sequences
        y: Target values
    """
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length, :])
        y.append(data[i+seq_length, target_col_idx])
    return np.array(X), np.array(y)

# ——————————————————————————————————————————————
#   Model architecture
# ——————————————————————————————————————————————

def build_model(input_shape):
    """
    Build BiLSTM model for price prediction.
    """
    model = Sequential([
        # Bidirectional LSTM for capturing complex patterns
        Bidirectional(LSTM(128, return_sequences=True), input_shape=input_shape),
        Dropout(0.3),
        
        # Second Bidirectional LSTM layer
        Bidirectional(LSTM(64, return_sequences=False)),
        Dropout(0.3),
        
        # Dense layers with regularization
        Dense(32, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(1e-4)),
        Dropout(0.2),
        
        # Output layer
        Dense(1)
    ])
    
    # Compile with Adam optimizer and MSE loss
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  loss='mse', metrics=['mae'])
    
    return model

# ——————————————————————————————————————————————
#   Forecasting functions
# ——————————————————————————————————————————————

def forecast_future(model, df_scaled, feature_cols, target_col_idx, seq_length, 
                   scaler_target, n_days=7):
    """
    Forecast future values of the target variable.
    
    Args:
        model: Trained LSTM model
        df_scaled: DataFrame with scaled values
        feature_cols: List of feature column names
        target_col_idx: Index of the target column
        seq_length: Length of input sequences
        scaler_target: Scaler for the target variable
        n_days: Number of days to forecast
    
    Returns:
        future_preds: Array of predicted values
    """
    # Get the last sequence
    last_seq = df_scaled[feature_cols].values[-seq_length:]
    
    future_preds_scaled = []
    seq = last_seq.copy()
    
    for _ in range(n_days):
        # Reshape for prediction
        x_input = seq.reshape(1, seq_length, -1)
        
        # Predict next value
        yhat = model.predict(x_input, verbose=0)[0,0]
        future_preds_scaled.append(yhat)
        
        # Create next sequence: drop first row and add prediction as last row
        next_row = np.zeros((1, len(feature_cols)))
        next_row[0, target_col_idx] = yhat  # Set the target variable
        seq = np.vstack([seq[1:], next_row])
    
    # Inverse transform the predictions
    future_preds = scaler_target.inverse_transform(
        np.array(future_preds_scaled).reshape(-1,1))
    
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
        'data_type': 'esios',
        'target_variable': 'precio_excedente',
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
        csv_filename = f'models/metrics_results/esios_bilstm_metrics_{timestamp_str}.csv'
        
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

def plot_results(test_dates, y_test, y_pred, future_dates, future_preds, target_var):
    """
    Plot test results and future predictions.
    """
    plt.figure(figsize=(14, 6))
    
    # Plot test data
    plt.plot(test_dates, y_test, label='Actual', color='blue', alpha=0.6)
    plt.plot(test_dates, y_pred, label='Predicted', color='red', alpha=0.6)
    
    # Plot future predictions
    plt.plot(future_dates, future_preds, label=f'Forecast (Next {len(future_dates)} days)', 
             color='green', linestyle='--')
    
    plt.title(f'{target_var.capitalize()} Prediction and Forecast - BiLSTM')
    plt.xlabel('Date')
    plt.ylabel(f'{target_var.capitalize()}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(f'models/visualizations/esios/bilstm_{target_var}_forecast.png')
    plt.close()

# ——————————————————————————————————————————————
#   Main function
# ——————————————————————————————————————————————

def main(n_days=5):
    """
    Main function to run the BiLSTM model for price prediction.
    """
    # Set target variable
    target_var = 'precio_excedente'
    
    # 1) Obtain data
    df, engine = data_obtention()
    
    # 2) Preprocess data
    df_scaled, scaler_all, scaler_target, feature_cols = data_preprocessing(df, target_var)
    
    # Get index of target variable
    target_col_idx = feature_cols.index(target_var)
    
    # 3) Create sequences
    seq_length = n_days
    X, y = create_sequences(df_scaled[feature_cols].values, target_col_idx, seq_length)
    
    # 4) Split data using TimeSeriesSplit for time series cross-validation
    tss = TimeSeriesSplit(n_splits=3)
    
    # We'll use the last split for testing
    for train_idx, test_idx in tss.split(X):
        pass
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    print(f"\nTraining set shape: {X_train.shape}")
    print(f"Test set shape: {X_test.shape}")
    
    # 5) Build and train model
    model = build_model(input_shape=(seq_length, len(feature_cols)))
    model.summary()
    
    # Callbacks for training
    early_stopping = EarlyStopping(
        monitor='val_loss', 
        patience=50, 
        restore_best_weights=True
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=10,
        min_lr=1e-5
    )
    
    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=200,
        batch_size=32,
        validation_split=0.2,
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )
    
    # 6) Evaluate model on test data
    y_pred = model.predict(X_test, verbose=0).flatten()
    
    # Inverse transform scaled values
    y_test_inv = scaler_target.inverse_transform(y_test.reshape(-1, 1)).flatten()
    y_pred_inv = scaler_target.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    
    # Evaluate and save metrics
    evaluate_model_and_save_metrics(y_test_inv, y_pred_inv, 'BiLSTM', engine)
    
    # 7) Make future predictions
    future_preds = forecast_future(
        model, df_scaled, feature_cols, target_col_idx, 
        seq_length, scaler_target, n_days=7
    )
    
    # Get test dates and future dates for plotting
    test_dates = df.index[seq_length + test_idx]  # Align with test data
    last_date = df.index[-1]
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=len(future_preds),
        freq='D'
    )
    
    # 8) Plot results
    plot_results(test_dates, y_test_inv, y_pred_inv, future_dates, future_preds, target_var)
    
    # 9) Save model and scalers
    os.makedirs('models/saved_models/esios', exist_ok=True)
    model.save(f'models/saved_models/esios/bilstm_{target_var}_model.h5')
    
    with open(f'models/saved_models/esios/scaler_all_{target_var}_bilstm.pkl', 'wb') as f:
        pickle.dump(scaler_all, f)
    
    with open(f'models/saved_models/esios/scaler_{target_var}_bilstm.pkl', 'wb') as f:
        pickle.dump(scaler_target, f)
    
    print(f"\nBiLSTM model and scalers saved to 'models/saved_models/esios/' directory")
    
    # 10) Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('BiLSTM Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['mae'], label='Training MAE')
    plt.plot(history.history['val_mae'], label='Validation MAE')
    plt.title('BiLSTM Model MAE')
    plt.xlabel('Epoch')
    plt.ylabel('MAE')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(f'models/visualizations/esios/bilstm_{target_var}_training_history.png')
    plt.close()
    
    print(f"BiLSTM model for {target_var} prediction completed successfully.")

    # 11) put predicted data into new postgres table
    future_df = pd.DataFrame({
        'fecha': future_dates,
        target_var: future_preds
    })
    future_df.set_index('fecha', inplace=True)
    future_df.to_sql(
        f'esios_forecast_{target_var}_bilstm', 
        engine, 
        if_exists='replace', 
        index=True
    )
    print(f"Predicted data saved to 'esios_forecast_{target_var}_bilstm' table in PostgreSQL.")

if __name__ == "__main__":
    main()
    
    print(f"LSTM model for {target_var} prediction completed successfully.")

    # 11) put predicted data into new postgres table
    future_df = pd.DataFrame({
        'fecha': future_dates,
        target_var: future_preds
    })
    future_df.set_index('fecha', inplace=True)
    future_df.to_sql(
        f'esios_forecast_{target_var}', 
        engine, 
        if_exists='replace', 
        index=True
    )



if __name__ == "__main__":
    main()
