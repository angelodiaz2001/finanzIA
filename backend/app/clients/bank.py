from __future__ import annotations

from typing import Any

from ..config import Settings
from .base import get_json


def fetch_bank(settings: Settings) -> dict[str, Any]:
    """Cuentas y transacciones de todas las cuentas del titular."""
    accounts = get_json(settings.bank_api_url, "/accounts", timeout=settings.source_timeout_seconds)
    transactions = get_json(settings.bank_api_url, "/transactions", params={"limit": 5000},
                            timeout=settings.source_timeout_seconds)
    return {"accounts": accounts, "transactions": transactions}
