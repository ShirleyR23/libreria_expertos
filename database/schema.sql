-- =====================================================
-- SISTEMA DE GESTIÓN PARA LIBRERÍA
-- Script de Esquema de Base de Datos
-- PostgreSQL Compatible con Docker
-- =====================================================

-- Eliminar tablas si existen (para recreación limpia)
DROP TABLE IF EXISTS facturas CASCADE;
DROP TABLE IF EXISTS venta_items CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;
DROP TABLE IF EXISTS compra_items CASCADE;
DROP TABLE IF EXISTS compras CASCADE;
DROP TABLE IF EXISTS libros CASCADE;
DROP TABLE IF EXISTS categorias_libro CASCADE;
DROP TABLE IF EXISTS empleados CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- =====================================================
-- TABLA: ROLES
-- =====================================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- Insertar roles del sistema
INSERT INTO roles (name, description) VALUES
    ('ADMIN', 'Administrador del sistema - Acceso total'),
    ('EMPLEADO', 'Empleado de la librería - Ventas e inventario'),
    ('CLIENTE', 'Cliente - Catálogo y compras online');

-- =====================================================
-- TABLA: USERS (Autenticación Unificada)
-- REGLA CRÍTICA: Un email solo puede existir UNA VEZ
-- =====================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda rápida por email
CREATE INDEX idx_users_email ON users(email);

