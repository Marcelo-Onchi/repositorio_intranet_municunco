from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import GoogleToken
from . import bp


def _get_scopes() -> list[str]:
    scopes = current_app.config.get("GOOGLE_SCOPES") or []
    if not scopes:
        scopes = ["https://www.googleapis.com/auth/calendar"]
    return scopes


def _google_oauth_authorize_url() -> str:
    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI", "")
    scopes = _get_scopes()

    if not client_id or not redirect_uri:
        return ""

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",  # refresh_token
        "prompt": "consent",       # fuerza refresh_token al conectar
        "include_granted_scopes": "true",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def _exchange_code_for_token(code: str) -> dict | None:
    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI", "")

    if not client_id or not client_secret or not redirect_uri:
        return None

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    r = requests.post(token_url, data=data, timeout=15)
    if r.status_code != 200:
        return None

    return r.json()


@bp.get("/")
@login_required
def index():
    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    connected = bool(token)

    events: list[dict] = []
    if connected:
        # Best-effort: si falla Google, no revienta la página
        try:
            from app.calendar_bp.google_service import list_upcoming_events

            events = list_upcoming_events(
                user_id=current_user.id,
                days=30,
                max_results=15,
            ) or []
        except Exception:
            flash("No se pudieron cargar eventos desde Google Calendar (revisa conexión/permisos).", "warning")
            events = []

    return render_template(
        "calendar/index.html",
        connected=connected,
        redirect_uri=current_app.config.get("GOOGLE_REDIRECT_URI", ""),
        events=events,
    )


@bp.get("/connect")
@login_required
def connect():
    url = _google_oauth_authorize_url()
    if not url:
        flash("Falta configurar GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI.", "danger")
        return redirect(url_for("calendar.index"))
    return redirect(url)


@bp.get("/callback")
@login_required
def callback():
    err = (request.args.get("error") or "").strip()
    if err:
        flash(f"Google OAuth cancelado o falló: {err}", "warning")
        return redirect(url_for("calendar.index"))

    code = (request.args.get("code") or "").strip()
    if not code:
        flash("No llegó el código de autorización de Google.", "danger")
        return redirect(url_for("calendar.index"))

    payload = _exchange_code_for_token(code)
    if not payload:
        flash("No se pudo obtener token desde Google (revisa credenciales y redirect URI).", "danger")
        return redirect(url_for("calendar.index"))

    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")  # puede venir vacío si ya se concedió antes
    expires_in = payload.get("expires_in")
    scope = payload.get("scope")

    if not access_token:
        flash("Google no entregó access_token.", "danger")
        return redirect(url_for("calendar.index"))

    expiry = None
    if isinstance(expires_in, int):
        expiry = datetime.utcnow().replace(microsecond=0) + timedelta(seconds=expires_in)

    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        token = GoogleToken(
            user_id=current_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scopes=scope,
        )
        db.session.add(token)
    else:
        token.access_token = access_token
        # No pisar refresh_token si viene vacío
        if refresh_token:
            token.refresh_token = refresh_token
        token.token_expiry = expiry
        token.scopes = scope

    db.session.commit()

    flash("✅ Google Calendar conectado correctamente.", "success")
    return redirect(url_for("calendar.index"))


@bp.post("/disconnect")
@login_required
def disconnect():
    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if token:
        db.session.delete(token)
        db.session.commit()

    flash("Google Calendar desconectado.", "info")
    return redirect(url_for("calendar.index"))