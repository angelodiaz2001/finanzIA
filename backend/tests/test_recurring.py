"""Pruebas de detección determinista de gastos recurrentes (Spec 005)."""
from __future__ import annotations

import json
from datetime import datetime
from itertools import count
from typing import Optional

import pytest

from backend.app.ai import assistant
from backend.app.categorizer import INTERNAL_TRANSFERS, SENT_TRANSFERS
from backend.app.models import Transaction

URL = "/api/analytics/recurring"
_ids = count(700)


def _tx(merchant: Optional[str], amount: float, day: datetime, *, category: str = "Entretenimiento",
        tx_type: str = "expense", is_duplicate: bool = False) -> Transaction:
    n = next(_ids)
    return Transaction(
        source="bank",
        external_id=f"REC-{n}",
        occurred_at=day,
        amount=amount,
        type=tx_type,
        currency="PEN",
        description=f"Suscripción {n}",
        merchant=merchant,
        category=category,
        is_duplicate=is_duplicate,
    )


def test_recurring_expenses_groups_by_distinct_months_and_excludes_transfers(client, db_session):
    db_session.add_all([
        # Streaming Sim: 3 meses distintos
        _tx("Streaming Sim", 39.9, datetime(2026, 8, 15, 10)),
        _tx("Streaming Sim", 39.9, datetime(2026, 9, 15, 10)),
        _tx("Streaming Sim", 39.9, datetime(2026, 10, 15, 10)),
        # Duplicado en octubre no debe inflar promedio ni ocurrencias
        _tx("Streaming Sim", 39.9, datetime(2026, 10, 15, 11), is_duplicate=True),
        # Internet Hogar: 2 meses distintos
        _tx("Internet Hogar", 90.0, datetime(2026, 9, 5, 9), category="Servicios"),
        _tx("Internet Hogar", 110.0, datetime(2026, 10, 5, 9), category="Servicios"),
        # Cine Sim: 3 compras pero todas en el mismo mes -> NO es recurrente mensual
        _tx("Cine Sim", 25.0, datetime(2026, 10, 1, 18)),
        _tx("Cine Sim", 25.0, datetime(2026, 10, 8, 18)),
        _tx("Cine Sim", 25.0, datetime(2026, 10, 22, 18)),
        # Envíos a personas y transferencias internas excluidos aunque ocurran varios meses
        _tx("Lucía", 100.0, datetime(2026, 8, 10, 12), category=SENT_TRANSFERS),
        _tx("Lucía", 100.0, datetime(2026, 9, 10, 12), category=SENT_TRANSFERS),
        _tx("Billetera", 200.0, datetime(2026, 8, 1, 12), category=INTERNAL_TRANSFERS),
        _tx("Billetera", 200.0, datetime(2026, 9, 1, 12), category=INTERNAL_TRANSFERS),
    ])
    db_session.commit()

    resp = client.get(URL, params={"limit": 5})
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["merchant"] for r in rows] == ["Streaming Sim", "Internet Hogar"]
    assert rows[0] == {
        "merchant": "Streaming Sim",
        "category": "Entretenimiento",
        "months_active": 3,
        "occurrences": 3,
        "average_amount": 39.9,
        "total_amount": 119.7,
        "last_charged_at": "2026-10-15",
    }
    assert rows[1]["average_amount"] == 100.0


@pytest.mark.parametrize("limit", [0, 31])
def test_recurring_validation_and_empty(client, limit):
    assert client.get(URL, params={"limit": limit}).status_code == 422
    assert client.get(URL).json() == []


def test_assistant_recurring_tool_registered(db_session, test_settings):
    db_session.add_all([
        _tx("Gimnasio Sim", 80.0, datetime(2026, 9, 1, 8), category="Salud"),
        _tx("Gimnasio Sim", 80.0, datetime(2026, 10, 1, 8), category="Salud"),
    ])
    db_session.commit()

    raw = assistant.execute_tool(db_session, test_settings, "get_recurring_expenses", {"limit": 5})
    parsed = json.loads(raw)
    assert len(parsed) == 1
    assert parsed[0]["merchant"] == "Gimnasio Sim"
