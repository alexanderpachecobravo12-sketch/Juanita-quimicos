from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Producto, CotejoSemanal
from app.utils import roles_required

cotejo_bp = Blueprint("cotejo", __name__)


@cotejo_bp.route("/cotejo", methods=["GET"])
@login_required
@roles_required("almacenero", "administrador")
def nuevo_cotejo():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    historial = CotejoSemanal.query.order_by(CotejoSemanal.fecha.desc()).limit(30).all()
    return render_template("cotejo.html", productos=productos, historial=historial)


@cotejo_bp.route("/cotejo", methods=["POST"])
@login_required
@roles_required("almacenero", "administrador")
def registrar_cotejo():
    producto_id = request.form.get("producto_id", type=int)
    conteo_fisico = request.form.get("conteo_fisico", type=float)
    observacion = request.form.get("observacion", "").strip()

    producto = Producto.query.get_or_404(producto_id)

    if conteo_fisico is None or conteo_fisico < 0:
        flash("Ingresa un conteo físico válido.", "danger")
        return redirect(url_for("cotejo.nuevo_cotejo"))

    saldo_sistema = producto.stock_actual
    diferencia = conteo_fisico - saldo_sistema

    cotejo = CotejoSemanal(
        producto_id=producto.id,
        saldo_sistema=saldo_sistema,
        conteo_fisico=conteo_fisico,
        diferencia=diferencia,
        responsable_id=current_user.id,
        observacion=observacion or None,
    )
    db.session.add(cotejo)
    db.session.commit()

    if diferencia != 0:
        flash(
            f"Cotejo registrado para {producto.nombre}. Diferencia detectada: "
            f"{diferencia:+.2f} {producto.unidad_medida} (sistema: {saldo_sistema:.2f}, físico: {conteo_fisico:.2f}).",
            "warning",
        )
    else:
        flash(f"Cotejo registrado para {producto.nombre}. Sin diferencias.", "success")

    return redirect(url_for("cotejo.nuevo_cotejo"))
