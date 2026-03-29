"""
Endpoints de Libros (Catálogo Público e Inventario).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.book import BookResponse, BookCreate, BookUpdate, BookCategoryResponse
from app.services.book_service import BookService
from app.utils.dependencies import get_current_user_optional, require_empleado, require_admin, get_current_user

from app.services.purchase_service import PurchaseService
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate
from decimal import Decimal

router = APIRouter(prefix="/books", tags=["Libros"])


@router.get("/catalog", response_model=List[BookResponse])
def get_catalog(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    categoria_id: Optional[int] = None,
    search: Optional[str] = None,
    solo_disponibles: bool = True,
    db: Session = Depends(get_db)
):
    """
    Catálogo público de libros.
    
    - Buscar libros por categoría
    - Visualizar nombre, autor, descripción, disponibilidad
    - No requiere autenticación
    """
    book_service = BookService(db)
    books = book_service.get_all_books(
        skip=skip,
        limit=limit,
        categoria_id=categoria_id,
        search=search,
        solo_disponibles=solo_disponibles
    )
    return books


@router.get("/categories", response_model=List[BookCategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Obtiene todas las categorías de libros disponibles.
    """
    book_service = BookService(db)
    return book_service.get_categories()


@router.get("/bestsellers", response_model=List[BookResponse])
def get_bestsellers(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Obtiene los libros más vendidos.
    """
    book_service = BookService(db)
    return book_service.get_bestsellers(limit)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un libro específico por ID.
    """
    book_service = BookService(db)
    book = book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book


# ============================================================
# ENDPOINTS PROTEGIDOS (Empleados y Admin)
# ============================================================

@router.get("/inventory/all", response_model=List[BookResponse])
def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene el inventario completo (solo empleados y admin).
    """
    book_service = BookService(db)
    return book_service.get_all_books(skip=skip, limit=limit, solo_disponibles=False)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo libro (solo admin).
    """
    book_service = BookService(db)
    # Verificar si viene con datos de compra
    tiene_compra = (
        book_data.proveedor_nombre and 
        book_data.cantidad_compra and 
        book_data.costo_compra
    )
    
    if tiene_compra:
        # Crear libro con stock=0 (la compra lo incrementará)
        book_dict = {
            "nombre": book_data.nombre,
            "isbn": book_data.isbn,
            "autor": book_data.autor,
            "descripcion": book_data.descripcion,
            "categoria_id": book_data.categoria_id,
            "editorial": book_data.editorial,
            "anio_publicacion": book_data.anio_publicacion,
            "precio": book_data.precio,
            "stock": 0,  # Stock inicial 0
            "stock_minimo": book_data.stock_minimo,
            "activo": True
        }
        
        # Crear libro usando diccionario
        new_book = book_service.create_book_from_dict(book_dict, db)
        
        # Crear la compra automática
        purchase_service = PurchaseService(db)
        empleado_id = current_user.employee.id if current_user.employee else current_user.id
        
        purchase_data = PurchaseCreate(
            proveedor_nombre=book_data.proveedor_nombre,
            proveedor_contacto=book_data.proveedor_contacto,
            proveedor_telefono=book_data.proveedor_telefono,
            items=[
                PurchaseItemCreate(
                    libro_id=new_book.id,
                    cantidad=book_data.cantidad_compra,
                    costo_unitario=book_data.costo_compra
                )
            ],
            notas=f"Compra automática por ingreso de nuevo libro: {new_book.nombre} (ISBN: {book_data.isbn})"
        )
        
        purchase_service.create_purchase(purchase_data, empleado_id)
        
        # Refrescar el libro para obtener el stock actualizado
        db.refresh(new_book)
        return new_book
    
    # Si no hay datos de compra, crear libro normalmente
    return book_service.create_book(book_data)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Actualiza un libro existente (empleados y admin).
    """
    book_service = BookService(db)
    return book_service.update_book(book_id, book_data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Elimina (desactiva) un libro (solo admin).
    """
    book_service = BookService(db)
    book_service.delete_book(book_id)
    return None


@router.get("/inventory/low-stock", response_model=List[BookResponse])
def get_low_stock(
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """
    Obtiene libros con stock bajo (sistema experto).
    """
    book_service = BookService(db)
    return book_service.get_low_stock_books()


from fastapi import HTTPException
