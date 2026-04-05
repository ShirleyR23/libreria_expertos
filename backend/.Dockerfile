# ── Backend Dockerfile ───────────────────────────────────────────────────────
# Usa Python 3.13 slim para mantener imagen liviana
FROM python:3.13-slim

# Evita que Python genere .pyc y que el output sea buffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python primero (se cachean si requirements.txt no cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código (en desarrollo esto se sobreescribe con el volumen montado)
COPY . .

# Crea carpeta de uploads
RUN mkdir -p uploads/covers uploads/pdfs

EXPOSE 8000

# El comando real se define en docker-compose.yml (con --reload para dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
