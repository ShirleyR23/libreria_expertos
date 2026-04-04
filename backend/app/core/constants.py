"""
Constantes del sistema de librería.
"""
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario del sistema."""
    ADMIN = "ADMIN"
    GERENTE  = "GERENTE"
    EMPLEADO = "EMPLEADO"
    CLIENTE = "CLIENTE"


class BookCategory(str, Enum):
    """Categorías de libros disponibles."""
    FICCION = "Ficción"
    NO_FICCION = "No Ficción"
    CIENCIA = "Ciencia"
    TECNOLOGIA = "Tecnología"
    HISTORIA = "Historia"
    ARTE = "Arte"
    LITERATURA = "Literatura"
    INFANTIL = "Infantil"
    ACADEMICO = "Académico"
    FILOSOFIA = "Filosofía"


# Umbrales del Sistema Experto
class ExpertSystemThresholds:
    """Umbrales para el sistema experto de inventario."""
    STOCK_MINIMO_ALERTA = 5
    STOCK_URGENTE = 10
    VENTAS_30_DIAS_URGENTE = 20
    VENTAS_MES_BESTSELLER = 50
    DIAS_SIN_VENTAS_PROMOCION = 60


# Estados de venta
class SaleStatus(str, Enum):
    """Estados posibles de una venta."""
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"


# Tipos de venta
class SaleType(str, Enum):
    """Tipos de venta."""
    ONLINE = "ONLINE"
    PRESENCIAL = "PRESENCIAL"
