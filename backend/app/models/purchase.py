"""
Modelo de Compras - Gestión de compras a proveedores.
Solo ADMIN puede gestionar compras.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Purchase(Base):
    """Tabla de compras a proveedores."""
    __tablename__ = "compras"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Proveedor
    proveedor_nombre = Column(String(150), nullable=False)
    proveedor_contacto = Column(String(100))
    proveedor_telefono = Column(String(20))
    
    # Empleado que registró la compra
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False)
    
    # Totales
    subtotal = Column(Numeric(12, 2), nullable=False)
    impuesto = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Estado
    estado = Column(String(20), default="RECIBIDA")
    
    # Metadatos
    notas = Column(Text)
    fecha_compra = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_recepcion = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones - Sin back_populates para evitar dependencias circulares
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Purchase(id={self.id}, proveedor={self.proveedor_nombre}, total={self.total})>"


class PurchaseItem(Base):
    """Tabla de items de compra - detalle de cada compra."""
    __tablename__ = "compra_items"
    
    id = Column(Integer, primary_key=True, index=True)
    compra_id = Column(Integer, ForeignKey("compras.id", ondelete="CASCADE"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    
    # Relaciones
    purchase = relationship("Purchase", back_populates="items")
    book = relationship("Book", back_populates="purchase_items")
    
    def __repr__(self) -> str:
        return f"<PurchaseItem(id={self.id}, libro_id={self.libro_id}, cantidad={self.cantidad})>"
