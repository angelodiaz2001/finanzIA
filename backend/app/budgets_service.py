"""Servicio determinista de presupuestos mensuales por categoría de gasto."""
from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .categorizer import EXPENSE_CATEGORIES, INTERNAL_TRANSFERS, SENT_TRANSFERS
from .models import CategoryBudget, Transaction

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
BUDGETABLE_CATEGORIES = [c for c in EXPENSE_CATEGORIES if c not in (INTERNAL_TRANSFERS, SENT_TRANSFERS)]


class BudgetValidationError(ValueError):
    """Error de dominio cuando el mes o la categoría no son válidos."""


class BudgetNotFoundError(LookupError):
    """Error cuando el identificador del presupuesto no existe."""


def normalize_month(month: Optional[str]) -> str:
    if not month:
        return date.today().strftime("%Y-%m")
    clean = month.strip()
    if not _MONTH_RE.match(clean):
        raise BudgetValidationError("Formato de mes inválido; usa YYYY-MM")
    return clean


def _month_bounds(month: str) -> tuple[datetime, datetime]:
    year, mon = int(month[:4]), int(month[5:7])
    last_day = monthrange(year, mon)[1]
    return datetime(year, mon, 1, 0, 0, 0), datetime.combine(date(year, mon, last_day), time.max)


def _expenses_by_category(db: Session, month: str) -> dict[str, float]:
    start_dt, end_dt = _month_bounds(month)
    stmt = (
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(
            Transaction.is_duplicate.is_(False),
            Transaction.type == "expense",
            Transaction.category.not_in((INTERNAL_TRANSFERS, SENT_TRANSFERS)),
            Transaction.occurred_at >= start_dt,
            Transaction.occurred_at <= end_dt,
        )
        .group_by(Transaction.category)
    )
    return {cat: float(total or 0.0) for cat, total in db.execute(stmt)}


def _build_item(budget: CategoryBudget, spent_raw: float) -> dict[str, Any]:
    limit_val = round(float(budget.limit_amount), 2)
    spent = round(float(spent_raw), 2)
    remaining = round(limit_val - spent, 2)
    ratio = round(spent / limit_val, 4) if limit_val > 0 else 0.0
    if spent > limit_val:
        status = "exceeded"
    elif ratio >= 0.8:
        status = "warning"
    else:
        status = "ok"
    return {
        "id": budget.id,
        "month": budget.month,
        "category": budget.category,
        "limit_amount": limit_val,
        "spent": spent,
        "remaining": remaining,
        "usage_ratio": ratio,
        "status": status,
        "currency": budget.currency,
    }


def upsert_budget(db: Session, month: str, category: str, limit_amount: float, currency: str) -> dict[str, Any]:
    norm_month = normalize_month(month)
    norm_cat = category.strip()
    if norm_cat not in BUDGETABLE_CATEGORIES:
        raise BudgetValidationError(f"La categoría '{norm_cat}' no es una categoría de gasto presupuestable")

    existing = db.execute(
        select(CategoryBudget).where(CategoryBudget.month == norm_month, CategoryBudget.category == norm_cat)
    ).scalar_one_or_none()

    rounded_limit = round(float(limit_amount), 2)
    if existing is None:
        existing = CategoryBudget(month=norm_month, category=norm_cat, limit_amount=rounded_limit, currency=currency)
        db.add(existing)
    else:
        existing.limit_amount = rounded_limit
        existing.currency = currency
    db.commit()
    db.refresh(existing)

    spent_map = _expenses_by_category(db, norm_month)
    return _build_item(existing, spent_map.get(norm_cat, 0.0))


def list_budgets_status(db: Session, month: Optional[str], currency: str) -> dict[str, Any]:
    norm_month = normalize_month(month)
    rows = list(
        db.execute(select(CategoryBudget).where(CategoryBudget.month == norm_month)).scalars()
    )
    if not rows:
        return {
            "month": norm_month,
            "currency": currency,
            "total_budgeted": 0.0,
            "total_spent": 0.0,
            "items": [],
        }

    spent_map = _expenses_by_category(db, norm_month)
    items = [_build_item(b, spent_map.get(b.category, 0.0)) for b in rows]
    items.sort(key=lambda it: (-it["usage_ratio"], it["category"]))
    total_budgeted = round(sum(it["limit_amount"] for it in items), 2)
    total_spent = round(sum(it["spent"] for it in items), 2)
    return {
        "month": norm_month,
        "currency": currency,
        "total_budgeted": total_budgeted,
        "total_spent": total_spent,
        "items": items,
    }


def delete_budget(db: Session, budget_id: int) -> None:
    budget = db.get(CategoryBudget, budget_id)
    if budget is None:
        raise BudgetNotFoundError("Presupuesto no encontrado")
    db.delete(budget)
    db.commit()
