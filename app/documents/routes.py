from __future__ import annotations

import mimetypes
import shutil
import subprocess
import tempfile
import time as time_mod
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from docx import Document as DocxDocument
from docx.shared import Pt
from flask import abort, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Category, Document, GoogleToken
from . import bp
from .forms import FillOficioForm


# =========================================================
# Helpers
# =========================================================
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
        return bool(GoogleToken.query.filter_by(user_id=user_id).first())
    except Exception:
        return False


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
        ok, err = create_deadline_event(
            user_id=current_user.id,
            title=(title or "")[:120],
            description=description,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        if not ok and err:
            try:
                current_app.logger.warning("Calendar reminder failed: %s", err)
            except Exception:
                pass
        return bool(ok)
    except Exception as e:
        try:
            current_app.logger.warning("Calendar best-effort exception: %s", e)
        except Exception:
            pass
        return False


def _is_previewable(filename: str) -> bool:
    fn = (filename or "").lower()
    return fn.endswith((".pdf", ".png", ".jpg", ".jpeg", ".webp"))


def _is_docx(filename: str) -> bool:
    return (filename or "").lower().endswith(".docx")


def _ddmmyyyy_to_slash(raw_dd_mm_yyyy: str) -> str:
    """
    UI: dd-mm-aaaa  -> Documento: dd/mm/aaaa
    """
    raw = (raw_dd_mm_yyyy or "").strip()
    if len(raw) == 10 and raw[2] == "-" and raw[5] == "-":
        return raw.replace("-", "/")
    return raw


def _safe_slug(value: str) -> str:
    raw = (value or "").strip()
    out = []
    for ch in raw:
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
    return "".join(out)[:60] or "generado"


def _generated_dir() -> Path:
    """
    Carpeta persistente para PDFs generados (para guardarlos como Document).
    """
    base = Path(current_app.config["UPLOAD_PATH"])
    gen = base / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    return gen


def _templates_dir() -> Path:
    """
    Carpeta persistente para plantillas DOCX fijas.
    Por defecto: uploads/templates
    """
    base = Path(current_app.config["UPLOAD_PATH"])
    configured = (current_app.config.get("DOCX_TEMPLATES_DIR") or "").strip()
    if configured:
        return Path(configured)
    return base / "templates"


def _oficio_template_path() -> Path:
    """
    Ruta final al DOCX oficial.
    """
    return _templates_dir() / (
        current_app.config.get("OFICIO_TEMPLATE_FILENAME") or "oficio_respuesta_template_v1.docx"
    )


def _ensure_default_font(doc: DocxDocument, font_name: str = "Arial", font_size_pt: int = 11) -> None:
    """
    Asegura que el estilo Normal del documento sea Arial 11.
    """
    try:
        style = doc.styles["Normal"]
        style.font.name = font_name
        style.font.size = Pt(font_size_pt)
    except Exception:
        pass


def _replace_in_paragraph_runs(paragraph, mapping: dict[str, str]) -> None:
    """
    Reemplaza placeholders dentro de runs SIN reasignar paragraph.text.
    Preserva formato de la plantilla.

    Nota: para máxima estabilidad, en la plantilla los placeholders deberían estar completos
    (no cortados por formato en múltiples runs). Aun así, esto funciona bien en la práctica.
    """
    if not paragraph.runs:
        return

    full_text = "".join(run.text for run in paragraph.runs)
    if not full_text:
        return

    changed = False
    for k, v in mapping.items():
        if k in full_text:
            full_text = full_text.replace(k, v)
            changed = True

    if not changed:
        return

    paragraph.runs[0].text = full_text
    for r in paragraph.runs[1:]:
        r.text = ""


def _docx_replace_text(doc: DocxDocument, mapping: dict[str, str]) -> None:
    """
    Reemplazo de placeholders manteniendo formato.
    """
    for p in doc.paragraphs:
        _replace_in_paragraph_runs(p, mapping)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _replace_in_paragraph_runs(p, mapping)


def _docx_force_bold_placeholders(
    doc: DocxDocument,
    keys: set[str],
    font_name: str = "Arial",
    font_size_pt: int = 11,
) -> None:
    """
    Aplica Arial 11 + negrita SOLO a los runs donde esté el placeholder.
    (Ideal si el placeholder no está partido en múltiples runs)
    """

    def _apply_on_paragraph(paragraph) -> None:
        for run in paragraph.runs:
            if not run.text:
                continue
            for k in keys:
                if k in run.text:
                    try:
                        run.bold = True
                        run.font.name = font_name
                        run.font.size = Pt(font_size_pt)
                    except Exception:
                        pass
                    break

    for p in doc.paragraphs:
        _apply_on_paragraph(p)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _apply_on_paragraph(p)


def _convert_docx_to_pdf(docx_path: Path, out_dir: Path) -> Path:
    """
    Convierte DOCX -> PDF.
    Prioridad:
      1) LibreOffice (Ubuntu recomendado)
      2) docx2pdf (Windows + Word instalado)

    Windows:
    - Inicializa COM (CoInitialize) para docx2pdf
    - Espera a que el PDF quede liberado (evita WinError 32)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) LibreOffice
    lo_bin = (current_app.config.get("LIBREOFFICE_BIN") or "soffice").strip()
    lo_real = shutil.which(lo_bin) or shutil.which("soffice")
    if lo_real:
        cmd = [
            lo_real,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"LibreOffice falló al convertir a PDF: {proc.stderr or proc.stdout}")

        pdf_path = out_dir / f"{docx_path.stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError("No se generó el PDF (salida inesperada de LibreOffice).")
        return pdf_path

    # 2) docx2pdf + Word
    try:
        from docx2pdf import convert  # type: ignore
    except Exception:
        raise RuntimeError(
            "No hay convertidor disponible. En servidor Ubuntu instala LibreOffice. "
            "En Windows instala docx2pdf + Microsoft Word."
        )

    pdf_path = out_dir / f"{docx_path.stem}.pdf"

    # COM init (soluciona -2147221008 CoInitialize)
    try:
        import pythoncom  # type: ignore

        pythoncom.CoInitialize()
        coinit = True
    except Exception:
        coinit = False

    try:
        convert(str(docx_path), str(pdf_path))
    except Exception as e:
        raise RuntimeError(f"docx2pdf falló (¿Word instalado?): {e}")
    finally:
        if coinit:
            try:
                import pythoncom  # type: ignore

                pythoncom.CoUninitialize()
            except Exception:
                pass

    # Espera a que Word suelte el archivo
    for _ in range(30):
        if pdf_path.exists():
            try:
                with open(pdf_path, "rb"):
                    pass
                return pdf_path
            except OSError:
                time_mod.sleep(0.15)

    if not pdf_path.exists():
        raise RuntimeError("No se generó el PDF con docx2pdf.")

    raise RuntimeError("El PDF fue generado pero quedó bloqueado por Word. Reintenta en unos segundos.")


def _send_pdf_from_temp(pdf_path: Path, download_name: str):
    """
    Solución WinError 32:
    - Copia el PDF a un temp persistente (delete=False)
    - Envía ese archivo
    - Lo elimina al cerrar la respuesta
    """
    tmp = tempfile.NamedTemporaryFile(prefix="municunco_dl_", suffix=".pdf", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    last_err: Exception | None = None
    for _ in range(20):
        try:
            shutil.copyfile(pdf_path, tmp_path)
            last_err = None
            break
        except Exception as e:
            last_err = e
            time_mod.sleep(0.15)

    if last_err is not None:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        raise last_err

    resp = send_file(
        tmp_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name,
    )

    @resp.call_on_close
    def _cleanup():
        try:
            tmp_path.unlink(missing_ok=True)
        except TypeError:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
        except Exception:
            pass

    return resp


# =========================================================
# Rutas
# =========================================================
@bp.get("/dashboard")
@login_required
def dashboard():
    total_docs = Document.query.count()
    total_cats = Category.query.count()

    used_bytes = db.session.query(db.func.coalesce(db.func.sum(Document.file_size), 0)).scalar() or 0
    used_mb = round((used_bytes / 1024 / 1024), 2)

    last_doc = Document.query.order_by(Document.created_at.desc()).first()
    last_doc_name = (last_doc.filename or last_doc.name) if last_doc else "Ninguno"

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
        last_doc_name=last_doc_name or "Ninguno",
        gc_connected=gc_connected,
        due_soon_docs=due_soon_docs,
        overdue_count=overdue_count,
    )


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
        if not original or not _allowed_file(original):
            rejected += 1
            continue

        ext = "." + original.rsplit(".", 1)[1].lower() if "." in original else ""
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


@bp.get("/preview/<int:doc_id>")
@login_required
def preview(doc_id: int):
    doc = Document.query.get_or_404(doc_id)
    path = Path(doc.path)
    if not path.exists():
        abort(404, description="Archivo no encontrado en disco.")

    if not _is_previewable(doc.filename):
        abort(415, description="Vista previa disponible solo para PDF e imágenes.")

    mime, _ = mimetypes.guess_type(doc.filename)
    return send_file(path, mimetype=mime or "application/octet-stream", as_attachment=False, download_name=doc.filename)


@bp.get("/download/<int:doc_id>")
@login_required
def download(doc_id: int):
    doc = Document.query.get_or_404(doc_id)
    path = Path(doc.path)
    if not path.exists():
        flash("Archivo no encontrado en disco.", "danger")
        return redirect(url_for("documents.index"))

    mime, _ = mimetypes.guess_type(doc.filename)
    return send_file(path, mimetype=mime or "application/octet-stream", as_attachment=True, download_name=doc.filename)


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
        pass

    flash("Documento eliminado.", "success")
    return redirect(url_for("documents.index"))


# =========================================================
# Oficio oficial (plantilla fija en uploads/templates) -> PDF
# URL: /documents/oficio
#
# IMPORTANTE:
# - La plantilla DOCX debe tener estos placeholders:
#   {{NUM_SOLICITUD}}, {{FECHA_SOLICITUD}}, {{DE_NOMBRE}}, {{DE_CARGO}}, {{A_NOMBRE}},
#   {{TENOR_LITERAL}}, {{RESPUESTA}}
# =========================================================
@bp.get("/oficio")
@login_required
def oficio():
    tpl_path = _oficio_template_path()
    if not tpl_path.exists():
        flash(f"No se encontró la plantilla oficial en: {tpl_path}", "danger")
        return redirect(url_for("documents.index"))

    form = FillOficioForm(
        numero_solicitud="MU071T0001762",
        fecha_solicitud="20-01-2026",
        de_nombre="NELSON OLIVERA STAUB",
        de_cargo="ADMINISTRADOR MUNICIPAL",
        a_nombre="CRISTINA INOSTROZA DELGADO",
        tenor_literal="texto de prueba",
        respuesta="respuesta de prueba",
        guardar_pdf=True,
    )
    return render_template("documents/oficio.html", form=form)


@bp.post("/oficio")
@login_required
def oficio_post():
    tpl_path = _oficio_template_path()
    if not tpl_path.exists():
        flash(f"No se encontró la plantilla oficial en: {tpl_path}", "danger")
        return redirect(url_for("documents.index"))

    form = FillOficioForm()
    if not form.validate_on_submit():
        return render_template("documents/oficio.html", form=form), 400

    numero = (form.numero_solicitud.data or "").strip()
    fecha_doc = _ddmmyyyy_to_slash(form.fecha_solicitud.data or "")

    de_nombre = (form.de_nombre.data or "").strip()
    de_cargo = (form.de_cargo.data or "").strip()
    a_nombre = (form.a_nombre.data or "").strip()

    tenor = (form.tenor_literal.data or "").strip()
    resp = (form.respuesta.data or "").strip()
    guardar_pdf = bool(form.guardar_pdf.data)

    mapping = {
        "{{NUM_SOLICITUD}}": numero,
        "{{FECHA_SOLICITUD}}": fecha_doc,
        "{{DE_NOMBRE}}": de_nombre,
        "{{DE_CARGO}}": de_cargo,
        "{{A_NOMBRE}}": a_nombre,
        "{{TENOR_LITERAL}}": tenor,
        "{{RESPUESTA}}": resp,
    }

    safe_num = _safe_slug(numero)

    try:
        with tempfile.TemporaryDirectory(prefix="municunco_oficio_") as tmp:
            tmp_dir = Path(tmp)

            d = DocxDocument(str(tpl_path))
            _ensure_default_font(d, "Arial", 11)

            # 1) Reemplazar placeholders preservando formato base
            _docx_replace_text(d, mapping)

            # 2) Forzar Arial 11 + negrita SOLO en DE/A/CARGO (placeholders)
            _docx_force_bold_placeholders(
                d,
                keys={"{{DE_NOMBRE}}", "{{DE_CARGO}}", "{{A_NOMBRE}}"},
                font_name="Arial",
                font_size_pt=11,
            )

            out_docx = tmp_dir / f"oficio_{safe_num}.docx"
            d.save(str(out_docx))

            tmp_pdf = _convert_docx_to_pdf(out_docx, tmp_dir)

            if guardar_pdf:
                gen_dir = _generated_dir()
                final_name = f"Oficio_{safe_num}_{uuid4().hex[:8]}.pdf"
                final_path = gen_dir / final_name
                shutil.copyfile(tmp_pdf, final_path)

                size = final_path.stat().st_size if final_path.exists() else 0
                new_doc = Document(
                    name=f"Oficio_{safe_num}"[:160],
                    filename=final_name[:260],
                    path=str(final_path),
                    file_size=int(size),
                    category_id=None,
                    uploaded_by_id=current_user.id,
                    due_date=None,
                )
                db.session.add(new_doc)
                db.session.commit()

                flash("✅ PDF generado y guardado en el repositorio.", "success")

                return send_file(
                    final_path,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=final_name,
                )

            # ✅ FIX WinError 32 cuando NO se guarda: servimos una copia temporal independiente
            return _send_pdf_from_temp(
                tmp_pdf,
                download_name=f"Oficio_{safe_num}.pdf",
            )

    except Exception as e:
        try:
            current_app.logger.exception("Oficio generation failed: %s", e)
        except Exception:
            pass
        flash(f"No se pudo generar el PDF: {e}", "danger")
        return render_template("documents/oficio.html", form=form), 500