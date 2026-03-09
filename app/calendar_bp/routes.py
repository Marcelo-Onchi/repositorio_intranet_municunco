from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import GoogleToken
from app.utils.dates import parse_datetime_ddmmyyyy
from . import bp


@bp.get("/")
@login_required
def index():
    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    connected = bool(token)

    desde_raw = (request.args.get("desde", "") or "").strip()
    hasta_raw = (request.args.get("hasta", "") or "").strip()

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    desde = parse_datetime_ddmmyyyy(desde_raw) or hoy
    hasta = parse_datetime_ddmmyyyy(hasta_raw) or (desde + timedelta(days=30))

    if hasta < desde:
        desde, hasta = hasta, desde

    hasta = hasta.replace(hour=23, minute=59, second=59, microsecond=0)

    events: list[dict] = []
    if connected:
        try:
            from .google_service import list_events_range

            events = list_events_range(current_user.id, desde, hasta, max_results=100)
            current_app.logger.info("Calendar list OK: %s evento(s)", len(events))
        except Exception as ex:
            current_app.logger.exception("Calendar reminder list failed: %s", ex)
            flash("No se pudieron cargar eventos desde Google Calendar.", "warning")
            events = []

    return render_template(
        "calendar/index.html",
        connected=connected,
        redirect_uri=current_app.config.get("GOOGLE_REDIRECT_URI", ""),
        events=events,
        desde=desde_raw,
        hasta=hasta_raw,
    )


@bp.get("/connect")
@login_required
def connect():
    client_id = (current_app.config.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (current_app.config.get("GOOGLE_CLIENT_SECRET") or "").strip()
    redirect_uri = (current_app.config.get("GOOGLE_REDIRECT_URI") or "").strip()
    scopes = current_app.config.get("GOOGLE_SCOPES") or [
        "https://www.googleapis.com/auth/calendar.events"
    ]

    if not client_id or not client_secret or not redirect_uri:
        flash(
            "Falta configurar GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET o GOOGLE_REDIRECT_URI.",
            "danger",
        )
        return redirect(url_for("calendar.index"))

    state = secrets.token_urlsafe(24)
    session["google_oauth_state"] = state

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return redirect(auth_url)


@bp.get("/callback")
@login_required
def callback():
    error = (request.args.get("error") or "").strip()
    if error:
        flash(f"Google OAuth cancelado o falló: {error}", "warning")
        return redirect(url_for("calendar.index"))

    state_in = (request.args.get("state") or "").strip()
    state_expected = (session.pop("google_oauth_state", "") or "").strip()
    if not state_in or not state_expected or state_in != state_expected:
        flash("OAuth inválido: el parámetro state no coincide.", "danger")
        return redirect(url_for("calendar.index"))

    code = (request.args.get("code") or "").strip()
    if not code:
        flash("No llegó el código de autorización de Google.", "danger")
        return redirect(url_for("calendar.index"))

    client_id = (current_app.config.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (current_app.config.get("GOOGLE_CLIENT_SECRET") or "").strip()
    redirect_uri = (current_app.config.get("GOOGLE_REDIRECT_URI") or "").strip()

    if not client_id or not client_secret or not redirect_uri:
        flash("La configuración de Google OAuth está incompleta.", "danger")
        return redirect(url_for("calendar.index"))

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(token_url, data=data, timeout=15)
    except requests.RequestException as ex:
        current_app.logger.exception("Google token exchange request failed: %s", ex)
        flash("No se pudo conectar con Google para obtener el token.", "danger")
        return redirect(url_for("calendar.index"))

    if response.status_code != 200:
        current_app.logger.warning(
            "Google token exchange failed: %s | %s",
            response.status_code,
            response.text[:500],
        )
        flash("No se pudo obtener el token desde Google.", "danger")
        return redirect(url_for("calendar.index"))

    payload = response.json()

    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_in = payload.get("expires_in")
    scope = payload.get("scope")

    if not access_token:
        flash("Google no entregó access_token.", "danger")
        return redirect(url_for("calendar.index"))

    token_expiry = None
    if isinstance(expires_in, int):
        token_expiry = datetime.utcnow().replace(microsecond=0) + timedelta(seconds=expires_in)

    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        token = GoogleToken(
            user_id=current_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            scopes=scope,
        )
        db.session.add(token)
    else:
        token.access_token = access_token
        if refresh_token:
            token.refresh_token = refresh_token
        token.token_expiry = token_expiry
        token.scopes = scope

    db.session.commit()

    flash("Google Calendar conectado correctamente.", "success")
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