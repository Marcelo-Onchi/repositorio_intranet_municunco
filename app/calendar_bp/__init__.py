from __future__ import annotations

from flask import Blueprint

bp = Blueprint("calendar", __name__, url_prefix="/calendar")

from . import routes  # noqa: E402,F401