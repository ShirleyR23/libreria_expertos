import sqlite3
conn = sqlite3.connect('libreria.db')
conn.execute("UPDATE libros SET anio_publicacion = 500 WHERE isbn = '9780140455526'")
conn.commit()
conn.close()
print('✅ Corregido: El arte de la guerra ahora tiene año 500')
