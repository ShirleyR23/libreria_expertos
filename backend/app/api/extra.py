"""
Endpoints extra:
  GET  /reports/sales/export       — CSV ventas
  GET  /reports/inventory/export   — CSV inventario
  GET  /reports/purchases/export   — CSV compras
  GET  /audit/logs                 — logs de auditoría (admin)
  GET  /isbn/{isbn}                — lookup Open Library
  GET  /admin/sales-by-month       — datos para gráfica de ventas por mes
"""
import csv, io, json, urllib.request
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.book import Book
from app.models.sale import Sale, SaleItem
from app.models.purchase import Purchase
from app.models.audit_log import AuditLog
from app.utils.dependencies import require_admin, require_empleado

reports_router = APIRouter(prefix="/reports", tags=["Reportes"])
audit_router   = APIRouter(prefix="/audit",   tags=["Auditoría"])
isbn_router    = APIRouter(prefix="/isbn",    tags=["ISBN"])
charts_router  = APIRouter(prefix="/admin",   tags=["Charts"])   # se monta en /api/v1/admin


# ─── helpers ──────────────────────────────────────────────────────────────────

def _csv_stream(headers, rows, filename):
    buf = io.StringIO()
    csv.writer(buf).writerow(headers)
    csv.writer(buf).writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── reportes CSV ─────────────────────────────────────────────────────────────

@reports_router.get("/sales/export")
def export_sales(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    sales = db.query(Sale).order_by(Sale.created_at.desc()).all()
    rows = [[
        s.id,
        s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
        s.tipo.value if s.tipo else "",
        s.status.value if s.status else "",
        s.cliente_nombre or "—",
        float(s.subtotal), float(s.impuesto), float(s.descuento), float(s.total),
    ] for s in sales]
    return _csv_stream(
        ["ID","Fecha","Tipo","Estado","Cliente","Subtotal","Impuesto","Descuento","Total"],
        rows, "ventas.csv"
    )


@reports_router.get("/inventory/export")
def export_inventory(current_user=Depends(require_empleado), db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.activo == True).order_by(Book.nombre).all()
    rows = [[
        b.id, b.isbn, b.nombre, b.autor, b.editorial or "",
        b.categoria.name.value if b.categoria else "",
        float(b.precio), b.stock, b.stock_minimo, b.total_ventas,
        "Sí" if b.es_bestseller else "No",
        f"Sí (L{float(b.precio_original):.2f}→L{float(b.precio):.2f})" if b.precio_original else "No",
    ] for b in books]
    return _csv_stream(
        ["ID","ISBN","Título","Autor","Editorial","Categoría","Precio","Stock",
         "Stock Mínimo","Ventas Totales","Bestseller","Descuento Activo"],
        rows, "inventario.csv"
    )


@reports_router.get("/purchases/export")
def export_purchases(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    purchases = db.query(Purchase).order_by(Purchase.fecha_compra.desc()).all()
    rows = [[
        p.id,
        p.fecha_compra.strftime("%Y-%m-%d") if p.fecha_compra else "",
        p.proveedor_nombre, p.proveedor_contacto or "",
        p.estado, float(p.subtotal), float(p.impuesto), float(p.total), p.notas or "",
    ] for p in purchases]
    return _csv_stream(
        ["ID","Fecha","Proveedor","Contacto","Estado","Subtotal","Impuesto","Total","Notas"],
        rows, "compras.csv"
    )


# ─── auditoría ────────────────────────────────────────────────────────────────

@audit_router.get("/logs")
def get_audit_logs(
    accion: Optional[str] = Query(None),
    tabla:  Optional[str] = Query(None),
    limit:  int = Query(100, le=500),
    skip:   int = Query(0),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if accion: q = q.filter(AuditLog.accion.ilike(f"%{accion}%"))
    if tabla:  q = q.filter(AuditLog.tabla == tabla)
    total = q.count()
    logs  = q.offset(skip).limit(limit).all()
    return {
        "total": total,
        "logs": [{
            "id": l.id,
            "user_nombre": l.user.nombre if l.user else "Sistema",
            "accion": l.accion,
            "tabla": l.tabla,
            "registro_id": l.registro_id,
            "detalle": l.detalle,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in logs]
    }


# ─── ISBN externo ─────────────────────────────────────────────────────────────

@isbn_router.get("/{isbn}")
def lookup_isbn(isbn: str):
    clean = isbn.replace("-", "").replace(" ", "")
    if len(clean) not in (10, 13):
        raise HTTPException(400, "ISBN inválido (10 ó 13 dígitos)")
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean}&format=json&jscmd=data"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LibreriaApp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw = json.loads(resp.read().decode())
    except Exception as e:
        raise HTTPException(502, f"Open Library no disponible: {e}")
    key = f"ISBN:{clean}"
    if key not in raw:
        raise HTTPException(404, "ISBN no encontrado en Open Library")
    d = raw[key]
    autores   = ", ".join(a["name"] for a in d.get("authors", []))
    editorial = (d.get("publishers") or [{}])[0].get("name")
    anio_raw  = (d.get("publish_date") or "")[:4]
    portada   = (d.get("cover") or {}).get("large") or (d.get("cover") or {}).get("medium")
    return {
        "isbn": clean,
        "nombre":           d.get("title", ""),
        "autor":            autores,
        "editorial":        editorial,
        "anio_publicacion": int(anio_raw) if anio_raw.isdigit() else None,
        "descripcion":      "",
        "imagen_url":       portada,
    }


# ─── datos para gráficas ──────────────────────────────────────────────────────

@charts_router.get("/sales-by-month")
def sales_by_month(
    months: int = Query(6, ge=1, le=24),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Devuelve ventas e ingresos agrupados por mes para los últimos N meses.
    Usa SQL nativo para máxima compatibilidad SQLite / PostgreSQL.
    """
    from app.database.connection import is_sqlite
    if is_sqlite:
        sql = text("""
            SELECT strftime('%Y-%m', created_at) AS mes,
                   COUNT(*) AS total_ventas,
                   COALESCE(SUM(total), 0) AS ingresos
            FROM ventas
            WHERE status = 'COMPLETADA'
              AND created_at >= datetime('now', :offset)
            GROUP BY mes
            ORDER BY mes ASC
        """)
        rows = db.execute(sql, {"offset": f"-{months} months"}).fetchall()
    else:
        sql = text("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') AS mes,
                   COUNT(*) AS total_ventas,
                   COALESCE(SUM(total), 0) AS ingresos
            FROM ventas
            WHERE status = 'COMPLETADA'
              AND created_at >= NOW() - (INTERVAL '1 month' * :months)
            GROUP BY mes
            ORDER BY mes ASC
        """)
        rows = db.execute(sql, {"months": months}).fetchall()

    # Top 5 libros más vendidos (histórico)
    top_sql = text("""
        SELECT l.nombre, COALESCE(SUM(vi.cantidad), 0) AS vendidos
        FROM libros l
        JOIN venta_items vi ON vi.libro_id = l.id
        JOIN ventas v ON v.id = vi.venta_id
        WHERE v.status = 'COMPLETADA'
        GROUP BY l.id, l.nombre
        ORDER BY vendidos DESC
        LIMIT 5
    """)
    top_rows = db.execute(top_sql).fetchall()

    return {
        "por_mes":   [{"mes": r[0], "ventas": int(r[1]), "ingresos": float(r[2])} for r in rows],
        "top_libros":[{"nombre": r[0], "vendidos": int(r[1])} for r in top_rows],
    }