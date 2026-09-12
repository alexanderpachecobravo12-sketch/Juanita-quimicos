from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Producto, Venta
from app.utils import roles_required

venta_bp = Blueprint("venta", __name__)

TERMINALES = ["Caja 1", "Caja 2", "Almacén"]
TERMINAL_CODIGOS = {"Caja 1": "C1", "Caja 2": "C2", "Almacén": "AL"}


def _generar_numero_ticket(terminal):
    codigo = TERMINAL_CODIGOS.get(terminal, "XX")
    hoy = date.today()
    prefijo = f"{codigo}-{hoy.strftime('%Y%m%d')}-"
    cantidad_hoy = Venta.query.filter(Venta.numero_ticket.like(f"{prefijo}%")).count()
    return f"{prefijo}{cantidad_hoy + 1:04d}"


@venta_bp.route("/venta", methods=["GET"])
@login_required
@roles_required("cajero", "administrador")
def nueva_venta():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template("venta.html", productos=productos, terminales=TERMINALES)


@venta_bp.route("/venta", methods=["POST"])
@login_required
@roles_required("cajero", "administrador")
def registrar_venta():
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=float)
    terminal = request.form.get("terminal", "").strip()
    confirmar_stock_insuficiente = request.form.get("confirmar_stock_insuficiente") == "1"

    producto = Producto.query.get_or_404(producto_id)

    if not cantidad or cantidad <= 0:
        flash("La cantidad debe ser mayor a cero.", "danger")
        return redirect(url_for("venta.nueva_venta"))

    if terminal not in TERMINALES:
        flash("Selecciona una terminal válida.", "danger")
        return redirect(url_for("venta.nueva_venta"))

    stock_disponible = producto.stock_actual
    stock_insuficiente = cantidad > stock_disponible

    if stock_insuficiente and not confirmar_stock_insuficiente:
        return render_template(
            "venta_confirmar.html",
            producto=producto,
            cantidad=cantidad,
            terminal=terminal,
            stock_disponible=stock_disponible,
        )

    numero_ticket = _generar_numero_ticket(terminal)

    venta = Venta(
        numero_ticket=numero_ticket,
        producto_id=producto.id,
        cantidad=cantidad,
        cajero_id=current_user.id,
        terminal=terminal,
        stock_insuficiente=stock_insuficiente,
    )
    db.session.add(venta)
    db.session.commit()

    flash(f"Ticket {numero_ticket} registrado correctamente.", "success")
    return redirect(url_for("venta.ver_ticket", venta_id=venta.id))


@venta_bp.route("/venta/ticket/<int:venta_id>")
@login_required
@roles_required("cajero", "administrador")
def ver_ticket(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    return render_template("ticket.html", venta=venta)
