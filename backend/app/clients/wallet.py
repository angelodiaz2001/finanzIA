from __future__ import annotations

from typing import Any

from ..config import Settings
from .base import get_json


def fetch_wallet(settings: Settings) -> dict[str, Any]:
    """Datos de la billetera y sus movimientos."""
    wallet = get_json(settings.wallet_api_url, "/wallet", timeout=settings.source_timeout_seconds)
    movements = get_json(settings.wallet_api_url, "/wallet/movements", params={"limit": 2000},
                         timeout=settings.source_timeout_seconds)
    return {"wallet": wallet, "movements": movements}
