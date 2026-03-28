-- =====================================================
-- SISTEMA DE GESTIÓN PARA LIBRERÍA
-- Datos iniciales (Seed)
-- =====================================================

-- =====================================================
-- USUARIO ADMINISTRADOR
-- Contraseña: admin123 (hasheada con bcrypt)
-- =====================================================
INSERT INTO users (nombre, email, password_hash, role_id, activo)
VALUES (
    'Administrador Principal',
    'admin@libreria.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G',
    (SELECT id FROM roles WHERE name = 'ADMIN'),
    TRUE
);

-- =====================================================
-- USUARIO EMPLEADO DE EJEMPLO
-- Contraseña: empleado123
-- =====================================================
INSERT INTO users (nombre, email, password_hash, role_id, activo)
VALUES (
    'Juan Pérez',
    'empleado@libreria.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G',
    (SELECT id FROM roles WHERE name = 'EMPLEADO'),
    TRUE
);

INSERT INTO empleados (user_id, salario, turno, telefono, direccion)
VALUES (
    (SELECT id FROM users WHERE email = 'empleado@libreria.com'),
    15000.00,
    'Completo',
    '5555-1234',
    'Calle Principal #123'
);

-- =====================================================
-- USUARIO CLIENTE DE EJEMPLO
-- Contraseña: cliente123
-- =====================================================
INSERT INTO users (nombre, email, password_hash, role_id, activo)
VALUES (
    'María García',
    'cliente@ejemplo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G',
    (SELECT id FROM roles WHERE name = 'CLIENTE'),
    TRUE
);

INSERT INTO clientes (user_id, telefono, direccion, ciudad, codigo_postal)
VALUES (
    (SELECT id FROM users WHERE email = 'cliente@ejemplo.com'),
    '5555-5678',
    'Av. Central #456',
    'Ciudad de México',
    '01000'
);

-- =====================================================
-- LIBROS DE EJEMPLO
-- =====================================================

-- Ficción
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Cien años de soledad',
    '9780307474728',
    'Gabriel García Márquez',
    'La novela narra la historia de la familia Buendía a lo largo de siete generaciones en el pueblo ficticio de Macondo.',
    (SELECT id FROM categorias_libro WHERE name = 'Ficción'),
    'Vintage Español',
    1967,
    450.00,
    25,
    5
);

INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    '1984',
    '9780451524935',
    'George Orwell',
    'Distopía clásica sobre un régimen totalitario que controla todos los aspectos de la vida.',
    (SELECT id FROM categorias_libro WHERE name = 'Ficción'),
    'Signet Classic',
    1949,
    320.00,
    18,
    5
);

-- Tecnología
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Clean Code',
    '9780132350884',
    'Robert C. Martin',
    'Manual de código limpio para programadores profesionales.',
    (SELECT id FROM categorias_libro WHERE name = 'Tecnología'),
    'Prentice Hall',
    2008,
    850.00,
    12,
    3
);

INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Python Crash Course',
    '9781593279288',
    'Eric Matthes',
    'Guía práctica para aprender Python desde cero.',
    (SELECT id FROM categorias_libro WHERE name = 'Tecnología'),
    'No Starch Press',
    2019,
    650.00,
    8,
    5
);

-- Ciencia
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Una breve historia del tiempo',
    '9780553380163',
    'Stephen Hawking',
    'Exploración de los misterios del universo, desde el Big Bang hasta los agujeros negros.',
    (SELECT id FROM categorias_libro WHERE name = 'Ciencia'),
    'Bantam',
    1988,
    380.00,
    15,
    5
);

-- Historia
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Sapiens: De animales a dioses',
    '9788499926223',
    'Yuval Noah Harari',
    'Breve historia de la humanidad, desde la prehistoria hasta la era moderna.',
    (SELECT id FROM categorias_libro WHERE name = 'Historia'),
    'Debate',
    2014,
    520.00,
    20,
    5
);

-- Literatura
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Don Quijote de la Mancha',
    '9788420412146',
    'Miguel de Cervantes',
    'La novela más famosa de la literatura española.',
    (SELECT id FROM categorias_libro WHERE name = 'Literatura'),
    'Alfaguara',
    1605,
    480.00,
    10,
    3
);

-- Infantil
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Harry Potter y la piedra filosofal',
    '9788478884452',
    'J.K. Rowling',
    'Primera aventura del joven mago Harry Potter.',
    (SELECT id FROM categorias_libro WHERE name = 'Infantil'),
    'Salamandra',
    1997,
    420.00,
    30,
    10
);

-- Académico
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Introducción a la economía',
    '9786071512921',
    'Paul A. Samuelson',
    'Texto clásico de economía para estudiantes universitarios.',
    (SELECT id FROM categorias_libro WHERE name = 'Académico'),
    'McGraw-Hill',
    2010,
    780.00,
    6,
    5
);

-- Filosofía
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Meditaciones',
    '9780140449334',
    'Marco Aurelio',
    'Reflexiones filosóficas del emperador romano.',
    (SELECT id FROM categorias_libro WHERE name = 'Filosofía'),
    'Penguin Classics',
    180,
    290.00,
    14,
    4
);

-- Arte
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Historia del arte',
    '9780133910117',
    'H.W. Janson',
    'Comprensivo estudio de la historia del arte occidental.',
    (SELECT id FROM categorias_libro WHERE name = 'Arte'),
    'Pearson',
    2015,
    1200.00,
    4,
    2
);

-- No Ficción
INSERT INTO libros (nombre, isbn, autor, descripcion, categoria_id, editorial, anio_publicacion, precio, stock, stock_minimo)
VALUES (
    'Steve Jobs',
    '9781451648539',
    'Walter Isaacson',
    'Biografía autorizada del cofundador de Apple.',
    (SELECT id FROM categorias_libro WHERE name = 'No Ficción'),
    'Simon & Schuster',
    2011,
    550.00,
    16,
    5
);

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
