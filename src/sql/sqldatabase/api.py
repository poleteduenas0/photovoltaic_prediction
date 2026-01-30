"""
FastAPI REST API para el sistema de predicción fotovoltaica
Endpoints para gestionar datos y predicciones
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import crud, models, schemas
from .database import SessionLocal, engine, get_db, init_db

# Inicializar base de datos al arrancar
init_db()

# Crear aplicación FastAPI
app = FastAPI(
    title="Photovoltaic Prediction API",
    description="API para gestión de datos meteorológicos, producción fotovoltaica y predicciones",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# Health Check
# ================================

@app.get("/", tags=["Health"])
def root():
    """Endpoint raíz - verificar que la API está funcionando"""
    return {
        "message": "Photovoltaic Prediction API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check con estadísticas de la base de datos"""
    try:
        stats = crud.get_database_stats(db)
        return {
            "status": "healthy",
            "database": "connected",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ================================
# AEMET Endpoints
# ================================

@app.post("/aemet/", response_model=schemas.AEMETDataResponse, status_code=status.HTTP_201_CREATED, tags=["AEMET"])
def create_aemet_record(data: schemas.AEMETDataCreate, db: Session = Depends(get_db)):
    """Crear un nuevo registro de datos AEMET"""
    try:
        # Verificar si ya existe
        existing = crud.get_aemet_by_date(db, data.fecha)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un registro para la fecha {data.fecha}"
            )
        
        return crud.create_aemet_data(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/aemet/bulk", status_code=status.HTTP_201_CREATED, tags=["AEMET"])
def create_aemet_bulk(data_list: List[schemas.AEMETDataCreate], db: Session = Depends(get_db)):
    """Inserción masiva de datos AEMET"""
    try:
        count = crud.create_aemet_data_bulk(db, data_list)
        return {"message": f"Se insertaron {count} registros correctamente", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/aemet/", response_model=List[schemas.AEMETDataResponse], tags=["AEMET"])
def get_aemet_records(
    start_date: Optional[datetime] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Obtener registros AEMET con filtros opcionales"""
    return crud.get_aemet_data(db, start_date, end_date, skip, limit)


@app.get("/aemet/summary", tags=["AEMET"])
def get_aemet_summary(db: Session = Depends(get_db)):
    """Obtener resumen estadístico de datos AEMET"""
    return crud.get_aemet_summary(db)


@app.get("/aemet/date/{fecha}", response_model=schemas.AEMETDataResponse, tags=["AEMET"])
def get_aemet_by_date(fecha: datetime, db: Session = Depends(get_db)):
    """Obtener registro AEMET por fecha específica"""
    record = crud.get_aemet_by_date(db, fecha)
    if not record:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return record


# ================================
# ESIOS Endpoints
# ================================

@app.post("/esios/", response_model=schemas.ESIOSDataResponse, status_code=status.HTTP_201_CREATED, tags=["ESIOS"])
def create_esios_record(data: schemas.ESIOSDataCreate, db: Session = Depends(get_db)):
    """Crear un nuevo registro de datos ESIOS"""
    try:
        return crud.create_esios_data(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/esios/bulk", status_code=status.HTTP_201_CREATED, tags=["ESIOS"])
def create_esios_bulk(data_list: List[schemas.ESIOSDataCreate], db: Session = Depends(get_db)):
    """Inserción masiva de datos ESIOS"""
    try:
        count = crud.create_esios_data_bulk(db, data_list)
        return {"message": f"Se insertaron {count} registros correctamente", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/esios/", response_model=List[schemas.ESIOSDataResponse], tags=["ESIOS"])
def get_esios_records(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Obtener registros ESIOS con filtros opcionales"""
    return crud.get_esios_data(db, start_date, end_date, skip, limit)


@app.get("/esios/summary", tags=["ESIOS"])
def get_esios_summary(db: Session = Depends(get_db)):
    """Obtener resumen estadístico de datos ESIOS"""
    return crud.get_esios_summary(db)


# ================================
# Production Endpoints
# ================================

@app.post("/production/", response_model=schemas.ProductionDataResponse, status_code=status.HTTP_201_CREATED, tags=["Production"])
def create_production_record(data: schemas.ProductionDataCreate, db: Session = Depends(get_db)):
    """Crear un nuevo registro de producción"""
    try:
        return crud.create_production_data(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/production/bulk", status_code=status.HTTP_201_CREATED, tags=["Production"])
def create_production_bulk(data_list: List[schemas.ProductionDataCreate], db: Session = Depends(get_db)):
    """Inserción masiva de datos de producción"""
    try:
        count = crud.create_production_data_bulk(db, data_list)
        return {"message": f"Se insertaron {count} registros correctamente", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/production/", response_model=List[schemas.ProductionDataResponse], tags=["Production"])
def get_production_records(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Obtener registros de producción con filtros opcionales"""
    return crud.get_production_data(db, start_date, end_date, skip, limit)


@app.get("/production/summary", tags=["Production"])
def get_production_summary(db: Session = Depends(get_db)):
    """Obtener resumen estadístico de datos de producción"""
    return crud.get_production_summary(db)


# ================================
# Model Metrics Endpoints
# ================================

@app.post("/metrics/", response_model=schemas.ModelMetricsResponse, status_code=status.HTTP_201_CREATED, tags=["Metrics"])
def create_metrics(metrics: schemas.ModelMetricsCreate, db: Session = Depends(get_db)):
    """Guardar métricas de evaluación de modelo"""
    return crud.create_model_metrics(db, metrics)


@app.get("/metrics/", response_model=List[schemas.ModelMetricsResponse], tags=["Metrics"])
def get_metrics(
    model_name: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Obtener métricas de modelos con filtros"""
    return crud.get_model_metrics(db, model_name, data_type, limit)


@app.get("/metrics/best", response_model=List[schemas.ModelMetricsResponse], tags=["Metrics"])
def get_best_models(
    metric: str = Query("mae", description="Métrica: mae, rmse, r2"),
    db: Session = Depends(get_db)
):
    """Obtener los mejores modelos según una métrica"""
    return crud.get_best_models_by_metric(db, metric)


# ================================
# Forecast Endpoints
# ================================

@app.post("/forecast/", response_model=schemas.ForecastResponse, status_code=status.HTTP_201_CREATED, tags=["Forecast"])
def create_forecast(forecast: schemas.ForecastCreate, db: Session = Depends(get_db)):
    """Guardar una predicción"""
    return crud.create_forecast(db, forecast)


@app.post("/forecast/bulk", status_code=status.HTTP_201_CREATED, tags=["Forecast"])
def create_forecast_bulk(forecast_list: List[schemas.ForecastCreate], db: Session = Depends(get_db)):
    """Inserción masiva de predicciones"""
    try:
        count = crud.create_forecast_bulk(db, forecast_list)
        return {"message": f"Se insertaron {count} predicciones correctamente", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/forecast/", response_model=List[schemas.ForecastResponse], tags=["Forecast"])
def get_forecasts(
    model_name: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Obtener predicciones con filtros"""
    return crud.get_forecasts(db, model_name, start_date, end_date, limit)


@app.get("/forecast/latest/{model_name}", response_model=List[schemas.ForecastResponse], tags=["Forecast"])
def get_latest_forecasts(
    model_name: str,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener las últimas predicciones de un modelo"""
    return crud.get_latest_forecasts(db, model_name, limit)


# ================================
# Utility Endpoints
# ================================

@app.delete("/forecast/cleanup", tags=["Utility"])
def cleanup_old_forecasts(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Eliminar predicciones antiguas"""
    deleted = crud.delete_old_forecasts(db, days)
    return {"message": f"Se eliminaron {deleted} predicciones antiguas", "deleted": deleted}


@app.get("/stats", tags=["Utility"])
def get_database_stats(db: Session = Depends(get_db)):
    """Obtener estadísticas generales de la base de datos"""
    return crud.get_database_stats(db)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
