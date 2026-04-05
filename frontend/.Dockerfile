# ── Frontend Dockerfile (Astro) ──────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Instala dependencias primero (se cachean si package.json no cambia)
COPY package*.json ./
RUN npm install

# Copia el resto del proyecto
COPY . .

EXPOSE 4321

# En desarrollo: modo dev con hot reload
# En producción: cambiar a: npm run build && node ./dist/server/entry.mjs
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
