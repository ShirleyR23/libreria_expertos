# Sistema de Gestión para Librería

Sistema completo de gestión para librería con arquitectura profesional, autenticación JWT, control de acceso basado en roles (RBAC) y sistema experto integrado.

---

## INICIO RÁPIDO

### Opción 1: Desarrollo Local (Sin Docker)

**Requisitos:** Python 3.13.9 y Node.js 20+

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2. Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

**Listo!** 
- Frontend: http://localhost:4321
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Opción 2: Con Docker (PostgreSQL)

**Requisitos:** Docker y Docker Compose

```bash
# En la raíz del proyecto
docker-compose up -d
```

**Listo!**
- Frontend: http://localhost:4321
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

##  Credenciales de Demo

| Email | Contraseña | Rol | Acceso |
|-------|------------|-----|--------|
| admin@libreria.com | admin123 | ADMIN | Todo el sistema |
| empleado@libreria.com | empleado123 | EMPLEADO | Ventas, inventario |
| cliente@ejemplo.com | cliente123 | CLIENTE | Catálogo, compras |

---

## 📁 Estructura del Proyecto

```
libreria-system/
├── backend/              # FastAPI + Python 3.13.9
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   ├── services/    # Lógica de negocio
│   │   ├── models/      # SQLAlchemy ORM
│   │   ├── schemas/     # Pydantic v2
│   │   └── main.py      # Punto de entrada
│   ├── requirements.txt # Dependencias
│   └── .env            # Configuración SQLite
├── frontend/            # Astro
│   ├── src/
│   │   ├── pages/      # 15 páginas
│   │   ├── components/ # Componentes UI
│   │   └── services/   # API client
│   ├── package.json
│   └── .env           # URL del backend
├── docker-compose.yml  # Orquestación Docker
└── README.md          # Este archivo
```

---

##  API Endpoints Principales

### Autenticación
```
POST /api/v1/auth/login              # Login
POST /api/v1/auth/register-client    # Registro
GET  /api/v1/auth/me                 # Perfil
```

### Libros
```
GET /api/v1/books/catalog            # Catálogo público
GET /api/v1/books/inventory/all      # Inventario (empleados)
```

### Ventas
```
POST /api/v1/sales/online            # Comprar (clientes)
POST /api/v1/sales/presencial        # Vender (empleados)
```

### Sistema Experto
```
GET /api/v1/expert/recommendations   # Recomendaciones
GET /api/v1/expert/inventory-alerts  # Alertas de stock
```

---

## 🤖 Sistema Experto

| Regla | Descripción |
|-------|-------------|
| **Recomendación** | Basada en historial de compras |
| **Stock < 5** | Alerta de reposición |
| **Ventas > 20 + Stock < 10** | Compra urgente |
| **Ventas > 50** | Marcar bestseller |
| **Sin ventas 60 días** | Sugerir promoción |

---

## 🛠️ Tecnologías

### Backend
- **Python 3.13.9** (OBLIGATORIO)
- **FastAPI** - Framework web
- **SQLAlchemy 2.0** - ORM
- **Pydantic v2** - Validación
- **JWT** - Autenticación

### Frontend
- **Astro** - Framework web
- **Fetch API** - HTTP client

### Base de Datos
- **SQLite** (desarrollo local)
- **PostgreSQL** (Docker)

---

## 📝 Configuración

### Variables de Entorno Backend (.env)
```env
# SQLite (desarrollo local - por defecto)
DATABASE_URL=sqlite:///./libreria.db

# PostgreSQL (solo con Docker)
# DATABASE_URL=postgresql://user:pass@localhost:5432/db

SECRET_KEY=tu-clave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Variables de Entorno Frontend (.env)
```env
PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Comandos Docker

```bash
# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reconstruir
docker-compose up -d --build
```

---

## Solución de Problemas

### Puerto 8000 ocupado
```bash
# Cambiar puerto en backend
uvicorn app.main:app --reload --port 8001
```

### Puerto 4321 ocupado
```bash
# Cambiar puerto en frontend
npm run dev -- --port 3000
```

### Error de CORS
Verificar que el backend esté corriendo en el puerto correcto.

---
