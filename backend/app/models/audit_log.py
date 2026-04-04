"""
Modelo de Logs de Auditoría - Trazabilidad de acciones en el sistema.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    accion      = Column(String(120), nullable=False, index=True)
    tabla       = Column(String(80),  index=True)
    registro_id = Column(Integer)
    detalle     = Column(Text)          # JSON libre con antes/después
    ip_address  = Column(String(50))
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", backref="audit_logs")


def log_action(db, user_id, accion: str, tabla: str = None,
               registro_id: int = None, detalle: str = None, ip: str = None):
    """Helper sin commit — el llamador decide cuándo hacer commit."""
    entry = AuditLog(user_id=user_id, accion=accion, tabla=tabla,
                     registro_id=registro_id, detalle=detalle, ip_address=ip)
    db.add(entry)
