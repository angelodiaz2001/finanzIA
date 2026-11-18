"""Pruebas de subtotales filtrados y exportación CSV en transacciones (Spec 004)."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from itertools import count

from backend.app.categorizer import INTERNAL_TRANSFERS
from backend.app.models import Transaction

_ids = count(500)


def _tx(desc: str, amount: float, day: datetime, *, tx_type: str = "expense",
        category: str = "Alimentación", is_duplicate: bool = False) -> Transaction:
    n = next(_ids)
    return Transaction(
        source="bank",
        external_id=f"EXP-{n}",
        occurred_at=day,
        amount=amount,
        type=tx_type,
        currency="PEN",
        description=desc,
        merchant="Comercio CSV",
        category=category,
        is_duplicate=is_duplicate,
    )


def test_transactions_filtered_subtotals_across_pages_and_exclusions(client, db_session):
    db_session.add_all([
        _tx("Sueldo octubre", 2500.0, datetime(2026, 10, 1, 9), tx_type="income", category="Salario"),
        _tx("Compra 1", 120.0, datetime(2026, 10, 5, 12)),
        _tx("Compra 2", 80.5, datetime(2026, 10, 10, 12)),
        _tx("Duplicado", 999.0, datetime(2026, 10, 11, 12), is_duplicate=True),
        _tx("Recarga propia", 400.0, datetime(2026, 10, 12, 12), category=INTERNAL_TRANSFERS),
    ])
    db_session.commit()

    # Pedimos page_size=1, pero los totales filtrados deben reflejar todas las filas del filtro
    resp = client.get("/api/transactions", params={"date_from": "2026-10-01", "date_to": "2026-10-31", "page_size": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 1
    assert body["filtered_income"] == 2500.0
    assert body["filtered_expenses"] == 200.5


def test_transactions_inverted_date_range_returns_400(client):
    resp = client.get("/api/transactions", params={"date_from": "2026-10-31", "date_to": "2026-10-01"})
    assert resp.status_code == 400
    assert "date_from" in resp.json()["detail"]


def test_transactions_csv_export_utf8_bom_and_formula_sanitization(client, db_session):
    db_session.add_all([
        _tx("=SUM(A1:A5) cargo sospechoso", 75.25, datetime(2026, 10, 15, 14)),
        _tx("Panadería artesanal", 18.0, datetime(2026, 10, 16, 8)),
    ])
    db_session.commit()

    resp = client.get("/api/transactions/export", params={"date_from": "2026-10-01", "date_to": "2026-10-31"})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "transacciones_finanzia.csv" in resp.headers.get("content-disposition", "")

    raw_text = resp.content.decode("utf-8")
    assert raw_text.startswith("\ufeff")
    reader = list(csv.DictReader(io.StringIO(raw_text.lstrip("\ufeff"))))
    assert len(reader) == 2
    descriptions = [r["descripcion"] for r in reader]
    assert any(d == "Panadería artesanal" for d in descriptions)
    assert any(d.startswith("'=SUM") for d in descriptions)
