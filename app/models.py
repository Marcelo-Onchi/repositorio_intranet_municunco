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
        passive_deletes=True,
    )

    google_token = db.relationship(
        "GoogleToken",
        back_populates="user",
        uselist=False,
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
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

    __table_args__ = (
        db.CheckConstraint("file_size >= 0", name="ck_document_file_size_nonneg"),
        db.Index("ix_document_category_id", "category_id"),
        db.Index("ix_document_uploaded_by_id", "uploaded_by_id"),
        db.Index("ix_document_created_at", "created_at"),
        db.Index("ix_document_due_date", "due_date"),
    )

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(160), nullable=False)
    filename = db.Column(db.String(260), nullable=False)
    path = db.Column(db.String(400), nullable=False)
    file_size = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
    )
    category = db.relationship(
        "Category",
        back_populates="documents",
        lazy="joined",
    )

    uploaded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by = db.relationship(
        "User",
        back_populates="documents",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename!r}>"


class GoogleToken(db.Model):
    """
    Token OAuth Google por usuario (Calendar).
    Guardamos refresh_token para poder renovar access_token.
    """

    __tablename__ = "google_token"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    user = db.relationship(
        "User",
        back_populates="google_token",
        lazy="joined",
    )

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

    def __repr__(self) -> str:
        return f"<GoogleToken user_id={self.user_id}>"