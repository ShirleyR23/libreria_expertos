"""
Configuración central de la aplicación usando Pydantic Settings.
Compatible con Python 3.13.9

Soporta SQLite (desarrollo local) y PostgreSQL (Docker)
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    # Base de datos - SQLite por defecto para desarrollo local
    # PostgreSQL cuando se usa Docker
    DATABASE_URL: str = "sqlite:///./libreria.db"
    
    # JWT Configuration
    SECRET_KEY: str = "tu-clave-secreta-super-segura-cambia-esto-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Entorno
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna instancia cacheada de configuración."""
    return Settings()
