"""Pruebas del endpoint GET /api/analytics/top-merchants."""
from __future__ import annotations

from datetime import datetime
from itertools import count
from typing import Optional

import pytest

from backend.app.categorizer import INTERNAL_TRANSFERS, SENT_TRANSFERS
from backend.app.models import Transaction

URL = "/api/analytics/top-merchants"
OCTOBER = {"date_from": "2026-10-01", "date_to": "2026-10-31"}

A, B, C = "Supermercado La Canasta", "Farmacia Sim", "Cine Sim"
EXPECTED = [
    {"merchant": A, "total": 150.5, "count": 2, "share": 0.5004},
    {"merchant": B, "total": 120.0, "count": 1, "share": 0.399},
    {"merchant": C, "total": 30.25, "count": 1, "share": 0.1006},
]

_ids = count(1)


def _tx(merchant: Optional[str], amount: float, day: datetime, *, tx_type: str = "expense",
        category: str = "Alimentación", is_duplicate: bool = False) -> Transaction:
    n = next(_ids)
    return Transaction(source="bank", external_id=f"TST-{n}", occurred_at=day, amount=amount, type=tx_type,
                       currency="PEN", description=f"Movimiento {n}", merchant=merchant, category=category,
                       is_duplicate=is_duplicate)


@pytest.fixture
def base_data(db_session):
    db_session.add_all([
        _tx(A, 100.0, datetime(2026, 10, 3, 12)),
        _tx(A, 50.5, datetime(2026, 10, 10, 12)),
        _tx(B, 120.0, datetime(2026, 10, 5, 12), category="Salud"),
        _tx(C, 30.25, datetime(2026, 10, 20, 12), category="Entretenimiento"),
    ])
    db_session.commit()
    return db_session


def test_top_merchants_order_and_totals(client, base_data):
    resp = client.get(URL, params=OCTOBER)
    assert resp.status_code == 200
    assert resp.json() == EXPECTED


def test_top_merchants_ignores_duplicates_and_internal_transfers(client, base_data):
    base_data.add_all([
        _tx(A, 999.0, datetime(2026, 10, 3, 12), is_duplicate=True),
        _tx(C, 500.0, datetime(2026, 10, 7, 12), category=INTERNAL_TRANSFERS),
        _tx("Billetera Sim", 500.0, datetime(2026, 10, 7, 12), category=INTERNAL_TRANSFERS),
        _tx(B, 800.0, datetime(2026, 10, 8, 12), tx_type="income", category="Otros ingresos"),
        _tx(None, 700.0, datetime(2026, 10, 9, 12), category="Otros gastos"),
    ])
    base_data.commit()
    assert client.get(URL, params=OCTOBER).json() == EXPECTED


def test_top_merchants_excludes_sent_transfers_to_people(client, base_data):
    base_data.add(_tx("Lucía", 400.0, datetime(2026, 10, 12, 18), category=SENT_TRANSFERS))
    base_data.commit()
    body = client.get(URL, params=OCTOBER).json()
    assert "Lucía" not in {row["merchant"] for row in body}
    assert body == EXPECTED   # el envío tampoco entra en el denominador del share


def test_top_merchants_limit(client, base_data):
    body = client.get(URL, params={**OCTOBER, "limit": 2}).json()
    assert body == EXPECTED[:2]   # share calculado sobre todo el gasto con comercio (300.75)


def test_top_merchants_date_range(client, base_data):
    base_data.add(_tx(A, 40.0, datetime(2026, 9, 28, 12)))
    base_data.commit()

    assert client.get(URL, params=OCTOBER).json() == EXPECTED

    body = client.get(URL, params={"date_from": "2026-09-01", "date_to": "2026-10-31"}).json()
    assert body[0] == {"merchant": A, "total": 190.5, "count": 3, "share": round(190.5 / 340.75, 4)}

    only_october_first_week = client.get(URL, params={"date_from": "2026-10-01", "date_to": "2026-10-05"}).json()
    assert only_october_first_week == [
        {"merchant": B, "total": 120.0, "count": 1, "share": round(120 / 220, 4)},
        {"merchant": A, "total": 100.0, "count": 1, "share": round(100 / 220, 4)},
    ]


@pytest.mark.parametrize("limit", [0, 21])
def test_top_merchants_invalid_limit(client, limit):
    assert client.get(URL, params={"limit": limit}).status_code == 422


def test_top_merchants_inverted_range(client):
    resp = client.get(URL, params={"date_from": "2026-10-31", "date_to": "2026-10-01"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "date_from no puede ser posterior a date_to"


def test_top_merchants_empty_period(client, base_data):
    resp = client.get(URL, params={"date_from": "2025-01-01", "date_to": "2025-01-31"})
    assert resp.status_code == 200
    assert resp.json() == []
