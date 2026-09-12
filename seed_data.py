"""Siembra el catálogo con productos típicos de una tienda de insecticidas y
crea usuarios de ejemplo para cajero(s) y almacenero. Es idempotente: no
duplica productos ni usuarios que ya existan. Ejecutar con:

    .venv\\Scripts\\python.exe seed_data.py
"""
from app import create_app, db
from app.models import Producto, Usuario

PRODUCTOS = [
    ("INS-001", "Insecticida Aerosol Multi Insectos 360ml", "unidad", 10),
    ("INS-002", "Insecticida Concentrado Cipermetrina 1L", "litro", 5),
    ("INS-003", "Raticida Bloques Cebo x1kg", "kg", 5),
    ("INS-004", "Raticida en Pastillas Fosfuro de Aluminio", "unidad", 8),
    ("INS-005", "Insecticida Polvo para Cucarachas 250g", "unidad", 10),
    ("INS-006", "Cebo Gel para Cucarachas 30g", "unidad", 15),
    ("INS-007", "Trampa Adhesiva para Roedores", "unidad", 20),
    ("INS-008", "Insecticida Piretrina Spray 500ml", "unidad", 10),
    ("INS-009", "Veneno para Hormigas en Cebo 100g", "unidad", 12),
    ("INS-010", "Repelente de Insectos en Gel 60g", "unidad", 10),
    ("INS-011", "Fumigador Manual de Presión 2L", "unidad", 3),
    ("INS-012", "Desinfectante Insecticida 1L", "litro", 8),
]

USUARIOS = [
    ("cajero1", "Cajero Uno", "cajero", "cajero123"),
    ("cajero2", "Cajero Dos", "cajero", "cajero123"),
    ("almacen1", "Almacenero", "almacenero", "almacen123"),
]


def main():
    app = create_app()
    with app.app_context():
        creados_prod = 0
        for codigo, nombre, unidad, minimo in PRODUCTOS:
            if Producto.query.filter_by(codigo=codigo).first():
                continue
            db.session.add(Producto(codigo=codigo, nombre=nombre, unidad_medida=unidad, stock_minimo=minimo))
            creados_prod += 1

        creados_user = 0
        for username, nombre, rol, password in USUARIOS:
            if Usuario.query.filter_by(username=username).first():
                continue
            u = Usuario(username=username, nombre=nombre, rol=rol)
            u.set_password(password)
            db.session.add(u)
            creados_user += 1

        db.session.commit()
        print(f"Productos creados: {creados_prod} (de {len(PRODUCTOS)} en la lista)")
        print(f"Usuarios creados: {creados_user} (de {len(USUARIOS)} en la lista)")
        if creados_user:
            print("Usuarios de ejemplo — cambia estas contraseñas cuanto antes:")
            for username, nombre, rol, password in USUARIOS:
                print(f"  {username} / {password}  ({rol} — {nombre})")


if __name__ == "__main__":
    main()
