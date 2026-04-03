"""
Endpoints de Proveedores.
Solo accesibles por ADMIN y EMPLEADO.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierBookCreate, OrderFromSupplier
)
from app.services.supplier_service import SupplierService
from app.utils.dependencies import require_admin, require_empleado

router = APIRouter(prefix="/suppliers", tags=["Proveedores"])


@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db),
):
    """Lista todos los proveedores activos."""
    return SupplierService(db).get_all(skip=skip, limit=limit)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db),
):
    """Obtiene un proveedor por ID con su catálogo de libros."""
    return SupplierService(db).get_by_id(supplier_id)


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Crea un nuevo proveedor (solo admin)."""
    return SupplierService(db).create(data)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Actualiza datos de un proveedor (solo admin)."""
    return SupplierService(db).update(supplier_id, data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Desactiva un proveedor (solo admin)."""
    SupplierService(db).delete(supplier_id)


@router.post("/{supplier_id}/catalog", response_model=SupplierResponse)
def add_book_to_catalog(
    supplier_id: int,
    data: SupplierBookCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Agrega o actualiza un libro en el catálogo del proveedor."""
    return SupplierService(db).add_book_to_catalog(supplier_id, data.libro_id, float(data.costo_unitario))


@router.delete("/{supplier_id}/catalog/{libro_id}", response_model=SupplierResponse)
def remove_book_from_catalog(
    supplier_id: int,
    libro_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Elimina un libro del catálogo del proveedor."""
    return SupplierService(db).remove_book_from_catalog(supplier_id, libro_id)


@router.post("/{supplier_id}/order")
def create_order(
    supplier_id: int,
    order: OrderFromSupplier,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db),
):
    """
    Crea un pedido (compra) a un proveedor.
    Actualiza el stock de los libros automáticamente.
    """
    from app.models.employee import Employee
    empleado = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not empleado:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo empleados pueden realizar pedidos")
    return SupplierService(db).create_order(supplier_id, order, empleado.id)
