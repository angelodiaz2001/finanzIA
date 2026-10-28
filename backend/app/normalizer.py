"""Validación y normalización de los movimientos de las tres fuentes.

Cada API devuelve estructuras distintas (nombres de campos, signos, fechas).
Este módulo las transforma a una estructura común (NormalizedTx) y rechaza los
datos inválidos antes de que lleguen a la base de datos.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Literal, Optional

TxType = Literal["income", "expense"]


class NormalizationError(ValueError):
    """El dato recibido es inválido y no puede convertirse a la estructura común."""


class SkippedEvent(Exception):
    """El evento es válido pero no representa una transacción utilizable."""


@dataclass
class NormalizedTx:
    source: str
    external_id: str
    occurred_at: datetime
    amount: float
    type: TxType
    currency: str
    description: str
    merchant: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time(12, 0))
    elif isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise NormalizationError(f"fecha inválida: {value!r}") from exc
    else:
        raise NormalizationError(f"fecha ausente o inválida: {value!r}")
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.replace(microsecond=0)


def _clean_text(value: Any, max_len: int = 255) -> str:
    text = " ".join(str(value or "").split())
    return text[:max_len]


def _require(payload: dict[str, Any], *keys: str) -> None:
    missing = [k for k in keys if payload.get(k) in (None, "")]
    if missing:
        raise NormalizationError(f"faltan campos obligatorios: {', '.join(missing)}")


def validate(tx: NormalizedTx) -> NormalizedTx:
    try:
        tx.amount = round(float(tx.amount), 2)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(f"importe inválido: {tx.amount!r}") from exc
    if not math.isfinite(tx.amount) or tx.amount <= 0:
        raise NormalizationError(f"el importe debe ser mayor que cero: {tx.amount}")
    if tx.type not in ("income", "expense"):
        raise NormalizationError(f"tipo inválido: {tx.type!r}")
    tx.currency = (tx.currency or "").strip().upper()
    if len(tx.currency) != 3:
        raise NormalizationError(f"moneda inválida: {tx.currency!r}")
    tx.description = _clean_text(tx.description)
    if not tx.description:
        raise NormalizationError("descripción vacía")
    tx.external_id = _clean_text(tx.external_id, 64)
    if not tx.external_id:
        raise NormalizationError("identificador externo vacío")
    if tx.merchant is not None:
        tx.merchant = _clean_text(tx.merchant, 120) or None
    return tx


# --------------------------------------------------------------------------- #
# Fuente 1: API bancaria
# --------------------------------------------------------------------------- #
def from_bank(payload: dict[str, Any]) -> NormalizedTx:
    _require(payload, "transaction_id", "posted_at", "amount", "type", "description", "currency")
    kind = str(payload["type"]).upper()
    if kind == "DEBIT":
        tx_type: TxType = "expense"
    elif kind == "CREDIT":
        tx_type = "income"
    else:
        raise NormalizationError(f"tipo bancario desconocido: {kind}")
    return validate(NormalizedTx(
        source="bank",
        external_id=str(payload["transaction_id"]),
        occurred_at=parse_datetime(payload["posted_at"]),
        amount=payload["amount"],
        type=tx_type,
        currency=str(payload["currency"]),
        description=str(payload["description"]),
        merchant=payload.get("merchant"),
        raw=dict(payload),
    ))


# --------------------------------------------------------------------------- #
# Fuente 2: billetera digital
# --------------------------------------------------------------------------- #
def from_wallet(payload: dict[str, Any], currency: str) -> NormalizedTx:
    _require(payload, "movement_id", "created_at", "amount", "direction", "concept")
    direction = str(payload["direction"]).upper()
    if direction == "IN":
        tx_type: TxType = "income"
    elif direction == "OUT":
        tx_type = "expense"
    else:
        raise NormalizationError(f"dirección desconocida: {direction}")
    return validate(NormalizedTx(
        source="wallet",
        external_id=str(payload["movement_id"]),
        occurred_at=parse_datetime(payload["created_at"]),
        amount=payload["amount"],
        type=tx_type,
        currency=currency,
        description=str(payload["concept"]),
        merchant=payload.get("counterparty"),
        raw=dict(payload),
    ))


# --------------------------------------------------------------------------- #
# Fuente 3: notificaciones (eventos ya analizados por la API de notificaciones)
# --------------------------------------------------------------------------- #
def from_notification(payload: dict[str, Any], min_confidence: float, default_currency: str) -> NormalizedTx:
    _require(payload, "event_id", "received_at")
    parsed = payload.get("parsed") or {}
    movement_type = parsed.get("movement_type")
    if movement_type not in ("income", "expense"):
        raise SkippedEvent("tipo de movimiento desconocido")
    if parsed.get("amount") is None:
        raise SkippedEvent("sin importe reconocible")
    confidence = float(parsed.get("confidence") or 0)
    if confidence < min_confidence:
        raise SkippedEvent(f"confianza {confidence:.2f} inferior al mínimo {min_confidence:.2f}")

    if parsed.get("event_date"):
        occurred_at = parse_datetime(parsed["event_date"])
    else:
        occurred_at = parse_datetime(payload["received_at"])

    merchant = parsed.get("merchant")
    if isinstance(merchant, str) and merchant.isupper():
        merchant = merchant.title()

    return validate(NormalizedTx(
        source="notification",
        external_id=str(payload["event_id"]),
        occurred_at=occurred_at,
        amount=parsed["amount"],
        type=movement_type,
        currency=str(parsed.get("currency") or default_currency),
        description=str(parsed.get("description") or payload.get("raw_text") or ""),
        merchant=merchant,
        raw=dict(payload),
    ))
