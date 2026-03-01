from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import Config
from .extensions import db, login_manager


def create_app() -> Flask:
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

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("documents.dashboard"))
        return redirect(url_for("auth.login"))

    return app