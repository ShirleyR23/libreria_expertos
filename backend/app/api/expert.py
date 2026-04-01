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


from fastapi import HTTPException, Body


@router.post("/restock/{book_id}")
def restock_book(
    book_id: int,
    cantidad: int = Body(..., embed=True),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Repone stock de un libro desde el sistema experto."""
    from app.models.book import Book
    book = db.query(Book).filter(Book.id == book_id, Book.activo == True).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")
    book.stock += cantidad
    db.commit()
    return {"message": f"Stock actualizado: {book.nombre} ahora tiene {book.stock} unidades", "nuevo_stock": book.stock}


@router.post("/apply-discount/{book_id}")
def apply_discount(
    book_id: int,
    porcentaje: float = Body(..., embed=True),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Aplica un descuento al precio de un libro. Guarda el precio original para poder restaurarlo."""
    from app.models.book import Book
    from decimal import Decimal
    book = db.query(Book).filter(Book.id == book_id, Book.activo == True).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    if not (1 <= porcentaje <= 90):
        raise HTTPException(status_code=400, detail="El porcentaje debe estar entre 1 y 90")
    # Guardar precio original solo si no tiene ya un descuento activo
    precio_orig_actual = getattr(book, 'precio_original', None)
    if precio_orig_actual is None:
        book.precio_original = book.precio
    precio_base = float(getattr(book, 'precio_original', book.precio))
    descuento = precio_base * (porcentaje / 100)
    book.precio = Decimal(str(round(precio_base - descuento, 2)))
    db.commit()
    return {
        "message": f"Descuento aplicado a '{book.nombre}'",
        "precio_original": precio_base,
        "precio_nuevo": float(book.precio),
        "descuento_aplicado": f"{porcentaje}%"
    }


@router.post("/remove-discount/{book_id}")
def remove_discount(
    book_id: int,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Restaura el precio original de un libro (quita el descuento)."""
    from app.models.book import Book
    book = db.query(Book).filter(Book.id == book_id, Book.activo == True).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    precio_orig = getattr(book, 'precio_original', None)
    if precio_orig is None:
        raise HTTPException(status_code=400, detail="Este libro no tiene descuento activo")
    precio_restaurado = float(precio_orig)
    book.precio = precio_orig
    book.precio_original = None
    db.commit()
    return {
        "message": f"Precio restaurado para '{book.nombre}'",
        "precio_restaurado": precio_restaurado
    }