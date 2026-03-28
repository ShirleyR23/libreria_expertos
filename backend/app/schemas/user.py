"""
Schemas de Usuario - Pydantic v2.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.constants import UserRole


class UserBase(BaseModel):
    """Base para schemas de usuario."""
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    """Schema para crear usuario."""
    password: str = Field(..., min_length=6, max_length=100)
    role_id: int


class UserLogin(BaseModel):
    """Schema para login de usuario."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema de respuesta para usuario."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role_id: int
    role_name: Optional[str] = None
    activo: bool
    created_at: datetime


class Token(BaseModel):
    """Schema para token JWT."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema para datos decodificados del token."""
    user_id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema para actualizar usuario."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    activo: Optional[bool] = None
