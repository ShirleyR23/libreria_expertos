"""
Servicio de Autenticación - JWT y manejo de usuarios.
Compatible con Python 3.13.9
"""
from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.models.client import Client
from app.models.employee import Employee
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.schemas.client import ClientRegister
from app.schemas.employee import EmployeeCreate
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.constants import UserRole
from app.models.audit_log import log_action


class AuthService:
    """Servicio de autenticación y gestión de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autentica un usuario por email y contraseña."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.activo:
            return None
        return user
    
    def login(self, login_data: UserLogin) -> Token:
        """Procesa el login y retorna token JWT."""
        user = self.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token con información del usuario
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role_name,
                "email": user.email,
                "nombre": user.nombre
            },
            expires_delta=access_token_expires
        )

        # Registrar en auditoría
        try:
            log_action(self.db, user.id, "LOGIN", "users", user.id,
                       f"Inicio de sesión: {user.email} ({user.role_name})")
            self.db.commit()
        except Exception:
            pass

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=self._user_to_response(user)
        )
    
    def register_client(self, register_data: ClientRegister) -> Token:
        """Registra un nuevo cliente."""
        # Verificar si el email ya existe
        existing_user = self.db.query(User).filter(User.email == register_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        
        # Obtener rol de cliente
        cliente_role = self.db.query(Role).filter(Role.name == UserRole.CLIENTE).first()
        if not cliente_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rol de cliente no encontrado"
            )
        
        # Crear usuario
        new_user = User(
            nombre=register_data.nombre,
            email=register_data.email,
            password_hash=get_password_hash(register_data.password),
            role_id=cliente_role.id,
            activo=True
        )
        self.db.add(new_user)
        self.db.flush()  # Para obtener el ID
        
        # Crear cliente
        new_client = Client(
            user_id=new_user.id,
        )
        self.db.add(new_client)
        log_action(self.db, new_user.id, "REGISTER_CLIENT", "users", new_user.id,
                   f"Nuevo cliente registrado: {new_user.nombre} ({new_user.email})")
        self.db.commit()
        self.db.refresh(new_user)

        # Generar token
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={
                "sub": str(new_user.id),
                "role": new_user.role_name,
                "email": new_user.email,
                "nombre": new_user.nombre
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=self._user_to_response(new_user)
        )
    
    def create_employee(self, employee_data: EmployeeCreate, admin_user_id: int) -> UserResponse:
        """Crea un nuevo empleado (solo admin)."""
        # Verificar que el usuario actual es admin
        admin = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin or not admin.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el administrador puede crear empleados"
            )
        
        # Verificar si el email ya existe
        existing_user = self.db.query(User).filter(User.email == employee_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        
        # Obtener rol de empleado
        empleado_role = self.db.query(Role).filter(Role.name == UserRole.EMPLEADO).first()
        if not empleado_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rol de empleado no encontrado"
            )
        
        # Crear usuario
        new_user = User(
            nombre=employee_data.nombre,
            email=employee_data.email,
            password_hash=get_password_hash(employee_data.password),
            role_id=empleado_role.id,
            activo=True
        )
        self.db.add(new_user)
        self.db.flush()
        
        # Crear empleado
        new_employee = Employee(
            user_id=new_user.id,
            salario=employee_data.salario,
            turno=employee_data.turno,
            telefono=employee_data.telefono,
            direccion=employee_data.direccion
        )
        self.db.add(new_employee)
        log_action(self.db, admin_user_id, "CREATE_EMPLOYEE", "users", new_user.id,
                   f"Empleado creado: {new_user.nombre} ({new_user.email}) por admin ID {admin_user_id}")
        self.db.commit()
        self.db.refresh(new_user)
        
        return self._user_to_response(new_user)
    
    def get_current_user(self, user_id: int) -> Optional[User]:
        """Obtiene el usuario actual por ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def _user_to_response(self, user: User) -> UserResponse:
        """Convierte un modelo User a UserResponse."""
        return UserResponse(
            id=user.id,
            nombre=user.nombre,
            email=user.email,
            role_id=user.role_id,
            role_name=user.role_name,
            activo=user.activo,
            created_at=user.created_at
        )