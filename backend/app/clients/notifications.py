from __future__ import annotations

from typing import Any

from ..config import Settings
from .base import get_json


def fetch_notifications(settings: Settings) -> dict[str, Any]:
    """Eventos ya analizados por la API de notificaciones."""
    events = get_json(settings.notifications_api_url, "/events", params={"limit": 2000},
                      timeout=settings.source_timeout_seconds)
    return {"events": events}
