from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.models import User
from . import bp


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not user.check_password(password):
        flash("Credenciales inválidas.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Bienvenido/a ✅", "success")

    nxt = request.args.get("next")
    return redirect(nxt or url_for("documents.dashboard"))


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))