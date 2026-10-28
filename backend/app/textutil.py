"""Utilidades de texto compartidas por la categorización y la deduplicación."""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "de", "del", "la", "el", "en", "con", "por", "a", "y", "al", "los", "las", "un", "una",
    "tu", "su", "es", "sim", "pen", "usd", "app", "pos", "web", "atm", "consumo", "pago",
    "compra", "aprobada", "para", "con", "tarjeta", "nuevo", "saldo",
}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", strip_accents(text or "").lower()).strip()


def tokens(text: str | None) -> set[str]:
    """Palabras significativas (sin acentos, sin stopwords, sin números sueltos)."""
    out: set[str] = set()
    for tok in re.split(r"[^a-z0-9]+", normalize(text)):
        if len(tok) < 3 or tok in STOPWORDS or tok.isdigit():
            continue
        out.add(tok)
    return out
