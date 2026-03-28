"""
Servicio de Libros - Gestión de inventario.
Compatible con Python 3.13.9
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.book import Book, BookCategory
from app.schemas.book import BookCreate, BookUpdate, BookResponse


class BookService:
    """Servicio de gestión de libros e inventario."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_books(
        self,
        skip: int = 0,
        limit: int = 100,
        categoria_id: Optional[int] = None,
        search: Optional[str] = None,
        solo_disponibles: bool = False
    ) -> List[Book]:
        """Obtiene lista de libros con filtros opcionales."""
        query = self.db.query(Book).options(joinedload(Book.categoria))
        
        if categoria_id:
            query = query.filter(Book.categoria_id == categoria_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Book.nombre.ilike(search_filter)) |
                (Book.autor.ilike(search_filter)) |
                (Book.isbn.ilike(search_filter))
            )
        
        if solo_disponibles:
            query = query.filter(Book.stock > 0)
        
        query = query.filter(Book.activo == True)
        
        return query.offset(skip).limit(limit).all()
    
    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Obtiene un libro por su ID."""
        return self.db.query(Book).options(joinedload(Book.categoria)).filter(
            Book.id == book_id,
            Book.activo == True
        ).first()
    
    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """Obtiene un libro por su ISBN."""
        return self.db.query(Book).filter(Book.isbn == isbn).first()
    
    def create_book(self, book_data: BookCreate) -> Book:
        """Crea un nuevo libro."""
        # Verificar ISBN único
        existing = self.get_book_by_isbn(book_data.isbn)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un libro con el ISBN: {book_data.isbn}"
            )
        
        new_book = Book(
            nombre=book_data.nombre,
            isbn=book_data.isbn,
            autor=book_data.autor,
            descripcion=book_data.descripcion,
            categoria_id=book_data.categoria_id,
            editorial=book_data.editorial,
            anio_publicacion=book_data.anio_publicacion,
            precio=book_data.precio,
            stock=book_data.stock,
            stock_minimo=book_data.stock_minimo,
            activo=True
        )
        
        self.db.add(new_book)
        self.db.commit()
        self.db.refresh(new_book)
        
        return new_book
    
    def update_book(self, book_id: int, book_data: BookUpdate) -> Book:
        """Actualiza un libro existente."""
        book = self.get_book_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Libro no encontrado"
            )
        
        # Verificar ISBN único si se está actualizando
        if book_data.isbn and book_data.isbn != book.isbn:
            existing = self.get_book_by_isbn(book_data.isbn)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un libro con el ISBN: {book_data.isbn}"
                )
        
        # Actualizar campos
        update_data = book_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
        
        self.db.commit()
        self.db.refresh(book)
        
        return book
    
    def delete_book(self, book_id: int) -> bool:
        """Elimina lógicamente un libro (desactiva)."""
        book = self.get_book_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Libro no encontrado"
            )
        
        book.activo = False
        self.db.commit()
        
        return True
    
    def update_stock(self, book_id: int, cantidad: int) -> Book:
        """Actualiza el stock de un libro."""
        book = self.get_book_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Libro no encontrado"
            )
        
        book.actualizar_stock(cantidad)
        self.db.commit()
        self.db.refresh(book)
        
        return book
    
    def get_low_stock_books(self) -> List[Book]:
        """Obtiene libros con stock bajo (para sistema experto)."""
        return self.db.query(Book).filter(
            Book.stock <= Book.stock_minimo,
            Book.activo == True
        ).all()
    
    def get_categories(self) -> List[BookCategory]:
        """Obtiene todas las categorías de libros."""
        return self.db.query(BookCategory).all()
    
    def get_bestsellers(self, limit: int = 10) -> List[Book]:
        """Obtiene los libros más vendidos."""
        return self.db.query(Book).filter(
            Book.activo == True
        ).order_by(Book.total_ventas.desc()).limit(limit).all()
