"""
Modelo de Empleado.
Los empleados están vinculados a un User mediante user_id.
Solo ADMIN puede crear empleados.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.database.connection import Base


class Employee(Base):
    """Tabla de empleados - información específica de empleados."""
    __tablename__ = "empleados"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    salario = Column(Numeric(10, 2), nullable=False)
    turno = Column(String(50), nullable=False)
    telefono = Column(String(20))
    direccion = Column(String(255))
    fecha_contratacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones - Usamos backref para evitar dependencias circulares
    # uselist=False en el backref es CRÍTICO: hace que User.employee sea un objeto único,
    # no una lista (InstrumentedList), lo que causaba AttributeError al acceder a .turno
    user = relationship("User", backref=backref("employee", uselist=False), uselist=False)
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, user_id={self.user_id}, salario={self.salario})>"