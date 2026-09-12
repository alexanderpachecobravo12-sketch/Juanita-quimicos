from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Usuario, ROLES
from app.utils import roles_required

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/usuarios")
@login_required
@roles_required("administrador")
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return render_template("usuarios.html", usuarios=usuarios, roles=ROLES)


@usuarios_bp.route("/usuarios/nuevo", methods=["POST"])
@login_required
@roles_required("administrador")
def crear_usuario():
    username = request.form.get("username", "").strip().lower()
    nombre = request.form.get("nombre", "").strip()
    rol = request.form.get("rol", "").strip()
    password = request.form.get("password", "")

    if not username or not nombre or rol not in ROLES or not password:
        flash("Completa todos los campos correctamente.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if Usuario.query.filter_by(username=username).first():
        flash(f"Ya existe un usuario con el nombre de usuario '{username}'.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    usuario = Usuario(username=username, nombre=nombre, rol=rol)
    usuario.set_password(password)
    db.session.add(usuario)
    db.session.commit()

    flash(f"Usuario '{username}' creado con rol {rol}.", "success")
    return redirect(url_for("usuarios.listar_usuarios"))


@usuarios_bp.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@login_required
@roles_required("administrador")
def toggle_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.id == current_user.id:
        flash("No puedes desactivar tu propio usuario.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    usuario.activo = not usuario.activo
    db.session.commit()
    estado = "activado" if usuario.activo else "desactivado"
    flash(f"Usuario '{usuario.username}' {estado}.", "info")
    return redirect(url_for("usuarios.listar_usuarios"))


@usuarios_bp.route("/usuarios/<int:usuario_id>/clave", methods=["POST"])
@login_required
@roles_required("administrador")
def cambiar_clave(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    password = request.form.get("password", "")

    if not password or len(password) < 4:
        flash("La contraseña debe tener al menos 4 caracteres.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    usuario.set_password(password)
    db.session.commit()
    flash(f"Contraseña de '{usuario.username}' actualizada.", "success")
    return redirect(url_for("usuarios.listar_usuarios"))
