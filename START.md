# 🚀 INICIO RÁPIDO

## Opción 1: Desarrollo Local (Recomendado para pruebas)

### Paso 1: Backend

```bash
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor (SQLite automático)
uvicorn app.main:app --reload
```

El backend estará en: **http://localhost:8000**

### Paso 2: Frontend

En otra terminal:

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor
npm run dev
```

El frontend estará en: **http://localhost:4321**

---

## Opción 2: Con Docker (PostgreSQL)

```bash
# En la raíz del proyecto
docker-compose up -d
```

Esto inicia:
- PostgreSQL en puerto 5432
- Backend en puerto 8000
- Frontend en puerto 4321

---

## ✅ Verificación

Abre tu navegador y visita:

1. **Catálogo:** http://localhost:4321/catalogo
2. **Login:** http://localhost:4321/login
3. **API Docs:** http://localhost:8000/docs
4. **Health Check:** http://localhost:8000/health

---

## 🔐 Login de Demo

| Email | Contraseña | Rol |
|-------|------------|-----|
| admin@libreria.com | admin123 | Administrador |
| empleado@libreria.com | empleado123 | Empleado |
| cliente@ejemplo.com | cliente123 | Cliente |

---

## 📂 Archivos Importantes

- `backend/libreria.db` - Base de datos SQLite (se crea automáticamente)
- `backend/.env` - Configuración del backend
- `frontend/.env` - Configuración del frontend

---

## 🛑 Detener

### Desarrollo Local
- Backend: `Ctrl + C`
- Frontend: `Ctrl + C`

### Docker
```bash
docker-compose down
```

---

**¡Listo! El sistema está funcionando.**
t:4321/dashboard-admin
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health

## 🛠️ Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Detener todo
docker-compose down

# Reconstruir
docker-compose up -d --build

# Eliminar todo (incluyendo datos)
docker-compose down -v
```

## ⚠️ Solución de Problemas

### Error de conexión a base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Reiniciar solo la base de datos
docker-compose restart db
```

### Error de CORS
```bash
# Verificar que el backend esté en el puerto 8000
# Verificar la configuración de CORS en backend/app/main.py
```

### Puerto ocupado
```bash
# Cambiar puertos en docker-compose.yml si es necesario
```

---

**¡Listo! El sistema debería estar funcionando en http://localhost:4321**
