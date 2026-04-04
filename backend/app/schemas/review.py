from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    libro_id:     int
    calificacion: int = Field(..., ge=1, le=5)
    titulo:       Optional[str] = None
    comentario:   Optional[str] = None


class ReviewUpdate(BaseModel):
    calificacion: Optional[int] = Field(None, ge=1, le=5)
    titulo:       Optional[str] = None
    comentario:   Optional[str] = None


class ReviewResponse(BaseModel):
    id:             int
    libro_id:       int
    cliente_id:     int
    calificacion:   int
    titulo:         Optional[str]
    comentario:     Optional[str]
    cliente_nombre: Optional[str] = None
    libro_nombre:   Optional[str] = None
    created_at:     datetime
    model_config = {"from_attributes": True}


class BookRatingSummary(BaseModel):
    libro_id:      int
    total_resenas: int
    promedio:      float
    distribucion:  dict   # {1:n, 2:n, 3:n, 4:n, 5:n}
