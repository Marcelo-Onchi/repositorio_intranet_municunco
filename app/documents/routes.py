from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Category, Document
from . import bp


@bp.get("/")
@login_required
def index():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    cats = Category.query.order_by(Category.name.asc()).all()
    return render_template("documents/index.html", docs=docs, cats=cats)


@bp.get("/dashboard")
@login_required
def dashboard():
    total_docs = Document.query.count()
    total_cats = Category.query.count()

    last_doc = Document.query.order_by(Document.created_at.desc()).first()
    last_doc_name = last_doc.name if last_doc else "Ninguno"

    used_bytes = sum(d.file_size for d in Document.query.all())
    used_mb = round(used_bytes / (1024 * 1024), 2) if used_bytes else 0.0

    # MVP: aun no OAuth real
    gc_connected = False

    return render_template(
        "dashboard.html",
        total_docs=total_docs,
        total_cats=total_cats,
        used_mb=used_mb,
        last_doc_name=last_doc_name,
        gc_connected=gc_connected,
    )


@bp.get("/upload")
@login_required
def upload():
    cats = Category.query.order_by(Category.name.asc()).all()
    return render_template("documents/upload.html", cats=cats)


@bp.post("/upload")
@login_required
def upload_post():
    name = (request.form.get("name") or "").strip()
    category_id_raw = (request.form.get("category_id") or "").strip() or None

    file = request.files.get("file")
    if not name:
        flash("Falta el nombre del documento.", "warning")
        return redirect(url_for("documents.upload"))

    if not file or not file.filename:
        flash("Selecciona un archivo.", "warning")
        return redirect(url_for("documents.upload"))

    upload_dir: Path = current_app.config["UPLOAD_PATH"]
    original = secure_filename(file.filename)
    ext = os.path.splitext(original)[1].lower()

    stored = f"{uuid.uuid4().hex}{ext}"
    save_path = upload_dir / stored
    file.save(save_path)

    size = save_path.stat().st_size if save_path.exists() else 0

    category_id = int(category_id_raw) if category_id_raw else None

    doc = Document(
        name=name,
        filename=stored,
        path=str(Path(current_app.config["UPLOAD_DIR"]) / stored),
        file_size=size,
        category_id=category_id,
        uploaded_by_id=current_user.id,
    )
    db.session.add(doc)
    db.session.commit()

    flash("Documento subido correctamente ✅", "success")
    return redirect(url_for("documents.index"))


@bp.get("/download/<int:doc_id>")
@login_required
def download(doc_id: int):
    doc = db.session.get(Document, doc_id)
    if not doc:
        flash("Documento no encontrado.", "danger")
        return redirect(url_for("documents.index"))

    upload_dir: Path = current_app.config["UPLOAD_PATH"]
    return send_from_directory(upload_dir, doc.filename, as_attachment=True)