"""
Routers de la API REST.
"""
from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.sales import router as sales_router
from app.api.purchases import router as purchases_router
from app.api.admin import router as admin_router
from app.api.expert import router as expert_router
from app.api.suppliers import router as suppliers_router
from app.api.reviews import router as reviews_router                          # ← NUEVO
from app.api.extra import reports_router, audit_router, isbn_router, charts_router  # ← NUEVO

__all__ = [
    "auth_router", "books_router", "sales_router", "purchases_router",
    "admin_router", "expert_router", "suppliers_router",
    "reviews_router",    # ← NUEVO
    "reports_router",    # ← NUEVO
    "audit_router",      # ← NUEVO
    "isbn_router",       # ← NUEVO
    "charts_router",     # ← NUEVO
]
