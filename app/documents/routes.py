from __future__ import annotations

import mimetypes
from datetime import date, datetime, time, timedelta
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
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Category, Document, GoogleToken
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

    # Explorer usa dd-mm-aaaa (y aceptamos yyyy-mm-dd por compatibilidad)
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_due_date(raw: str) -> Optional[date]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d-%m-%Y").date()
    except ValueError:
        return None


def _google_connected(user_id: int) -> bool:
    try:
        token = GoogleToken.query.filter_by(user_id=user_id).first()
        return bool(token)
    except Exception:
        return False


def _iso_local(dt_naive: datetime) -> str:
    """
    Genera ISO8601 con offset usando ZoneInfo (Python 3.9+).
    Si algo falla, retorna iso sin tz.
    """
    tz_name = current_app.config.get("APP_TIMEZONE", "America/Santiago")
    try:
        from zoneinfo import ZoneInfo

        aware = dt_naive.replace(tzinfo=ZoneInfo(tz_name))
        return aware.isoformat()
    except Exception:
        return dt_naive.isoformat()


def _create_calendar_deadline_best_effort(title: str, due: date) -> bool:
    """
    Best-effort: crea evento a las 09:00 hora local (1h duración).
    Si falla, retorna False sin romper el flujo.
    """
    try:
        from app.calendar_bp.google_service import create_deadline_event  # type: ignore
    except Exception:
        return False

    start_dt = datetime.combine(due, time(9, 0))
    end_dt = start_dt + timedelta(hours=1)

    description = (
        "Recordatorio creado desde Repositorio Municunco.\n"
        "Tip: Mantén los documentos al día para auditoría y trazabilidad."
    )

    try:
        return bool(
            create_deadline_event(
                user_id=current_user.id,
                title=(title or "")[:120],
                description=description,
                start_iso=_iso_local(start_dt),
                end_iso=_iso_local(end_dt),
            )
        )
    except Exception:
        return False


def _is_previewable(filename: str) -> bool:
    fn = (filename or "").lower()
    return fn.endswith(".pdf") or fn.endswith(".png") or fn.endswith(".jpg") or fn.endswith(".jpeg") or fn.endswith(".webp")


# =========================
# Dashboard
# =========================
@bp.get("/dashboard")
@login_required
def dashboard():
    total_docs = Document.query.count()
    total_cats = Category.query.count()

    used_bytes = db.session.query(db.func.coalesce(db.func.sum(Document.file_size), 0)).scalar() or 0
    used_mb = round((used_bytes / 1024 / 1024), 2)

    last_doc = Document.query.order_by(Document.created_at.desc()).first()

    # Mostramos filename (lo que el usuario entiende). Si no existe, cae a name.
    if last_doc:
        last_doc_name = last_doc.filename or last_doc.name or "Ninguno"
    else:
        last_doc_name = "Ninguno"

    gc_connected = _google_connected(current_user.id)

    today = date.today()
    until = today + timedelta(days=7)

    due_soon_docs = (
        Document.query.filter(Document.due_date.isnot(None))
        .filter(Document.due_date >= today)
        .filter(Document.due_date <= until)
        .order_by(Document.due_date.asc())
        .limit(8)
        .all()
    )

    overdue_count = (
        Document.query.filter(Document.due_date.isnot(None))
        .filter(Document.due_date < today)
        .count()
    )

    return render_template(
        "dashboard.html",
        total_docs=total_docs,
        total_cats=total_cats,
        used_mb=used_mb,
        last_doc_name=last_doc_name,
        gc_connected=gc_connected,
        due_soon_docs=due_soon_docs,
        overdue_count=overdue_count,
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

    due_status = (request.args.get("due_status") or "all").strip()
    sort = (request.args.get("sort") or "created_desc").strip()

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

    # Filtro vencimientos
    today = date.today()
    if due_status == "has_due":
        query = query.filter(Document.due_date.isnot(None))
    elif due_status == "no_due":
        query = query.filter(Document.due_date.is_(None))
    elif due_status == "overdue":
        query = query.filter(Document.due_date.isnot(None)).filter(Document.due_date < today)
    elif due_status == "due_soon":
        query = (
            query.filter(Document.due_date.isnot(None))
            .filter(Document.due_date >= today)
            .filter(Document.due_date <= (today + timedelta(days=7)))
        )

    # Orden
    if sort == "due_asc":
        query = query.order_by(
            db.case((Document.due_date.is_(None), 1), else_=0),
            Document.due_date.asc(),
            Document.created_at.desc(),
        )
    elif sort == "due_desc":
        query = query.order_by(
            db.case((Document.due_date.is_(None), 1), else_=0),
            Document.due_date.desc(),
            Document.created_at.desc(),
        )
    else:
        query = query.order_by(Document.created_at.desc())

    docs = query.all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "documents/index.html",
        docs=docs,
        categories=categories,
        q=q,
        category_id=cat_id,
        desde=desde_raw,
        hasta=hasta_raw,
        due_status=due_status,
        sort=sort,
    )


