-- =====================================================
-- MIGRACIÓN: Agregar columna precio_original a libros
-- =====================================================
-- Ejecutar este script en bases de datos existentes que
-- no tengan la columna precio_original.
--
-- Para SQLite (desarrollo local):
--   sqlite3 libreria.db < migrate_add_precio_original.sql
--
-- Para PostgreSQL (Docker):
--   psql -U postgres -d libreria -f migrate_add_precio_original.sql

-- SQLite y PostgreSQL comparten esta sintaxis:
ALTER TABLE libros ADD COLUMN IF NOT EXISTS precio_original NUMERIC(10, 2);

-- Para SQLite (no soporta IF NOT EXISTS en ALTER TABLE),
-- usar este bloque alternativo si el anterior falla:
-- ALTER TABLE libros ADD COLUMN precio_original NUMERIC(10, 2);
