"""
Endpoints de Autenticación.
POST /auth/login
POST /auth/register-client
GET /auth/me
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user import UserLogin, Token, UserResponse
from app.schemas.client import ClientRegister
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login unificado para todos los usuarios (ADMIN, EMPLEADO, CLIENTE).
    
    - Empleados inician sesión por correo y contraseña igual que clientes.
    - JWT incluye el rol del usuario.
    """
    auth_service = AuthService(db)
    return auth_service.login(login_data)


@router.post("/register-client", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_client(
    register_data: ClientRegister,
    db: Session = Depends(get_db)
):
    """
    Registro público de nuevos clientes.
    
    REGLA: Un correo solo puede existir UNA VEZ.
    Si un empleado ya tiene cuenta, NO puede registrarse como cliente.
    """
    auth_service = AuthService(db)
    return auth_service.register_client(register_data)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene la información del usuario autenticado.
    """
    return current_user
