from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import budgets_service
from ..config import Settings, get_settings
from ..database import get_db
from ..schemas import BudgetMonthSummary, BudgetStatusOut, BudgetUpsert

router = APIRouter(prefix="/budgets", tags=["presupuestos"])


@router.get("", response_model=BudgetMonthSummary)
def get_budgets(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BudgetMonthSummary:
    try:
        data = budgets_service.list_budgets_status(db, month, settings.default_currency)
    except budgets_service.BudgetValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BudgetMonthSummary(**data)


@router.put("", response_model=BudgetStatusOut)
def put_budget(
    body: BudgetUpsert,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BudgetStatusOut:
    try:
        item = budgets_service.upsert_budget(
            db, body.month, body.category, body.limit_amount, settings.default_currency
        )
    except budgets_service.BudgetValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BudgetStatusOut(**item)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget(budget_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        budgets_service.delete_budget(db, budget_id)
    except budgets_service.BudgetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
