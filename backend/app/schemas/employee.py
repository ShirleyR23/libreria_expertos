"""
Schemas de Empleados - Pydantic v2.
Solo ADMIN puede crear empleados.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class EmployeeBase(BaseModel):
    """Base para schemas de empleado."""
    salario: Decimal = Field(..., ge=0, decimal_places=2)
    turno: str = Field(..., max_length=50)  # Mañana, Tarde, Completo
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)


class EmployeeCreate(BaseModel):
    """Schema para crear empleado (incluye datos de usuario)."""
    # Datos de usuario
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=6)
    
    # Datos de empleado
    salario: Decimal = Field(..., ge=0, decimal_places=2)
    turno: str = Field(..., max_length=50)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)


class EmployeeResponse(EmployeeBase):
    """Schema de respuesta para empleado."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    user_nombre: Optional[str] = None
    user_email: Optional[str] = None
    fecha_contratacion: datetime
    created_at: datetime
