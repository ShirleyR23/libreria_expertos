"""
Schemas de Libros - Pydantic v2.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import BookCategory


class BookCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: BookCategory
    description: Optional[str] = None


class BookBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    autor: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None
    categoria_id: int
    editorial: Optional[str] = Field(None, max_length=100)
    anio_publicacion: Optional[int] = Field(None, ge=100, le=2100)
    precio: Decimal = Field(..., ge=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5, ge=0)
    imagen_url: Optional[str] = Field(None, max_length=500)
    pdf_url: Optional[str] = Field(None, max_length=500)
    pdf_preview_pages: Optional[int] = Field(3, ge=1, le=20)


class BookCreate(BookBase):
    """Schema para crear libro. Incluye campos opcionales de compra al proveedor."""
    proveedor_nombre: Optional[str] = Field(None, max_length=150)
    proveedor_contacto: Optional[str] = Field(None, max_length=150)
    proveedor_telefono: Optional[str] = Field(None, max_length=20)
    cantidad_compra: Optional[int] = Field(None, ge=1)
    costo_compra: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class BookUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    autor: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    editorial: Optional[str] = Field(None, max_length=100)
    anio_publicacion: Optional[int] = Field(None, ge=1000, le=2100)
    precio: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None
    imagen_url: Optional[str] = Field(None, max_length=500)
    pdf_url: Optional[str] = Field(None, max_length=500)
    pdf_preview_pages: Optional[int] = Field(3, ge=1, le=20)


class BookResponse(BookBase):
    """imagen_url ya viene de BookBase — no se duplica aquí."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    has_pdf: Optional[bool] = None  # True si tiene PDF disponible
    categoria: Optional[BookCategoryResponse] = None
    disponible: bool
    necesita_reposicion: bool
    es_bestseller: bool
    total_ventas: int
    ventas_ultimos_30_dias: int
    ultima_venta: Optional[datetime] = None
    activo: bool
    precio_original: Optional[Decimal] = None  # Precio antes del descuento (None = sin descuento activo)
    created_at: datetime
    updated_at: datetime