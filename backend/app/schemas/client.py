"""
Schemas de Clientes - Pydantic v2.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ClientBase(BaseModel):
    """Base para schemas de cliente."""
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=20)


class ClientCreate(ClientBase):
    """Schema para crear cliente (requiere user_id)."""
    user_id: int


class ClientRegister(BaseModel):
    """Schema para registro de cliente público."""
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=6)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=20)


class ClientResponse(ClientBase):
    """Schema de respuesta para cliente."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    user_nombre: Optional[str] = None
    user_email: Optional[str] = None
    fecha_registro: datetime
    created_at: datetime
