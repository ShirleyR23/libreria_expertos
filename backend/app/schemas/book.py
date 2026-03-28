"""
Schemas de Libros - Pydantic v2.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import BookCategory


class BookCategoryResponse(BaseModel):
    """Schema para categoría de libro."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: BookCategory
    description: Optional[str] = None


class BookBase(BaseModel):
    """Base para schemas de libro."""
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


class BookCreate(BookBase):
    """Schema para crear libro."""
    pass


class BookUpdate(BaseModel):
    """Schema para actualizar libro."""
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


class BookResponse(BookBase):
    """Schema de respuesta para libro."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    categoria: Optional[BookCategoryResponse] = None
    disponible: bool
    necesita_reposicion: bool
    es_bestseller: bool
    total_ventas: int
    ventas_ultimos_30_dias: int
    ultima_venta: Optional[datetime] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
