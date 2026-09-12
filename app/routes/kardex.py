from flask import Blueprint, render_template
from flask_login import login_required

from app.models import Producto
from app.utils import roles_required

kardex_bp = Blueprint("kardex", __name__)


@kardex_bp.route("/kardex")
@login_required
@roles_required("cajero", "almacenero", "administrador")
def ver_kardex():
    productos = Producto.query.order_by(Producto.nombre).all()
    filas = [
        {
            "producto": p,
            "entradas": p.total_entradas,
            "salidas": p.total_salidas,
            "saldo": p.stock_actual,
            "bajo_minimo": p.bajo_minimo,
        }
        for p in productos
    ]
    return render_template("kardex.html", filas=filas)
