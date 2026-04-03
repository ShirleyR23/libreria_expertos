"""
Endpoints de Autenticación.
POST /auth/login
POST /auth/register-client
GET /auth/me
POST /auth/forgot-password
POST /auth/reset-password
GET /auth/validate-reset-token
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user import UserLogin, Token, UserResponse
from app.schemas.client import ClientRegister
from app.schemas.password_reset import PasswordResetRequest, PasswordResetConfirm
from app.services.auth_service import AuthService
from app.services.password_reset_service import (
    request_password_reset, confirm_password_reset, validate_reset_token
)
from app.utils.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login unificado para todos los usuarios (ADMIN, EMPLEADO, CLIENTE)."""
    auth_service = AuthService(db)
    return auth_service.login(login_data)


@router.post("/register-client", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_client(register_data: ClientRegister, db: Session = Depends(get_db)):
    """Registro público de nuevos clientes."""
    auth_service = AuthService(db)
    result = auth_service.register_client(register_data)
    # Enviar email de bienvenida en background (no bloquea la respuesta)
    try:
        from app.services.email_service import send_welcome_email
        send_welcome_email(register_data.email, register_data.nombre)
    except Exception:
        pass
    return result


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Obtiene la información del usuario autenticado."""
    return current_user


@router.post("/forgot-password")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Solicita restablecimiento de contraseña.
    Siempre responde con éxito para no revelar si el email existe.
    """
    request_password_reset(db, data.email)
    return {"message": "Si el correo existe, recibirás un enlace para restablecer tu contraseña."}


@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirma el restablecimiento de contraseña con el token recibido por email."""
    confirm_password_reset(db, data.token, data.new_password)
    return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}


@router.get("/validate-reset-token")
def validate_token(token: str, db: Session = Depends(get_db)):
    """Valida si un token de reset es válido (sin consumirlo)."""
    email = validate_reset_token(token)
    if not email:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    return {"valid": True, "email": email}

