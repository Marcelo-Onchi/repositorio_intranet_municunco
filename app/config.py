from __future__ import annotations

import os
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-super-simple")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    UPLOAD_PATH = Path(UPLOAD_DIR)