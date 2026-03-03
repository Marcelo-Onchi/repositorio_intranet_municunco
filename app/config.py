from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # ==========================================================
    # Seguridad
    # ==========================================================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-super-simple")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    # ==========================================================
    # Base de Datos
    # ==========================================================
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db").strip()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # ==========================================================
    # Uploads
    # ==========================================================
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads").strip()
    UPLOAD_PATH = UPLOAD_DIR  # string/relativo para que __init__ lo resuelva

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(20 * 1024 * 1024)))

    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg", "zip",
    }

    # ==========================================================
    # Admin inicial (dev)
    # ==========================================================
    ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # ==========================================================
    # Google OAuth (Calendar)
    # ==========================================================
    GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()

    # OJO: debe coincidir con lo registrado en Google Cloud
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5000/calendar/callback",
    ).strip()

    # Scopes: recomendado para tu caso (crear/editar eventos, no todo el calendar)
    # Si ya tienes el full y lo quieres mantener, cambia a "https://www.googleapis.com/auth/calendar"
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/calendar.events",
    ]

    # ==========================================================
    # App general
    # ==========================================================
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Santiago").strip()

    # ==========================================================
    # Static cache-buster (CSS/JS)
    # ==========================================================
    # Sube este número/string cada vez que cambies CSS/JS y el navegador no refresque.
    STATIC_VERSION = 2