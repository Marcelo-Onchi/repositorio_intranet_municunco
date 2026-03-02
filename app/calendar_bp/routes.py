from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import login_required, current_user

from . import bp


@bp.get("/")
@login_required
def index():
    connected = False
    try:
        from app.models import GoogleToken  # type: ignore

        connected = bool(GoogleToken.query.filter_by(user_id=current_user.id).first())
    except Exception:
        connected = False

    return render_template("calendar/index.html", connected=connected)


@bp.get("/connect")
@login_required
def connect():
    # MVP: aún no OAuth real, solo mensaje claro
    flash("Google Calendar: falta configurar OAuth (CLIENT_ID/SECRET) para conectar tu cuenta.", "warning")
    return redirect(url_for("calendar.index"))