"""
Schemas para recuperación de contraseña.
"""
from pydantic import BaseModel, Field


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=6, max_length=100)
