"""Detección de transacciones duplicadas.

Dos niveles:
1. Duplicado exacto: misma fuente y mismo identificador externo (se resuelve
   con la restricción única de la tabla y una consulta previa).
2. Duplicado entre fuentes: el mismo movimiento de dinero reportado por dos
   fuentes distintas (p. ej. una compra que aparece en la API bancaria y en
   una notificación). Se detecta por importe igual, mismo tipo, fecha cercana
   y descripción/comercio similares.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Transaction
from .normalizer import NormalizedTx
from .textutil import normalize, tokens

AMOUNT_TOLERANCE = 0.005


def similarity(a_description: str, a_merchant: Optional[str],
               b_description: str, b_merchant: Optional[str]) -> float:
    """Similitud entre 0 y 1 basada en palabras compartidas (contención)."""
    if a_merchant and b_merchant and normalize(a_merchant) == normalize(b_merchant):
        return 1.0
    ta = tokens(f"{a_description} {a_merchant or ''}")
    tb = tokens(f"{b_description} {b_merchant or ''}")
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def find_cross_source_duplicate(db: Session, tx: NormalizedTx, window_hours: int,
                                threshold: float) -> Optional[Transaction]:
    """Devuelve la transacción existente (de otra fuente) que parece ser el mismo movimiento."""
    window = timedelta(hours=window_hours)
    stmt = (
        select(Transaction)
        .where(Transaction.source != tx.source)
        .where(Transaction.type == tx.type)
        .where(Transaction.is_duplicate.is_(False))
        .where(Transaction.amount >= tx.amount - AMOUNT_TOLERANCE)
        .where(Transaction.amount <= tx.amount + AMOUNT_TOLERANCE)
        .where(Transaction.occurred_at >= tx.occurred_at - window)
        .where(Transaction.occurred_at <= tx.occurred_at + window)
    )
    best: Optional[Transaction] = None
    best_score = 0.0
    for candidate in db.execute(stmt).scalars():
        score = similarity(tx.description, tx.merchant, candidate.description, candidate.merchant)
        if score > best_score:
            best, best_score = candidate, score
    if best is not None and best_score >= threshold:
        return best
    return None
