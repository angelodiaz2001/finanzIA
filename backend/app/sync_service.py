"""Orquestación de la sincronización: consumir las 3 APIs, normalizar,
deduplicar, categorizar y persistir en la base de datos."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import clients
from .categorizer import categorize
from .config import Settings
from .dedup import find_cross_source_duplicate
from .models import Account, SyncRun, Transaction
from .normalizer import NormalizationError, NormalizedTx, SkippedEvent, from_bank, from_notification, from_wallet

log = logging.getLogger(__name__)

Fetcher = Callable[[Settings], dict[str, Any]]
PRIMARY_SOURCES = {"bank", "wallet"}

DEFAULT_FETCHERS: dict[str, Fetcher] = {
    "bank": clients.fetch_bank,
    "wallet": clients.fetch_wallet,
    "notification": clients.fetch_notifications,
}


def _upsert_account(db: Session, source: str, external_id: str, name: str, account_type: str,
                    currency: str, balance: float) -> None:
    acc = db.execute(
        select(Account).where(Account.source == source, Account.external_id == external_id)
    ).scalar_one_or_none()
    if acc is None:
        acc = Account(source=source, external_id=external_id, name=name, account_type=account_type,
                      currency=currency, balance=balance)
        db.add(acc)
    else:
        acc.name, acc.account_type, acc.currency, acc.balance = name, account_type, currency, balance


def _persist(db: Session, tx: NormalizedTx, settings: Settings, report: dict[str, Any]) -> None:
    existing = db.execute(
        select(Transaction).where(Transaction.source == tx.source, Transaction.external_id == tx.external_id)
    ).scalar_one_or_none()
    if existing is not None:
        report["duplicates_exact"] += 1
        return

    category, _ = categorize(tx.description, tx.merchant, tx.type)
    match = find_cross_source_duplicate(db, tx, settings.dedup_window_hours, settings.dedup_similarity_threshold)

    row = Transaction(
        source=tx.source, external_id=tx.external_id, occurred_at=tx.occurred_at, amount=tx.amount,
        type=tx.type, currency=tx.currency, description=tx.description, merchant=tx.merchant,
        category=category, category_source="rules", raw=tx.raw,
    )
    db.add(row)
    db.flush()

    if match is None:
        report["inserted"][tx.source] += 1
        return

    # Las fuentes primarias (banco, billetera) prevalecen sobre las notificaciones.
    if tx.source in PRIMARY_SOURCES and match.source not in PRIMARY_SOURCES:
        match.is_duplicate = True
        match.duplicate_of_id = row.id
        report["inserted"][tx.source] += 1
    else:
        row.is_duplicate = True
        row.duplicate_of_id = match.id
    report["duplicates_cross"] += 1


def run_sync(db: Session, settings: Settings, fetchers: dict[str, Fetcher] | None = None) -> dict[str, Any]:
    fetchers = fetchers or DEFAULT_FETCHERS
    run = SyncRun(started_at=datetime.now().replace(microsecond=0), status="running")
    db.add(run)
    db.flush()

    report: dict[str, Any] = {
        "run_id": run.id, "started_at": run.started_at, "finished_at": None, "status": "running",
        "fetched": {"bank": 0, "wallet": 0, "notification": 0},
        "inserted": {"bank": 0, "wallet": 0, "notification": 0},
        "duplicates_exact": 0, "duplicates_cross": 0, "skipped": 0, "rejected": 0,
        "errors": [],    # fuentes que no respondieron
        "warnings": [],  # registros rechazados por validación
    }

    def handle(source: str, items: list[dict[str, Any]], convert: Callable[[dict[str, Any]], NormalizedTx]) -> None:
        report["fetched"][source] = len(items)
        for item in items:
            try:
                tx = convert(item)
            except SkippedEvent as exc:
                report["skipped"] += 1
                log.debug("%s: evento omitido (%s)", source, exc)
                continue
            except NormalizationError as exc:
                report["rejected"] += 1
                report["warnings"].append(f"{source}: registro rechazado ({exc})")
                continue
            _persist(db, tx, settings, report)

    # 1) Banco --------------------------------------------------------------
    try:
        data = fetchers["bank"](settings)
        for acc in data.get("accounts", []):
            _upsert_account(db, "bank", str(acc["account_id"]), str(acc.get("alias") or acc["account_id"]),
                            str(acc.get("account_type", "")), str(acc.get("currency", settings.default_currency)),
                            float(acc.get("balance", 0)))
        handle("bank", data.get("transactions", []), from_bank)
    except clients.SourceUnavailable as exc:
        report["errors"].append(f"bank: {exc}")

    # 2) Billetera ----------------------------------------------------------
    try:
        data = fetchers["wallet"](settings)
        wallet = data.get("wallet") or {}
        currency = str(wallet.get("currency") or settings.default_currency)
        if wallet:
            _upsert_account(db, "wallet", str(wallet["wallet_id"]), f"Billetera {wallet.get('owner', '')}".strip(),
                            "BILLETERA", currency, float(wallet.get("balance", 0)))
        handle("wallet", data.get("movements", []), lambda m: from_wallet(m, currency))
    except clients.SourceUnavailable as exc:
        report["errors"].append(f"wallet: {exc}")

    # 3) Notificaciones -----------------------------------------------------
    try:
        data = fetchers["notification"](settings)
        handle("notification", data.get("events", []),
               lambda e: from_notification(e, settings.notification_min_confidence, settings.default_currency))
    except clients.SourceUnavailable as exc:
        report["errors"].append(f"notification: {exc}")

    source_failures = len(report["errors"])
    report["status"] = "error" if source_failures == 3 else "partial" if source_failures else "ok"
    report["finished_at"] = datetime.now().replace(microsecond=0)

    run.status = report["status"]
    run.finished_at = report["finished_at"]
    run.report = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in report.items()}
    db.commit()
    return report
