"""
Servicio de Compras - Gestión de compras a proveedores.
Solo ADMIN puede gestionar compras.
Compatible con Python 3.13.9
"""
from datetime import datetime, timezone
from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.purchase import Purchase, PurchaseItem
from app.models.book import Book
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate


class PurchaseService:
    """Servicio de gestión de compras a proveedores."""
    
    IVA_RATE = Decimal("0.15")  # 15% IVA
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_purchase(
        self,
        purchase_data: PurchaseCreate,
        empleado_id: int
    ) -> Purchase:
        """Crea una nueva compra a proveedor."""
        
        # Calcular totales
        items_detalle = []
        subtotal = Decimal("0")
        
        for item_data in purchase_data.items:
            book = self.db.query(Book).filter(
                Book.id == item_data.libro_id,
                Book.activo == True
            ).first()
            
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Libro con ID {item_data.libro_id} no encontrado"
                )
            
            item_subtotal = item_data.costo_unitario * item_data.cantidad
            subtotal += item_subtotal
            
            items_detalle.append({
                "book": book,
                "cantidad": item_data.cantidad,
                "costo_unitario": item_data.costo_unitario,
                "subtotal": item_subtotal
            })
        
        # Calcular totales
        impuesto = subtotal * self.IVA_RATE
        total = subtotal + impuesto
        
        # Crear compra
        new_purchase = Purchase(
            proveedor_nombre=purchase_data.proveedor_nombre,
            proveedor_contacto=purchase_data.proveedor_contacto,
            proveedor_telefono=purchase_data.proveedor_telefono,
            empleado_id=empleado_id,
            subtotal=subtotal,
            impuesto=impuesto,
            total=total,
            estado="RECIBIDA",
            notas=purchase_data.notas,
            fecha_recepcion=datetime.now(timezone.utc)
        )
        
        self.db.add(new_purchase)
        self.db.flush()
        
        # Crear items de compra y actualizar stock
        for detalle in items_detalle:
            purchase_item = PurchaseItem(
                compra_id=new_purchase.id,
                libro_id=detalle["book"].id,
                cantidad=detalle["cantidad"],
                costo_unitario=detalle["costo_unitario"],
                subtotal=detalle["subtotal"]
            )
            self.db.add(purchase_item)
            
            # Actualizar stock del libro
            detalle["book"].actualizar_stock(detalle["cantidad"])
        
        self.db.commit()
        self.db.refresh(new_purchase)
        
        return new_purchase
    
    def get_purchase_by_id(self, purchase_id: int) -> Purchase:
        """Obtiene una compra por su ID."""
        purchase = self.db.query(Purchase).options(
            joinedload(Purchase.items).joinedload(PurchaseItem.book),
            joinedload(Purchase.empleado)
        ).filter(Purchase.id == purchase_id).first()
        
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compra no encontrada"
            )
        
        return purchase
    
    def get_by_supplier(self, supplier_id: int, limit: int = 5) -> List[Purchase]:
        """Obtiene las compras más recientes de un proveedor."""
        return self.db.query(Purchase).options(
            joinedload(Purchase.items).joinedload(PurchaseItem.book)
        ).filter(
            Purchase.supplier_id == supplier_id
        ).order_by(Purchase.fecha_compra.desc()).limit(limit).all()

    def get_all_purchases(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Purchase]:
        """Obtiene todas las compras."""
        return self.db.query(Purchase).options(
            joinedload(Purchase.items).joinedload(PurchaseItem.book)
        ).order_by(Purchase.fecha_compra.desc()).offset(skip).limit(limit).all()
    
    def cancel_purchase(self, purchase_id: int) -> Purchase:
        """Cancela una compra y ajusta el stock."""
        purchase = self.get_purchase_by_id(purchase_id)
        
        if purchase.estado == "CANCELADA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La compra ya está cancelada"
            )
        
        # Verificar que hay suficiente stock para descontar
        for item in purchase.items:
            if item.book.stock < item.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede cancelar: stock insuficiente para '{item.book.nombre}'"
                )
        
        # Descontar stock
        for item in purchase.items:
            item.book.stock -= item.cantidad
        
        purchase.estado = "CANCELADA"
        
        self.db.commit()
        self.db.refresh(purchase)
        
        return purchase