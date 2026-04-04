"""
Endpoints de Reseñas.
  GET    /reviews/book/{libro_id}          — reseñas públicas
  GET    /reviews/book/{libro_id}/summary  — resumen estadístico
  GET    /reviews/can-review/{libro_id}    — ¿puedo reseñar?
  GET    /reviews/my                       — mis reseñas
  POST   /reviews/                         — crear reseña
  PUT    /reviews/{id}                     — editar mi reseña
  DELETE /reviews/{id}                     — borrar mi reseña
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse, BookRatingSummary
from app.models.review import Review
from app.models.client import Client
from app.models.sale import Sale, SaleItem
from app.core.constants import SaleStatus
from app.utils.dependencies import require_cliente

router = APIRouter(prefix="/reviews", tags=["Reseñas"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _client(db, user_id):
    c = db.query(Client).filter(Client.user_id == user_id).first()
    if not c:
        raise HTTPException(403, "Solo clientes pueden gestionar reseñas")
    return c

def _purchased(db, cliente_id, libro_id):
    return db.query(Sale).join(SaleItem, Sale.id == SaleItem.venta_id).filter(
        Sale.cliente_id == cliente_id,
        SaleItem.libro_id == libro_id,
        Sale.status == SaleStatus.COMPLETADA,
    ).first() is not None

def _resp(r: Review) -> ReviewResponse:
    nombre = r.cliente.user.nombre if (r.cliente and r.cliente.user) else "Anónimo"
    libro  = r.book.nombre if r.book else None
    return ReviewResponse(
        id=r.id, libro_id=r.libro_id, cliente_id=r.cliente_id,
        calificacion=r.calificacion, titulo=r.titulo, comentario=r.comentario,
        cliente_nombre=nombre, libro_nombre=libro, created_at=r.created_at,
    )


# ── públicos ──────────────────────────────────────────────────────────────────

@router.get("/book/{libro_id}", response_model=List[ReviewResponse])
def get_book_reviews(libro_id: int, db: Session = Depends(get_db)):
    rows = db.query(Review).filter(Review.libro_id == libro_id)\
             .order_by(Review.created_at.desc()).all()
    return [_resp(r) for r in rows]


@router.get("/book/{libro_id}/summary", response_model=BookRatingSummary)
def get_summary(libro_id: int, db: Session = Depends(get_db)):
    rows = db.query(Review).filter(Review.libro_id == libro_id).all()
    total = len(rows)
    if not total:
        return BookRatingSummary(libro_id=libro_id, total_resenas=0,
                                  promedio=0.0, distribucion={i:0 for i in range(1,6)})
    dist = {i: 0 for i in range(1, 6)}
    for r in rows:
        dist[r.calificacion] += 1
    return BookRatingSummary(libro_id=libro_id, total_resenas=total,
                              promedio=round(sum(r.calificacion for r in rows)/total, 1),
                              distribucion=dist)


# ── autenticados ──────────────────────────────────────────────────────────────

@router.get("/can-review/{libro_id}")
def can_review(libro_id: int, current_user=Depends(require_cliente),
               db: Session = Depends(get_db)):
    try:
        c = _client(db, current_user.id)
    except HTTPException:
        return {"can_review": False, "reason": "not_client"}

    if not _purchased(db, c.id, libro_id):
        return {"can_review": False, "reason": "no_purchase"}

    existing = db.query(Review).filter(Review.cliente_id == c.id,
                                        Review.libro_id == libro_id).first()
    if existing:
        return {"can_review": False, "reason": "already_reviewed",
                "review": _resp(existing).model_dump()}
    return {"can_review": True}


@router.get("/my", response_model=List[ReviewResponse])
def my_reviews(current_user=Depends(require_cliente), db: Session = Depends(get_db)):
    c = _client(db, current_user.id)
    rows = db.query(Review).filter(Review.cliente_id == c.id)\
             .order_by(Review.created_at.desc()).all()
    return [_resp(r) for r in rows]


@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(data: ReviewCreate, current_user=Depends(require_cliente),
                  db: Session = Depends(get_db)):
    c = _client(db, current_user.id)
    if not _purchased(db, c.id, data.libro_id):
        raise HTTPException(403, "Solo puedes reseñar libros que hayas comprado (venta completada).")
    if db.query(Review).filter(Review.cliente_id==c.id, Review.libro_id==data.libro_id).first():
        raise HTTPException(409, "Ya tienes una reseña para este libro.")
    rev = Review(libro_id=data.libro_id, cliente_id=c.id, calificacion=data.calificacion,
                 titulo=data.titulo, comentario=data.comentario)
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return _resp(rev)


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, data: ReviewUpdate,
                  current_user=Depends(require_cliente), db: Session = Depends(get_db)):
    c = _client(db, current_user.id)
    rev = db.query(Review).filter(Review.id==review_id, Review.cliente_id==c.id).first()
    if not rev:
        raise HTTPException(404, "Reseña no encontrada")
    if data.calificacion is not None: rev.calificacion = data.calificacion
    if data.titulo       is not None: rev.titulo       = data.titulo
    if data.comentario   is not None: rev.comentario   = data.comentario
    db.commit(); db.refresh(rev)
    return _resp(rev)


@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: int, current_user=Depends(require_cliente),
                  db: Session = Depends(get_db)):
    c = _client(db, current_user.id)
    rev = db.query(Review).filter(Review.id==review_id, Review.cliente_id==c.id).first()
    if not rev:
        raise HTTPException(404, "Reseña no encontrada")
    db.delete(rev); db.commit()