-- =====================================================
-- TABLA: EMPLEADOS
-- Información específica de empleados
-- =====================================================
CREATE TABLE empleados (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    salario NUMERIC(10, 2) NOT NULL,
    turno VARCHAR(50) NOT NULL, -- Mañana, Tarde, Completo
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    fecha_contratacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: CLIENTES
-- Información específica de clientes
-- =====================================================
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    codigo_postal VARCHAR(20),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: CATEGORIAS_LIBRO
-- Categorías disponibles para libros
-- =====================================================
CREATE TABLE categorias_libro (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Insertar categorías de libros
INSERT INTO categorias_libro (name, description) VALUES
    ('Ficción', 'Novelas, cuentos y literatura de ficción'),
    ('No Ficción', 'Biografías, ensayos y literatura documental'),
    ('Ciencia', 'Libros de ciencia y divulgación científica'),
    ('Tecnología', 'Programación, informática y tecnología'),
    ('Historia', 'Historia mundial, local y biografías históricas'),
    ('Arte', 'Arte, diseño y arquitectura'),
    ('Literatura', 'Clásicos de la literatura universal'),
    ('Infantil', 'Libros para niños y jóvenes'),
    ('Académico', 'Textos universitarios y académicos'),
    ('Filosofía', 'Filosofía, ética y pensamiento');

-- =====================================================
-- TABLA: LIBROS
-- Inventario principal de la librería
-- =====================================================
CREATE TABLE libros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    autor VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER NOT NULL REFERENCES categorias_libro(id),
    editorial VARCHAR(100),
    anio_publicacion INTEGER,
    precio NUMERIC(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0 NOT NULL,
    stock_minimo INTEGER DEFAULT 5,
    
    -- Campos para sistema experto
    es_bestseller BOOLEAN DEFAULT FALSE,
    total_ventas INTEGER DEFAULT 0,
    ventas_ultimos_30_dias INTEGER DEFAULT 0,
    ultima_venta TIMESTAMP WITH TIME ZONE,
    
    -- Estado
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas frecuentes
CREATE INDEX idx_libros_nombre ON libros(nombre);
CREATE INDEX idx_libros_autor ON libros(autor);
CREATE INDEX idx_libros_isbn ON libros(isbn);
CREATE INDEX idx_libros_categoria ON libros(categoria_id);
CREATE INDEX idx_libros_stock ON libros(stock);

-- =====================================================
-- TABLA: VENTAS
-- Registro de ventas online y presenciales
-- =====================================================
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    empleado_id INTEGER REFERENCES empleados(id),
    
    -- Tipo y estado
    tipo VARCHAR(20) NOT NULL, -- ONLINE, PRESENCIAL
    status VARCHAR(20) DEFAULT 'PENDIENTE', -- PENDIENTE, COMPLETADA, CANCELADA
    
    -- Totales
    subtotal NUMERIC(12, 2) NOT NULL,
    impuesto NUMERIC(12, 2) DEFAULT 0,
    descuento NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL,
    
    -- Metadatos
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: VENTA_ITEMS
-- Detalle de items en cada venta
-- =====================================================
CREATE TABLE venta_items (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    libro_id INTEGER NOT NULL REFERENCES libros(id),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL
);

-- =====================================================
-- TABLA: FACTURAS
-- Facturación electrónica simulada (estructura SAR)
-- =====================================================
CREATE TABLE facturas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER UNIQUE NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    
    -- Datos de factura SAR
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    serie VARCHAR(20) NOT NULL,
    numero_correlativo INTEGER NOT NULL,
    
    -- Información fiscal
    rtn_emisor VARCHAR(20) NOT NULL,
    rtn_cliente VARCHAR(20),
    nombre_cliente VARCHAR(200),
    
    -- Totales
    subtotal NUMERIC(12, 2) NOT NULL,
    impuesto NUMERIC(12, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    
    -- Estado y firma
    estado VARCHAR(20) DEFAULT 'EMITIDA', -- EMITIDA, ANULADA
    firma_electronica TEXT,
    
    -- Fechas
    fecha_emision TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_certificacion TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- TABLA: COMPRAS
-- Compras a proveedores (solo ADMIN)
-- =====================================================
CREATE TABLE compras (
    id SERIAL PRIMARY KEY,
    
    -- Proveedor
    proveedor_nombre VARCHAR(150) NOT NULL,
    proveedor_contacto VARCHAR(100),
    proveedor_telefono VARCHAR(20),
    
    -- Empleado que registró
    empleado_id INTEGER NOT NULL REFERENCES empleados(id),
    
    -- Totales
    subtotal NUMERIC(12, 2) NOT NULL,
    impuesto NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL,
    
    -- Estado
    estado VARCHAR(20) DEFAULT 'RECIBIDA', -- PENDIENTE, RECIBIDA, CANCELADA
    
    -- Metadatos
    notas TEXT,
    fecha_compra TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_recepcion TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: COMPRA_ITEMS
-- Detalle de items en cada compra
-- =====================================================
CREATE TABLE compra_items (
    id SERIAL PRIMARY KEY,
    compra_id INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    libro_id INTEGER NOT NULL REFERENCES libros(id),
    cantidad INTEGER NOT NULL,
    costo_unitario NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL
);

-- =====================================================
-- FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar updated_at automáticamente
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_empleados_updated_at BEFORE UPDATE ON empleados
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clientes_updated_at BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_libros_updated_at BEFORE UPDATE ON libros
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ventas_updated_at BEFORE UPDATE ON ventas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compras_updated_at BEFORE UPDATE ON compras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista de inventario con información de categoría
CREATE VIEW vista_inventario AS
SELECT 
    l.id,
    l.nombre,
    l.isbn,
    l.autor,
    l.precio,
    l.stock,
    l.stock_minimo,
    CASE WHEN l.stock <= l.stock_minimo THEN TRUE ELSE FALSE END AS necesita_reposicion,
    c.name AS categoria,
    l.es_bestseller,
    l.total_ventas
FROM libros l
JOIN categorias_libro c ON l.categoria_id = c.id
WHERE l.activo = TRUE;

-- Vista de ventas con detalles
CREATE VIEW vista_ventas AS
SELECT 
    v.id,
    v.tipo,
    v.status,
    v.total,
    v.created_at AS fecha_venta,
    u_cliente.nombre AS cliente_nombre,
    u_empleado.nombre AS empleado_nombre,
    f.numero_factura
FROM ventas v
LEFT JOIN clientes c ON v.cliente_id = c.id
LEFT JOIN users u_cliente ON c.user_id = u_cliente.id
LEFT JOIN empleados e ON v.empleado_id = e.id
LEFT JOIN users u_empleado ON e.user_id = u_empleado.id
LEFT JOIN facturas f ON v.id = f.venta_id;

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
