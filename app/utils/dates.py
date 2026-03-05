# app/utils/dates.py
from __future__ import annotations

from datetime import date, datetime
from typing import Optional


def parse_date_ddmmyyyy(raw: str) -> Optional[date]:
    """
    Parsea fecha 'dd-mm-YYYY' -> date.
    Retorna None si viene vacío o inválido.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d-%m-%Y").date()
    except ValueError:
        return None


def parse_datetime_ddmmyyyy(raw: str) -> Optional[datetime]:
    """
    Parsea fecha 'dd-mm-YYYY' -> datetime (00:00).
    Retorna None si viene vacío o inválido.
    """
    d = parse_date_ddmmyyyy(raw)
    if not d:
        return None
    return datetime.combine(d, datetime.min.time())


def ddmmyyyy_to_slash(raw_dd_mm_yyyy: str) -> str:
    """
    UI: dd-mm-aaaa -> Documento: dd/mm/aaaa
    """
    raw = (raw_dd_mm_yyyy or "").strip()
    if len(raw) == 10 and raw[2] == "-" and raw[5] == "-":
        return raw.replace("-", "/")
    return raw