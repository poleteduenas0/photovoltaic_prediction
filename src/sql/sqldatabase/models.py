"""
Modelos SQLAlchemy para SQLite
Define todas las tablas de la base de datos
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .database import Base

class AEMETData(Base):
    """
    Tabla para datos meteorológicos de AEMET
    """
    __tablename__ = "aemet_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(DateTime, nullable=False, index=True, unique=True)
    
    # Variables meteorológicas principales
    tmed = Column(Float)  # Temperatura media (°C)
    tmin = Column(Float)  # Temperatura mínima (°C)
    tmax = Column(Float)  # Temperatura máxima (°C)
    prec = Column(Float)  # Precipitación (mm)
    
    # Viento
    velmedia = Column(Float)  # Velocidad media del viento (km/h)
    racha = Column(Float)     # Racha máxima (km/h)
    
    # Presión atmosférica
    presmax = Column(Float)  # Presión máxima (hPa)
    presmin = Column(Float)  # Presión mínima (hPa)
    
    # Humedad
    hrmedia = Column(Float)  # Humedad relativa media (%)
    hrmax = Column(Float)    # Humedad máxima (%)
    hrmin = Column(Float)    # Humedad mínima (%)
    
    # Sol (variable objetivo para predicción)
    sol = Column(Float)  # Horas de sol
    
    # Características temporales
    mes = Column(Integer)
    dia = Column(Integer)
    dia_semana = Column(Integer)
    es_fin_semana = Column(Boolean, default=False)
    estacion = Column(Integer)  # 1=Invierno, 2=Primavera, 3=Verano, 4=Otoño
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AEMETData(fecha={self.fecha}, tmed={self.tmed}, sol={self.sol})>"


class ESIOSData(Base):
    """
    Tabla para datos del mercado eléctrico (ESIOS)
    """
    __tablename__ = "esios_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(DateTime, nullable=False, index=True, unique=True)
    
    # Precio de excedente (variable objetivo)
    precio_excedente = Column(Float)
    
    # Generación renovable
    solar_fotovoltaica = Column(Float)
    eolica = Column(Float)
    hidraulica = Column(Float)
    generacion_renovable = Column(Float)
    
    # Generación no renovable
    nuclear = Column(Float)
    ciclo_combinado = Column(Float)
    generacion_no_renovable = Column(Float)
    
    # Demanda
    demanda = Column(Float)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ESIOSData(fecha={self.fecha}, precio_excedente={self.precio_excedente})>"


class ProductionData(Base):
    """
    Tabla para datos de producción fotovoltaica real
    """
    __tablename__ = "production_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(DateTime, nullable=False, index=True, unique=True)
    
    # Producción total (variable objetivo)
    totalproduction = Column(Float, nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProductionData(fecha={self.fecha}, totalproduction={self.totalproduction})>"


class ModelMetrics(Base):
    """
    Tabla para almacenar métricas de rendimiento de modelos
    """
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Identificación del modelo
    model_name = Column(String(100), nullable=False)  # ej: "LSTM", "BiLSTM", "ARIMA"
    data_type = Column(String(50))   # ej: "aemet", "esios", "production"
    target_variable = Column(String(50))  # ej: "sol", "precio_excedente"
    
    # Métricas
    mae = Column(Float)   # Mean Absolute Error
    mse = Column(Float)   # Mean Squared Error
    rmse = Column(Float)  # Root Mean Squared Error
    r2_score = Column(Float, nullable=True)  # R² Score (opcional)
    
    # Timestamp de ejecución
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Información adicional (JSON como texto)
    additional_info = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ModelMetrics(model={self.model_name}, mae={self.mae})>"


class Forecast(Base):
    """
    Tabla para almacenar predicciones futuras de todos los modelos
    """
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Fecha de la predicción
    fecha_prediccion = Column(DateTime, nullable=False, index=True)
    
    # Identificación del modelo
    model_name = Column(String(100), nullable=False)
    data_type = Column(String(50))
    target_variable = Column(String(50))
    
    # Valor predicho
    predicted_value = Column(Float, nullable=False)
    
    # Intervalo de confianza (opcional)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    
    # Timestamp de cuándo se hizo la predicción
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Forecast(fecha={self.fecha_prediccion}, model={self.model_name}, value={self.predicted_value})>"