# =========================
# Subida
# =========================
@bp.get("/upload")
@login_required
def upload():
    categories = Category.query.order_by(Category.name.asc()).all()
    gc_connected = _google_connected(current_user.id)
    return render_template("documents/upload.html", categories=categories, gc_connected=gc_connected)


@bp.post("/upload")
@login_required
def upload_post():
    files = request.files.getlist("files")
    category_id_raw = (request.form.get("category_id") or "").strip()
    category_id = int(category_id_raw) if category_id_raw.isdigit() else None

    due_raw = request.form.get("due_date") or ""
    due = _parse_due_date(due_raw)

    # Server-side: no fechas pasadas
    if due and due < date.today():
        flash("La fecha límite no puede ser en el pasado.", "warning")
        return redirect(url_for("documents.upload"))

    if not files or all((f is None or not f.filename) for f in files):
        flash("Selecciona al menos un archivo.", "warning")
        return redirect(url_for("documents.upload"))

    upload_path = Path(current_app.config["UPLOAD_PATH"])
    upload_path.mkdir(parents=True, exist_ok=True)

    saved = 0
    rejected = 0
    created_calendar = 0
    calendar_failed = 0

    gc_connected = _google_connected(current_user.id)

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
            due_date=due,
        )
        db.session.add(doc)
        saved += 1

        # Best-effort: evento por archivo si hay fecha y GC está conectado
        if due and gc_connected:
            ok = _create_calendar_deadline_best_effort(title=doc.filename, due=due)
            if ok:
                created_calendar += 1
            else:
                calendar_failed += 1

    db.session.commit()

    if saved:
        flash(f"✅ Subida completada: {saved} archivo(s).", "success")
    if rejected:
        flash(f"⚠️ {rejected} archivo(s) rechazado(s) por nombre/extensión.", "warning")

    if due and gc_connected:
        if created_calendar:
            flash(f"🗓️ Recordatorios creados en Google Calendar: {created_calendar}.", "info")
        if calendar_failed:
            flash(f"⚠️ No se pudieron crear {calendar_failed} recordatorio(s) en Google Calendar.", "warning")

    return redirect(url_for("documents.index"))


# =========================
# Preview / Download
# =========================
@bp.get("/preview/<int:doc_id>")
@login_required
def preview(doc_id: int):
    """
    IMPORTANTE:
    - Nunca hacer redirect aquí, porque el iframe termina cargando HTML del sistema.
    - Solo permitimos inline para PDF e imágenes.
    """
    doc = Document.query.get_or_404(doc_id)

    path = Path(doc.path)
    if not path.exists():
        abort(404, description="Archivo no encontrado en disco.")

    if not _is_previewable(doc.filename):
        abort(415, description="Vista previa disponible solo para PDF e imágenes.")

    mime, _ = mimetypes.guess_type(doc.filename)
    mime = mime or "application/octet-stream"
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

    try:
        if path.exists():
            path.unlink()
    except Exception:
        # Best-effort: si no se puede borrar en disco, igual ya se eliminó en DB.
        pass

    flash("Documento eliminado.", "success")
    return redirect(url_for("documents.index"))