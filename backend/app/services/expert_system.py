"""
SISTEMA EXPERTO PARA LIBRERÍA
==============================
Servicio de inteligencia de negocio que proporciona:
- Recomendaciones personalizadas para clientes
- Alertas de inventario inteligentes
- Análisis de ventas y sugerencias de promoción

Compatible con Python 3.13.9
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.book import Book
from app.models.sale import Sale, SaleItem
from app.models.client import Client
from app.core.constants import ExpertSystemThresholds


class ExpertSystemService:
    """
    Sistema Experto para la Librería.
    
    Implementa reglas de negocio inteligentes para:
    1. Recomendaciones de libros
    2. Gestión inteligente de inventario
    3. Análisis de ventas y promociones
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.thresholds = ExpertSystemThresholds()
    
    # ============================================================
    # REGLAS DE RECOMENDACIÓN
    # ============================================================
    
    def get_recommendations_for_client(self, cliente_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones personalizadas para un cliente.
        
        REGLAS:
        1. Obtener TODOS los libros ya comprados por el cliente → excluirlos siempre
        2. Obtener las TOP 3 categorías favoritas del cliente
        3. Para cada categoría: recomendar libros no comprados, ordenados por popularidad
        4. Si cliente nuevo (0 compras) → fallback a más vendidos con razón "Populares entre lectores"
        5. Enriquecer cada recomendación con la razón personalizada
        """
        # Libros ya comprados por el cliente (para excluir)
        libros_ya_comprados = self.db.query(SaleItem.libro_id).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.cliente_id == cliente_id,
            Sale.status == "COMPLETADA"
        ).distinct().subquery()

        # Verificar si es cliente nuevo
        compras_count = self.db.query(func.count(Sale.id)).filter(
            Sale.cliente_id == cliente_id,
            Sale.status == "COMPLETADA"
        ).scalar() or 0

        if compras_count == 0:
            return self._get_bestseller_recommendations(limit, razon="Populares entre nuestros lectores")

        # Top 3 categorías favoritas del cliente
        top_categorias = self.db.query(
            Book.categoria_id,
            func.sum(SaleItem.cantidad).label("total_comprado")
        ).join(
            SaleItem, SaleItem.libro_id == Book.id
        ).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.cliente_id == cliente_id,
            Sale.status == "COMPLETADA"
        ).group_by(
            Book.categoria_id
        ).order_by(
            func.sum(SaleItem.cantidad).desc()
        ).limit(3).all()

        recomendaciones = []
        seen_ids = set()

        for cat_id, _ in top_categorias:
            # Nombre de la categoría para personalizar el mensaje
            from app.models.book import BookCategory
            cat = self.db.query(BookCategory).filter(BookCategory.id == cat_id).first()
            cat_name = cat.name.value if cat and hasattr(cat.name, 'value') else str(cat.name) if cat else "tu categoría favorita"

            libros = self.db.query(Book).filter(
                Book.categoria_id == cat_id,
                Book.stock > 0,
                Book.activo == True,
                ~Book.id.in_(libros_ya_comprados)
            ).order_by(
                Book.total_ventas.desc()
            ).limit(limit).all()

            for book in libros:
                if book.id not in seen_ids and len(recomendaciones) < limit:
                    seen_ids.add(book.id)
                    recomendaciones.append(
                        self._book_to_dict(book, razon=f"Te puede gustar · {cat_name}")
                    )

        # Complementar si hacen falta
        if len(recomendaciones) < limit:
            extra = self.db.query(Book).filter(
                Book.stock > 0,
                Book.activo == True,
                ~Book.id.in_(libros_ya_comprados)
            ).order_by(Book.total_ventas.desc()).limit(limit * 2).all()

            for book in extra:
                if book.id not in seen_ids and len(recomendaciones) < limit:
                    seen_ids.add(book.id)
                    recomendaciones.append(
                        self._book_to_dict(book, razon="También te podría interesar")
                    )

        return recomendaciones[:limit]
    
    def _get_client_favorite_category(self, cliente_id: int) -> Optional[int]:
        """Obtiene la categoría más comprada por un cliente."""
        result = self.db.query(
            Book.categoria_id,
            func.count(SaleItem.id).label("total")
        ).join(
            SaleItem, SaleItem.libro_id == Book.id
        ).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.cliente_id == cliente_id,
            Sale.status == "COMPLETADA"
        ).group_by(
            Book.categoria_id
        ).order_by(
            func.count(SaleItem.id).desc()
        ).first()
        
        return result[0] if result else None
    
    def _get_recommendations_by_category(
        self, 
        categoria_id: int, 
        exclude_client_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones de una categoría específica."""
        # Libros de la categoría que el cliente no ha comprado
        libros_comprados = self.db.query(SaleItem.libro_id).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.cliente_id == exclude_client_id
        ).subquery()
        
        books = self.db.query(Book).filter(
            Book.categoria_id == categoria_id,
            Book.stock > 0,
            Book.activo == True,
            ~Book.id.in_(libros_comprados)
        ).order_by(
            Book.total_ventas.desc()
        ).limit(limit).all()
        
        return [self._book_to_dict(b, razon="Basado en tus preferencias") for b in books]
    
    def _get_bestseller_recommendations(self, limit: int, razon: str = "Los más vendidos") -> List[Dict[str, Any]]:
        """Obtiene recomendaciones de libros más vendidos."""
        books = self.db.query(Book).filter(
            Book.stock > 0,
            Book.activo == True
        ).order_by(
            Book.total_ventas.desc()
        ).limit(limit).all()
        
        return [self._book_to_dict(b, razon=razon) for b in books]
    
    # ============================================================
    # REGLAS DE INVENTARIO INTELIGENTE
    # ============================================================
    
    def get_inventory_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Genera alertas inteligentes de inventario.
        
        REGLAS:
        - stock < 5 → alerta reposición
        - ventas_30_dias > 20 Y stock < 10 → compra urgente
        - ventas_mes > 50 → marcar bestseller
        """
        alerts = {
            "reposicion": [],
            "compra_urgente": [],
            "nuevos_bestsellers": [],
            "resumen": {}
        }
        
        # Alerta de reposición: stock < 5
        reposicion = self.db.query(Book).filter(
            Book.stock < self.thresholds.STOCK_MINIMO_ALERTA,
            Book.activo == True
        ).all()
        
        for book in reposicion:
            alerts["reposicion"].append({
                "id": book.id,
                "nombre": book.nombre,
                "stock_actual": book.stock,
                "stock_minimo": book.stock_minimo,
                "mensaje": f"Stock crítico: {book.stock} unidades"
            })
        
        # Compra urgente: ventas_30_dias > 20 Y stock < 10
        compra_urgente = self.db.query(Book).filter(
            Book.ventas_ultimos_30_dias > self.thresholds.VENTAS_30_DIAS_URGENTE,
            Book.stock < self.thresholds.STOCK_URGENTE,
            Book.activo == True
        ).all()
        
        for book in compra_urgente:
            alerts["compra_urgente"].append({
                "id": book.id,
                "nombre": book.nombre,
                "stock_actual": book.stock,
                "ventas_30_dias": book.ventas_ultimos_30_dias,
                "mensaje": f"Compra urgente: {book.ventas_ultimos_30_dias} ventas en 30 días, solo {book.stock} en stock"
            })
        
        # Bestseller: el libro con MÁS copias vendidas (total_ventas) es el único bestseller
        # Primero, desmarcar todos los bestsellers actuales
        all_books_bs = self.db.query(Book).filter(Book.activo == True).all()
        
        # Encontrar el libro con más ventas totales (mínimo 1 venta)
        top_book = self.db.query(Book).filter(
            Book.activo == True,
            Book.total_ventas > 0
        ).order_by(Book.total_ventas.desc()).first()
        
        for book in all_books_bs:
            was_bestseller = book.es_bestseller
            book.es_bestseller = (top_book is not None and book.id == top_book.id)
            if book.es_bestseller and not was_bestseller:
                alerts["nuevos_bestsellers"].append({
                    "id": book.id,
                    "nombre": book.nombre,
                    "total_ventas": book.total_ventas,
                    "mensaje": f"¡Bestseller! {book.total_ventas} copias vendidas (el más vendido)"
                })
        
        self.db.commit()
        
        # Resumen
        alerts["resumen"] = {
            "total_alertas_reposicion": len(alerts["reposicion"]),
            "total_compras_urgentes": len(alerts["compra_urgente"]),
            "nuevos_bestsellers": len(alerts["nuevos_bestsellers"])
        }
        
        return alerts
    
    # ============================================================
    # REGLAS DE ANÁLISIS Y PROMOCIONES
    # ============================================================
    
    def get_promotion_suggestions(self) -> List[Dict[str, Any]]:
        """
        Sugiere libros para promoción.
        
        REGLA:
        - sin ventas en 60 días → sugerir promoción
        """
        fecha_limite = datetime.now(timezone.utc) - timedelta(days=self.thresholds.DIAS_SIN_VENTAS_PROMOCION)
        
        # Libros sin ventas en 60 días
        libros_sin_ventas = self.db.query(Book).filter(
            (Book.ultima_venta < fecha_limite) | (Book.ultima_venta.is_(None)),
            Book.activo == True,
            Book.stock > 0
        ).all()
        
        sugerencias = []
        for book in libros_sin_ventas:
            dias_sin_venta = (
                (datetime.now(timezone.utc) - book.ultima_venta).days 
                if book.ultima_venta 
                else "Nunca"
            )
            
            sugerencias.append({
                "id": book.id,
                "nombre": book.nombre,
                "autor": book.autor,
                "stock": book.stock,
                "precio": float(book.precio),
                "precio_original": float(getattr(book, 'precio_original', None) or 0) or None,
                "tiene_descuento": bool(getattr(book, 'precio_original', None)),
                "dias_sin_venta": dias_sin_venta,
                "ultima_venta": book.ultima_venta.isoformat() if book.ultima_venta else None,
                "sugerencia": "Aplicar descuento o promoción",
                "descuento_recomendado": "15-20%"
            })
        
        return sugerencias
    
    def get_sales_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Análisis de ventas del período.
        """
        fecha_desde = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Ventas totales del período
        ventas_totales = self.db.query(func.count(Sale.id)).filter(
            Sale.created_at >= fecha_desde,
            Sale.status == "COMPLETADA"
        ).scalar() or 0
        
        # Ingresos totales
        ingresos = self.db.query(func.sum(Sale.total)).filter(
            Sale.created_at >= fecha_desde,
            Sale.status == "COMPLETADA"
        ).scalar() or 0
        
        # Top 5 libros vendidos
        top_libros = self.db.query(
            Book.nombre,
            func.sum(SaleItem.cantidad).label("total_vendido")
        ).join(
            SaleItem, SaleItem.libro_id == Book.id
        ).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.created_at >= fecha_desde,
            Sale.status == "COMPLETADA"
        ).group_by(
            Book.id, Book.nombre
        ).order_by(
            func.sum(SaleItem.cantidad).desc()
        ).limit(5).all()
        
        # Categorías más vendidas
        top_categorias = self.db.query(
            Book.categoria_id,
            func.sum(SaleItem.cantidad).label("total_vendido")
        ).join(
            SaleItem, SaleItem.libro_id == Book.id
        ).join(
            Sale, Sale.id == SaleItem.venta_id
        ).filter(
            Sale.created_at >= fecha_desde,
            Sale.status == "COMPLETADA"
        ).group_by(
            Book.categoria_id
        ).order_by(
            func.sum(SaleItem.cantidad).desc()
        ).limit(5).all()
        
        return {
            "periodo_dias": days,
            "ventas_totales": ventas_totales,
            "ingresos_totales": float(ingresos),
            "promedio_venta": float(ingresos / ventas_totales) if ventas_totales > 0 else 0,
            "top_libros": [{"nombre": nombre, "vendidos": int(cantidad)} for nombre, cantidad in top_libros],
            "top_categorias": [{"categoria_id": cat_id, "vendidos": int(cantidad)} for cat_id, cantidad in top_categorias]
        }
    
    def _book_to_dict(self, book: Book, razon: str = "") -> Dict[str, Any]:
        """Convierte un libro a diccionario con información de recomendación."""
        return {
            "id": book.id,
            "nombre": book.nombre,
            "autor": book.autor,
            "precio": float(book.precio),
            "stock": book.stock,
            "categoria_id": book.categoria_id,
            "total_ventas": book.total_ventas,
            "es_bestseller": book.es_bestseller,
            "razon_recomendacion": razon
        }
    
    def reset_monthly_sales_counter(self) -> int:
        """
        Reinicia el contador de ventas de 30 días.
        Debe ejecutarse periódicamente (ej: cada mes).
        """
        books = self.db.query(Book).all()
        count = 0
        for book in books:
            book.ventas_ultimos_30_dias = 0
            count += 1
        
        self.db.commit()
        return count