"""Pruebas de detección determinista de gastos atípicos (Spec 003)."""
from __future__ import annotations

import json
from datetime import datetime
from itertools import count
from typing import Optional

import pytest

from backend.app.ai import assistant
from backend.app.categorizer import INTERNAL_TRANSFERS, SENT_TRANSFERS
from backend.app.models import Transaction

URL = "/api/analytics/anomalies"
_ids = count(300)


def _tx(category: str, amount: float, day: datetime, *, merchant: Optional[str] = "Comercio Sim",
        tx_type: str = "expense", is_duplicate: bool = False) -> Transaction:
    n = next(_ids)
    return Transaction(
        source="bank",
        external_id=f"ANM-{n}",
        occurred_at=day,
        amount=amount,
        type=tx_type,
        currency="PEN",
        description=f"Cargo {n}",
        merchant=merchant,
        category=category,
        is_duplicate=is_duplicate,
    )


def test_anomalies_detects_outliers_with_min_three_samples_and_exclusions(client, db_session):
    db_session.add_all([
        # Alimentación: 50 + 50 + 50 + 450 = 600 -> promedio = 150.0 -> 450 tiene ratio 3.0
        _tx("Alimentación", 50.0, datetime(2026, 9, 10, 12)),
        _tx("Alimentación", 50.0, datetime(2026, 9, 20, 12)),
        _tx("Alimentación", 50.0, datetime(2026, 10, 5, 12)),
        _tx("Alimentación", 450.0, datetime(2026, 10, 18, 19), merchant="Restaurante Gourmet"),
        # Duplicado gigante no debe alterar el promedio ni aparecer como anomalía
        _tx("Alimentación", 5000.0, datetime(2026, 10, 19, 12), is_duplicate=True),
        # Salud: solo 2 movimientos (50 y 400) -> no alcanza muestra mínima de 3
        _tx("Salud", 50.0, datetime(2026, 10, 2, 10)),
        _tx("Salud", 400.0, datetime(2026, 10, 15, 10)),
        # Transferencias e ingresos nunca cuentan como gastos atípicos
        _tx(INTERNAL_TRANSFERS, 50.0, datetime(2026, 10, 1, 10)),
        _tx(INTERNAL_TRANSFERS, 50.0, datetime(2026, 10, 2, 10)),
        _tx(INTERNAL_TRANSFERS, 1000.0, datetime(2026, 10, 20, 10)),
        _tx(SENT_TRANSFERS, 40.0, datetime(2026, 10, 1, 10)),
        _tx(SENT_TRANSFERS, 40.0, datetime(2026, 10, 2, 10)),
        _tx(SENT_TRANSFERS, 900.0, datetime(2026, 10, 21, 10)),
    ])
    db_session.commit()

    resp = client.get(URL, params={"date_from": "2026-10-01", "date_to": "2026-10-31", "multiplier": 2.0})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["category"] == "Alimentación"
    assert items[0]["merchant"] == "Restaurante Gourmet"
    assert items[0]["amount"] == 450.0
    assert items[0]["category_average"] == 150.0
    assert items[0]["ratio"] == 3.0


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"date_from": "2026-10-31", "date_to": "2026-10-01"}, 400),
        ({"multiplier": 1.0}, 422),
        ({"multiplier": 12.0}, 422),
        ({"limit": 0}, 422),
        ({"limit": 51}, 422),
    ],
)
def test_anomalies_validation_and_empty(client, params, expected):
    assert client.get(URL, params=params).status_code == expected
    assert client.get(URL).json() == []


def test_assistant_anomalies_tool_registered_and_strict(db_session, test_settings):
    db_session.add_all([
        _tx("Transporte", 20.0, datetime(2026, 10, 1, 8)),
        _tx("Transporte", 20.0, datetime(2026, 10, 2, 8)),
        _tx("Transporte", 140.0, datetime(2026, 10, 12, 8), merchant="Taxi Aeropuerto"),
    ])
    db_session.commit()

    raw = assistant.execute_tool(
        db_session,
        test_settings,
        "get_spending_anomalies",
        {"from_date": "2026-10-01", "to_date": "2026-10-31", "multiplier": 2.0},
    )
    parsed = json.loads(raw)
    assert len(parsed) == 1
    assert parsed[0]["merchant"] == "Taxi Aeropuerto"
