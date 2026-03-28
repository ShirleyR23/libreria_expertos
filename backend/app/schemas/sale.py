"""
Schemas de Ventas - Pydantic v2.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import SaleStatus, SaleType


class SaleItemCreate(BaseModel):
    """Schema para crear item de venta."""
    libro_id: int
    cantidad: int = Field(..., ge=1)


class SaleItemResponse(BaseModel):
    """Schema de respuesta para item de venta."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    libro_id: int
    libro_nombre: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class SaleCreate(BaseModel):
    """Schema para crear venta."""
    items: List[SaleItemCreate] = Field(..., min_length=1)
    tipo: SaleType
    notas: Optional[str] = None


class SaleResponse(BaseModel):
    """Schema de respuesta para venta."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cliente_id: Optional[int] = None
    cliente_nombre: Optional[str] = None
    empleado_id: Optional[int] = None
    empleado_nombre: Optional[str] = None
    tipo: SaleType
    status: SaleStatus
    items: List[SaleItemResponse]
    subtotal: Decimal
    impuesto: Decimal
    descuento: Decimal
    total: Decimal
    notas: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InvoiceResponse(BaseModel):
    """Schema de respuesta para factura."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    venta_id: int
    numero_factura: str
    serie: str
    numero_correlativo: int
    rtn_emisor: str
    rtn_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None
    subtotal: Decimal
    impuesto: Decimal
    total: Decimal
    estado: str
    fecha_emision: datetime
