"""
Operaciones CRUD (Create, Read, Update, Delete)
Funciones para interactuar con la base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime
from typing import List, Optional

from . import models, schemas


# ================================
# AEMET CRUD Operations
# ================================

def create_aemet_data(db: Session, data: schemas.AEMETDataCreate) -> models.AEMETData:
    """Crear nuevo registro AEMET"""
    db_item = models.AEMETData(**data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_aemet_data_bulk(db: Session, data_list: List[schemas.AEMETDataCreate]) -> int:
    """Insertar múltiples registros AEMET (bulk insert)"""
    db_items = [models.AEMETData(**data.model_dump()) for data in data_list]
    db.bulk_save_objects(db_items)
    db.commit()
    return len(db_items)


def get_aemet_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[models.AEMETData]:
    """Obtener datos AEMET con filtros opcionales"""
    query = db.query(models.AEMETData)
    
    if start_date:
        query = query.filter(models.AEMETData.fecha >= start_date)
    if end_date:
        query = query.filter(models.AEMETData.fecha <= end_date)
    
    return query.order_by(models.AEMETData.fecha).offset(skip).limit(limit).all()


def get_aemet_by_date(db: Session, fecha: datetime) -> Optional[models.AEMETData]:
    """Obtener registro AEMET por fecha específica"""
    return db.query(models.AEMETData).filter(models.AEMETData.fecha == fecha).first()


def get_aemet_summary(db: Session) -> dict:
    """Obtener resumen estadístico de datos AEMET"""
    total = db.query(func.count(models.AEMETData.id)).scalar()
    
    if total == 0:
        return {
            "total_records": 0,
            "date_range_start": None,
            "date_range_end": None,
            "avg_temperature": None,
            "avg_sun_hours": None
        }
    
    min_date = db.query(func.min(models.AEMETData.fecha)).scalar()
    max_date = db.query(func.max(models.AEMETData.fecha)).scalar()
    avg_temp = db.query(func.avg(models.AEMETData.tmed)).scalar()
    avg_sol = db.query(func.avg(models.AEMETData.sol)).scalar()
    
    return {
        "total_records": total,
        "date_range_start": min_date,
        "date_range_end": max_date,
        "avg_temperature": round(avg_temp, 2) if avg_temp else None,
        "avg_sun_hours": round(avg_sol, 2) if avg_sol else None
    }


# ================================
# ESIOS CRUD Operations
# ================================

def create_esios_data(db: Session, data: schemas.ESIOSDataCreate) -> models.ESIOSData:
    """Crear nuevo registro ESIOS"""
    db_item = models.ESIOSData(**data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_esios_data_bulk(db: Session, data_list: List[schemas.ESIOSDataCreate]) -> int:
    """Insertar múltiples registros ESIOS"""
    db_items = [models.ESIOSData(**data.model_dump()) for data in data_list]
    db.bulk_save_objects(db_items)
    db.commit()
    return len(db_items)


def get_esios_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[models.ESIOSData]:
    """Obtener datos ESIOS con filtros opcionales"""
    query = db.query(models.ESIOSData)
    
    if start_date:
        query = query.filter(models.ESIOSData.fecha >= start_date)
    if end_date:
        query = query.filter(models.ESIOSData.fecha <= end_date)
    
    return query.order_by(models.ESIOSData.fecha).offset(skip).limit(limit).all()


def get_esios_summary(db: Session) -> dict:
    """Obtener resumen estadístico de datos ESIOS"""
    total = db.query(func.count(models.ESIOSData.id)).scalar()
    
    if total == 0:
        return {
            "total_records": 0,
            "date_range_start": None,
            "date_range_end": None,
            "avg_precio_excedente": None
        }
    
    min_date = db.query(func.min(models.ESIOSData.fecha)).scalar()
    max_date = db.query(func.max(models.ESIOSData.fecha)).scalar()
    avg_precio = db.query(func.avg(models.ESIOSData.precio_excedente)).scalar()
    
    return {
        "total_records": total,
        "date_range_start": min_date,
        "date_range_end": max_date,
        "avg_precio_excedente": round(avg_precio, 4) if avg_precio else None
    }


# ================================
# Production CRUD Operations
# ================================

def create_production_data(db: Session, data: schemas.ProductionDataCreate) -> models.ProductionData:
    """Crear nuevo registro de producción"""
    db_item = models.ProductionData(**data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_production_data_bulk(db: Session, data_list: List[schemas.ProductionDataCreate]) -> int:
    """Insertar múltiples registros de producción"""
    db_items = [models.ProductionData(**data.model_dump()) for data in data_list]
    db.bulk_save_objects(db_items)
    db.commit()
    return len(db_items)


def get_production_data(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[models.ProductionData]:
    """Obtener datos de producción con filtros opcionales"""
    query = db.query(models.ProductionData)
    
    if start_date:
        query = query.filter(models.ProductionData.fecha >= start_date)
    if end_date:
        query = query.filter(models.ProductionData.fecha <= end_date)
    
    return query.order_by(models.ProductionData.fecha).offset(skip).limit(limit).all()


def get_production_summary(db: Session) -> dict:
    """Obtener resumen estadístico de datos de producción"""
    total = db.query(func.count(models.ProductionData.id)).scalar()
    
    if total == 0:
        return {
            "total_records": 0,
            "date_range_start": None,
            "date_range_end": None,
            "avg_production": None,
            "total_production": None
        }
    
    min_date = db.query(func.min(models.ProductionData.fecha)).scalar()
    max_date = db.query(func.max(models.ProductionData.fecha)).scalar()
    avg_prod = db.query(func.avg(models.ProductionData.totalproduction)).scalar()
    total_prod = db.query(func.sum(models.ProductionData.totalproduction)).scalar()
    
    return {
        "total_records": total,
        "date_range_start": min_date,
        "date_range_end": max_date,
        "avg_production": round(avg_prod, 2) if avg_prod else None,
        "total_production": round(total_prod, 2) if total_prod else None
    }


# ================================
# Model Metrics CRUD Operations
# ================================

def create_model_metrics(db: Session, metrics: schemas.ModelMetricsCreate) -> models.ModelMetrics:
    """Guardar métricas de modelo"""
    db_item = models.ModelMetrics(**metrics.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_model_metrics(
    db: Session,
    model_name: Optional[str] = None,
    data_type: Optional[str] = None,
    limit: int = 100
) -> List[models.ModelMetrics]:
    """Obtener métricas de modelos con filtros"""
    query = db.query(models.ModelMetrics)
    
    if model_name:
        query = query.filter(models.ModelMetrics.model_name == model_name)
    if data_type:
        query = query.filter(models.ModelMetrics.data_type == data_type)
    
    return query.order_by(desc(models.ModelMetrics.timestamp)).limit(limit).all()


def get_best_models_by_metric(db: Session, metric: str = "mae") -> List[models.ModelMetrics]:
    """Obtener los mejores modelos según una métrica"""
    if metric == "mae":
        return db.query(models.ModelMetrics).order_by(models.ModelMetrics.mae).limit(10).all()
    elif metric == "rmse":
        return db.query(models.ModelMetrics).order_by(models.ModelMetrics.rmse).limit(10).all()
    elif metric == "r2":
        return db.query(models.ModelMetrics).order_by(desc(models.ModelMetrics.r2_score)).limit(10).all()
    else:
        return []


# ================================
# Forecast CRUD Operations
# ================================

def create_forecast(db: Session, forecast: schemas.ForecastCreate) -> models.Forecast:
    """Guardar predicción"""
    db_item = models.Forecast(**forecast.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_forecast_bulk(db: Session, forecast_list: List[schemas.ForecastCreate]) -> int:
    """Insertar múltiples predicciones"""
    db_items = [models.Forecast(**forecast.model_dump()) for forecast in forecast_list]
    db.bulk_save_objects(db_items)
    db.commit()
    return len(db_items)


def get_forecasts(
    db: Session,
    model_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 1000
) -> List[models.Forecast]:
    """Obtener predicciones con filtros"""
    query = db.query(models.Forecast)
    
    if model_name:
        query = query.filter(models.Forecast.model_name == model_name)
    if start_date:
        query = query.filter(models.Forecast.fecha_prediccion >= start_date)
    if end_date:
        query = query.filter(models.Forecast.fecha_prediccion <= end_date)
    
    return query.order_by(models.Forecast.fecha_prediccion).limit(limit).all()


def get_latest_forecasts(db: Session, model_name: str, limit: int = 30) -> List[models.Forecast]:
    """Obtener las últimas predicciones de un modelo"""
    return db.query(models.Forecast)\
        .filter(models.Forecast.model_name == model_name)\
        .order_by(desc(models.Forecast.created_at))\
        .limit(limit)\
        .all()


# ================================
# Utility Functions
# ================================

def delete_old_forecasts(db: Session, days: int = 30) -> int:
    """Eliminar predicciones antiguas (limpieza)"""
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted = db.query(models.Forecast)\
        .filter(models.Forecast.created_at < cutoff_date)\
        .delete()
    
    db.commit()
    return deleted


def get_database_stats(db: Session) -> dict:
    """Obtener estadísticas generales de la base de datos"""
    aemet_count = db.query(func.count(models.AEMETData.id)).scalar()
    esios_count = db.query(func.count(models.ESIOSData.id)).scalar()
    production_count = db.query(func.count(models.ProductionData.id)).scalar()
    metrics_count = db.query(func.count(models.ModelMetrics.id)).scalar()
    forecast_count = db.query(func.count(models.Forecast.id)).scalar()
    
    return {
        "aemet_records": aemet_count,
        "esios_records": esios_count,
        "production_records": production_count,
        "model_metrics_records": metrics_count,
        "forecast_records": forecast_count,
        "total_records": aemet_count + esios_count + production_count + metrics_count + forecast_count
    }
