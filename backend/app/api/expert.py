"""
Endpoints del Sistema Experto.
Recomendaciones, alertas de inventario y análisis.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.expert_system import ExpertSystemService
from app.utils.dependencies import get_current_user, require_cliente, require_empleado, require_any_authenticated

router = APIRouter(prefix="/expert", tags=["Sistema Experto"])


@router.get("/recommendations")
def get_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user=Depends(require_cliente),
    db: Session = Depends(get_db)
):
    """
    Obtiene recomendaciones personalizadas para el cliente.
    
    REGLAS:
    - SI cliente compra categoría frecuente → recomendar misma.
    - SI cliente nuevo → recomendar más vendidos.
    - SI compra principiante → recomendar introductorios.
    """
    cliente_id = current_user.client.id if current_user.client else None
    
    if not cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de cliente"
        )
    
    expert_service = ExpertSystemService(db)
    return expert_service.get_recommendations_for_client(cliente_id, limit)


@router.get("/inventory-alerts")
def get_inventory_alerts(
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene alertas inteligentes de inventario.
    
    REGLAS:
    - stock < 5 → alerta reposición
    - ventas_30_dias > 20 Y stock < 10 → compra urgente
    - ventas_mes > 50 → marcar bestseller
    """
    expert_service = ExpertSystemService(db)
    return expert_service.get_inventory_alerts()


@router.get("/promotion-suggestions")
def get_promotion_suggestions(
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene sugerencias de libros para promoción.
    
    REGLA:
    - sin ventas en 60 días → sugerir promoción
    """
    expert_service = ExpertSystemService(db)
    return expert_service.get_promotion_suggestions()


@router.get("/sales-analysis")
def get_sales_analysis(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene análisis de ventas del período.
    """
    expert_service = ExpertSystemService(db)
    return expert_service.get_sales_analysis(days)


@router.post("/reset-monthly-counter")
def reset_monthly_counter(
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Reinicia el contador mensual de ventas (para mantenimiento).
    """
    expert_service = ExpertSystemService(db)
    count = expert_service.reset_monthly_sales_counter()
    
    return {
        "message": f"Contador mensual reiniciado para {count} libros",
        "libros_actualizados": count
    }


from fastapi import HTTPException
