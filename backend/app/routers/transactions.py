from __future__ import annotations

import csv
import io
from datetime import date, datetime, time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..categorizer import INTERNAL_TRANSFERS
from ..database import get_db
from ..models import Transaction
from ..schemas import CategoryUpdate, TransactionDetail, TransactionOut, TransactionPage

router = APIRouter(prefix="/transactions", tags=["transacciones"])

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe_csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


def _build_conditions(
    source: Optional[str],
    tx_type: Optional[str],
    category: Optional[str],
    q: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    include_duplicates: bool,
) -> list[Any]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from no puede ser posterior a date_to")
    conds: list[Any] = []
    if not include_duplicates:
        conds.append(Transaction.is_duplicate.is_(False))
    if source:
        conds.append(Transaction.source == source)
    if tx_type:
        conds.append(Transaction.type == tx_type)
    if category:
        conds.append(Transaction.category == category)
    if q:
        like = f"%{q}%"
        conds.append(or_(Transaction.description.ilike(like), Transaction.merchant.ilike(like)))
    if date_from:
        conds.append(Transaction.occurred_at >= datetime.combine(date_from, time.min))
    if date_to:
        conds.append(Transaction.occurred_at <= datetime.combine(date_to, time.max))
    return conds


@router.get("", response_model=TransactionPage)
def list_transactions(
    source: Optional[str] = Query(None, pattern="^(bank|wallet|notification)$"),
    type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category: Optional[str] = None,
    q: Optional[str] = Query(None, max_length=100, description="Texto en descripción o comercio"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_duplicates: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
) -> TransactionPage:
    conds = _build_conditions(source, type, category, q, date_from, date_to, include_duplicates)
    total = int(db.execute(select(func.count(Transaction.id)).where(*conds)).scalar_one())

    # Subtotales del filtro completo (siempre sin duplicados ni transferencias internas)
    sub_conds = _build_conditions(source, type, category, q, date_from, date_to, False)
    sub_stmt = (
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(*sub_conds, Transaction.category != INTERNAL_TRANSFERS)
        .group_by(Transaction.type)
    )
    totals_by_type = {t: float(val or 0.0) for t, val in db.execute(sub_stmt)}

    stmt = (
        select(Transaction).where(*conds)
        .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = [TransactionOut.model_validate(t) for t in db.execute(stmt).scalars()]
    return TransactionPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        filtered_income=round(totals_by_type.get("income", 0.0), 2),
        filtered_expenses=round(totals_by_type.get("expense", 0.0), 2),
    )


@router.get("/export")
def export_transactions_csv(
    source: Optional[str] = Query(None, pattern="^(bank|wallet|notification)$"),
    type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category: Optional[str] = None,
    q: Optional[str] = Query(None, max_length=100),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_duplicates: bool = False,
    db: Session = Depends(get_db),
) -> Response:
    conds = _build_conditions(source, type, category, q, date_from, date_to, include_duplicates)
    stmt = select(Transaction).where(*conds).order_by(Transaction.occurred_at.desc(), Transaction.id.desc())

    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(["id", "fecha", "fuente", "tipo", "categoria", "comercio", "descripcion", "monto", "moneda", "duplicado"])
    for tx in db.execute(stmt).scalars():
        writer.writerow([
            tx.id,
            tx.occurred_at.isoformat(),
            tx.source,
            tx.type,
            _safe_csv_cell(tx.category),
            _safe_csv_cell(tx.merchant or ""),
            _safe_csv_cell(tx.description),
            f"{float(tx.amount):.2f}",
            tx.currency,
            "si" if tx.is_duplicate else "no",
        ])

    return Response(
        content=buf.getvalue().encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transacciones_finanzia.csv"'},
    )


@router.get("/{transaction_id}", response_model=TransactionDetail)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> TransactionDetail:
    tx = db.get(Transaction, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return TransactionDetail.model_validate(tx)


@router.patch("/{transaction_id}/category", response_model=TransactionOut)
def update_category(transaction_id: int, body: CategoryUpdate, db: Session = Depends(get_db)) -> TransactionOut:
    """Corrección manual de la categoría (prevalece sobre reglas e IA)."""
    tx = db.get(Transaction, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    tx.category = body.category.strip()
    tx.category_source = "manual"
    db.commit()
    db.refresh(tx)
    return TransactionOut.model_validate(tx)
