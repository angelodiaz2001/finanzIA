from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..categorizer import EXPENSE_CATEGORIES, INCOME_CATEGORIES, INTERNAL_TRANSFERS
from ..database import get_db
from ..models import Account
from ..schemas import AccountOut

router = APIRouter(tags=["catálogo"])


@router.get("/accounts", response_model=list[AccountOut])
def accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    stmt = select(Account).order_by(Account.source, Account.name)
    return [AccountOut.model_validate(a) for a in db.execute(stmt).scalars()]


@router.get("/categories")
def categories() -> dict[str, object]:
    return {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORIES, "internal": INTERNAL_TRANSFERS}
