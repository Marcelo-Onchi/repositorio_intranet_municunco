from __future__ import annotations

import mimetypes
from datetime import datetime, time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Category, Document
from . import bp


# =========================
# Helpers
# =========================
def _allowed_file(filename: str) -> bool:
    allowed = current_app.config.get("ALLOWED_EXTENSIONS") or set()
    if not allowed:
        return True
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed


def _parse_date_ddmmyyyy(raw: str) -> Optional[datetime]:
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _get_gc_status_and_items() -> tuple[bool, list[dict], list[dict]]:
    """
    Retorna:
      - gc_connected: bool
      - deadlines_7d: list[dict] (eventos tipo "📌 Subir:" dentro de 7 días)
      - upcoming_events: list[dict] (próximos eventos generales)

    Best-effort:
    - Si no existe GoogleToken o falla Google API, no revienta el dashboard.
    """
    gc_connected = False
    deadlines_7d: list[dict] = []
    upcoming_events: list[dict] = []

    # 1) Detectar token en BD
    try:
        from app.models import GoogleToken  # type: ignore

        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        gc_connected = bool(token)
    except Exception:
        gc_connected = False

    # 2) Si está conectado, traer info desde tu google_service.py
    if gc_connected:
        try:
            from app.calendar_bp.google_service import (
                list_upcoming_deadlines_7d,
                list_upcoming_events,
            )

            deadlines_7d = list_upcoming_deadlines_7d(current_user.id, days=7) or []
            upcoming_events = list_upcoming_events(current_user.id, days=30, max_results=5) or []
        except Exception:
            deadlines_7d = []
            upcoming_events = []

    return gc_connected, deadlines_7d, upcoming_events


# =========================
# Dashboard
# =========================
@bp.get("/dashboard")
@login_required
def dashboard():
    total_docs = Document.query.count()
    total_cats = Category.query.count()

    used_bytes = (
        db.session.query(db.func.coalesce(db.func.sum(Document.file_size), 0)).scalar() or 0
    )
    used_mb = round((used_bytes / 1024 / 1024), 2)

    last_doc = Document.query.order_by(Document.created_at.desc()).first()
    last_doc_name = last_doc.name if last_doc else "Ninguno"

    gc_connected, deadlines_7d, upcoming_events = _get_gc_status_and_items()

    return render_template(
        "dashboard.html",
        total_docs=total_docs,
        total_cats=total_cats,
        used_mb=used_mb,
        last_doc_name=last_doc_name,
        gc_connected=gc_connected,
        deadlines_7d=deadlines_7d,
        upcoming_events=upcoming_events,
    )


# =========================
# Listado / Explorer
# =========================
@bp.get("/")
@login_required
def index():
    q = (request.args.get("q") or "").strip()
    cat_id = (request.args.get("category_id") or "").strip()

    desde_raw = request.args.get("desde") or ""
    hasta_raw = request.args.get("hasta") or ""

    desde_dt = _parse_date_ddmmyyyy(desde_raw)
    hasta_dt = _parse_date_ddmmyyyy(hasta_raw)

    query = Document.query

    if q:
        like = f"%{q.lower()}%"
        query = query.filter(db.func.lower(Document.name).like(like))

    if cat_id.isdigit():
        query = query.filter(Document.category_id == int(cat_id))

    if desde_dt:
        query = query.filter(Document.created_at >= datetime.combine(desde_dt.date(), time.min))
    if hasta_dt:
        query = query.filter(Document.created_at <= datetime.combine(hasta_dt.date(), time.max))

    docs = query.order_by(Document.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "documents/index.html",
        docs=docs,
        categories=categories,
        q=q,
        category_id=cat_id,
        desde=desde_raw,
        hasta=hasta_raw,
    )


# =========================
# Subida
# =========================
@bp.get("/upload")
@login_required
def upload():
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("documents/upload.html", categories=categories)


@bp.post("/upload")
@login_required
def upload_post():
    files = request.files.getlist("files")
    category_id_raw = (request.form.get("category_id") or "").strip()
    category_id = int(category_id_raw) if category_id_raw.isdigit() else None

    if not files or all((f is None or not f.filename) for f in files):
        flash("Selecciona al menos un archivo.", "warning")
        return redirect(url_for("documents.upload"))

    upload_path = Path(current_app.config["UPLOAD_PATH"])
    upload_path.mkdir(parents=True, exist_ok=True)

    saved = 0
    rejected = 0

    for f in files:
        if not f or not f.filename:
            continue

        original = secure_filename(f.filename)
        if not original:
            rejected += 1
            continue

        if not _allowed_file(original):
            rejected += 1
            continue

        ext = ""
        if "." in original:
            ext = "." + original.rsplit(".", 1)[1].lower()

        storage_name = f"{uuid4().hex}{ext}"
        disk_path = upload_path / storage_name

        f.save(disk_path)

        size = disk_path.stat().st_size if disk_path.exists() else 0

        doc = Document(
            name=Path(original).stem[:160] or original[:160],
            filename=original[:260],
            path=str(disk_path),
            file_size=int(size),
            category_id=category_id,
            uploaded_by_id=current_user.id,
        )
        db.session.add(doc)
        saved += 1

    db.session.commit()

    if saved:
        flash(f"✅ Subida completada: {saved} archivo(s).", "success")
    if rejected:
        flash(f"⚠️ {rejected} archivo(s) rechazado(s) por nombre/extensión.", "warning")

    return redirect(url_for("documents.index"))


# =========================
# Preview / Download
# =========================
@bp.get("/preview/<int:doc_id>")
@login_required
def preview(doc_id: int):
    doc = Document.query.get_or_404(doc_id)

    path = Path(doc.path)
    if not path.exists():
        flash("Archivo no encontrado en disco.", "danger")
        return redirect(url_for("documents.index"))

    mime, _ = mimetypes.guess_type(doc.filename)
    mime = mime or "application/octet-stream"

    is_inline = mime.startswith("image/") or mime == "application/pdf"
    if not is_inline:
        flash("Vista previa disponible solo para PDF e imágenes. Descarga para abrir.", "info")
        return redirect(url_for("documents.index"))

    return send_file(path, mimetype=mime, as_attachment=False, download_name=doc.filename)


@bp.get("/download/<int:doc_id>")
@login_required
def download(doc_id: int):
    doc = Document.query.get_or_404(doc_id)
    path = Path(doc.path)
    if not path.exists():
        flash("Archivo no encontrado en disco.", "danger")
        return redirect(url_for("documents.index"))

    mime, _ = mimetypes.guess_type(doc.filename)
    mime = mime or "application/octet-stream"
    return send_file(path, mimetype=mime, as_attachment=True, download_name=doc.filename)


# =========================
# Delete
# =========================
@bp.post("/delete/<int:doc_id>")
@login_required
def delete(doc_id: int):
    if not current_user.is_admin:
        abort(403)

    doc = Document.query.get_or_404(doc_id)
    path = Path(doc.path)

    db.session.delete(doc)
    db.session.commit()

    # borrar archivo (best-effort)
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass

    flash("Documento eliminado.", "success")
    return redirect(url_for("documents.index"))