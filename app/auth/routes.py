from __future__ import annotations

import re

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.extensions import db
from app.models import User
from . import bp


_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")


def _normalize_username(value: str) -> str:
    return (value or "").strip()


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    email = _normalize_email(email)
    return "@" in email and "." in email and len(email) >= 6


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def login_post():
    username = _normalize_username(request.form.get("username", ""))
    password = request.form.get("password") or ""

    if not username or "@" in username:
        flash("Usuario inválido. Ingresa tu usuario (sin @).", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()
    if not user or not user.is_active or not user.check_password(password):
        flash("Credenciales inválidas.", "error")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Bienvenido/a ✅", "success")

    nxt = request.args.get("next")
    return redirect(nxt or url_for("documents.dashboard"))


@bp.get("/register")
def register():
    return render_template("auth/register.html")


@bp.post("/register")
def register_post():
    username = _normalize_username(request.form.get("username", ""))
    full_name = (request.form.get("full_name") or "").strip()
    email = _normalize_email(request.form.get("email", ""))
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    # Validaciones
    if not username:
        flash("Debes ingresar un usuario.", "error")
        return redirect(url_for("auth.register"))

    if "@" in username:
        flash("El usuario no puede contener @.", "error")
        return redirect(url_for("auth.register"))

    if not _USERNAME_RE.match(username):
        flash("Usuario inválido. Usa 3–32 caracteres: letras/números/punto/guión/guión bajo.", "error")
        return redirect(url_for("auth.register"))

    if not full_name or len(full_name) < 3:
        flash("Debes ingresar tu nombre completo.", "error")
        return redirect(url_for("auth.register"))

    if not _is_valid_email(email):
        flash("Correo inválido.", "error")
        return redirect(url_for("auth.register"))

    if len(password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("auth.register"))

    if password != password2:
        flash("Las contraseñas no coinciden.", "error")
        return redirect(url_for("auth.register"))

    # Unicidad
    if User.query.filter_by(username=username).first():
        flash("Ese usuario ya existe.", "error")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("Ese correo ya está registrado.", "error")
        return redirect(url_for("auth.register"))

    # Crear
    user = User(username=username, email=email, full_name=full_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash("Usuario creado. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))