from __future__ import annotations

from flask import Flask

from .extensions import db


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        """Crea todas las tablas (DEV / primera puesta en marcha)."""
        with app.app_context():
            db.create_all()
            print("OK: tablas creadas.")

    @app.cli.command("db-info")
    def db_info() -> None:
        """Muestra la DB real (para detectar DBs fantasma)."""
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        print(f"SQLALCHEMY_DATABASE_URI = {uri}")
        print(f"INSTANCE_PATH = {app.instance_path}")