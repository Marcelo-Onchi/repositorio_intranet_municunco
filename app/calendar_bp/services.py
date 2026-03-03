from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Any, Tuple

from flask import current_app

from .google_service import create_deadline_event, list_events_range

DEADLINE_PREFIX = "📌 Subir:"


def list_deadlines_next_days(user_id: int, days: int = 7) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    end = now + timedelta(days=days)
    items = list_events_range(user_id, now, end, max_results=50)

    out: list[dict[str, Any]] = []
    for ev in items:
        summary = (ev.get("summary") or "").strip()
        if summary.startswith(DEADLINE_PREFIX):
            out.append(ev)
    return out


def create_due_date_event_for_document(
    user_id: int,
    doc_title: str,
    due_date,  # date
    description: str = "",
) -> Tuple[bool, str]:
    """
    Evento 09:00-10:00 hora local el día del vencimiento.
    Retorna (ok, error_msg).
    """
    if not due_date:
        return False, "Documento sin fecha de vencimiento."

    tz_name = current_app.config.get("APP_TIMEZONE", "America/Santiago")

    start_dt = datetime.combine(due_date, time(9, 0))
    end_dt = start_dt + timedelta(hours=1)

    ok = create_deadline_event(
        user_id=user_id,
        title=doc_title,
        description=description or "",
        start_dt=start_dt,
        end_dt=end_dt,
    )

    return (bool(ok), "" if ok else f"No se pudo crear el evento en Google Calendar ({tz_name}).")