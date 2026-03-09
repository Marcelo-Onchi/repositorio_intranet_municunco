from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # ==========================================================
    # Seguridad
    # ==========================================================
    SECRET_KEY = os.getenv("SECRET_KEY", "municunco-dev-2026")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), default=False)

    # ==========================================================
    # Base de datos
    # ==========================================================
    DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{(INSTANCE_DIR / 'local.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ==========================================================
    # Uploads
    # ==========================================================
    UPLOAD_DIR = (os.getenv("UPLOAD_DIR") or "uploads").strip()
    UPLOAD_PATH = UPLOAD_DIR

    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", str(20 * 1024 * 1024))
    )

    ALLOWED_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "png",
        "jpg",
        "jpeg",
        "zip",
    }

    # ==========================================================
    # Admin inicial
    # ==========================================================
    ADMIN_USERNAME = (os.getenv("ADMIN_USERNAME") or "admin").strip().lower()
    ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # ==========================================================
    # Google OAuth
    # ==========================================================
    GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
    GOOGLE_REDIRECT_URI = (
        os.getenv("GOOGLE_REDIRECT_URI")
        or "http://127.0.0.1:8000/calendar/callback"
    ).strip()

    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/calendar.events",
    ]

    # ==========================================================
    # App general
    # ==========================================================
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Santiago").strip()

    # ==========================================================
    # Plantillas DOCX / PDF
    # ==========================================================
    DOCX_TEMPLATES_DIR = (os.getenv("DOCX_TEMPLATES_DIR") or "").strip()
    OFICIO_TEMPLATE_FILENAME = (
        os.getenv("OFICIO_TEMPLATE_FILENAME") or "oficio_respuesta_template_v1.docx"
    ).strip()
    LIBREOFFICE_BIN = (os.getenv("LIBREOFFICE_BIN") or "soffice").strip()

    # ==========================================================
    # Static cache-buster
    # ==========================================================
    STATIC_VERSION = int(os.getenv("STATIC_VERSION", "6"))