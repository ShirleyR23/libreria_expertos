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
from app.utils.dependencies import require_admin

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
    empleado_id = current_user.employee.id if current_user.employee else None
    
    if not empleado_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El administrador debe tener perfil de empleado"
        )
    
    purchase_service = PurchaseService(db)
    return purchase_service.create_purchase(purchase_data, empleado_id)


@router.get("/", response_model=List[PurchaseResponse])
def get_all_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las compras a proveedores (solo ADMIN).
    """
    purchase_service = PurchaseService(db)
    return purchase_service.get_all_purchases(skip=skip, limit=limit)


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene una compra específica por ID (solo ADMIN).
    """
    purchase_service = PurchaseService(db)
    return purchase_service.get_purchase_by_id(purchase_id)


@router.post("/{purchase_id}/cancel", response_model=PurchaseResponse)
def cancel_purchase(
    purchase_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Cancela una compra y ajusta el stock (solo ADMIN).
    """
    purchase_service = PurchaseService(db)
    return purchase_service.cancel_purchase(purchase_id)


from fastapi import HTTPException
