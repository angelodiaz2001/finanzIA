"""Indicadores financieros calculados con código convencional (no con IA).

Todas las funciones excluyen las transacciones marcadas como duplicadas y
tratan las transferencias internas (entre cuentas del mismo usuario) aparte,
para no inflar ingresos ni gastos.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .categorizer import INTERNAL_TRANSFERS
from .models import Account, Transaction


def _range_conditions(date_from: Optional[date], date_to: Optional[date]) -> list[Any]:
    conds: list[Any] = []
    if date_from:
        conds.append(Transaction.occurred_at >= datetime.combine(date_from, time.min))
    if date_to:
        conds.append(Transaction.occurred_at <= datetime.combine(date_to, time.max))
    return conds


def summary(db: Session, date_from: Optional[date], date_to: Optional[date], currency: str) -> dict[str, Any]:
    conds = _range_conditions(date_from, date_to)
    stmt = (
        select(Transaction.source, Transaction.type, Transaction.category,
               func.count(Transaction.id), func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.is_duplicate.is_(False), *conds)
        .group_by(Transaction.source, Transaction.type, Transaction.category)
    )
    income = expenses = internal = 0.0
    count = 0
    by_source: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "income": 0.0, "expenses": 0.0})
    for source, tx_type, category, n, total in db.execute(stmt):
        total = float(total or 0)
        count += n
        by_source[source]["count"] += n
        if category == INTERNAL_TRANSFERS:
            internal += total
            continue
        if tx_type == "income":
            income += total
            by_source[source]["income"] += total
        else:
            expenses += total
            by_source[source]["expenses"] += total

    dup_stmt = select(func.count(Transaction.id)).where(Transaction.is_duplicate.is_(True), *conds)
    duplicates = int(db.execute(dup_stmt).scalar_one() or 0)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "currency": currency,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net": round(income - expenses, 2),
        "internal_transfers": round(internal, 2),
        "count": count,
        "duplicates_detected": duplicates,
        "by_source": [
            {"source": s, "count": int(v["count"]), "income": round(v["income"], 2), "expenses": round(v["expenses"], 2)}
            for s, v in sorted(by_source.items())
        ],
    }


def by_category(db: Session, date_from: Optional[date], date_to: Optional[date],
                tx_type: str = "expense") -> list[dict[str, Any]]:
    stmt = (
        select(Transaction.category, func.count(Transaction.id), func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.is_duplicate.is_(False), Transaction.type == tx_type,
               Transaction.category != INTERNAL_TRANSFERS, *_range_conditions(date_from, date_to))
        .group_by(Transaction.category)
    )
    rows = [(c, int(n), float(t or 0)) for c, n, t in db.execute(stmt)]
    grand_total = sum(t for _, _, t in rows) or 0.0
    rows.sort(key=lambda r: r[2], reverse=True)
    return [
        {"category": c, "type": tx_type, "total": round(t, 2), "count": n,
         "share": round(t / grand_total, 4) if grand_total else 0.0}
        for c, n, t in rows
    ]


def monthly(db: Session, months: int = 6, today: Optional[date] = None) -> list[dict[str, Any]]:
    today = today or date.today()
    months = max(1, min(months, 36))
    year, month = today.year, today.month
    keys: list[str] = []
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    keys.reverse()
    first_year, first_month = int(keys[0][:4]), int(keys[0][5:])
    start = datetime(first_year, first_month, 1)

    stmt = (
        select(Transaction.occurred_at, Transaction.amount, Transaction.type, Transaction.category)
        .where(Transaction.is_duplicate.is_(False), Transaction.occurred_at >= start,
               Transaction.category != INTERNAL_TRANSFERS)
    )
    agg: dict[str, dict[str, float]] = {k: {"income": 0.0, "expenses": 0.0} for k in keys}
    for occurred_at, amount, tx_type, _ in db.execute(stmt):
        key = occurred_at.strftime("%Y-%m")
        if key not in agg:
            continue
        agg[key]["income" if tx_type == "income" else "expenses"] += float(amount or 0)
    return [
        {"month": k, "income": round(v["income"], 2), "expenses": round(v["expenses"], 2),
         "net": round(v["income"] - v["expenses"], 2)}
        for k, v in agg.items()
    ]


def search_transactions(db: Session, query: Optional[str] = None, category: Optional[str] = None,
                        tx_type: Optional[str] = None, date_from: Optional[date] = None,
                        date_to: Optional[date] = None, limit: int = 20) -> list[dict[str, Any]]:
    stmt = select(Transaction).where(Transaction.is_duplicate.is_(False), *_range_conditions(date_from, date_to))
    if query:
        like = f"%{query}%"
        stmt = stmt.where(or_(Transaction.description.ilike(like), Transaction.merchant.ilike(like)))
    if category:
        stmt = stmt.where(Transaction.category == category)
    if tx_type:
        stmt = stmt.where(Transaction.type == tx_type)
    stmt = stmt.order_by(Transaction.amount.desc(), Transaction.occurred_at.desc()).limit(max(1, min(limit, 100)))
    return [
        {"id": t.id, "date": t.occurred_at.date().isoformat(), "amount": float(t.amount), "type": t.type,
         "currency": t.currency, "description": t.description, "merchant": t.merchant,
         "category": t.category, "source": t.source}
        for t in db.execute(stmt).scalars()
    ]


def balances(db: Session) -> list[dict[str, Any]]:
    return [
        {"source": a.source, "name": a.name, "type": a.account_type, "currency": a.currency,
         "balance": float(a.balance), "updated_at": a.updated_at.isoformat()}
        for a in db.execute(select(Account).order_by(Account.source, Account.name)).scalars()
    ]
