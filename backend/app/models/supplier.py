"""
Modelo de Proveedores - Gestión de proveedores de la librería.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Supplier(Base):
    """Tabla de proveedores."""
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(255), index=True)
    direccion = Column(String(255))
    notas = Column(Text)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    catalogo = relationship("SupplierBook", back_populates="supplier", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Supplier(id={self.id}, nombre={self.nombre})>"


class SupplierBook(Base):
    """Catálogo de libros que vende un proveedor."""
    __tablename__ = "proveedor_libros"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id", ondelete="CASCADE"), nullable=False)
    costo_unitario = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    supplier = relationship("Supplier", back_populates="catalogo")
    book = relationship("Book")
