from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # ==========================================================
    # Seguridad
    # ==========================================================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-super-simple")

    # ==========================================================
    # Base de Datos
    # ==========================================================
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # Uploads
    # ==========================================================
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    UPLOAD_PATH = (BASE_DIR / UPLOAD_DIR).resolve()

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 20 * 1024 * 1024))

    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg", "zip",
    }

    # ==========================================================
    # Admin inicial (dev)
    # ==========================================================
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # ==========================================================
    # Google OAuth
    # ==========================================================
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5000/calendar/callback",
    )
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/calendar",
    ]

    # ==========================================================
    # App general
    # ==========================================================
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Santiago")