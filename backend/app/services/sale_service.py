"""
Servicio de Ventas - Gestión de ventas y facturación.
Compatible con Python 3.13.9
"""
from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.sale import Sale, SaleItem, Invoice
from app.models.book import Book
from app.models.client import Client
from app.models.employee import Employee
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.core.constants import SaleType, SaleStatus


class SaleService:
    """Servicio de gestión de ventas y facturación."""
    
    IVA_RATE = Decimal("0.15")  # 15% IVA
    RTN_EMPRESA = "08011990123456"  # RTN simulado de la librería
    SERIE_FACTURA = "A001"  # Serie de facturación
    
    def __init__(self, db: Session):
        self.db = db
        self._correlativo_actual = self._get_last_correlativo()
    
    def _get_last_correlativo(self) -> int:
        """Obtiene el último número correlativo de factura."""
        last_invoice = self.db.query(Invoice).order_by(Invoice.numero_correlativo.desc()).first()
        return last_invoice.numero_correlativo if last_invoice else 0
    
    def create_sale(
        self,
        sale_data: SaleCreate,
        cliente_id: Optional[int] = None,
        empleado_id: Optional[int] = None
    ) -> Sale:
        """Crea una nueva venta con sus items."""
        
        # Validar stock para cada item
        items_detalle = []
        subtotal = Decimal("0")
        
        for item_data in sale_data.items:
            book = self.db.query(Book).filter(
                Book.id == item_data.libro_id,
                Book.activo == True
            ).first()
            
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Libro con ID {item_data.libro_id} no encontrado"
                )
            
            if book.stock < item_data.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para '{book.nombre}'. Disponible: {book.stock}, Solicitado: {item_data.cantidad}"
                )
            
            item_subtotal = Decimal(str(book.precio)) * item_data.cantidad
            subtotal += item_subtotal
            
            items_detalle.append({
                "book": book,
                "cantidad": item_data.cantidad,
                "precio_unitario": book.precio,
                "subtotal": item_subtotal
            })
        
        # Calcular totales
        impuesto = subtotal * self.IVA_RATE
        descuento = Decimal("0")  # Lógica de descuentos puede agregarse aquí
        total = subtotal + impuesto - descuento
        
        # Crear venta
        new_sale = Sale(
            cliente_id=cliente_id,
            empleado_id=empleado_id,
            tipo=sale_data.tipo,
            status=SaleStatus.COMPLETADA,
            subtotal=subtotal,
            impuesto=impuesto,
            descuento=descuento,
            total=total,
            notas=sale_data.notas
        )
        
        self.db.add(new_sale)
        self.db.flush()  # Para obtener el ID
        
        # Crear items de venta y actualizar stock
        for detalle in items_detalle:
            sale_item = SaleItem(
                venta_id=new_sale.id,
                libro_id=detalle["book"].id,
                cantidad=detalle["cantidad"],
                precio_unitario=detalle["precio_unitario"],
                subtotal=detalle["subtotal"]
            )
            self.db.add(sale_item)
            
            # Actualizar stock del libro
            detalle["book"].registrar_venta(detalle["cantidad"])
        
        self.db.commit()
        
        # Recalcular bestseller: el libro con más ventas totales
        from app.services.book_service import BookService
        BookService(self.db).recalculate_bestseller()
        
        # Generar factura
        self._create_invoice(new_sale, subtotal, impuesto, total, cliente_id)
        
        self.db.commit()
        self.db.refresh(new_sale)
        
        return new_sale
    
    def _create_invoice(
        self,
        sale: Sale,
        subtotal: Decimal,
        impuesto: Decimal,
        total: Decimal,
        cliente_id: Optional[int]
    ) -> Invoice:
        """Genera la factura electrónica para una venta."""
        
        self._correlativo_actual += 1
        numero_factura = f"{self.SERIE_FACTURA}-{self._correlativo_actual:08d}"
        
        # Obtener nombre del cliente si existe
        nombre_cliente = None
        rtn_cliente = None
        if cliente_id:
            client = self.db.query(Client).options(joinedload(Client.user)).filter(
                Client.id == cliente_id
            ).first()
            if client:
                nombre_cliente = client.user.nombre
        
        invoice = Invoice(
            venta_id=sale.id,
            numero_factura=numero_factura,
            serie=self.SERIE_FACTURA,
            numero_correlativo=self._correlativo_actual,
            rtn_emisor=self.RTN_EMPRESA,
            rtn_cliente=rtn_cliente,
            nombre_cliente=nombre_cliente,
            subtotal=subtotal,
            impuesto=impuesto,
            total=total,
            estado="EMITIDA",
            firma_electronica=self._generate_signature(numero_factura, total),
            fecha_certificacion=datetime.now(timezone.utc)
        )
        
        self.db.add(invoice)
        
        return invoice
    
    def _generate_signature(self, numero_factura: str, total: Decimal) -> str:
        """Genera una firma electrónica simulada."""
        import hashlib
        data = f"{numero_factura}:{total}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Obtiene una venta por su ID."""
        return self.db.query(Sale).options(
            joinedload(Sale.items).joinedload(SaleItem.book),
            joinedload(Sale.invoice),
            joinedload(Sale.cliente).joinedload(Client.user),
            joinedload(Sale.empleado).joinedload(Employee.user)
        ).filter(Sale.id == sale_id).first()
    
    def get_sales_by_client(self, cliente_id: int) -> List[Sale]:
        """Obtiene las ventas de un cliente."""
        return self.db.query(Sale).options(
            joinedload(Sale.items).joinedload(SaleItem.book),
            joinedload(Sale.invoice),
            joinedload(Sale.cliente).joinedload(Client.user),
            joinedload(Sale.empleado).joinedload(Employee.user)
        ).filter(
            Sale.cliente_id == cliente_id
        ).order_by(Sale.created_at.desc()).all()
    
    def get_all_sales(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo: Optional[SaleType] = None
    ) -> List[Sale]:
        """Obtiene todas las ventas con filtros opcionales."""
        query = self.db.query(Sale).options(
            joinedload(Sale.items).joinedload(SaleItem.book),
            joinedload(Sale.invoice),
            joinedload(Sale.cliente).joinedload(Client.user),
            joinedload(Sale.empleado).joinedload(Employee.user)
        )
        
        if tipo:
            query = query.filter(Sale.tipo == tipo)
        
        return query.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()
    
    def cancel_sale(self, sale_id: int) -> Sale:
        """Cancela una venta y restaura el stock."""
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada"
            )
        
        if sale.status == SaleStatus.CANCELADA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La venta ya está cancelada"
            )
        
        # Restaurar stock
        for item in sale.items:
            item.book.stock += item.cantidad
            item.book.total_ventas -= item.cantidad
        
        # Actualizar estado
        sale.status = SaleStatus.CANCELADA
        if sale.invoice:
            sale.invoice.estado = "ANULADA"
        
        self.db.commit()
        self.db.refresh(sale)
        
        return sale