"""Extracción de información estructurada a partir de notificaciones financieras.

Recibe el texto crudo de un SMS / correo / push (como los que envían bancos y
billeteras) y extrae importe, moneda, tipo de movimiento, comercio o
contraparte, últimos dígitos de tarjeta y fecha. Es la función distintiva de
la tercera API: transforma un evento sin procesar en datos estructurados.

La extracción usa heurísticas (expresiones regulares y palabras clave), por lo
que devuelve un nivel de confianza en lugar de garantizar exactitud.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

MovementType = Literal["expense", "income", "unknown"]

# Patrones de importe: "S/ 45.90", "S/. 1,250.00", "US$ 5.99", "$ 20", "PEN 30.00", "USD 10"
AMOUNT_RE = re.compile(
    r"(?P<cur>S/\.?|PEN|USD|US\$|\$|EUR|€)\s*(?P<amt>\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)
AMOUNT_FALLBACK_RE = re.compile(r"(?:monto|importe|por|de)\s+(?:de\s+)?(?P<amt>\d+(?:[.,]\d{1,2})?)", re.IGNORECASE)
CARD_RE = re.compile(r"\*{2,}\s?(?P<last4>\d{4})")
DATE_RE = re.compile(r"\b(?P<d>\d{1,2})/(?P<m>\d{1,2})(?:/(?P<y>\d{2,4}))?\b")

EXPENSE_KEYWORDS = [
    "consumo", "compra", "pago de", "pagaste", "pago realizado", "pago aprobado", "cargo",
    "retiro", "debito", "enviaste", "transferiste", "transferencia enviada", "retiraste",
    "pago en", "aprobada por", "suscripcion",
]
INCOME_KEYWORDS = [
    "abono", "acredit", "recibiste", "deposito", "devolucion", "reembolso", "ingreso",
    "transferencia recibida", "te envio", "pago recibido",
]
NON_MOVEMENT_KEYWORDS = ["vence", "vencimiento", "recordatorio", "codigo de verificacion", "clave"]

CURRENCY_MAP = {"s/": "PEN", "s/.": "PEN", "pen": "PEN", "usd": "USD", "us$": "USD", "$": "USD", "eur": "EUR", "€": "EUR"}

# Caracteres permitidos dentro de un nombre de comercio / contraparte
_NAME = r"[\wÁÉÍÓÚÑáéíóúñ&.\-\x27 ]"


@dataclass
class ParsedInfo:
    amount: Optional[float] = None
    currency: Optional[str] = None
    movement_type: MovementType = "unknown"
    description: str = ""
    merchant: Optional[str] = None
    card_last4: Optional[str] = None
    event_date: Optional[date] = None
    confidence: float = 0.0
    signals: list[str] = field(default_factory=list)


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _parse_amount(raw: str) -> float:
    """Convierte 1,250.00 / 1.250,00 / 45,90 / 45.90 a float."""
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):   # formato europeo 1.250,00
            raw = raw.replace(".", "").replace(",", ".")
        else:                                 # formato 1,250.00
            raw = raw.replace(",", "")
    elif "," in raw:
        head, _, tail = raw.rpartition(",")
        raw = f"{head}.{tail}" if len(tail) <= 2 else raw.replace(",", "")
    return round(float(raw), 2)


def _extract_merchant(text: str, movement_type: MovementType) -> Optional[str]:
    # "en SUPERMERCADO LA CANASTA el 12/10", "en FARMACIA VIDA ****0001", "en Bodega San Martín."
    in_pattern = (
        r"\ben\s+(?P<m>[A-ZÁÉÍÓÚÑ]" + _NAME + r"{2,60}?)"
        r"(?=\s+(?:el\s+\d|con\s|por\s|\*{2,}|\d{1,2}/\d{1,2})|[.,;]|$)"
    )
    # "a Carlos R. Tu nuevo saldo", "para María L."
    to_pattern = (
        r"\b(?:a|para)\s+(?P<m>[A-ZÁÉÍÓÚÑ]" + _NAME + r"{1,40}?)"
        r"(?=\s+(?:por\s|el\s|tu\s|su\s|desde\s)|[.,;]|$)"
    )
    # "de EMPRESA FICTICIA SAC el 01/10", "desde Banco Sim"
    from_pattern = (
        r"\b(?:de|desde)\s+(?P<m>[A-ZÁÉÍÓÚÑ]" + _NAME + r"{2,60}?)"
        r"(?=\s+(?:el\s+\d|por\s|con\s)|[.,;]|$)"
    )
    patterns = [in_pattern, to_pattern, from_pattern]
    if movement_type == "income":
        patterns = [from_pattern, in_pattern]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group("m").strip(" .,-")
            if candidate.lower() in {"tu", "su", "la", "el"} or len(candidate) < 3:
                continue
            return candidate
    return None


def parse_notification(raw_text: str, received_on: Optional[date] = None) -> ParsedInfo:
    info = ParsedInfo()
    text = re.sub(r"\s+", " ", raw_text or "").strip()
    info.description = text
    if not text:
        return info
    plain = _strip_accents(text).lower()
    score = 0.0

    # --- Importe y moneda -------------------------------------------------
    m = AMOUNT_RE.search(text)
    if m:
        try:
            info.amount = _parse_amount(m.group("amt"))
            info.currency = CURRENCY_MAP.get(m.group("cur").lower(), m.group("cur").upper())
            score += 0.4
            info.signals.append("amount:currency_prefix")
        except ValueError:
            pass
    if info.amount is None:
        m2 = AMOUNT_FALLBACK_RE.search(plain)
        if m2:
            try:
                info.amount = _parse_amount(m2.group("amt"))
                score += 0.25
                info.signals.append("amount:keyword")
            except ValueError:
                pass

    # --- Tipo de movimiento ----------------------------------------------
    strong_expense = any(k in plain for k in ("pagaste", "pago realizado", "consumo", "compra aprobada"))
    if any(k in plain for k in NON_MOVEMENT_KEYWORDS) and not strong_expense:
        info.movement_type = "unknown"
        info.signals.append("type:non_movement_hint")
    elif any(k in plain for k in INCOME_KEYWORDS):
        info.movement_type = "income"
        score += 0.3
        info.signals.append("type:income_keyword")
    elif any(k in plain for k in EXPENSE_KEYWORDS):
        info.movement_type = "expense"
        score += 0.3
        info.signals.append("type:expense_keyword")

    # --- Comercio / contraparte ------------------------------------------
    info.merchant = _extract_merchant(text, info.movement_type)
    if info.merchant:
        score += 0.2
        info.signals.append("merchant:pattern")

    # --- Tarjeta y fecha --------------------------------------------------
    c = CARD_RE.search(text)
    if c:
        info.card_last4 = c.group("last4")
    d = DATE_RE.search(text)
    if d:
        try:
            base = received_on or date.today()
            year = int(d.group("y")) if d.group("y") else base.year
            if year < 100:
                year += 2000
            candidate = date(year, int(d.group("m")), int(d.group("d")))
            if not d.group("y") and candidate > base:
                candidate = date(year - 1, candidate.month, candidate.day)
            info.event_date = candidate
            score += 0.1
            info.signals.append("date:pattern")
        except ValueError:
            pass

    info.confidence = round(min(score, 1.0), 2)
    return info
