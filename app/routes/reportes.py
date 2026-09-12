import csv
import io

from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from openpyxl import Workbook

from app.models import Producto, RecepcionGuia, Venta, IncidenciaFactura
from app.utils import roles_required

reportes_bp = Blueprint("reportes", __name__)


def _movimientos_producto(producto_id):
    recepciones = RecepcionGuia.query.filter_by(producto_id=producto_id).all()
    ventas = Venta.query.filter_by(producto_id=producto_id).all()

    filas = []
    for r in recepciones:
        filas.append({
            "fecha": r.fecha,
            "tipo": "Entrada (guía)",
            "referencia": r.numero_guia,
            "cantidad": float(r.cantidad_fisica),
            "usuario": r.usuario.nombre,
            "detalle": f"Proveedor: {r.proveedor}",
        })
    for v in ventas:
        filas.append({
            "fecha": v.fecha,
            "tipo": "Salida (venta)",
            "referencia": v.numero_ticket,
            "cantidad": -float(v.cantidad),
            "usuario": v.cajero.nombre,
            "detalle": f"Terminal: {v.terminal}" + (" — STOCK INSUFICIENTE" if v.stock_insuficiente else ""),
        })
    filas.sort(key=lambda f: f["fecha"])
    return filas


@reportes_bp.route("/reportes")
@login_required
@roles_required("administrador")
def ver_reportes():
    productos = Producto.query.order_by(Producto.nombre).all()
    producto_id = request.args.get("producto_id", type=int)

    movimientos = []
    producto_seleccionado = None
    if producto_id:
        producto_seleccionado = Producto.query.get_or_404(producto_id)
        movimientos = _movimientos_producto(producto_id)

    incidencias_pendientes = (
        IncidenciaFactura.query.filter_by(estado="pendiente").order_by(IncidenciaFactura.fecha.desc()).all()
    )

    return render_template(
        "reportes.html",
        productos=productos,
        producto_seleccionado=producto_seleccionado,
        movimientos=movimientos,
        incidencias_pendientes=incidencias_pendientes,
    )


@reportes_bp.route("/reportes/movimientos/export")
@login_required
@roles_required("administrador")
def exportar_movimientos():
    producto_id = request.args.get("producto_id", type=int)
    formato = request.args.get("formato", "xlsx")
    producto = Producto.query.get_or_404(producto_id)
    filas = _movimientos_producto(producto_id)

    encabezados = ["Fecha", "Tipo", "Referencia", "Cantidad", "Usuario", "Detalle"]
    datos = [
        [f["fecha"].strftime("%d/%m/%Y %H:%M"), f["tipo"], f["referencia"], f["cantidad"], f["usuario"], f["detalle"]]
        for f in filas
    ]

    nombre_archivo = f"movimientos_{producto.codigo}"

    if formato == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(encabezados)
        writer.writerows(datos)
        mem = io.BytesIO(buffer.getvalue().encode("utf-8-sig"))
        return send_file(
            mem, mimetype="text/csv", as_attachment=True, download_name=f"{nombre_archivo}.csv"
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"
    ws.append(encabezados)
    for fila in datos:
        ws.append(fila)
    mem = io.BytesIO()
    wb.save(mem)
    mem.seek(0)
    return send_file(
        mem,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{nombre_archivo}.xlsx",
    )


@reportes_bp.route("/reportes/incidencias/export")
@login_required
@roles_required("administrador")
def exportar_incidencias():
    incidencias = IncidenciaFactura.query.order_by(IncidenciaFactura.fecha.desc()).all()

    encabezados = [
        "Fecha", "Nº Factura", "Nº Guía", "Producto", "Cant. Facturada",
        "Cant. Física Recibida", "Diferencia", "Estado", "Resolución",
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "Incidencias"
    ws.append(encabezados)
    for i in incidencias:
        ws.append([
            i.fecha.strftime("%d/%m/%Y %H:%M"),
            i.numero_factura,
            i.recepcion.numero_guia,
            i.recepcion.producto.nombre,
            float(i.cantidad_facturada),
            float(i.recepcion.cantidad_fisica),
            i.diferencia,
            i.estado,
            i.resolucion or "",
        ])
    mem = io.BytesIO()
    wb.save(mem)
    mem.seek(0)
    return send_file(
        mem,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="incidencias_factura.xlsx",
    )
