from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Producto
from app.utils import roles_required

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/catalogo")
@login_required
@roles_required("administrador")
def listar_productos():
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template("catalogo.html", productos=productos)


@catalogo_bp.route("/catalogo/nuevo", methods=["POST"])
@login_required
@roles_required("administrador")
def crear_producto():
    codigo = request.form.get("codigo", "").strip()
    nombre = request.form.get("nombre", "").strip()
    unidad_medida = request.form.get("unidad_medida", "unidad").strip() or "unidad"
    stock_minimo = request.form.get("stock_minimo", type=float) or 0

    if not codigo or not nombre:
        flash("Código y nombre son obligatorios.", "danger")
        return redirect(url_for("catalogo.listar_productos"))

    if Producto.query.filter_by(codigo=codigo).first():
        flash(f"Ya existe un producto con el código '{codigo}'.", "danger")
        return redirect(url_for("catalogo.listar_productos"))

    producto = Producto(
        codigo=codigo,
        nombre=nombre,
        unidad_medida=unidad_medida,
        stock_minimo=stock_minimo,
        creado_por_id=current_user.id,
    )
    db.session.add(producto)
    db.session.commit()
    flash(f"Producto '{nombre}' creado.", "success")
    return redirect(url_for("catalogo.listar_productos"))


@catalogo_bp.route("/catalogo/<int:producto_id>/editar", methods=["POST"])
@login_required
@roles_required("administrador")
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    nombre = request.form.get("nombre", "").strip()
    unidad_medida = request.form.get("unidad_medida", "").strip()
    stock_minimo = request.form.get("stock_minimo", type=float)

    if nombre:
        producto.nombre = nombre
    if unidad_medida:
        producto.unidad_medida = unidad_medida
    if stock_minimo is not None:
        producto.stock_minimo = stock_minimo

    db.session.commit()
    flash(f"Producto '{producto.nombre}' actualizado.", "success")
    return redirect(url_for("catalogo.listar_productos"))


@catalogo_bp.route("/catalogo/<int:producto_id>/toggle", methods=["POST"])
@login_required
@roles_required("administrador")
def toggle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.activo = not producto.activo
    db.session.commit()
    estado = "activado" if producto.activo else "desactivado"
    flash(f"Producto '{producto.nombre}' {estado}.", "info")
    return redirect(url_for("catalogo.listar_productos"))
