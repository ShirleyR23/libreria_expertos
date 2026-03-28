"""
Endpoints de Ventas.
Gestiona ventas online y presenciales, facturación.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.sale import SaleCreate, SaleResponse, SaleItemCreate
from app.services.sale_service import SaleService
from app.utils.dependencies import get_current_user, require_empleado, require_cliente, require_any_authenticated
from app.core.constants import SaleType

router = APIRouter(prefix="/sales", tags=["Ventas"])


@router.post("/online", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_online_sale(
    sale_data: SaleCreate,
    current_user=Depends(require_cliente),
    db: Session = Depends(get_db)
):
    """
    Crea una venta online (clientes autenticados).
    
    REGLA: Cliente debe registrarse para comprar.
    REGLA: No vender sin stock.
    """
    # Obtener el cliente_id del usuario actual
    cliente_id = current_user.client.id if current_user.client else None
    
    if not cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de cliente"
        )
    
    sale_service = SaleService(db)
    return sale_service.create_sale(
        sale_data=sale_data,
        cliente_id=cliente_id,
        empleado_id=None
    )


@router.post("/presencial", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_presencial_sale(
    sale_data: SaleCreate,
    cliente_id: Optional[int] = None,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Crea una venta presencial (empleados).
    
    - Ventas en tienda física
    - Puede asociarse a un cliente o ser anónima
    """
    empleado_id = current_user.employee.id if current_user.employee else None
    
    if not empleado_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de empleado"
        )
    
    sale_service = SaleService(db)
    return sale_service.create_sale(
        sale_data=sale_data,
        cliente_id=cliente_id,
        empleado_id=empleado_id
    )


@router.get("/my-purchases", response_model=List[SaleResponse])
def get_my_purchases(
    current_user=Depends(require_cliente),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de compras del cliente autenticado.
    """
    cliente_id = current_user.client.id if current_user.client else None
    
    if not cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de cliente"
        )
    
    sale_service = SaleService(db)
    return sale_service.get_sales_by_client(cliente_id)


@router.get("/all", response_model=List[SaleResponse])
def get_all_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tipo: Optional[SaleType] = None,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las ventas (empleados y admin).
    """
    sale_service = SaleService(db)
    return sale_service.get_all_sales(skip=skip, limit=limit, tipo=tipo)


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    current_user=Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """
    Obtiene una venta específica por ID.
    
    - Clientes solo pueden ver sus propias compras
    - Empleados pueden ver todas
    """
    sale_service = SaleService(db)
    sale = sale_service.get_sale_by_id(sale_id)
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Si es cliente, verificar que sea su compra
    if current_user.is_cliente():
        cliente_id = current_user.client.id if current_user.client else None
        if sale.cliente_id != cliente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta venta"
            )
    
    return sale


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
def cancel_sale(
    sale_id: int,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Cancela una venta y restaura el stock (empleados y admin).
    """
    sale_service = SaleService(db)
    return sale_service.cancel_sale(sale_id)
