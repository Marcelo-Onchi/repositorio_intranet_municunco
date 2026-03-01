from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Category, User
from . import bp


def _require_admin() -> None:
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@bp.get("/")
@login_required
def index():
    _require_admin()

    users = User.query.order_by(User.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template("admin/index.html", users=users, categories=categories)


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

    flash(
        f"Usuario {'activado' if user.is_active else 'desactivado'}: {user.username}",
        "success",
    )
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

    flash(
        f"Permisos admin {'activados' if user.is_admin else 'quitados'} para: {user.username}",
        "success",
    )
    return redirect(url_for("admin.index"))


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

    # Ojo: si hay documentos asociados, mejor no borrar.
    if cat.documents and len(cat.documents) > 0:  # type: ignore[attr-defined]
        flash("No puedes eliminar una categoría con documentos asociados.", "warning")
        return redirect(url_for("admin.index"))

    db.session.delete(cat)
    db.session.commit()

    flash("Categoría eliminada.", "success")
    return redirect(url_for("admin.index"))