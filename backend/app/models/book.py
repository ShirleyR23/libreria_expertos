"""
Modelo de Libros - Inventario de la librería.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.core.constants import BookCategory as BookCategoryEnum


class BookCategory(Base):
    """Tabla de categorías de libros."""
    __tablename__ = "categorias_libro"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(BookCategoryEnum), unique=True, nullable=False)
    description = Column(Text)
    
    # Relaciones
    books = relationship("Book", back_populates="categoria")


class Book(Base):
    """Tabla de libros - inventario principal."""
    __tablename__ = "libros"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False, index=True)
    autor = Column(String(150), nullable=False, index=True)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categorias_libro.id"), nullable=False)
    editorial = Column(String(100))
    anio_publicacion = Column(Integer)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=5)
    
    # Campos para sistema experto
    es_bestseller = Column(Boolean, default=False)
    total_ventas = Column(Integer, default=0)
    ventas_ultimos_30_dias = Column(Integer, default=0)
    ultima_venta = Column(DateTime)
    
    # Metadatos
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    categoria = relationship("BookCategory", back_populates="books")
    sale_items = relationship("SaleItem", back_populates="book")
    purchase_items = relationship("PurchaseItem", back_populates="book")
    
    def __repr__(self) -> str:
        return f"<Book(id={self.id}, nombre={self.nombre}, stock={self.stock})>"
    
    @property
    def disponible(self) -> bool:
        """Retorna True si hay stock disponible."""
        return self.stock > 0
    
    @property
    def necesita_reposicion(self) -> bool:
        """Retorna True si el stock está por debajo del mínimo."""
        return self.stock <= self.stock_minimo
    
    def actualizar_stock(self, cantidad: int) -> None:
        """Actualiza el stock del libro."""
        self.stock += cantidad
        if self.stock < 0:
            self.stock = 0
    
    def registrar_venta(self, cantidad: int = 1) -> None:
        """Registra una venta del libro."""
        from datetime import datetime, timezone
        self.stock -= cantidad
        self.total_ventas += cantidad
        self.ventas_ultimos_30_dias += cantidad
        self.ultima_venta = datetime.now(timezone.utc)
