"""
SISTEMA DE GESTIÓN PARA LIBRERÍA
================================
Backend API con FastAPI + Python 3.13.9
"""
import os
import re
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.database.connection import init_db
from app.api import (
    auth_router,
    books_router,
    sales_router,
    purchases_router,
    admin_router,
    expert_router,
    suppliers_router,
    reviews_router,   # ← NUEVO
    reports_router,   # ← NUEVO
    audit_router,     # ← NUEVO
    isbn_router,      # ← NUEVO
    charts_router,    # ← NUEVO
)

settings = get_settings()

# Directorio para imágenes de portadas
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "covers")
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ─── RATE LIMITER (in-memory) ──────────────────────────────────────────────
_rate_buckets: dict = defaultdict(list)
RATE_LIMIT_REQUESTS = 120   # solicitudes máximas
RATE_LIMIT_WINDOW   = 60    # por 60 segundos


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─── PATRONES SQL INJECTION ────────────────────────────────────────────────
_SQL_PATTERNS = re.compile(
    r"(--|\b(union|select|insert|update|delete|drop|create|alter|exec|execute|"
    r"xp_|sp_|declare|cast|convert|char|nchar|varchar|nvarchar|waitfor|sleep)\b"
    r"|;|\bor\b\s+\d|\band\b\s+\d|\/\*|\*\/|0x[0-9a-fA-F]+)",
    re.IGNORECASE,
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de seguridad: rate limiting, anti-SQLi, headers de seguridad."""

    async def dispatch(self, request: Request, call_next):
        client_ip = _get_client_ip(request)
        now = time.time()

        # ── Rate limiting ──────────────────────────────────────────────────
        window = _rate_buckets[client_ip]
        _rate_buckets[client_ip] = [t for t in window if now - t < RATE_LIMIT_WINDOW]
        if len(_rate_buckets[client_ip]) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intenta de nuevo en un momento."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )
        _rate_buckets[client_ip].append(now)

        # ── SQL Injection check (query params + path) ──────────────────────
        target = str(request.url.query) + str(request.url.path)
        if _SQL_PATTERNS.search(target):
            return JSONResponse(
                status_code=400,
                content={"detail": "Solicitud no permitida."},
            )

        # ── Body SQL injection check (solo para JSON pequeños) ─────────────
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body_bytes = await request.body()
                if len(body_bytes) < 8192:  # sólo revisar bodies pequeños
                    body_str = body_bytes.decode("utf-8", errors="ignore")
                    if _SQL_PATTERNS.search(body_str):
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Solicitud no permitida."},
                        )

        response = await call_next(request)

        # ── Security headers ───────────────────────────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Permitir SAMEORIGIN para rutas de PDF (lector interno), DENY para el resto
        if "/books/pdf-" in str(request.url.path):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Evitar que el navegador cachee respuestas de la API
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        # Ocultar tecnología del servidor
        try:
            del response.headers["server"]
        except (KeyError, Exception):
            pass

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Base de datos inicializada")
    yield
    print("👋 Aplicación cerrada")


app = FastAPI(
    title="Sistema de Gestión para Librería",
    description="API REST para gestión de librería",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Servir archivos estáticos (imágenes subidas)
# Directorios de uploads
uploads_base = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(os.path.join(uploads_base, "covers"), exist_ok=True)
os.makedirs(os.path.join(uploads_base, "pdfs"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_base), name="uploads")

# ── Middleware (orden importa: primero seguridad, luego CORS) ──────────────
app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://localhost:3000",
        "http://127.0.0.1:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(purchases_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(expert_router, prefix="/api/v1")
app.include_router(suppliers_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")   # ← NUEVO
app.include_router(reports_router, prefix="/api/v1")   # ← NUEVO
app.include_router(audit_router,   prefix="/api/v1")   # ← NUEVO
app.include_router(isbn_router,    prefix="/api/v1")   # ← NUEVO
app.include_router(charts_router,  prefix="/api/v1")   # ← NUEVO


@app.get("/")
def root():
    return {"nombre": "Sistema de Gestión para Librería", "version": "1.0.0", "status": "operativo"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development")