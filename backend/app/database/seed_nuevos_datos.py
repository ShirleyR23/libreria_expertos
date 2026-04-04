"""
SEED - Nuevos datos para Honduletras
======================================
Este archivo agrega:
  - Rol GERENTE + usuario gerente demo
  - Columnas imagen_url, pdf_url, pdf_preview_pages en libros
  - 18 libros nuevos (total_ventas=0, es_bestseller=False)
  - Portadas y PDFs asignados via UPDATE después del INSERT

Se llama automáticamente desde connection.py al arrancar el backend.
Es seguro re-ejecutarlo: no duplica datos.
"""

def run_seed(engine, SessionLocal, is_sqlite):
    from sqlalchemy import text

    # ─────────────────────────────────────────────────────────────
    # 1. MIGRACIONES DE COLUMNAS EN libros
    # ─────────────────────────────────────────────────────────────
    with engine.connect() as conn:
        if is_sqlite:
            result = conn.execute(text("PRAGMA table_info(libros)"))
            columnas = [row[1] for row in result.fetchall()]
            for col, definition in [
                ("imagen_url",        "VARCHAR(500)"),
                ("pdf_url",           "VARCHAR(500)"),
                ("pdf_preview_pages", "INTEGER DEFAULT 3"),
            ]:
                if col not in columnas:
                    conn.execute(text(f"ALTER TABLE libros ADD COLUMN {col} {definition}"))
                    conn.commit()
                    print(f"✅ Migración: {col} agregada")
        else:
            for col, definition in [
                ("imagen_url",        "VARCHAR(500)"),
                ("pdf_url",           "VARCHAR(500)"),
                ("pdf_preview_pages", "INTEGER DEFAULT 3"),
            ]:
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name='libros' AND column_name='{col}'"
                ))
                if not result.fetchone():
                    conn.execute(text(f"ALTER TABLE libros ADD COLUMN {col} {definition}"))
                    conn.commit()
                    print(f"✅ Migración: {col} agregada")

    # ─────────────────────────────────────────────────────────────
    # 2. ROL GERENTE
    # ─────────────────────────────────────────────────────────────
    from app.models.user import Role, User
    from app.models.employee import Employee

    db = SessionLocal()
    try:
        if not db.query(Role).filter(Role.name == "GERENTE").first():
            db.add(Role(
                name="GERENTE",
                description="Gerente / Supervisor — Acceso de lectura y análisis completo"
            ))
            db.commit()
            print("✅ Rol GERENTE creado")

        # ─────────────────────────────────────────────────────────
        # 3. USUARIO GERENTE DEMO
        # ─────────────────────────────────────────────────────────
        if not db.query(User).filter(User.email == "gerente@honduletras.com").first():
            from app.core.security import get_password_hash
            gerente_role = db.query(Role).filter(Role.name == "GERENTE").first()
            gerente_user = User(
                nombre="Gerente Demo",
                email="gerente@honduletras.com",
                password_hash=get_password_hash("gerente123"),
                role_id=gerente_role.id,
                activo=True
            )
            db.add(gerente_user)
            db.flush()
            db.add(Employee(
                user_id=gerente_user.id,
                salario=25000.00,
                turno="Completo",
                telefono="5555-9999",
                direccion="Oficina Central"
            ))
            db.commit()
            print("✅ Usuario gerente@honduletras.com creado (contraseña: gerente123)")

        # ─────────────────────────────────────────────────────────
        # 4. LIBROS NUEVOS
        #    total_ventas=0 y es_bestseller=False para que el
        #    ranking de bestsellers solo refleje ventas reales.
        # ─────────────────────────────────────────────────────────
        from app.models.book import Book, BookCategory

        def cat(nombre):
            return db.query(BookCategory).filter(BookCategory.name == nombre).first()

        libros_nuevos = [
            dict(nombre="El principito",               isbn="9780156012195", autor="Antoine de Saint-Exupéry",
                 descripcion="Un aviador perdido en el desierto conoce a un pequeño príncipe. Fábula sobre la amistad y la inocencia.",
                 categoria_id=cat("Literatura").id,    editorial="Harcourt",            anio_publicacion=1943,
                 precio=280.00, stock=40, stock_minimo=10, es_bestseller=False, total_ventas=0),

            dict(nombre="Orgullo y prejuicio",         isbn="9780141439518", autor="Jane Austen",
                 descripcion="Elizabeth Bennet y el orgulloso Mr. Darcy en uno de los romances más célebres de la literatura inglesa.",
                 categoria_id=cat("Literatura").id,    editorial="Penguin Classics",    anio_publicacion=1813,
                 precio=310.00, stock=22, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="Drácula",                     isbn="9780141439846", autor="Bram Stoker",
                 descripcion="El conde Drácula busca mudarse a Inglaterra. Clásico del horror gótico.",
                 categoria_id=cat("Ficción").id,       editorial="Penguin Classics",    anio_publicacion=1897,
                 precio=295.00, stock=17, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="El arte de la guerra",        isbn="9780140455526", autor="Sun Tzu",
                 descripcion="Tratado militar del siglo V a.C. Sus principios se aplican en negocios y liderazgo.",
                 categoria_id=cat("Filosofía").id,     editorial="Penguin Classics",    anio_publicacion=500,
                 precio=220.00, stock=35, stock_minimo=8,  es_bestseller=False, total_ventas=0),

            dict(nombre="Moby Dick",                   isbn="9780142437247", autor="Herman Melville",
                 descripcion="El capitán Ahab persigue obsesivamente a la gran ballena blanca.",
                 categoria_id=cat("Literatura").id,    editorial="Penguin Classics",    anio_publicacion=1851,
                 precio=340.00, stock=11, stock_minimo=4,  es_bestseller=False, total_ventas=0),

            dict(nombre="Atomic Habits",               isbn="9780735211292", autor="James Clear",
                 descripcion="Sistema comprobado para construir buenos hábitos y eliminar los malos.",
                 categoria_id=cat("No Ficción").id,    editorial="Avery",               anio_publicacion=2018,
                 precio=590.00, stock=28, stock_minimo=8,  es_bestseller=False, total_ventas=0),

            dict(nombre="El nombre del viento",        isbn="9780756404741", autor="Patrick Rothfuss",
                 descripcion="Kvothe, el legendario mago y músico, narra su propia historia en esta épica fantasía.",
                 categoria_id=cat("Ficción").id,       editorial="DAW Books",           anio_publicacion=2007,
                 precio=480.00, stock=14, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="Cosmos",                      isbn="9780345539434", autor="Carl Sagan",
                 descripcion="Carl Sagan lleva al lector en un viaje por el universo explorando astronomía y vida.",
                 categoria_id=cat("Ciencia").id,       editorial="Ballantine Books",    anio_publicacion=1980,
                 precio=520.00, stock=19, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="Thinking, Fast and Slow",     isbn="9780374533557", autor="Daniel Kahneman",
                 descripcion="Kahneman explora los dos sistemas del pensamiento: el rápido intuitivo y el lento racional.",
                 categoria_id=cat("No Ficción").id,    editorial="Farrar, Straus and Giroux", anio_publicacion=2011,
                 precio=610.00, stock=13, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="Rayuela",                     isbn="9788437604572", autor="Julio Cortázar",
                 descripcion="Novela experimental que puede leerse de múltiples formas. Búsqueda existencial en París.",
                 categoria_id=cat("Literatura").id,    editorial="Cátedra",             anio_publicacion=1963,
                 precio=420.00, stock=9,  stock_minimo=4,  es_bestseller=False, total_ventas=0),

            dict(nombre="The Design of Everyday Things", isbn="9780465050659", autor="Don Norman",
                 descripcion="Clásico del diseño centrado en el usuario. Por qué algunos objetos nos frustran.",
                 categoria_id=cat("Arte").id,          editorial="Basic Books",         anio_publicacion=2013,
                 precio=720.00, stock=7,  stock_minimo=3,  es_bestseller=False, total_ventas=0),

            dict(nombre="Estructura y algoritmos de datos", isbn="9780131911932", autor="Mark Allen Weiss",
                 descripcion="Texto universitario completo sobre estructuras de datos y algoritmos.",
                 categoria_id=cat("Académico").id,     editorial="Pearson",             anio_publicacion=2006,
                 precio=890.00, stock=5,  stock_minimo=3,  es_bestseller=False, total_ventas=0),

            dict(nombre="La metamorfosis",             isbn="9780553213690", autor="Franz Kafka",
                 descripcion="Gregor Samsa despierta convertido en un insecto gigante. Exploración de la alienación.",
                 categoria_id=cat("Literatura").id,    editorial="Bantam Classics",     anio_publicacion=1915,
                 precio=190.00, stock=23, stock_minimo=6,  es_bestseller=False, total_ventas=0),

            dict(nombre="Frankenstein",                isbn="9780141439471", autor="Mary Shelley",
                 descripcion="Victor Frankenstein crea vida a partir de materia inanimada. Relato de ambición.",
                 categoria_id=cat("Ficción").id,       editorial="Penguin Classics",    anio_publicacion=1818,
                 precio=260.00, stock=16, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="Los viajes de Gulliver",      isbn="9780140436228", autor="Jonathan Swift",
                 descripcion="Gulliver narra sus viajes a tierras fantásticas. Brillante sátira de la sociedad.",
                 categoria_id=cat("Literatura").id,    editorial="Penguin Classics",    anio_publicacion=1726,
                 precio=230.00, stock=12, stock_minimo=4,  es_bestseller=False, total_ventas=0),

            dict(nombre="El túnel",                    isbn="9788423307937", autor="Ernesto Sabato",
                 descripcion="Juan Pablo Castel narra el crimen que cometió. Novela noir de obsesión existencial.",
                 categoria_id=cat("Ficción").id,       editorial="Booket",              anio_publicacion=1948,
                 precio=240.00, stock=11, stock_minimo=4,  es_bestseller=False, total_ventas=0),

            dict(nombre="Inteligencia artificial: Un enfoque moderno", isbn="9780136042594",
                 autor="Stuart Russell y Peter Norvig",
                 descripcion="El texto de referencia más completo sobre IA, desde búsqueda hasta aprendizaje automático.",
                 categoria_id=cat("Tecnología").id,    editorial="Prentice Hall",       anio_publicacion=2009,
                 precio=1450.00, stock=4, stock_minimo=2,  es_bestseller=False, total_ventas=0),

            dict(nombre="Breve historia de casi todo", isbn="9781784161859", autor="Bill Bryson",
                 descripcion="Viaje por la historia de la ciencia, desde el origen del universo hasta el ser humano.",
                 categoria_id=cat("Ciencia").id,       editorial="Black Swan",          anio_publicacion=2003,
                 precio=430.00, stock=15, stock_minimo=5,  es_bestseller=False, total_ventas=0),

            dict(nombre="La casa de los espíritus",    isbn="9788401242458", autor="Isabel Allende",
                 descripcion="La saga de la familia Trueba en Chile entretejiendo amor, política, magia y tragedia.",
                 categoria_id=cat("Ficción").id,       editorial="Plaza & Janés",       anio_publicacion=1982,
                 precio=390.00, stock=13, stock_minimo=5,  es_bestseller=False, total_ventas=0),
        ]

        agregados = 0
        for datos in libros_nuevos:
            if not db.query(Book).filter(Book.isbn == datos["isbn"]).first():
                db.add(Book(**datos))
                agregados += 1

        if agregados > 0:
            db.commit()
            print(f"✅ {agregados} libros nuevos agregados")
        else:
            print("ℹ️  Libros nuevos ya existían, no se agregaron duplicados")

        # ─────────────────────────────────────────────────────────
        # 5. ASIGNAR PORTADAS Y PDFs via UPDATE
        #    Se hace por UPDATE para que siempre se apliquen,
        #    incluso si el libro ya existía de un seed anterior.
        # ─────────────────────────────────────────────────────────
        portadas_y_pdfs = [
            ("9780156012195", "https://covers.openlibrary.org/b/isbn/9780156012195-L.jpg",
             "https://archive.org/download/lepetitprince0000sain/lepetitprince0000sain.pdf", 5),
            ("9780141439518", "https://covers.openlibrary.org/b/isbn/9780141439518-L.jpg",
             "https://archive.org/download/prideprejudice00aust/prideprejudice00aust.pdf", 4),
            ("9780141439846", "https://covers.openlibrary.org/b/isbn/9780141439846-L.jpg",
             "https://archive.org/download/draculabram00stok/draculabram00stok.pdf", 3),
            ("9780140455526", "https://covers.openlibrary.org/b/isbn/9780140455526-L.jpg",
             "https://archive.org/download/theartofwar00suntgoog/theartofwar00suntgoog.pdf", 3),
            ("9780142437247", "https://covers.openlibrary.org/b/isbn/9780142437247-L.jpg",
             "https://archive.org/download/mobydickorwhale00melv/mobydickorwhale00melv.pdf", 3),
            ("9780735211292", "https://covers.openlibrary.org/b/isbn/9780735211292-L.jpg", None, 3),
            ("9780756404741", "https://covers.openlibrary.org/b/isbn/9780756404741-L.jpg", None, 3),
            ("9780345539434", "https://covers.openlibrary.org/b/isbn/9780345539434-L.jpg", None, 3),
            ("9780374533557", "https://covers.openlibrary.org/b/isbn/9780374533557-L.jpg", None, 3),
            ("9788437604572", "https://covers.openlibrary.org/b/isbn/9788437604572-L.jpg", None, 3),
            ("9780465050659", "https://covers.openlibrary.org/b/isbn/9780465050659-L.jpg", None, 3),
            ("9780131911932", "https://covers.openlibrary.org/b/isbn/9780131911932-L.jpg", None, 3),
            ("9780553213690", None,
             "https://archive.org/download/themetamorphosis00kafk/themetamorphosis00kafk.pdf", 3),
            ("9780141439471", None,
             "https://archive.org/download/frankensteinormo00shel/frankensteinormo00shel.pdf", 3),
            ("9780140436228", None,
             "https://archive.org/download/gulliverstravels00swif/gulliverstravels00swif.pdf", 3),
        ]

        actualizados = 0
        for isbn, imagen_url, pdf_url, pages in portadas_y_pdfs:
            libro = db.query(Book).filter(Book.isbn == isbn).first()
            if libro:
                libro.imagen_url        = imagen_url
                libro.pdf_url           = pdf_url
                libro.pdf_preview_pages = pages
                actualizados += 1

        if actualizados > 0:
            db.commit()
            print(f"✅ Portadas y PDFs asignados a {actualizados} libros")

        # ─────────────────────────────────────────────────────────
        # 6. RESETEAR total_ventas A 0
        #    Los libros del seed anterior tenían ventas inventadas
        #    que distorsionaban el ranking de bestsellers.
        #    Solo se resetean si aún tienen el valor falso
        #    (es decir, si no hay ventas reales registradas).
        # ─────────────────────────────────────────────────────────
        isbns_seed = [
            "9780156012195", "9780141439518", "9780141439846",
            "9780140455526", "9780142437247", "9780735211292",
            "9780756404741", "9780345539434", "9780374533557",
            "9788437604572", "9780465050659", "9780131911932",
            "9780553213690", "9780141439471", "9780140436228",
            "9788423307937", "9780136042594", "9781784161859",
            "9788401242458",
        ]
        resetados = 0
        for isbn in isbns_seed:
            libro = db.query(Book).filter(Book.isbn == isbn).first()
            if libro and libro.total_ventas > 0:
                libro.total_ventas  = 0
                libro.es_bestseller = False
                resetados += 1

        if resetados > 0:
            db.commit()
            print(f"✅ Ventas reseteadas a 0 en {resetados} libros (ranking ahora es real)")
        else:
            print("ℹ️  Ventas ya estaban en 0, sin cambios")

    except Exception as e:
        db.rollback()
        print(f"⚠️  Error en seed_nuevos_datos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()