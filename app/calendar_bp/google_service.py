from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Any

from flask import current_app
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.extensions import db
from app.models import GoogleToken


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials(user_id: int) -> Credentials | None:
    token = GoogleToken.query.filter_by(user_id=user_id).first()
    if not token:
        return None

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config.get("GOOGLE_CLIENT_ID", ""),
        client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET", ""),
        scopes=SCOPES,
    )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.access_token = creds.token
        if creds.expiry:
            token.token_expiry = creds.expiry.replace(tzinfo=None)
        db.session.commit()

    return creds


def list_upcoming_events(user_id: int, days: int = 30, max_results: int = 5) -> list[dict[str, Any]]:
    creds = _get_credentials(user_id)
    if not creds:
        return []

    service = build("calendar", "v3", credentials=creds)
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days)).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    items = events_result.get("items", [])
    out = []
    for ev in items:
        start = ev.get("start", {})
        dt = start.get("dateTime") or start.get("date")
        out.append({
            "id": ev.get("id"),
            "summary": ev.get("summary", "(sin título)"),
            "when": dt,
        })
    return out


def list_upcoming_deadlines_7d(user_id: int, days: int = 7) -> list[dict[str, Any]]:
    creds = _get_credentials(user_id)
    if not creds:
        return []

    service = build("calendar", "v3", credentials=creds)
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days)).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime",
        q="📌 Subir:",
    ).execute()

    items = events_result.get("items", [])
    out = []
    for ev in items:
        summary = ev.get("summary", "")
        start = ev.get("start", {})
        dt_str = start.get("dateTime") or start.get("date")
        d: date | None = None
        try:
            if dt_str and "T" in dt_str:
                d = datetime.fromisoformat(dt_str.replace("Z", "")).date()
            elif dt_str:
                d = date.fromisoformat(dt_str)
        except Exception:
            d = None

        out.append({
            "id": ev.get("id"),
            "summary": summary,
            "when": dt_str,
            "date": d,
        })
    return out


def create_deadline_event(
    user_id: int,
    title: str,
    description: str,
    start_iso: str,
    end_iso: str,
) -> bool:
    creds = _get_credentials(user_id)
    if not creds:
        return False

    service = build("calendar", "v3", credentials=creds)

    event = {
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

    service.events().insert(calendarId="primary", body=event).execute()
    return True