# ============================================================
# DOCKERFILE PARA FRONTEND ASTRO
# Node.js 20 + Astro
# ============================================================

FROM node:20-alpine

# Configurar entorno
ENV NODE_ENV=development
ENV NPM_CONFIG_CACHE=/tmp/npm-cache

# Crear directorio de trabajo
WORKDIR /app

# Copiar package.json primero para aprovechar cache
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar código de la aplicación
COPY . .

# Exponer puerto de Astro
EXPOSE 4321

# Comando por defecto
CMD ["npm", "run", "dev", "--", "--host"]
