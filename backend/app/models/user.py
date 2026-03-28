"""
Modelo de Usuario - Tabla unificada de autenticación.
REGLA CRÍTICA: Un correo solo puede existir UNA VEZ en todo el sistema.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.core.constants import UserRole


class Role(Base):
    """Tabla de roles del sistema."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserRole), unique=True, nullable=False)
    description = Column(String(255))
    
    # Relaciones
    users = relationship("User", back_populates="role")


class User(Base):
    """
    Tabla unificada de usuarios.
    Todos los empleados, clientes y admins se autentican mediante esta tabla.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    # Las relaciones a Employee y Client se definen con backref en esos modelos
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.name if self.role else None})>"
    
    @property
    def role_name(self) -> str:
        """Retorna el nombre del rol como string."""
        return self.role.name.value if self.role else None
    
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.role.name == UserRole.ADMIN if self.role else False
    
    def is_empleado(self) -> bool:
        """Verifica si el usuario es empleado."""
        return self.role.name == UserRole.EMPLEADO if self.role else False
    
    def is_cliente(self) -> bool:
        """Verifica si el usuario es cliente."""
        return self.role.name == UserRole.CLIENTE if self.role else False
