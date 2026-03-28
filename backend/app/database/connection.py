"""
Configuración de conexión a base de datos con SQLAlchemy 2.0.
Soporta SQLite y PostgreSQL automáticamente.
Compatible con Python 3.13.9
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import get_settings

settings = get_settings()

# Detectar tipo de base de datos
is_sqlite = settings.DATABASE_URL.startswith('sqlite')

# Crear engine con SQLAlchemy 2.0
if is_sqlite:
    # Configuración para SQLite
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.ENVIRONMENT == "development",
        connect_args={"check_same_thread": False}
    )
else:
    # Configuración para PostgreSQL
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.ENVIRONMENT == "development",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para modelos
Base = declarative_base()


def get_db() -> Session:
    """Generador de sesiones de base de datos para dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa todas las tablas en la base de datos."""
    # Importar TODOS los modelos primero para que SQLAlchemy los registre
    from app.models.user import User, Role
    from app.models.employee import Employee
    from app.models.client import Client
    from app.models.book import Book, BookCategory
    from app.models.sale import Sale, SaleItem, Invoice
    from app.models.purchase import Purchase, PurchaseItem
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Insertar datos iniciales
    seed_initial_data()


def seed_initial_data() -> None:
    """Inserta datos iniciales si las tablas están vacías."""
    from sqlalchemy.orm import Session
    from app.models.user import Role, User
    from app.models.client import Client
    from app.models.employee import Employee
    from app.models.book import BookCategory, Book
    from app.core.security import get_password_hash
    from app.core.constants import UserRole, BookCategory as BookCatEnum
    
    db = SessionLocal()
    try:
        # Verificar si ya hay roles
        if db.query(Role).first() is None:
            # Insertar roles
            roles = [
                Role(name=UserRole.ADMIN, description="Administrador del sistema - Acceso total"),
                Role(name=UserRole.EMPLEADO, description="Empleado de la librería - Ventas e inventario"),
                Role(name=UserRole.CLIENTE, description="Cliente - Catálogo y compras online"),
            ]
            db.add_all(roles)
            db.commit()
            print("✅ Roles creados")
        
        # Verificar si ya hay categorías
        if db.query(BookCategory).first() is None:
            # Insertar categorías
            categories = [
                BookCategory(name=BookCatEnum.FICCION, description="Novelas, cuentos y literatura de ficción"),
                BookCategory(name=BookCatEnum.NO_FICCION, description="Biografías, ensayos y literatura documental"),
                BookCategory(name=BookCatEnum.CIENCIA, description="Libros de ciencia y divulgación científica"),
                BookCategory(name=BookCatEnum.TECNOLOGIA, description="Programación, informática y tecnología"),
                BookCategory(name=BookCatEnum.HISTORIA, description="Historia mundial, local y biografías históricas"),
                BookCategory(name=BookCatEnum.ARTE, description="Arte, diseño y arquitectura"),
                BookCategory(name=BookCatEnum.LITERATURA, description="Clásicos de la literatura universal"),
                BookCategory(name=BookCatEnum.INFANTIL, description="Libros para niños y jóvenes"),
                BookCategory(name=BookCatEnum.ACADEMICO, description="Textos universitarios y académicos"),
                BookCategory(name=BookCatEnum.FILOSOFIA, description="Filosofía, ética y pensamiento"),
            ]
            db.add_all(categories)
            db.commit()
            print("✅ Categorías de libros creadas")
        
        # Verificar si ya hay usuarios
        if db.query(User).first() is None:
            # Obtener IDs de roles
            admin_role = db.query(Role).filter(Role.name == UserRole.ADMIN).first()
            empleado_role = db.query(Role).filter(Role.name == UserRole.EMPLEADO).first()
            cliente_role = db.query(Role).filter(Role.name == UserRole.CLIENTE).first()
            
            # Crear usuario admin
            admin_user = User(
                nombre="Administrador Principal",
                email="admin@libreria.com",
                password_hash=get_password_hash("admin123"),
                role_id=admin_role.id,
                activo=True
            )
            db.add(admin_user)
            db.flush()
            
            # Crear usuario empleado
            empleado_user = User(
                nombre="Juan Pérez",
                email="empleado@libreria.com",
                password_hash=get_password_hash("empleado123"),
                role_id=empleado_role.id,
                activo=True
            )
            db.add(empleado_user)
            db.flush()
            
            # Crear empleado
            empleado = Employee(
                user_id=empleado_user.id,
                salario=15000.00,
                turno="Completo",
                telefono="5555-1234",
                direccion="Calle Principal #123"
            )
            db.add(empleado)
            
            # Crear usuario cliente
            cliente_user = User(
                nombre="María García",
                email="cliente@ejemplo.com",
                password_hash=get_password_hash("cliente123"),
                role_id=cliente_role.id,
                activo=True
            )
            db.add(cliente_user)
            db.flush()
            
            # Crear cliente
            cliente = Client(
                user_id=cliente_user.id,
                telefono="5555-5678",
                direccion="Av. Central #456",
                ciudad="Ciudad de México",
                codigo_postal="01000"
            )
            db.add(cliente)
            db.commit()
            print("✅ Usuarios de demo creados")
        
        # Verificar si ya hay libros
        if db.query(Book).first() is None:
            # Obtener IDs de categorías
            cat_ficcion = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.FICCION).first()
            cat_tecnologia = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.TECNOLOGIA).first()
            cat_ciencia = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.CIENCIA).first()
            cat_historia = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.HISTORIA).first()
            cat_literatura = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.LITERATURA).first()
            cat_infantil = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.INFANTIL).first()
            cat_academico = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.ACADEMICO).first()
            cat_filosofia = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.FILOSOFIA).first()
            cat_arte = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.ARTE).first()
            cat_no_ficcion = db.query(BookCategory).filter(BookCategory.name == BookCatEnum.NO_FICCION).first()
            
            books = [
                Book(nombre="Cien años de soledad", isbn="9780307474728", autor="Gabriel García Márquez",
                     descripcion="La novela narra la historia de la familia Buendía", categoria_id=cat_ficcion.id,
                     editorial="Vintage Español", anio_publicacion=1967, precio=450.00, stock=25, stock_minimo=5),
                Book(nombre="1984", isbn="9780451524935", autor="George Orwell",
                     descripcion="Distopía clásica sobre un régimen totalitario", categoria_id=cat_ficcion.id,
                     editorial="Signet Classic", anio_publicacion=1949, precio=320.00, stock=18, stock_minimo=5),
                Book(nombre="Clean Code", isbn="9780132350884", autor="Robert C. Martin",
                     descripcion="Manual de código limpio para programadores", categoria_id=cat_tecnologia.id,
                     editorial="Prentice Hall", anio_publicacion=2008, precio=850.00, stock=12, stock_minimo=3),
                Book(nombre="Python Crash Course", isbn="9781593279288", autor="Eric Matthes",
                     descripcion="Guía práctica para aprender Python", categoria_id=cat_tecnologia.id,
                     editorial="No Starch Press", anio_publicacion=2019, precio=650.00, stock=8, stock_minimo=5),
                Book(nombre="Una breve historia del tiempo", isbn="9780553380163", autor="Stephen Hawking",
                     descripcion="Exploración de los misterios del universo", categoria_id=cat_ciencia.id,
                     editorial="Bantam", anio_publicacion=1988, precio=380.00, stock=15, stock_minimo=5),
                Book(nombre="Sapiens: De animales a dioses", isbn="9788499926223", autor="Yuval Noah Harari",
                     descripcion="Breve historia de la humanidad", categoria_id=cat_historia.id,
                     editorial="Debate", anio_publicacion=2014, precio=520.00, stock=20, stock_minimo=5),
                Book(nombre="Don Quijote de la Mancha", isbn="9788420412146", autor="Miguel de Cervantes",
                     descripcion="La novela más famosa de la literatura española", categoria_id=cat_literatura.id,
                     editorial="Alfaguara", anio_publicacion=1605, precio=480.00, stock=10, stock_minimo=3),
                Book(nombre="Harry Potter y la piedra filosofal", isbn="9788478884452", autor="J.K. Rowling",
                     descripcion="Primera aventura del joven mago Harry Potter", categoria_id=cat_infantil.id,
                     editorial="Salamandra", anio_publicacion=1997, precio=420.00, stock=30, stock_minimo=10),
                Book(nombre="Introducción a la economía", isbn="9786071512921", autor="Paul A. Samuelson",
                     descripcion="Texto clásico de economía", categoria_id=cat_academico.id,
                     editorial="McGraw-Hill", anio_publicacion=2010, precio=780.00, stock=6, stock_minimo=5),
                Book(nombre="Meditaciones", isbn="9780140449334", autor="Marco Aurelio",
                     descripcion="Reflexiones filosóficas del emperador romano", categoria_id=cat_filosofia.id,
                     editorial="Penguin Classics", anio_publicacion=180, precio=290.00, stock=14, stock_minimo=4),
                Book(nombre="Historia del arte", isbn="9780133910117", autor="H.W. Janson",
                     descripcion="Comprensivo estudio de la historia del arte", categoria_id=cat_arte.id,
                     editorial="Pearson", anio_publicacion=2015, precio=1200.00, stock=4, stock_minimo=2),
                Book(nombre="Steve Jobs", isbn="9781451648539", autor="Walter Isaacson",
                     descripcion="Biografía autorizada del cofundador de Apple", categoria_id=cat_no_ficcion.id,
                     editorial="Simon & Schuster", anio_publicacion=2011, precio=550.00, stock=16, stock_minimo=5),
            ]
            db.add_all(books)
            db.commit()
            print("✅ Libros de ejemplo creados")
        
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        db.rollback()
        print(f"⚠️ Error al insertar datos iniciales: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
