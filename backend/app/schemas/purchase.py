"""
Schemas de Compras - Pydantic v2.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class PurchaseItemCreate(BaseModel):
    """Schema para crear item de compra."""
    libro_id: int
    cantidad: int = Field(..., ge=1)
    costo_unitario: Decimal = Field(..., ge=0, decimal_places=2)


class PurchaseItemResponse(BaseModel):
    """Schema de respuesta para item de compra."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    libro_id: int
    libro_nombre: Optional[str] = None
    cantidad: int
    costo_unitario: Decimal
    subtotal: Decimal


class PurchaseCreate(BaseModel):
    """Schema para crear compra."""
    proveedor_nombre: str = Field(..., min_length=1, max_length=150)
    proveedor_contacto: Optional[str] = Field(None, max_length=100)
    proveedor_telefono: Optional[str] = Field(None, max_length=20)
    items: List[PurchaseItemCreate] = Field(..., min_length=1)
    notas: Optional[str] = None


class PurchaseResponse(BaseModel):
    """Schema de respuesta para compra."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    proveedor_nombre: str
    proveedor_contacto: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    empleado_id: int
    empleado_nombre: Optional[str] = None
    items: List[PurchaseItemResponse]
    subtotal: Decimal
    impuesto: Decimal
    total: Decimal
    estado: str
    notas: Optional[str] = None
    fecha_compra: datetime
    fecha_recepcion: Optional[datetime] = None
    created_at: datetime
