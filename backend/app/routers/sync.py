from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..database import get_db
from ..models import SyncRun
from ..schemas import SyncReport, SyncRunOut
from ..sync_service import run_sync

router = APIRouter(prefix="/sync", tags=["sincronización"])


@router.post("", response_model=SyncReport)
def sync(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> SyncReport:
    """Consume las tres APIs, normaliza, deduplica y guarda los movimientos nuevos."""
    return SyncReport(**run_sync(db, settings))


@router.get("/runs", response_model=list[SyncRunOut])
def runs(limit: int = 20, db: Session = Depends(get_db)) -> list[SyncRunOut]:
    stmt = select(SyncRun).order_by(SyncRun.id.desc()).limit(max(1, min(limit, 100)))
    return [SyncRunOut.model_validate(r) for r in db.execute(stmt).scalars()]
