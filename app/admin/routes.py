from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Category, User
from . import bp


def _require_admin() -> bool:
    if not current_user.is_admin:
        flash("Acceso restringido (solo admin).", "danger")
        return False
    return True


@bp.get("/")
@login_required
def index():
    if not _require_admin():
        return redirect(url_for("documents.dashboard"))
    return render_template("admin/index.html")


@bp.get("/users")
@login_required
def users():
    if not _require_admin():
        return redirect(url_for("documents.dashboard"))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@bp.post("/users/toggle/<int:user_id>")
@login_required
def users_toggle(user_id: int):
    if not _require_admin():
        return redirect(url_for("documents.dashboard"))

    u = db.session.get(User, user_id)
    if not u:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.users"))

    if u.id == current_user.id:
        flash("No puedes desactivarte a ti mismo.", "warning")
        return redirect(url_for("admin.users"))

    u.is_active = not u.is_active
    db.session.commit()
    flash("Estado actualizado.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/categories")
@login_required
def categories():
    if not _require_admin():
        return redirect(url_for("documents.dashboard"))
    cats = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/categories.html", cats=cats)


@bp.post("/categories")
@login_required
def categories_create():
    if not _require_admin():
        return redirect(url_for("documents.dashboard"))

    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Nombre de categoría requerido.", "warning")
        return redirect(url_for("admin.categories"))

    exists = Category.query.filter_by(name=name).first()
    if exists:
        flash("Esa categoría ya existe.", "warning")
        return redirect(url_for("admin.categories"))

    db.session.add(Category(name=name))
    db.session.commit()
    flash("Categoría creada ✅", "success")
    return redirect(url_for("admin.categories"))