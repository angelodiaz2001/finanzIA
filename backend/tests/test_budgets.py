"""Pruebas del CRUD y cálculo de presupuestos mensuales (Spec 001)."""
from __future__ import annotations

import json
from datetime import datetime
from itertools import count

import pytest

from backend.app.ai import assistant
from backend.app.categorizer import INTERNAL_TRANSFERS, SENT_TRANSFERS
from backend.app.models import Transaction

_ids = count(100)


def _tx(category: str, amount: float, day: datetime, *, tx_type: str = "expense",
        is_duplicate: bool = False) -> Transaction:
    n = next(_ids)
    return Transaction(
        source="bank",
        external_id=f"BDG-{n}",
        occurred_at=day,
        amount=amount,
        type=tx_type,
        currency="PEN",
        description=f"Movimiento {n}",
        merchant="Comercio Sim",
        category=category,
        is_duplicate=is_duplicate,
    )


def test_upsert_and_list_budgets_statuses_and_exclusions(client, db_session):
    db_session.add_all([
        _tx("Alimentación", 200.0, datetime(2026, 10, 5, 12)),
        _tx("Alimentación", 225.0, datetime(2026, 10, 18, 12)),
        _tx("Alimentación", 999.0, datetime(2026, 10, 19, 12), is_duplicate=True),
        _tx("Salud", 150.0, datetime(2026, 10, 8, 12)),
        _tx("Transporte", 40.0, datetime(2026, 10, 11, 12)),
        _tx("Transporte", 80.0, datetime(2026, 9, 28, 12)),
        _tx(INTERNAL_TRANSFERS, 500.0, datetime(2026, 10, 10, 12)),
        _tx(SENT_TRANSFERS, 300.0, datetime(2026, 10, 12, 12)),
    ])
    db_session.commit()

    r1 = client.put("/api/budgets", json={"month": "2026-10", "category": "Alimentación", "limit_amount": 500.0})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["spent"] == 425.0
    assert body1["remaining"] == 75.0
    assert body1["usage_ratio"] == 0.85
    assert body1["status"] == "warning"

    # Upsert idempotente sobre el mismo (month, category)
    r1_upd = client.put("/api/budgets", json={"month": "2026-10", "category": "Alimentación", "limit_amount": 500.0})
    assert r1_upd.status_code == 200
    assert r1_upd.json()["id"] == body1["id"]

    client.put("/api/budgets", json={"month": "2026-10", "category": "Salud", "limit_amount": 100.0})
    client.put("/api/budgets", json={"month": "2026-10", "category": "Transporte", "limit_amount": 200.0})

    summary = client.get("/api/budgets", params={"month": "2026-10"}).json()
    assert summary["month"] == "2026-10"
    assert summary["total_budgeted"] == 800.0
    assert summary["total_spent"] == 615.0
    assert [it["category"] for it in summary["items"]] == ["Salud", "Alimentación", "Transporte"]
    assert [it["status"] for it in summary["items"]] == ["exceeded", "warning", "ok"]
    assert summary["items"][0]["remaining"] == -50.0


@pytest.mark.parametrize(
    "payload,expected_code",
    [
        ({"month": "2026-13", "category": "Alimentación", "limit_amount": 200.0}, 400),
        ({"month": "oct-2026", "category": "Alimentación", "limit_amount": 200.0}, 400),
        ({"month": "2026-10", "category": INTERNAL_TRANSFERS, "limit_amount": 200.0}, 400),
        ({"month": "2026-10", "category": SENT_TRANSFERS, "limit_amount": 200.0}, 400),
        ({"month": "2026-10", "category": "Salario", "limit_amount": 200.0}, 400),
        ({"month": "2026-10", "category": "Alimentación", "limit_amount": 0}, 422),
        ({"month": "2026-10", "category": "Alimentación", "limit_amount": -10}, 422),
    ],
)
def test_budgets_validation_errors(client, payload, expected_code):
    resp = client.put("/api/budgets", json=payload)
    assert resp.status_code == expected_code


def test_delete_budget_and_empty_month(client):
    empty = client.get("/api/budgets", params={"month": "2025-05"})
    assert empty.status_code == 200
    assert empty.json() == {
        "month": "2025-05",
        "currency": "PEN",
        "total_budgeted": 0.0,
        "total_spent": 0.0,
        "items": [],
    }

    created = client.put("/api/budgets", json={"month": "2026-11", "category": "Educación", "limit_amount": 300.0}).json()
    del_ok = client.delete(f"/api/budgets/{created['id']}")
    assert del_ok.status_code == 204
    assert client.delete(f"/api/budgets/{created['id']}").status_code == 404


def test_assistant_budget_tool_returns_deterministic_summary(db_session, test_settings):
    db_session.add(_tx("Servicios", 120.0, datetime(2026, 10, 15, 10)))
    db_session.commit()
    tool_names = {t["name"] for t in assistant.TOOLS}
    assert "get_budgets_status" in tool_names

    raw = assistant.execute_tool(db_session, test_settings, "get_budgets_status", {"month": "2026-10"})
    parsed = json.loads(raw)
    assert parsed["month"] == "2026-10"
    assert parsed["items"] == []
