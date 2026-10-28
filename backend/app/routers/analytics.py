from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import analytics
from ..config import Settings, get_settings
from ..database import get_db
from ..schemas import CategoryShare, MonthPoint, Summary

router = APIRouter(prefix="/analytics", tags=["indicadores"])


def _check_range(date_from: Optional[date], date_to: Optional[date]) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from no puede ser posterior a date_to")


@router.get("/summary", response_model=Summary)
def summary(date_from: Optional[date] = None, date_to: Optional[date] = None,
            db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> Summary:
    _check_range(date_from, date_to)
    return Summary(**analytics.summary(db, date_from, date_to, settings.default_currency))


@router.get("/by-category", response_model=list[CategoryShare])
def by_category(date_from: Optional[date] = None, date_to: Optional[date] = None,
                type: str = Query("expense", pattern="^(income|expense)$"),
                db: Session = Depends(get_db)) -> list[CategoryShare]:
    _check_range(date_from, date_to)
    return [CategoryShare(**row) for row in analytics.by_category(db, date_from, date_to, type)]


@router.get("/monthly", response_model=list[MonthPoint])
def monthly(months: int = Query(6, ge=1, le=36), db: Session = Depends(get_db)) -> list[MonthPoint]:
    return [MonthPoint(**row) for row in analytics.monthly(db, months)]
