from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import Config
from .extensions import db, login_manager, migrate


def create_app() -> Flask:
    # Carga variables del .env en el entorno (os.environ)
    load_dotenv()

    # instance_relative_config=True -> permite usar instance/config.py en server
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # uploads (normalizar a Path sí o sí)
    upload_path = Path(app.config.get("UPLOAD_PATH", "uploads"))
    upload_path.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_PATH"] = upload_path

    # extensions
    db.init_app(app)
    migrate.init_app(app, db)

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

    # Admin inicial (no debe reventar el arranque)
    with app.app_context():
        _ensure_admin_user_safe(app)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("documents.dashboard"))
        return redirect(url_for("auth.login"))

    return app


def _ensure_admin_user_safe(app: Flask) -> None:
    """
    Garantiza un usuario admin para dev / primera puesta en marcha.

    Reglas:
    - Si no hay tablas o la DB aún no está lista, NO debe reventar el arranque.
    - Usa ADMIN_EMAIL y ADMIN_PASSWORD desde .env
    """
    try:
        from sqlalchemy import inspect
        from sqlalchemy.exc import SQLAlchemyError

        from .models import User  # import local para evitar ciclos

        try:
            inspector = inspect(db.engine)
            if "user" not in inspector.get_table_names():
                return
        except SQLAlchemyError:
            # DB no disponible / credenciales malas / server caído
            return

        admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD") or ""
        if not admin_email or not admin_password:
            return

        app.config["ADMIN_EMAIL"] = admin_email
        app.config["ADMIN_PASSWORD"] = admin_password

        admin_username = "admin"

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

        # En dev: mantener clave del .env siempre vigente
        user.set_password(admin_password)
        changed = True

        if changed:
            db.session.commit()

    except Exception:
        # Si algo raro pasa, no queremos botar la app por un seed de admin
        return