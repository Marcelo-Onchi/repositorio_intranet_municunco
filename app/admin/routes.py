from __future__ import annotations

import re

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Category, User
from . import bp

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")


def _require_admin() -> None:
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


def _normalize_username(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    email = _normalize_email(email)
    return "@" in email and "." in email and len(email) >= 6


@bp.get("/")
@login_required
def index():
    _require_admin()
    users = User.query.order_by(User.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/index.html", users=users, categories=categories)


# =========================
# Usuarios
# =========================
@bp.post("/users/create")
@login_required
def create_user():
    _require_admin()

    username = _normalize_username(request.form.get("username", ""))
    full_name = (request.form.get("full_name") or "").strip()
    email = _normalize_email(request.form.get("email", ""))
    password = request.form.get("password") or ""
    is_admin = bool(request.form.get("is_admin"))
    is_active = bool(request.form.get("is_active"))

    if not username or "@" in username or not _USERNAME_RE.match(username):
        flash("Usuario inválido. Usa 3–32 caracteres: letras/números/punto/guión/guión bajo.", "error")
        return redirect(url_for("admin.index"))

    if not full_name or len(full_name) < 3:
        flash("Nombre completo inválido.", "error")
        return redirect(url_for("admin.index"))

    if not _is_valid_email(email):
        flash("Correo inválido.", "error")
        return redirect(url_for("admin.index"))

    if len(password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("admin.index"))

    if User.query.filter_by(username=username).first():
        flash("Ese usuario ya existe.", "error")
        return redirect(url_for("admin.index"))

    if User.query.filter_by(email=email).first():
        flash("Ese correo ya está registrado.", "error")
        return redirect(url_for("admin.index"))

    user = User(
        username=username,
        full_name=full_name,
        email=email,
        is_admin=is_admin,
        is_active=is_active,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash(f"Usuario creado: {user.username}", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/update")
@login_required
def update_user(user_id: int):
    _require_admin()

    if current_user.id == user_id:
        flash("Por seguridad, edita tu cuenta desde una pantalla dedicada (evita bloquearte).", "warning")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)

    username = _normalize_username(request.form.get("username", ""))
    full_name = (request.form.get("full_name") or "").strip()
    email = _normalize_email(request.form.get("email", ""))
    is_admin = bool(request.form.get("is_admin"))
    is_active = bool(request.form.get("is_active"))

    if not username or "@" in username or not _USERNAME_RE.match(username):
        flash("Usuario inválido.", "error")
        return redirect(url_for("admin.index"))

    if not full_name or len(full_name) < 3:
        flash("Nombre completo inválido.", "error")
        return redirect(url_for("admin.index"))

    if not _is_valid_email(email):
        flash("Correo inválido.", "error")
        return redirect(url_for("admin.index"))

    # Unicidad (si cambió)
    other_u = User.query.filter(User.username == username, User.id != user.id).first()
    if other_u:
        flash("Ese username ya está en uso.", "error")
        return redirect(url_for("admin.index"))

    other_e = User.query.filter(User.email == email, User.id != user.id).first()
    if other_e:
        flash("Ese correo ya está en uso.", "error")
        return redirect(url_for("admin.index"))

    user.username = username
    user.full_name = full_name
    user.email = email
    user.is_admin = is_admin
    user.is_active = is_active

    db.session.commit()
    flash(f"Cambios guardados: {user.username}", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/reset-password")
@login_required
def reset_password(user_id: int):
    _require_admin()

    if current_user.id == user_id:
        flash("No puedes resetear tu propia contraseña desde aquí.", "warning")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    password = request.form.get("password") or ""

    if len(password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("admin.index"))

    user.set_password(password)
    db.session.commit()

    flash(f"Contraseña actualizada: {user.username}", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/toggle-active")
@login_required
def toggle_user_active(user_id: int):
    _require_admin()

    if current_user.id == user_id:
        flash("No puedes desactivarte a ti mismo.", "warning")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    flash(f"Usuario {'activado' if user.is_active else 'desactivado'}: {user.username}", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/toggle-admin")
@login_required
def toggle_user_admin(user_id: int):
    _require_admin()

    if current_user.id == user_id:
        flash("No puedes quitarte el rol admin a ti mismo.", "warning")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()

    flash(f"Permisos admin {'activados' if user.is_admin else 'quitados'} para: {user.username}", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/delete")
@login_required
def delete_user(user_id: int):
    _require_admin()

    if current_user.id == user_id:
        flash("No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("Usuario eliminado.", "success")
    return redirect(url_for("admin.index"))


# =========================
# Categorías
# =========================
@bp.post("/categories/create")
@login_required
def create_category():
    _require_admin()

    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Ingresa un nombre de categoría.", "warning")
        return redirect(url_for("admin.index"))

    exists = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
    if exists:
        flash("Esa categoría ya existe.", "warning")
        return redirect(url_for("admin.index"))

    cat = Category(name=name[:120])
    db.session.add(cat)
    db.session.commit()

    flash("Categoría creada.", "success")
    return redirect(url_for("admin.index"))


@bp.post("/categories/<int:cat_id>/delete")
@login_required
def delete_category(cat_id: int):
    _require_admin()

    cat = Category.query.get_or_404(cat_id)

    if cat.documents and len(cat.documents) > 0:  # type: ignore[attr-defined]
        flash("No puedes eliminar una categoría con documentos asociados.", "warning")
        return redirect(url_for("admin.index"))

    db.session.delete(cat)
    db.session.commit()

    flash("Categoría eliminada.", "success")
    return redirect(url_for("admin.index"))