"""
Modelo de Reseñas - Valoraciones de clientes sobre libros comprados.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Review(Base):
    __tablename__ = "resenas"

    id = Column(Integer, primary_key=True, index=True)
    libro_id  = Column(Integer, ForeignKey("libros.id",   ondelete="CASCADE"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    calificacion = Column(Integer, nullable=False)   # 1–5
    titulo       = Column(String(200))
    comentario   = Column(Text)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("calificacion >= 1 AND calificacion <= 5", name="ck_cal_rango"),
        UniqueConstraint("cliente_id", "libro_id", name="uq_resena_cliente_libro"),
    )

    book    = relationship("Book",   backref="reviews")
    cliente = relationship("Client", backref="reviews")
