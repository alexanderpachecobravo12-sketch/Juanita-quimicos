import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-desarrollo-cambiar-en-produccion")
    db_path = os.path.join(app.instance_path, "inventario.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.Usuario.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.venta import venta_bp
    from app.routes.recepcion import recepcion_bp
    from app.routes.kardex import kardex_bp
    from app.routes.cotejo import cotejo_bp
    from app.routes.incidencias import incidencias_bp
    from app.routes.catalogo import catalogo_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.reportes import reportes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(venta_bp)
    app.register_blueprint(recepcion_bp)
    app.register_blueprint(kardex_bp)
    app.register_blueprint(cotejo_bp)
    app.register_blueprint(incidencias_bp)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reportes_bp)

    with app.app_context():
        db.create_all()
        _migrar_columnas_faltantes()
        _seed_admin()

    @app.context_processor
    def inject_globals():
        from datetime import datetime as _dt
        return {"anio_actual": _dt.now().year, "ahora": _dt.utcnow()}

    return app


def _migrar_columnas_faltantes():
    """Agrega columnas nuevas a bases de datos creadas con una versión anterior del modelo."""
    from sqlalchemy import text

    columnas = [row[1] for row in db.session.execute(text("PRAGMA table_info(incidencia_factura)")).fetchall()]
    if columnas and "resuelto_por_id" not in columnas:
        db.session.execute(text("ALTER TABLE incidencia_factura ADD COLUMN resuelto_por_id INTEGER"))
        db.session.commit()


def _seed_admin():
    """Crea un usuario administrador inicial si no existe ningún usuario."""
    from app.models import Usuario

    if Usuario.query.count() == 0:
        admin = Usuario(username="admin", nombre="Administrador", rol="administrador", activo=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("=" * 60)
        print("Usuario administrador creado: admin / admin123")
        print("Por favor cambia esta contraseña desde Usuarios > Editar.")
        print("=" * 60)
