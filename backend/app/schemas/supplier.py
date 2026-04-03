"""
Schemas de Proveedores - Pydantic v2.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class SupplierBookItem(BaseModel):
    """Libro en el catálogo de un proveedor."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    libro_id: int
    costo_unitario: Decimal
    libro_nombre: Optional[str] = None
    libro_autor: Optional[str] = None
    libro_isbn: Optional[str] = None
    libro_stock: Optional[int] = None
    libro_precio: Optional[Decimal] = None
    libro_imagen_url: Optional[str] = None


class SupplierBookCreate(BaseModel):
    libro_id: int
    costo_unitario: Decimal = Field(..., ge=0, decimal_places=2)


class SupplierCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    contacto: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = Field(None, max_length=255)
    notas: Optional[str] = None
    catalogo: Optional[List[SupplierBookCreate]] = []


class SupplierUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    contacto: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = Field(None, max_length=255)
    notas: Optional[str] = None
    activo: Optional[bool] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    activo: bool
    total_pedidos: Optional[int] = 0
    created_at: datetime
    catalogo: Optional[List[SupplierBookItem]] = []


class OrderFromSupplierItem(BaseModel):
    libro_id: int
    cantidad: int = Field(..., ge=1)
    costo_unitario: Decimal = Field(..., ge=0, decimal_places=2)


class OrderFromSupplier(BaseModel):
    """Pedido de libros a un proveedor."""
    items: List[OrderFromSupplierItem] = Field(..., min_length=1)
    notas: Optional[str] = None
