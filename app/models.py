from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

ROLES = ("cajero", "almacenero", "administrador")


class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    unidad_medida = db.Column(db.String(20), nullable=False, default="unidad")
    stock_minimo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    creado_por = db.relationship("Usuario")

    @property
    def total_entradas(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(RecepcionGuia.cantidad_fisica), 0))
            .filter(RecepcionGuia.producto_id == self.id)
            .scalar()
        )
        return float(total)

    @property
    def total_salidas(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Venta.cantidad), 0))
            .filter(Venta.producto_id == self.id)
            .scalar()
        )
        return float(total)

    @property
    def stock_actual(self):
        return self.total_entradas - self.total_salidas

    @property
    def bajo_minimo(self):
        return self.stock_actual < float(self.stock_minimo or 0)


class RecepcionGuia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    numero_guia = db.Column(db.String(50), nullable=False)
    proveedor = db.Column(db.String(150), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad_guia = db.Column(db.Numeric(12, 2), nullable=False)
    cantidad_fisica = db.Column(db.Numeric(12, 2), nullable=False)
    observaciones = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("numero_guia", "producto_id", name="uq_guia_producto"),
    )

    producto = db.relationship("Producto")
    usuario = db.relationship("Usuario")

    @property
    def diferencia_guia_fisica(self):
        return float(self.cantidad_guia) - float(self.cantidad_fisica)


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    numero_ticket = db.Column(db.String(50), unique=True, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    cajero_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    terminal = db.Column(db.String(50), nullable=False)
    stock_insuficiente = db.Column(db.Boolean, default=False, nullable=False)

    producto = db.relationship("Producto")
    cajero = db.relationship("Usuario")


class CotejoSemanal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    saldo_sistema = db.Column(db.Numeric(12, 2), nullable=False)
    conteo_fisico = db.Column(db.Numeric(12, 2), nullable=False)
    diferencia = db.Column(db.Numeric(12, 2), nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    observacion = db.Column(db.Text)

    producto = db.relationship("Producto")
    responsable = db.relationship("Usuario")


class IncidenciaFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    numero_factura = db.Column(db.String(50), nullable=False)
    recepcion_id = db.Column(db.Integer, db.ForeignKey("recepcion_guia.id"), nullable=False)
    cantidad_facturada = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.String(20), default="pendiente", nullable=False)
    resolucion = db.Column(db.Text)
    creado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    resuelto_en = db.Column(db.DateTime)
    resuelto_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    recepcion = db.relationship("RecepcionGuia")
    creado_por = db.relationship("Usuario", foreign_keys=[creado_por_id])
    resuelto_por = db.relationship("Usuario", foreign_keys=[resuelto_por_id])

    @property
    def diferencia(self):
        return float(self.cantidad_facturada) - float(self.recepcion.cantidad_fisica)

    @property
    def dias_abierta(self):
        fin = self.resuelto_en or datetime.utcnow()
        return (fin - self.fecha).days
