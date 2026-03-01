from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from . import bp


@bp.get("/")
@login_required
def index():
    return render_template("calendar/index.html", connected=False)


@bp.get("/connect")
@login_required
def connect():
    flash("Google Calendar (MVP): falta configurar OAuth real (CLIENT_ID/SECRET).", "warning")
    return redirect(url_for("calendar.index"))