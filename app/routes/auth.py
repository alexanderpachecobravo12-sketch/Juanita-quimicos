from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models import Usuario

auth_bp = Blueprint("auth", __name__)

DESTINO_POR_ROL = {
    "cajero": "venta.nueva_venta",
    "almacenero": "recepcion.nueva_recepcion",
    "administrador": "kardex.ver_kardex",
}


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for(DESTINO_POR_ROL.get(current_user.rol, "auth.login")))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(DESTINO_POR_ROL.get(current_user.rol, "auth.login")))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(username=username).first()

        if usuario is None or not usuario.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
        elif not usuario.activo:
            flash("Este usuario está desactivado. Contacta al administrador.", "danger")
        else:
            login_user(usuario)
            return redirect(url_for(DESTINO_POR_ROL.get(usuario.rol, "venta.nueva_venta")))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
