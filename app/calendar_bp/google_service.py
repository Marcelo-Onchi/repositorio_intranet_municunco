from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.extensions import db
from app.models import GoogleToken


def _scopes() -> list[str]:
    scopes = current_app.config.get("GOOGLE_SCOPES") or []
    return scopes or ["https://www.googleapis.com/auth/calendar"]


def _get_credentials(user_id: int) -> Credentials | None:
    """
    Construye Credentials desde DB y refresca access_token si está expirado.
    Retorna None si el usuario no tiene token guardado.
    """
    token = GoogleToken.query.filter_by(user_id=user_id).first()
    if not token:
        return None

    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=_scopes(),
    )

    # Refrescar si corresponde
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.access_token = creds.token

            # Guardar expiración si viene
            if creds.expiry:
                token.token_expiry = creds.expiry.replace(tzinfo=None)

            db.session.commit()
    except Exception:
        # Si refresh falla, no reventamos el sistema
        return None

    return creds


def list_events_range(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """
    Lista eventos del calendario primary en un rango [start_dt, end_dt].
    """
    creds = _get_credentials(user_id)
    if not creds:
        return []

    service = build("calendar", "v3", credentials=creds)

    time_min = start_dt.isoformat() + "Z"
    time_max = end_dt.isoformat() + "Z"

    res = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    items = res.get("items", [])
    out: list[dict[str, Any]] = []

    for ev in items:
        start = ev.get("start", {})
        when = start.get("dateTime") or start.get("date")
        out.append(
            {
                "id": ev.get("id"),
                "summary": ev.get("summary", "(sin título)"),
                "when": when,
                "link": ev.get("htmlLink"),
            }
        )

    return out


def create_deadline_event(
    user_id: int,
    title: str,
    description: str,
    start_iso: str,
    end_iso: str,
) -> bool:
    """
    Crea un evento en Google Calendar.
    start_iso/end_iso deben venir en ISO8601 (ideal con timezone o local asumido).
    """
    creds = _get_credentials(user_id)
    if not creds:
        return False

    service = build("calendar", "v3", credentials=creds)

    body = {
        "summary": f"📌 Subir: {title}",
        "description": description,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    service.events().insert(calendarId="primary", body=body).execute()
    return True