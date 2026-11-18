"""Pruebas agregadas tras la auditoría de mutación AST sobre analytics.py.

Eliminan tres mutantes que sobrevivieron en la primera corrida:
- M-03 (`analytics.py:127`): cruce de año cuando `monthly()` retrocede de enero a diciembre.
- M-04 (`analytics.py:146`): signo exacto de `net = income - expenses` cuando hay ambos tipos en el mes.
- M-06 (`analytics.py:221`): gasto intermedio por encima de `avg / multiplier` pero debajo de `avg * multiplier`.
"""
from __future__ import annotations

from datetime import date, datetime

from backend.app import analytics
from backend.app.models import Transaction


def test_monthly_crosses_year_boundary_and_computes_exact_net(db_session):
    db_session.add_all([
        Transaction(
            source="bank",
            external_id="MUT-DEC",
            occurred_at=datetime(2025, 12, 15, 10),
            amount=1000.0,
            type="income",
            currency="PEN",
            description="Sueldo diciembre",
            merchant="Empresa",
            category="Salario",
            is_duplicate=False,
        ),
        Transaction(
            source="bank",
            external_id="MUT-DEC-EXP",
            occurred_at=datetime(2025, 12, 20, 12),
            amount=350.0,
            type="expense",
            currency="PEN",
            description="Mercado diciembre",
            merchant="Mercado",
            category="Alimentación",
            is_duplicate=False,
        ),
    ])
    db_session.commit()

    series = analytics.monthly(db_session, months=3, today=date(2026, 2, 10))
    assert [row["month"] for row in series] == ["2025-12", "2026-01", "2026-02"]
    assert series[0] == {"month": "2025-12", "income": 1000.0, "expenses": 350.0, "net": 650.0}


def test_anomalies_does_not_flag_normal_purchase_near_average(db_session):
    # Promedio = (100 + 100 + 100 + 300) / 4 = 150.0.
    # Con multiplier=2.0 el umbral es 300.0: la compra de 100.0 NO debe marcarse (100 >= 150/2 pero < 150*2).
    db_session.add_all([
        Transaction(
            source="bank",
            external_id=f"MUT-AN-{i}",
            occurred_at=datetime(2026, 10, i + 1, 12),
            amount=amt,
            type="expense",
            currency="PEN",
            description=f"Compra {i}",
            merchant="Tienda",
            category="Compras",
            is_duplicate=False,
        )
        for i, amt in enumerate([100.0, 100.0, 100.0, 300.0])
    ])
    db_session.commit()

    flagged = analytics.spending_anomalies(
        db_session, date_from=date(2026, 10, 1), date_to=date(2026, 10, 31), multiplier=2.0
    )
    assert [r["amount"] for r in flagged] == [300.0]
