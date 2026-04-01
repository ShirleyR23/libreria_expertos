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


@router.get("/employees")
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
    
    result = []
    for e in employees:
        emp_data = {
            "id": e.id,
            "nombre": e.nombre,
            "email": e.email,
            "role_id": e.role_id,
            "role_name": e.role_name,
            "activo": e.activo,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "turno": e.employee.turno if e.employee else None,
            "salario": float(e.employee.salario) if e.employee and e.employee.salario else None,
            "telefono": e.employee.telefono if e.employee else None,
            "direccion": e.employee.direccion if e.employee else None,
            "employee_id": e.employee.id if e.employee else None,
        }
        result.append(emp_data)
    return result



@router.get("/employees/{employee_id}")
def get_employee(
    employee_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtiene un empleado por ID."""
    from app.models.user import User
    e = db.query(User).filter(User.id == employee_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return {
        "id": e.id,
        "nombre": e.nombre,
        "email": e.email,
        "role_id": e.role_id,
        "role_name": e.role_name,
        "activo": e.activo,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "turno": e.employee.turno if e.employee else None,
        "salario": float(e.employee.salario) if e.employee and e.employee.salario else None,
        "telefono": e.employee.telefono if e.employee else None,
        "direccion": e.employee.direccion if e.employee else None,
        "employee_id": e.employee.id if e.employee else None,
    }


@router.put("/employees/{employee_id}")
def update_employee(
    employee_id: int,
    data: dict,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Actualiza datos de un empleado."""
    from app.models.user import User
    from app.models.employee import Employee
    
    user = db.query(User).filter(User.id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Update user fields
    if "nombre" in data and data["nombre"]:
        user.nombre = data["nombre"]
    if "email" in data and data["email"]:
        user.email = data["email"]
    if "activo" in data and data["activo"] is not None:
        user.activo = data["activo"]
    
    # Update employee fields
    if user.employee:
        if "turno" in data and data["turno"]:
            user.employee.turno = data["turno"]
        if "salario" in data and data["salario"] is not None:
            user.employee.salario = data["salario"]
        if "telefono" in data:
            user.employee.telefono = data["telefono"]
        if "direccion" in data:
            user.employee.direccion = data["direccion"]
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "nombre": user.nombre,
        "email": user.email,
        "activo": user.activo,
        "turno": user.employee.turno if user.employee else None,
        "salario": float(user.employee.salario) if user.employee and user.employee.salario else None,
        "telefono": user.employee.telefono if user.employee else None,
        "direccion": user.employee.direccion if user.employee else None,
    }


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
