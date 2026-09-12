from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import RecepcionGuia, IncidenciaFactura
from app.utils import roles_required

incidencias_bp = Blueprint("incidencias", __name__)


@incidencias_bp.route("/incidencias", methods=["GET"])
@login_required
@roles_required("almacenero", "administrador")
def listar_incidencias():
    recepciones = RecepcionGuia.query.order_by(RecepcionGuia.fecha.desc()).limit(100).all()
    pendientes = IncidenciaFactura.query.filter_by(estado="pendiente").order_by(IncidenciaFactura.fecha.desc()).all()
    resueltas = IncidenciaFactura.query.filter_by(estado="resuelto").order_by(IncidenciaFactura.fecha.desc()).limit(30).all()
    return render_template(
        "incidencias.html", recepciones=recepciones, pendientes=pendientes, resueltas=resueltas
    )


@incidencias_bp.route("/incidencias", methods=["POST"])
@login_required
@roles_required("almacenero", "administrador")
def registrar_incidencia():
    numero_factura = request.form.get("numero_factura", "").strip()
    recepcion_id = request.form.get("recepcion_id", type=int)
    cantidad_facturada = request.form.get("cantidad_facturada", type=float)

    recepcion = RecepcionGuia.query.get_or_404(recepcion_id)

    if not numero_factura or cantidad_facturada is None:
        flash("Completa el número de factura y la cantidad facturada.", "danger")
        return redirect(url_for("incidencias.listar_incidencias"))

    incidencia = IncidenciaFactura(
        numero_factura=numero_factura,
        recepcion_id=recepcion.id,
        cantidad_facturada=cantidad_facturada,
        estado="pendiente",
        creado_por_id=current_user.id,
    )
    db.session.add(incidencia)
    db.session.commit()

    flash(
        f"Incidencia registrada: factura {numero_factura} indica {cantidad_facturada} pero se recibieron "
        f"físicamente {recepcion.cantidad_fisica} de '{recepcion.producto.nombre}'. El stock NO se modifica.",
        "warning",
    )
    return redirect(url_for("incidencias.listar_incidencias"))


@incidencias_bp.route("/incidencias/<int:incidencia_id>/resolver", methods=["POST"])
@login_required
@roles_required("administrador")
def resolver_incidencia(incidencia_id):
    incidencia = IncidenciaFactura.query.get_or_404(incidencia_id)
    resolucion = request.form.get("resolucion", "").strip()

    incidencia.estado = "resuelto"
    incidencia.resolucion = resolucion or None
    incidencia.resuelto_en = datetime.utcnow()
    incidencia.resuelto_por_id = current_user.id
    db.session.commit()

    flash("Incidencia marcada como resuelta.", "success")
    return redirect(url_for("incidencias.listar_incidencias"))
