from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id: str) -> Optional["User"]:
    if not user_id:
        return None
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


class User(db.Model, UserMixin):
    """
    Usuario del sistema.

    Reglas:
    - Login por username (sin @)
    - Registro exige username + email + full_name + password
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(32), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    documents = db.relationship(
        "Document",
        back_populates="uploaded_by",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    documents = db.relationship(
        "Document",
        back_populates="category",
        lazy="select",
    )


class Document(db.Model):
    __tablename__ = "document"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(160), nullable=False)
    filename = db.Column(db.String(260), nullable=False)
    path = db.Column(db.String(400), nullable=False)
    file_size = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Fecha límite opcional (para vencimientos)
    due_date = db.Column(db.Date, nullable=True)

    # Id del evento de Google (opcional, por si después lo implementamos)
    gc_event_id = db.Column(db.String(128), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    category = db.relationship("Category", back_populates="documents", lazy="joined")

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_by = db.relationship("User", back_populates="documents", lazy="joined")


class GoogleToken(db.Model):
    """
    Token OAuth de Google Calendar por usuario.
    """

    __tablename__ = "google_token"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    user = db.relationship("User", lazy="joined")

    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)

    token_expiry = db.Column(db.DateTime, nullable=True)
    scopes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )