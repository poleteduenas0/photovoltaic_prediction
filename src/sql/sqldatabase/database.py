"""
Configuración de SQLite Database con SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuración SQLite
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/photovoltaic_prediction.db")

# Crear directorio si no existe
os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

# URL de conexión SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# Crear engine con configuración para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necesario para SQLite
    echo=True  # Logging SQL queries (desactivar en producción)
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """
    Dependency para FastAPI
    Proporciona una sesión de base de datos que se cierra automáticamente
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializar base de datos creando todas las tablas
    """
    from . import models  # Import local para evitar circular imports
    Base.metadata.create_all(bind=engine)
    print(f"✅ Base de datos SQLite inicializada en: {SQLITE_DB_PATH}")