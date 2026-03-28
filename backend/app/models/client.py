"""
Modelo de Cliente.
Los clientes están vinculados a un User mediante user_id.
Un empleado NO puede registrarse como cliente (mismo email).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.database.connection import Base


class Client(Base):
    """Tabla de clientes - información específica de clientes."""
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    telefono = Column(String(20))
    direccion = Column(String(255))
    ciudad = Column(String(100))
    codigo_postal = Column(String(20))
    fecha_registro = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones - Usamos backref para evitar dependencias circulares
    user = relationship("User", backref="client", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, user_id={self.user_id})>"
