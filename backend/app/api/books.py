"""
Endpoints de Libros (Catálogo Público e Inventario).
IMPORTANTE: Las rutas específicas (/catalog, /categories, etc.)
deben ir ANTES que la ruta dinámica (/{book_id}).
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.book import BookResponse, BookCreate, BookUpdate, BookCategoryResponse
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate
from app.services.book_service import BookService
from app.services.purchase_service import PurchaseService
from app.utils.dependencies import require_empleado, require_admin, require_any_authenticated
from decimal import Decimal

router = APIRouter(prefix="/books", tags=["Libros"])

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "covers")
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "pdfs")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


# ============================================================
# RUTAS ESTÁTICAS PRIMERO (antes de /{book_id})
# ============================================================

@router.post("/upload-image", status_code=200)
async def upload_book_image(
    file: UploadFile = File(...),
    current_user=Depends(require_admin),
):
    """Sube una imagen de portada (solo admin). Máx. 5 MB, JPG/PNG/WebP."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Use JPEG, PNG o WebP.")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB.")
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(UPLOADS_DIR, filename), "wb") as f:
        f.write(content)
    return {"url": f"/uploads/covers/{filename}"}


@router.post("/upload-pdf/{book_id}", status_code=200)
async def upload_book_pdf(
    book_id: int,
    file: UploadFile = File(...),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Sube el PDF de un libro (solo admin). Máx. 50 MB."""
    from app.models.book import Book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="El PDF no puede superar 50 MB.")
    os.makedirs(PDF_DIR, exist_ok=True)
    filename = f"book_{book_id}_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    # Remove old PDF if exists
    if book.pdf_url:
        old_path = os.path.join(os.path.dirname(__file__), "..", "..", book.pdf_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)
    with open(filepath, "wb") as f:
        f.write(content)
    book.pdf_url = f"/uploads/pdfs/{filename}"
    db.commit()
    return {"message": "PDF subido correctamente", "pdf_url": book.pdf_url}


@router.get("/pdf-preview/{book_id}")
def get_pdf_preview(
    book_id: int,
    db: Session = Depends(get_db),
):
    """
    Sirve las primeras N páginas del PDF como preview público.
    Usa pypdf para extraer solo las páginas de preview.
    Devuelve el PDF con headers anti-descarga.
    """
    from app.models.book import Book
    import io
    book = db.query(Book).filter(Book.id == book_id, Book.activo == True).first()
    if not book or not book.pdf_url:
        raise HTTPException(status_code=404, detail="Este libro no tiene PDF disponible")

    pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", book.pdf_url.lstrip("/"))
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")

    preview_pages = int(book.pdf_preview_pages or 3)

    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        total = len(reader.pages)
        for i in range(min(preview_pages, total)):
            writer.add_page(reader.pages[i])
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        data = buf.read()
    except ImportError:
        # If pypdf not installed, serve full file (should not happen in prod)
        with open(pdf_path, "rb") as f:
            data = f.read()

    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache",
            "Content-Security-Policy": "default-src 'self'",
        }
    )


@router.get("/pdf-full/{book_id}")
def get_pdf_full(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(lambda: None),  # override below
):
    """
    Sirve el PDF completo SOLO para clientes que compraron el libro.
    Requiere token JWT válido + verificación de compra.
    """
    raise HTTPException(status_code=401, detail="Use /pdf-full-auth/{book_id}")


@router.get("/pdf-full-auth/{book_id}")
def get_pdf_full_auth(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_authenticated),
):
    """
    PDF completo para clientes autenticados que compraron el libro.
    Headers anti-descarga/anti-print.
    """
    from app.models.book import Book
    from app.models.sale import Sale, SaleItem
    from app.core.constants import SaleStatus

    book = db.query(Book).filter(Book.id == book_id, Book.activo == True).first()
    if not book or not book.pdf_url:
        raise HTTPException(status_code=404, detail="PDF no disponible")

    # Admin/empleado pueden ver cualquier PDF
    if not current_user.is_cliente:
        pass  # allowed
    else:
        # Verificar que el cliente compró este libro
        cliente = getattr(current_user, 'client', None)
        cliente_id = cliente.id if cliente else None
        if not cliente_id:
            raise HTTPException(status_code=403, detail="No tienes acceso a este libro")
        compro = db.query(SaleItem).join(Sale).filter(
            Sale.cliente_id == cliente_id,
            SaleItem.libro_id == book_id,
            Sale.status == SaleStatus.COMPLETADA
        ).first()
        if not compro:
            raise HTTPException(status_code=403, detail="No has comprado este libro")

    pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", book.pdf_url.lstrip("/"))
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado en el servidor")

    def stream_pdf():
        with open(pdf_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        stream_pdf(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",  # inline = no descarga directa
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache, private",
            "Pragma": "no-cache",
            "X-Frame-Options": "SAMEORIGIN",
        }
    )


@router.get("/catalog", response_model=List[BookResponse])
def get_catalog(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    categoria_id: Optional[int] = None,
    search: Optional[str] = None,
    solo_disponibles: bool = True,
    db: Session = Depends(get_db)
):
    """Catálogo público de libros. No requiere autenticación."""
    book_service = BookService(db)
    # Siempre recalcular antes de servir para que es_bestseller sea fiel al movimiento real
    book_service.recalculate_bestseller()
    return book_service.get_all_books(
        skip=skip, limit=limit, categoria_id=categoria_id,
        search=search, solo_disponibles=solo_disponibles
    )



@router.get("/catalog/admin")
def get_admin_catalog(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=500),
    categoria_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Catálogo completo para admin/empleados. Incluye libros sin stock."""
    book_service = BookService(db)
    return book_service.get_all_books(
        skip=skip, limit=limit, categoria_id=categoria_id,
        search=search, solo_disponibles=False
    )


@router.get("/categories", response_model=List[BookCategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Obtiene todas las categorías disponibles."""
    return BookService(db).get_categories()


@router.get("/bestsellers", response_model=List[BookResponse])
def get_bestsellers(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Obtiene los libros más vendidos."""
    return BookService(db).get_bestsellers(limit)


@router.get("/inventory/all", response_model=List[BookResponse])
def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Inventario completo (solo empleados y admin)."""
    return BookService(db).get_all_books(skip=skip, limit=limit, solo_disponibles=False)


@router.get("/inventory/low-stock", response_model=List[BookResponse])
def get_low_stock(current_user=Depends(require_empleado), db: Session = Depends(get_db)):
    """Libros con stock bajo (sistema experto)."""
    return BookService(db).get_low_stock_books()


# ============================================================
# CRUD PRINCIPAL
# ============================================================

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo libro (solo admin).
    Si se incluyen proveedor_nombre + cantidad_compra + costo_compra,
    se genera automáticamente una compra al proveedor y el stock se actualiza.
    """
    book_service = BookService(db)

    tiene_compra = (
        book_data.proveedor_nombre and
        book_data.cantidad_compra and
        book_data.costo_compra
    )

    if tiene_compra:
        book_dict = {
            "nombre": book_data.nombre,
            "isbn": book_data.isbn,
            "autor": book_data.autor,
            "descripcion": book_data.descripcion,
            "categoria_id": book_data.categoria_id,
            "editorial": book_data.editorial,
            "anio_publicacion": book_data.anio_publicacion,
            "precio": book_data.precio,
            "stock": 0,
            "stock_minimo": book_data.stock_minimo,
            "imagen_url": book_data.imagen_url,
            "activo": True,
        }
        new_book = book_service.create_book_from_dict(book_dict, db)

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
            notas=f"Compra automática al ingresar libro: {new_book.nombre} (ISBN: {book_data.isbn})"
        )
        purchase_service.create_purchase(purchase_data, empleado_id)
        db.refresh(new_book)
        return new_book

    return book_service.create_book(book_data)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    current_user=Depends(require_empleado),
    db: Session = Depends(get_db)
):
    """Actualiza un libro existente (empleados y admin)."""
    return BookService(db).update_book(book_id, book_data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Elimina (desactiva) un libro (solo admin)."""
    BookService(db).delete_book(book_id)
    return None


# ============================================================
# RUTA DINÁMICA AL FINAL (después de todas las estáticas)
# ============================================================

@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Obtiene un libro por ID."""
    book = BookService(db).get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book