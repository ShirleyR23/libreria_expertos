"""
Routers de la API REST.
"""
from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.sales import router as sales_router
from app.api.purchases import router as purchases_router
from app.api.admin import router as admin_router
from app.api.expert import router as expert_router

__all__ = [
    "auth_router",
    "books_router",
    "sales_router",
    "purchases_router",
    "admin_router",
    "expert_router",
]
