# 📋 INSTRUCCIONES DE ACTUALIZACIÓN
# =====================================
# Aplica los cambios en este orden exacto.

## 1. MIGRACIÓN DE BASE DE DATOS (OBLIGATORIO PRIMERO)

### SQLite (desarrollo local):
sqlite3 backend/libreria.db "ALTER TABLE libros ADD COLUMN precio_original NUMERIC(10,2);"

### PostgreSQL (Docker):
psql -U postgres -d libreria -c "ALTER TABLE libros ADD COLUMN IF NOT EXISTS precio_original NUMERIC(10,2);"

### Alternativa automática:
# Si reiniciar el servidor aplica _run_migrations() en connection.py,
# simplemente reinicia el backend — lo detecta y agrega la columna solo.


## 2. ARCHIVOS BACKEND — reemplazar en tu proyecto:

backend/backend/app/main.py           → Middleware de seguridad completo
backend/backend/app/models/book.py    → Campo precio_original en modelo
backend/backend/app/schemas/book.py   → Campo precio_original en schema
backend/backend/app/database/connection.py → Migración automática
backend/database/schema.sql           → Schema actualizado (para bases nuevas)


## 3. ARCHIVOS FRONTEND — reemplazar en tu proyecto:

src/middleware.ts                      → NUEVO: alias de rutas + auth guard + headers
src/utils/session-guard.js            → NUEVO: auto-logout por inactividad (30 min)
src/layouts/DashboardLayout.astro     → session guard inyectado
src/components/LoginForm.astro        → aviso de sesión expirada
src/pages/catalogo.astro              → etiqueta roja de descuento
src/pages/catalogo-admin.astro        → etiqueta roja de descuento
src/pages/recomendaciones.astro       → etiqueta roja de descuento
src/pages/sistema-experto.astro       → porcentaje de descuento visible en cards


## 4. RUTAS ALIAS DISPONIBLES (middleware.ts)

Puedes compartir estas URLs en lugar de las rutas reales:

/panel              → /dashboard-admin
/mi-panel           → /dashboard-empleado
/gestion            → /inventario
/equipo             → /empleados
/experto            → /sistema-experto
/catalogo-interno   → /catalogo-admin
/mis-ventas         → /ventas
/mis-pedidos        → /mis-compras


## 5. RESUMEN DE SEGURIDAD IMPLEMENTADA

Backend (main.py):
  ✅ Rate limiting: 120 req/IP/60s → HTTP 429
  ✅ SQL Injection: bloquea UNION/SELECT/DROP/-- en URL y body JSON
  ✅ Headers: X-Frame-Options DENY, X-Content-Type-Options, X-XSS-Protection
  ✅ Oculta header "server"
  ✅ /docs y /openapi.json deshabilitados en producción

Frontend (middleware.ts):
  ✅ Rutas protegidas redirigen a /login si no hay cookie de sesión
  ✅ Security headers en todas las respuestas HTML
  ✅ Alias de rutas (los nombres reales no aparecen en navegación)

Frontend (session-guard.js):
  ✅ Auto-logout después de 30 min de inactividad
  ✅ Aviso visual 2 min antes de expirar con cuenta regresiva
  ✅ Botón "Continuar sesión" para renovar
  ✅ Sincronización entre pestañas (si una pestaña hace logout, todas lo hacen)
  ✅ Mensaje en login al regresar por sesión expirada
