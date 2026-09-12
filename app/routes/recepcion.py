from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Producto, RecepcionGuia
from app.utils import roles_required

recepcion_bp = Blueprint("recepcion", __name__)


@recepcion_bp.route("/recepcion", methods=["GET"])
@login_required
@roles_required("almacenero", "administrador")
def nueva_recepcion():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    ultimas = RecepcionGuia.query.order_by(RecepcionGuia.creado_en.desc()).limit(15).all()
    return render_template("recepcion.html", productos=productos, ultimas=ultimas)


@recepcion_bp.route("/recepcion", methods=["POST"])
@login_required
@roles_required("almacenero", "administrador")
def registrar_recepcion():
    numero_guia = request.form.get("numero_guia", "").strip()
    proveedor = request.form.get("proveedor", "").strip()
    producto_id = request.form.get("producto_id", type=int)
    cantidad_guia = request.form.get("cantidad_guia", type=float)
    cantidad_fisica = request.form.get("cantidad_fisica", type=float)
    observaciones = request.form.get("observaciones", "").strip()

    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    ultimas = RecepcionGuia.query.order_by(RecepcionGuia.creado_en.desc()).limit(15).all()

    if not numero_guia or not proveedor or not producto_id or cantidad_guia is None or cantidad_fisica is None:
        flash("Completa todos los campos obligatorios.", "danger")
        return render_template("recepcion.html", productos=productos, ultimas=ultimas)

    if cantidad_guia < 0 or cantidad_fisica < 0:
        flash("Las cantidades no pueden ser negativas.", "danger")
        return render_template("recepcion.html", productos=productos, ultimas=ultimas)

    if cantidad_guia != cantidad_fisica and not observaciones:
        flash(
            "La cantidad física no coincide con la guía "
            f"(guía: {cantidad_guia}, físico: {cantidad_fisica}). "
            "Escribe en Observaciones si fue exceso o faltante y, de ser posible, el motivo, "
            "para mantener la trazabilidad antes de registrar.",
            "danger",
        )
        return render_template("recepcion.html", productos=productos, ultimas=ultimas)

    existente = RecepcionGuia.query.filter_by(numero_guia=numero_guia, producto_id=producto_id).first()
    if existente:
        producto = Producto.query.get(producto_id)
        flash(
            f"La guía Nº {numero_guia} ya fue registrada para el producto "
            f"'{producto.nombre if producto else producto_id}' el "
            f"{existente.fecha.strftime('%d/%m/%Y %H:%M')}. No se puede duplicar.",
            "danger",
        )
        return render_template("recepcion.html", productos=productos, ultimas=ultimas)

    recepcion = RecepcionGuia(
        numero_guia=numero_guia,
        proveedor=proveedor,
        producto_id=producto_id,
        cantidad_guia=cantidad_guia,
        cantidad_fisica=cantidad_fisica,
        observaciones=observaciones or None,
        usuario_id=current_user.id,
    )
    db.session.add(recepcion)
    db.session.commit()

    if cantidad_guia != cantidad_fisica:
        flash(
            f"Guía {numero_guia} registrada. OJO: la guía indica {cantidad_guia} pero se contaron "
            f"físicamente {cantidad_fisica}. El stock se movió con la cantidad física. "
            f"Cuando llegue la factura, registra la incidencia correspondiente.",
            "warning",
        )
    else:
        flash(f"Guía {numero_guia} registrada correctamente. Stock actualizado.", "success")

    return redirect(url_for("recepcion.nueva_recepcion"))
