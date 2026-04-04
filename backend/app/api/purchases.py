"""
Endpoints de Compras a Proveedores.
Solo ADMIN puede gestionar compras.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.purchase import PurchaseCreate, PurchaseResponse
from app.services.purchase_service import PurchaseService
from app.utils.dependencies import require_admin, require_empleado
from app.models.audit_log import log_action

router = APIRouter(prefix="/purchases", tags=["Compras"])


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    purchase_data: PurchaseCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva compra a proveedor (solo ADMIN).

    - Actualización automática de inventario
    - Registra el empleado que realizó la compra
    """
    from app.models.employee import Employee
    empleado = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not empleado and current_user.is_admin:
        empleado = db.query(Employee).first()
    empleado_id = empleado.id if empleado else None

    purchase_service = PurchaseService(db)
    result = purchase_service.create_purchase(purchase_data, empleado_id)
    log_action(db, current_user.id, "CREATE_PURCHASE", "purchases", result.id,
               f"Compra #{result.id} proveedor:'{purchase_data.proveedor_nombre}' total:L.{result.total}")
    db.commit()
    return result


@router.get("/by-supplier/{supplier_id}", response_model=List[PurchaseResponse])
def get_purchases_by_supplier(
    supplier_id: int,
    limit: int = Query(5, ge=1, le=50),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db),
):
    """Obtiene las compras más recientes de un proveedor específico."""
    return PurchaseService(db).get_by_supplier(supplier_id, limit)


@router.get("/", response_model=List[PurchaseResponse])
def get_all_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtiene todas las compras a proveedores (solo ADMIN)."""
    purchase_service = PurchaseService(db)
    return purchase_service.get_all_purchases(skip=skip, limit=limit)


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtiene una compra específica por ID (solo ADMIN)."""
    purchase_service = PurchaseService(db)
    return purchase_service.get_purchase_by_id(purchase_id)


@router.post("/{purchase_id}/cancel", response_model=PurchaseResponse)
def cancel_purchase(
    purchase_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cancela una compra y ajusta el stock (solo ADMIN)."""
    purchase_service = PurchaseService(db)
    result = purchase_service.cancel_purchase(purchase_id)
    log_action(db, current_user.id, "CANCEL_PURCHASE", "purchases", purchase_id,
               f"Compra #{purchase_id} cancelada por {current_user.nombre}")
    db.commit()
    return result