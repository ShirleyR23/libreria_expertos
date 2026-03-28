"""
SISTEMA DE GESTIÓN PARA LIBRERÍA
================================
Backend API con FastAPI + Python 3.13.9

Arquitectura:
- FastAPI para API REST
- SQLAlchemy 2.0 para ORM
- PostgreSQL para base de datos
- JWT para autenticación
- RBAC para control de acceso

Compatible con Python 3.13.9
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.connection import init_db
from app.api import (
    auth_router,
    books_router,
    sales_router,
    purchases_router,
    admin_router,
    expert_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Inicializa la base de datos al iniciar.
    """
    # Inicializar base de datos
    init_db()
    print("✅ Base de datos inicializada")
    yield
    # Cleanup al cerrar (si es necesario)
    print("👋 Aplicación cerrada")


# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión para Librería",
    description="""
    API REST para gestión de librería con:
    - Autenticación JWT unificada
    - Control de acceso basado en roles (RBAC)
    - Gestión de inventario y ventas
    - Sistema experto de recomendaciones
    - Facturación electrónica simulada (SAR)
    """,
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Configurar CORS para comunicación con frontend Astro
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Astro dev server
        "http://localhost:3000",  # Alternativo
        "http://127.0.0.1:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

# Autenticación
app.include_router(auth_router, prefix="/api/v1")

# Libros y Catálogo
app.include_router(books_router, prefix="/api/v1")

# Ventas
app.include_router(sales_router, prefix="/api/v1")

# Compras (solo admin)
app.include_router(purchases_router, prefix="/api/v1")

# Administración
app.include_router(admin_router, prefix="/api/v1")

# Sistema Experto
app.include_router(expert_router, prefix="/api/v1")


# ============================================================
# ENDPOINTS DE SALUD
# ============================================================

@app.get("/")
def root():
    """Endpoint raíz - información del sistema."""
    return {
        "nombre": "Sistema de Gestión para Librería",
        "version": "1.0.0",
        "api_version": "v1",
        "documentacion": "/docs",
        "status": "operativo"
    }


@app.get("/health")
def health_check():
    """Endpoint de verificación de salud."""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
