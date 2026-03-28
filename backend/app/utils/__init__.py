"""
Utilidades del sistema.
"""
from app.utils.dependencies import (
    get_current_user,
    require_role,
    require_admin,
    require_empleado,
    require_cliente,
    require_any_authenticated,
)

__all__ = [
    "get_current_user",
    "require_role",
    "require_admin",
    "require_empleado",
    "require_cliente",
    "require_any_authenticated",
]
