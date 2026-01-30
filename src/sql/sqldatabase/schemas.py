"""
Schemas Pydantic para validación de datos y respuestas API
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# ================================
# AEMET Schemas
# ================================

class AEMETDataBase(BaseModel):
    """Schema base para datos AEMET"""
    fecha: datetime
    tmed: Optional[float] = None
    tmin: Optional[float] = None
    tmax: Optional[float] = None
    prec: Optional[float] = None
    velmedia: Optional[float] = None
    racha: Optional[float] = None
    presmax: Optional[float] = None
    presmin: Optional[float] = None
    hrmedia: Optional[float] = None
    hrmax: Optional[float] = None
    hrmin: Optional[float] = None
    sol: Optional[float] = None
    mes: Optional[int] = None
    dia: Optional[int] = None
    dia_semana: Optional[int] = None
    es_fin_semana: Optional[bool] = False
    estacion: Optional[int] = None


class AEMETDataCreate(AEMETDataBase):
    """Schema para crear registro AEMET"""
    pass


class AEMETDataResponse(AEMETDataBase):
    """Schema para respuesta de API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================================
# ESIOS Schemas
# ================================

class ESIOSDataBase(BaseModel):
    """Schema base para datos ESIOS"""
    fecha: datetime
    precio_excedente: Optional[float] = None
    solar_fotovoltaica: Optional[float] = None
    eolica: Optional[float] = None
    hidraulica: Optional[float] = None
    generacion_renovable: Optional[float] = None
    nuclear: Optional[float] = None
    ciclo_combinado: Optional[float] = None
    generacion_no_renovable: Optional[float] = None
    demanda: Optional[float] = None


class ESIOSDataCreate(ESIOSDataBase):
    """Schema para crear registro ESIOS"""
    pass


class ESIOSDataResponse(ESIOSDataBase):
    """Schema para respuesta de API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================================
# Production Schemas
# ================================

class ProductionDataBase(BaseModel):
    """Schema base para datos de producción"""
    fecha: datetime
    totalproduction: float


class ProductionDataCreate(ProductionDataBase):
    """Schema para crear registro de producción"""
    pass


class ProductionDataResponse(ProductionDataBase):
    """Schema para respuesta de API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================================
# Model Metrics Schemas
# ================================

class ModelMetricsBase(BaseModel):
    """Schema base para métricas de modelo"""
    model_name: str = Field(..., max_length=100)
    data_type: Optional[str] = Field(None, max_length=50)
    target_variable: Optional[str] = Field(None, max_length=50)
    mae: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    additional_info: Optional[str] = None


class ModelMetricsCreate(ModelMetricsBase):
    """Schema para crear métricas"""
    pass


class ModelMetricsResponse(ModelMetricsBase):
    """Schema para respuesta de API"""
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ================================
# Forecast Schemas
# ================================

class ForecastBase(BaseModel):
    """Schema base para predicciones"""
    fecha_prediccion: datetime
    model_name: str = Field(..., max_length=100)
    data_type: Optional[str] = Field(None, max_length=50)
    target_variable: Optional[str] = Field(None, max_length=50)
    predicted_value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastCreate(ForecastBase):
    """Schema para crear predicción"""
    pass


class ForecastResponse(ForecastBase):
    """Schema para respuesta de API"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ================================
# Query Schemas (para filtros)
# ================================

class DateRangeQuery(BaseModel):
    """Schema para queries con rango de fechas"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class DataSummary(BaseModel):
    """Schema para resumen de datos"""
    total_records: int
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    last_updated: Optional[datetime] = None