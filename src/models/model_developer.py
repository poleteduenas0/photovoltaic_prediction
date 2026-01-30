"""
Script creado por: Pablo Dueñas Fernández.
Este script orquesta la ejecución de todos los modelos de predicción LSTM y BiLSTM
para datos de AEMET, ESIOS y producción fotovoltaica. Coordina el entrenamiento
secuencial de los modelos y la generación de predicciones.
"""
from model_aemet_lstm import main as aemet_lstm_main
from model_esios_lstm import main as esios_lstm_main
from model_production_lstm import main as production_lstm_main
from model_aemet_bilstm import main as aemet_bilstm_main
from model_esios_bilstm import main as esios_bilstm_main
from model_production_bilstm import main as production_bilstm_main
# traemos el days_to_predict de interfa.py que esta fuera de esta carpeta
from interfaz import days_to_predict as n_days
# recibo variable de numero de días de predicción
n_days = 7
print("Starting model development...")
# Run the LSTM models
print("Running AEMET LSTM model...")
aemet_lstm_main(n_days)
print("Running ESIOS LSTM model...")
esios_lstm_main(n_days)
print("Running Production LSTM model...")
production_lstm_main(n_days)
# Run the BiLSTM models
print("Running AEMET BiLSTM model...")
aemet_bilstm_main(n_days)
print("Running ESIOS BiLSTM model...")
esios_bilstm_main(n_days)
print("Running Production BiLSTM model...")
production_bilstm_main(n_days)
print("All models completed successfully!")

