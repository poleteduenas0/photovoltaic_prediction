"""
SQLite Database Module
Sistema de base de datos local con FastAPI
"""
from .database import engine, SessionLocal, Base, get_db, init_db
from .models import (
    AEMETData,
    ESIOSData,
    ProductionData,
    ModelMetrics,
    Forecast
)
from .schemas import (
    # AEMET
    AEMETDataCreate,
    AEMETDataResponse,
    # ESIOS
    ESIOSDataCreate,
    ESIOSDataResponse,
    # Production
    ProductionDataCreate,
    ProductionDataResponse,
    # Metrics
    ModelMetricsCreate,
    ModelMetricsResponse,
    # Forecast
    ForecastCreate,
    ForecastResponse,
    # Queries
    DateRangeQuery,
    DataSummary
)

__all__ = [
    # Database
    "engine",
    "SessionLocal", 
    "Base",
    "get_db",
    "init_db",
    
    # Models
    "AEMETData",
    "ESIOSData",
    "ProductionData",
    "ModelMetrics",
    "Forecast",
    
    # Schemas
    "AEMETDataCreate",
    "AEMETDataResponse",
    "ESIOSDataCreate",
    "ESIOSDataResponse",
    "ProductionDataCreate",
    "ProductionDataResponse",
    "ModelMetricsCreate",
    "ModelMetricsResponse",
    "ForecastCreate",
    "ForecastResponse",
    "DateRangeQuery",
    "DataSummary"
]