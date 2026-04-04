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
from app.models.audit_log import log_action

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
    result = sale_service.create_sale(
        sale_data=sale_data,
        cliente_id=cliente_id,
        empleado_id=None
    )
    log_action(db, current_user.id, "CREATE_SALE_ONLINE", "sales", result.id,
               f"Venta online #{result.id} por cliente ID:{cliente_id} total:L.{result.total}")
    db.commit()
    return result


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
    empleado_id = current_user.employee.id if current_user.employee else current_user.id
    
    if not empleado_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de empleado"
        )
    
    sale_service = SaleService(db)
    result = sale_service.create_sale(
        sale_data=sale_data,
        cliente_id=cliente_id,
        empleado_id=empleado_id
    )
    log_action(db, current_user.id, "CREATE_SALE_PRESENCIAL", "sales", result.id,
               f"Venta presencial #{result.id} por empleado ID:{empleado_id} total:L.{result.total}")
    db.commit()
    return result


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


@router.get("/my-books")
def get_my_books(
    current_user=Depends(require_cliente),
    db: Session = Depends(get_db),
):
    """
    Devuelve la lista de libros ÚNICOS que el cliente ha comprado.
    Muestra todos los libros comprados; has_pdf indica si tiene PDF para leer.
    """
    from app.models.sale import Sale, SaleItem
    from app.models.book import Book
    from app.core.constants import SaleStatus

    cliente_id = current_user.client.id if current_user.client else None
    if not cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene perfil de cliente"
        )

    # Todos los libros únicos comprados por el cliente (con o sin PDF)
    libros = db.query(Book).join(
        SaleItem, SaleItem.libro_id == Book.id
    ).join(
        Sale, Sale.id == SaleItem.venta_id
    ).filter(
        Sale.cliente_id == cliente_id,
        Sale.status == SaleStatus.COMPLETADA,
        Book.activo == True
    ).distinct().all()

    return [
        {
            "id": b.id,
            "nombre": b.nombre,
            "autor": b.autor,
            "descripcion": b.descripcion,
            "categoria": b.categoria.name.value if b.categoria else None,
            "editorial": b.editorial,
            "anio_publicacion": b.anio_publicacion,
            "imagen_url": b.imagen_url,
            "has_pdf": bool(b.pdf_url),
        }
        for b in libros
    ]


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


@router.get("/{sale_id}/invoice")
def get_invoice(
    sale_id: int,
    current_user=Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """Obtiene la factura de una venta específica."""
    from app.models.sale import Invoice
    from app.schemas.sale import InvoiceResponse
    
    sale_service = SaleService(db)
    sale = sale_service.get_sale_by_id(sale_id)
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Cliente solo puede ver sus propias facturas
    if current_user.is_cliente():
        cliente_id = current_user.client.id if current_user.client else None
        if sale.cliente_id != cliente_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver esta factura")
    
    if not sale.invoice:
        raise HTTPException(status_code=404, detail="Esta venta no tiene factura generada")
    
    # Devolver datos enriquecidos para la factura
    inv = sale.invoice
    return {
        "id": inv.id,
        "venta_id": inv.venta_id,
        "numero_factura": inv.numero_factura,
        "serie": inv.serie,
        "numero_correlativo": inv.numero_correlativo,
        "rtn_emisor": inv.rtn_emisor,
        "rtn_cliente": inv.rtn_cliente,
        "nombre_cliente": inv.nombre_cliente or sale.cliente_nombre or "Consumidor Final",
        "subtotal": float(inv.subtotal),
        "impuesto": float(inv.impuesto),
        "total": float(inv.total),
        "estado": inv.estado,
        "fecha_emision": inv.fecha_emision.isoformat(),
        "items": [
            {
                "libro_nombre": item.libro_nombre or f"Libro #{item.libro_id}",
                "cantidad": item.cantidad,
                "precio_unitario": float(item.precio_unitario),
                "subtotal": float(item.subtotal),
            }
            for item in sale.items
        ],
        "empleado_nombre": sale.empleado_nombre,
        "tipo": sale.tipo.value if sale.tipo else "PRESENCIAL",
        "notas": sale.notas,
    }


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
    result = sale_service.cancel_sale(sale_id)
    log_action(db, current_user.id, "CANCEL_SALE", "sales", sale_id,
               f"Venta #{sale_id} cancelada por {current_user.nombre}")
    db.commit()
    return result