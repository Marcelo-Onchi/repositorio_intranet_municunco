from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.extensions import db
from app.models import GoogleToken


def _tz_name() -> str:
    return (current_app.config.get("APP_TIMEZONE") or "America/Santiago").strip()


def _scopes() -> list[str]:
    scopes = current_app.config.get("GOOGLE_SCOPES") or []
    return scopes or ["https://www.googleapis.com/auth/calendar.events"]


def _http_error_details(e: HttpError) -> str:
    try:
        raw = e.content.decode("utf-8", errors="ignore") if getattr(e, "content", None) else ""
        if not raw:
            return str(e)
        data = json.loads(raw)
        err = data.get("error") or {}
        msg = err.get("message") or ""
        status = err.get("status") or ""
        code = err.get("code") or ""
        parts = [p for p in [str(code), str(status), str(msg)] if p]
        return " | ".join(parts) if parts else raw
    except Exception:
        return str(e)


def _get_credentials(user_id: int) -> Optional[Credentials]:
    token = GoogleToken.query.filter_by(user_id=user_id).first()
    if not token:
        return None

    client_id = (current_app.config.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (current_app.config.get("GOOGLE_CLIENT_SECRET") or "").strip()
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

    # expiry NAIVE UTC (evita naive vs aware en google-auth)
    if token.token_expiry:
        try:
            creds.expiry = token.token_expiry.replace(tzinfo=None)
        except Exception:
            pass

    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.access_token = creds.token
            if creds.expiry:
                token.token_expiry = creds.expiry.replace(tzinfo=None)
            db.session.commit()
    except Exception as ex:
        current_app.logger.warning("Google token refresh failed: %s", ex)
        return None

    return creds


def _localize_naive(dt_naive: datetime) -> datetime:
    """
    Toma un datetime naive y lo interpreta como hora local del sistema (Chile),
    devolviendo un datetime aware con tzinfo.
    """
    try:
        from zoneinfo import ZoneInfo

        return dt_naive.replace(tzinfo=ZoneInfo(_tz_name()))
    except Exception:
        # Fallback: asumir UTC si no hay zoneinfo (raro, pero mejor que romper)
        return dt_naive.replace(tzinfo=timezone.utc)


def _to_rfc3339_utc(dt_naive_local: datetime) -> str:
    """
    Google se porta mejor si timeMin/timeMax van en UTC.
    """
    aware_local = _localize_naive(dt_naive_local)
    aware_utc = aware_local.astimezone(timezone.utc)
    # isoformat() con +00:00 está bien; no uses Z para evitar parse raros
    return aware_utc.isoformat()


def _human_when(start: dict[str, Any]) -> str:
    """
    start puede traer:
      - {"dateTime": "2026-03-05T09:00:00-03:00"}
      - {"date": "2026-03-05"} (evento todo el día)
    """
    raw_dt = (start or {}).get("dateTime")
    raw_d = (start or {}).get("date")

    if raw_dt:
        try:
            # soportar ...Z
            raw_dt2 = raw_dt.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw_dt2)
            # convertir a TZ app
            try:
                from zoneinfo import ZoneInfo

                dt = dt.astimezone(ZoneInfo(_tz_name()))
            except Exception:
                pass
            return dt.strftime("%d-%m-%Y %H:%M")
        except Exception:
            return str(raw_dt)

    if raw_d:
        try:
            d = datetime.strptime(raw_d, "%Y-%m-%d").date()
            return d.strftime("%d-%m-%Y")
        except Exception:
            return str(raw_d)

    return "—"


def list_events_range(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    creds = _get_credentials(user_id)
    if not creds:
        return []

    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt

    service = build("calendar", "v3", credentials=creds)

    time_min = _to_rfc3339_utc(start_dt)
    time_max = _to_rfc3339_utc(end_dt)

    try:
        res = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except HttpError as e:
        current_app.logger.warning("Google Calendar list failed: %s", _http_error_details(e))
        return []
    except Exception as e:
        current_app.logger.warning("Google Calendar list exception: %s", e)
        return []

    items = res.get("items", []) or []
    out: list[dict[str, Any]] = []

    for ev in items:
        start = ev.get("start", {}) or {}
        out.append(
            {
                "id": ev.get("id"),
                "summary": ev.get("summary", "(sin título)"),
                "when": _human_when(start),
                "link": ev.get("htmlLink"),
            }
        )

    return out


def create_deadline_event(
    user_id: int,
    title: str,
    description: str,
    start_dt: datetime,
    end_dt: datetime,
) -> Tuple[bool, str]:
    creds = _get_credentials(user_id)
    if not creds:
        return False, "Sin credenciales Google (token no encontrado o expirado)."

    service = build("calendar", "v3", credentials=creds)

    # Evento con dateTime local (Google guarda bien con TZ)
    body = {
        "summary": f"📌 Subir: {title}",
        "description": description,
        "start": {"dateTime": _localize_naive(start_dt).isoformat(), "timeZone": _tz_name()},
        "end": {"dateTime": _localize_naive(end_dt).isoformat(), "timeZone": _tz_name()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    try:
        service.events().insert(calendarId="primary", body=body).execute()
        return True, ""
    except HttpError as e:
        detail = _http_error_details(e)
        current_app.logger.warning("Google Calendar insert failed: %s", detail)
        return False, detail
    except Exception as e:
        current_app.logger.warning("Google Calendar insert exception: %s", e)
        return False, str(e)