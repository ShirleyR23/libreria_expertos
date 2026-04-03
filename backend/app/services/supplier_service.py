"""
Servicio de Proveedores.
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.supplier import Supplier, SupplierBook
from app.models.purchase import Purchase, PurchaseItem
from app.models.book import Book
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierBookItem, OrderFromSupplier


class SupplierService:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[SupplierResponse]:
        suppliers = (
            self.db.query(Supplier)
            .options(joinedload(Supplier.catalogo).joinedload(SupplierBook.book))
            .filter(Supplier.activo == True)
            .offset(skip).limit(limit).all()
        )
        return [self._to_response(s) for s in suppliers]

    def get_by_id(self, supplier_id: int) -> SupplierResponse:
        supplier = (
            self.db.query(Supplier)
            .options(joinedload(Supplier.catalogo).joinedload(SupplierBook.book))
            .filter(Supplier.id == supplier_id)
            .first()
        )
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        return self._to_response(supplier)

    def create(self, data: SupplierCreate) -> SupplierResponse:
        supplier = Supplier(
            nombre=data.nombre,
            contacto=data.contacto,
            telefono=data.telefono,
            email=data.email,
            direccion=data.direccion,
            notas=data.notas,
        )
        self.db.add(supplier)
        self.db.flush()

        for item in (data.catalogo or []):
            book = self.db.query(Book).filter(Book.id == item.libro_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Libro {item.libro_id} no encontrado")
            sb = SupplierBook(
                supplier_id=supplier.id,
                libro_id=item.libro_id,
                costo_unitario=item.costo_unitario,
            )
            self.db.add(sb)

        self.db.commit()
        self.db.refresh(supplier)
        return self.get_by_id(supplier.id)

    def update(self, supplier_id: int, data: SupplierUpdate) -> SupplierResponse:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(supplier, field, value)

        self.db.commit()
        return self.get_by_id(supplier_id)

    def delete(self, supplier_id: int):
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        supplier.activo = False
        self.db.commit()

    def add_book_to_catalog(self, supplier_id: int, libro_id: int, costo: float) -> SupplierResponse:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        book = self.db.query(Book).filter(Book.id == libro_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        existing = self.db.query(SupplierBook).filter(
            SupplierBook.supplier_id == supplier_id,
            SupplierBook.libro_id == libro_id
        ).first()
        if existing:
            existing.costo_unitario = costo
        else:
            self.db.add(SupplierBook(supplier_id=supplier_id, libro_id=libro_id, costo_unitario=costo))

        self.db.commit()
        return self.get_by_id(supplier_id)

    def remove_book_from_catalog(self, supplier_id: int, libro_id: int) -> SupplierResponse:
        sb = self.db.query(SupplierBook).filter(
            SupplierBook.supplier_id == supplier_id,
            SupplierBook.libro_id == libro_id
        ).first()
        if sb:
            self.db.delete(sb)
            self.db.commit()
        return self.get_by_id(supplier_id)

    def create_order(self, supplier_id: int, order: OrderFromSupplier, empleado_id: int) -> dict:
        """Crea una compra (pedido) a un proveedor."""
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")

        subtotal = sum(item.cantidad * float(item.costo_unitario) for item in order.items)
        total = subtotal

        purchase = Purchase(
            proveedor_nombre=supplier.nombre,
            proveedor_contacto=supplier.contacto,
            proveedor_telefono=supplier.telefono,
            supplier_id=supplier_id,  # guardamos el ID directamente
            empleado_id=empleado_id,
            subtotal=subtotal,
            impuesto=0,
            total=total,
            estado="RECIBIDA",
            notas=order.notas or f"Pedido a {supplier.nombre}",
        )
        self.db.add(purchase)
        self.db.flush()

        for item in order.items:
            book = self.db.query(Book).filter(Book.id == item.libro_id).first()
            if not book:
                raise HTTPException(status_code=404, detail=f"Libro {item.libro_id} no encontrado")

            pi = PurchaseItem(
                compra_id=purchase.id,
                libro_id=item.libro_id,
                cantidad=item.cantidad,
                costo_unitario=item.costo_unitario,
                subtotal=float(item.costo_unitario) * item.cantidad,
            )
            self.db.add(pi)
            book.stock += item.cantidad

        self.db.commit()
        return {"message": "Pedido creado correctamente", "compra_id": purchase.id, "total": total}

    def _to_response(self, supplier: Supplier) -> SupplierResponse:
        total_pedidos = self.db.query(func.count(Purchase.id)).filter(
            Purchase.supplier_id == supplier.id
        ).scalar() or 0

        catalogo = []
        for sb in (supplier.catalogo or []):
            book = sb.book
            catalogo.append(SupplierBookItem(
                id=sb.id,
                libro_id=sb.libro_id,
                costo_unitario=sb.costo_unitario,
                libro_nombre=book.nombre if book else None,
                libro_autor=book.autor if book else None,
                libro_isbn=book.isbn if book else None,
                libro_stock=book.stock if book else None,
                libro_precio=book.precio if book else None,
                libro_imagen_url=book.imagen_url if book else None,
            ))

        return SupplierResponse(
            id=supplier.id,
            nombre=supplier.nombre,
            contacto=supplier.contacto,
            telefono=supplier.telefono,
            email=supplier.email,
            direccion=supplier.direccion,
            notas=supplier.notas,
            activo=supplier.activo,
            total_pedidos=total_pedidos,
            created_at=supplier.created_at,
            catalogo=catalogo,
        )
