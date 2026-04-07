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
from fastapi.exceptions import RequestValidationError
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

# ── Middleware (orden importa: SecurityMiddleware primero, CORS al final = más externo) ──
# En Starlette el último add_middleware queda como capa más externa (primera en procesar).
# CORSMiddleware DEBE ser el más externo para manejar preflight OPTIONS correctamente.

app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://localhost:3000",
        "http://127.0.0.1:4321",
        "http://127.0.0.1:3000",
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


# ─── TRADUCCIÓN DE ERRORES DE VALIDACIÓN (Pydantic → Español) ─────────────
_VALIDATION_MESSAGES_ES: dict[str, str] = {
    # Email
    "value_error.email": "El correo electrónico no es válido.",
    "value is not a valid email address": "El correo electrónico no es válido.",
    "an email address must have an @-sign": "El correo electrónico debe contener @.",
    "an email address must have a domain part": "El correo electrónico debe tener un dominio (ej: usuario@dominio.com).",
    "the email address is not valid": "La dirección de correo no es válida.",
    # Campos requeridos
    "field required": "Este campo es obligatorio.",
    "none is not an allowed value": "Este campo no puede estar vacío.",
    "value_error.missing": "Este campo es obligatorio.",
    # Longitudes de cadena
    "string_too_short": "El valor ingresado es demasiado corto.",
    "string_too_long": "El valor ingresado es demasiado largo.",
    "ensure this value has at least": "El valor es demasiado corto.",
    "ensure this value has at most": "El valor es demasiado largo.",
    # Tipos
    "value is not a valid integer": "Debe ingresar un número entero válido.",
    "value is not a valid float": "Debe ingresar un número válido.",
    "value is not a valid boolean": "El valor debe ser verdadero o falso.",
    "value is not a valid list": "Se esperaba una lista de valores.",
    "value is not a valid dict": "Formato de datos no válido.",
    # URL
    "invalid or missing URL scheme": "La URL ingresada no es válida.",
    "url_scheme": "La URL ingresada no es válida.",
    # Números
    "ensure this value is greater than": "El valor debe ser mayor.",
    "ensure this value is less than": "El valor debe ser menor.",
    "ensure this value is greater than or equal to": "El valor debe ser mayor o igual.",
    "ensure this value is less than or equal to": "El valor debe ser menor o igual.",
    "value is not a valid number": "Debe ingresar un número válido.",
    # Genéricos
    "literal_error": "Valor no permitido.",
    "type_error": "Tipo de dato incorrecto.",
}


def _translate_validation_error(msg: str) -> str:
    """Convierte mensajes de error de Pydantic al español."""
    msg_lower = msg.lower()
    for key, translated in _VALIDATION_MESSAGES_ES.items():
        if key.lower() in msg_lower:
            return translated
    return "El valor ingresado no es válido."


def _field_label(loc: tuple) -> str:
    """Convierte la ubicación del campo en un nombre legible en español."""
    _FIELD_NAMES_ES = {
        "email": "correo electrónico",
        "password": "contraseña",
        "nombre": "nombre",
        "telefono": "teléfono",
        "direccion": "dirección",
        "ciudad": "ciudad",
        "codigo_postal": "código postal",
        "role_id": "rol",
        "activo": "estado",
        "precio": "precio",
        "stock": "stock",
        "isbn": "ISBN",
        "titulo": "título",
        "autor": "autor",
        "cantidad": "cantidad",
        "new_password": "nueva contraseña",
        "token": "token",
    }
    parts = [str(p) for p in loc if p != "body"]
    if parts:
        last = parts[-1]
        return _FIELD_NAMES_ES.get(last, last.replace("_", " "))
    return "campo"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Retorna errores de validación de Pydantic en español."""
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=422,
            content={"detail": "Los datos enviados no son válidos."},
        )

    messages = []
    for error in errors:
        loc = error.get("loc", ())
        raw_msg = error.get("msg", "")
        field = _field_label(loc)
        translated = _translate_validation_error(raw_msg)
        messages.append(f"{field.capitalize()}: {translated}")

    detail = " | ".join(messages) if len(messages) > 1 else messages[0]
    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )


@app.get("/")
def root():
    return {"nombre": "Sistema de Gestión para Librería", "version": "1.0.0", "status": "operativo"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development")