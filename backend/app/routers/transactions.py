from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction
from ..schemas import CategoryUpdate, TransactionDetail, TransactionOut, TransactionPage

router = APIRouter(prefix="/transactions", tags=["transacciones"])


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
    conds = []
    if not include_duplicates:
        conds.append(Transaction.is_duplicate.is_(False))
    if source:
        conds.append(Transaction.source == source)
    if type:
        conds.append(Transaction.type == type)
    if category:
        conds.append(Transaction.category == category)
    if q:
        like = f"%{q}%"
        conds.append(or_(Transaction.description.ilike(like), Transaction.merchant.ilike(like)))
    if date_from:
        conds.append(Transaction.occurred_at >= datetime.combine(date_from, time.min))
    if date_to:
        conds.append(Transaction.occurred_at <= datetime.combine(date_to, time.max))

    total = int(db.execute(select(func.count(Transaction.id)).where(*conds)).scalar_one())
    stmt = (
        select(Transaction).where(*conds)
        .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = [TransactionOut.model_validate(t) for t in db.execute(stmt).scalars()]
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


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
