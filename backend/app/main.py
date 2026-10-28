"""Backend principal de FinanzIA.

Consume las tres APIs simuladas, normaliza y deduplica los movimientos, los
guarda en la base de datos, calcula indicadores y expone el asistente de IA.

Arranque (desde la raíz del repositorio):
    uvicorn backend.app.main:app --port 8000 --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .ai import assistant
from .clients import ping
from .config import Settings, get_settings
from .database import get_db, init_db
from .routers import analytics, assistant as assistant_router, catalog, sync, transactions
from .schemas import HealthOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Prototipo académico. Integra tres fuentes simuladas (banco, billetera digital y "
        "notificaciones) en una estructura común y expone indicadores y un asistente de IA. "
        "No administra dinero real ni se conecta a entidades financieras reales."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
app.include_router(sync.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(assistant_router.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health", response_model=HealthOut, tags=["sistema"])
def health(db: Session = Depends(get_db), cfg: Settings = Depends(get_settings)) -> HealthOut:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:  # noqa: BLE001
        database = f"error: {exc.__class__.__name__}"
    sources = {
        "bank": ping(cfg.bank_api_url),
        "wallet": ping(cfg.wallet_api_url),
        "notification": ping(cfg.notifications_api_url),
    }
    status = "ok" if database == "ok" and all(v == "ok" for v in sources.values()) else "degraded"
    return HealthOut(status=status, database=database, sources=sources, ai_configured=assistant.is_configured(cfg))
