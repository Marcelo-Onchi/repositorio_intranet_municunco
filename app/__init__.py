from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import Config
from .extensions import db, login_manager


def create_app() -> Flask:
    # Carga variables del .env en el entorno (os.environ)
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    # uploads
    upload_path: Path = app.config["UPLOAD_PATH"]
    upload_path.mkdir(parents=True, exist_ok=True)

    # extensions
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión."
    login_manager.login_message_category = "warning"

    # blueprints
    from .auth import bp as auth_bp
    from .documents import bp as documents_bp
    from .admin import bp as admin_bp
    from .calendar_bp import bp as calendar_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(calendar_bp)

    # DB init (dev-friendly)
    with app.app_context():
        db.create_all()
        _ensure_admin_user(app)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("documents.dashboard"))
        return redirect(url_for("auth.login"))

    return app


def _ensure_admin_user(app: Flask) -> None:
    """
    Garantiza un usuario admin para desarrollo / primera puesta en marcha.

    - Lee ADMIN_EMAIL / ADMIN_PASSWORD desde entorno (.env via load_dotenv()).
    - Si no existe, lo crea.
    - Si existe, asegura rol admin y usuario activo.
    - En dev: resetea la contraseña al valor de ADMIN_PASSWORD para que siempre funcione.
    """
    from .models import User  # import local para evitar ciclos

    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD") or ""

    # Si no están en .env, no hacemos nada.
    if not admin_email or not admin_password:
        return

    # Opcional: guardar en config (sirve si luego quieres mostrarlo o usarlo en otros módulos)
    app.config["ADMIN_EMAIL"] = admin_email
    app.config["ADMIN_PASSWORD"] = admin_password

    admin_username = "admin"

    # Buscar por username o email (por si ya existía con otra combinación)
    user = User.query.filter_by(username=admin_username).first()
    if not user:
        user = User.query.filter_by(email=admin_email).first()

    if not user:
        user = User(
            username=admin_username,
            email=admin_email,
            full_name="Administrador",
            is_admin=True,
            is_active=True,
        )
        user.set_password(admin_password)
        db.session.add(user)
        db.session.commit()
        return

    # Si existe: asegurar flags + resetear contraseña (dev)
    changed = False

    if user.username != admin_username:
        user.username = admin_username
        changed = True

    if user.email != admin_email:
        user.email = admin_email
        changed = True

    if not user.is_admin:
        user.is_admin = True
        changed = True

    if not user.is_active:
        user.is_active = True
        changed = True

    # En desarrollo: aseguramos que siempre puedas entrar con la clave del .env
    user.set_password(admin_password)
    changed = True

    if changed:
        db.session.commit()