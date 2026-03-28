"""
Endpoints de Administración.
Gestión exclusiva de administrador.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.post("/employees", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo empleado (solo ADMIN).
    
    - Crea el usuario con rol EMPLEADO
    - Crea el registro de empleado con datos adicionales
    - REGLA: Un correo solo puede existir UNA VEZ
    """
    auth_service = AuthService(db)
    return auth_service.create_employee(employee_data, current_user.id)


@router.get("/employees", response_model=List[UserResponse])
def get_all_employees(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los empleados (solo ADMIN).
    """
    from app.models.user import User
    from app.core.constants import UserRole
    
    employees = db.query(User).filter(
        User.role.has(name=UserRole.EMPLEADO)
    ).all()
    
    return [
        UserResponse(
            id=e.id,
            nombre=e.nombre,
            email=e.email,
            role_id=e.role_id,
            role_name=e.role_name,
            activo=e.activo,
            created_at=e.created_at
        )
        for e in employees
    ]


@router.get("/dashboard-stats")
def get_dashboard_stats(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas para el dashboard de administrador.
    """
    from sqlalchemy import func
    from app.models.book import Book
    from app.models.sale import Sale
    from app.models.user import User
    from app.core.constants import UserRole
    
    # Total de libros
    total_libros = db.query(func.count(Book.id)).filter(Book.activo == True).scalar()
    
    # Libros con stock bajo
    stock_bajo = db.query(func.count(Book.id)).filter(
        Book.stock <= Book.stock_minimo,
        Book.activo == True
    ).scalar()
    
    # Total de ventas
    total_ventas = db.query(func.count(Sale.id)).scalar()
    
    # Ingresos totales
    ingresos_totales = db.query(func.sum(Sale.total)).filter(
        Sale.status == "COMPLETADA"
    ).scalar() or 0
    
    # Total de clientes
    total_clientes = db.query(func.count(User.id)).filter(
        User.role.has(name=UserRole.CLIENTE)
    ).scalar()
    
    # Total de empleados
    total_empleados = db.query(func.count(User.id)).filter(
        User.role.has(name=UserRole.EMPLEADO)
    ).scalar()
    
    return {
        "total_libros": total_libros,
        "stock_bajo": stock_bajo,
        "total_ventas": total_ventas,
        "ingresos_totales": float(ingresos_totales),
        "total_clientes": total_clientes,
        "total_empleados": total_empleados
    }
