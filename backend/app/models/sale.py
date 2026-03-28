"""
Modelo de Ventas - Gestión de ventas online y presenciales.
Incluye facturación electrónica simulada (estructura SAR).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.core.constants import SaleStatus, SaleType


class Sale(Base):
    """Tabla de ventas - registro de todas las ventas."""
    __tablename__ = "ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones - Foreign Keys
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)
    
    # Información de venta
    tipo = Column(Enum(SaleType), nullable=False)
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDIENTE)
    
    # Totales
    subtotal = Column(Numeric(12, 2), nullable=False)
    impuesto = Column(Numeric(12, 2), default=0)
    descuento = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Metadatos
    notas = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones ORM - Sin back_populates para evitar dependencias circulares
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="sale", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Sale(id={self.id}, tipo={self.tipo}, total={self.total})>"


class SaleItem(Base):
    """Tabla de items de venta - detalle de cada venta."""
    __tablename__ = "venta_items"
    
    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="items")
    book = relationship("Book", back_populates="sale_items")
    
    def __repr__(self) -> str:
        return f"<SaleItem(id={self.id}, libro_id={self.libro_id}, cantidad={self.cantidad})>"


class Invoice(Base):
    """
    Tabla de facturas - estructura SAR simulada.
    """
    __tablename__ = "facturas"
    
    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Datos de factura SAR simulada
    numero_factura = Column(String(50), unique=True, nullable=False)
    serie = Column(String(20), nullable=False)
    numero_correlativo = Column(Integer, nullable=False)
    
    # Información fiscal
    rtn_emisor = Column(String(20), nullable=False)
    rtn_cliente = Column(String(20))
    nombre_cliente = Column(String(200))
    
    # Totales
    subtotal = Column(Numeric(12, 2), nullable=False)
    impuesto = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Estado y firma
    estado = Column(String(20), default="EMITIDA")
    firma_electronica = Column(Text)
    
    # Fechas
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_certificacion = Column(DateTime)
    
    # Relaciones
    sale = relationship("Sale", back_populates="invoice")
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, numero={self.numero_factura})>"
    
    @staticmethod
    def generar_numero_factura(serie: str, correlativo: int) -> str:
        """Genera número de factura en formato SAR."""
        return f"{serie}-{correlativo:08d}"
