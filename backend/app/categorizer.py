"""Categorización de movimientos mediante reglas por palabras clave.

Es la categorización determinista del backend. El asistente de IA puede
sugerir una categoría alternativa (ver ai/assistant.py), pero las reglas
garantizan que toda transacción tenga categoría aunque la IA no esté
configurada.
"""
from __future__ import annotations

from typing import Optional

from .textutil import normalize

INTERNAL_TRANSFERS = "Transferencias internas"
DEFAULT_EXPENSE = "Otros gastos"
DEFAULT_INCOME = "Otros ingresos"

# El orden importa: se devuelve la primera regla que coincide.
EXPENSE_RULES: list[tuple[str, list[str]]] = [
    (INTERNAL_TRANSFERS, ["transferencia a billetera", "recarga desde cuenta", "recarga desde tarjeta",
                          "recarga desde agente", "pago tarjeta de credito", "pago recibido - tarjeta"]),
    ("Vivienda", ["alquiler", "arriendo", "hipoteca", "condominio", "departamento"]),
    ("Servicios", ["recibo de luz", "electr", "recibo de agua", "agua sim", "internet", "cable",
                   "telefon", "celular", "telco", "gas natural", "recarga celular"]),
    ("Educación", ["pension", "universidad", "instituto", "diplomado", "colegio", "curso",
                   "matricula", "libreria", "libro"]),
    ("Mascotas", ["veterinaria", "mascota", "patitas"]),
    ("Salud", ["farmacia", "botica", "clinica", "medic", "dentista", "hospital", "seguro de salud"]),
    ("Transporte", ["movilidad", "taxi", "grifo", "gasolina", "combustible", "peaje", "pasaje",
                    "estacionamiento", "metro ", "bus "]),
    ("Alimentación", ["supermercado", "minimarket", "bodega", "mercado", "restaurante", "polleria",
                      "pizzeria", "cafe", "jugueria", "delivery", "comida", "almuerzo", "panaderia"]),
    ("Entretenimiento", ["cine", "streaming", "suscripcion", "musica", "video", "concierto", "juego"]),
    ("Hogar y cuidado personal", ["lavanderia", "peluqueria", "barberia", "limpieza", "ferreteria"]),
    ("Compras", ["tienda", "ropa", "zapatillas", "electronica", "compra online", "libreria"]),
    ("Retiros de efectivo", ["retiro", "cajero", "atm "]),
    ("Transferencias enviadas", ["envio a", "enviaste", "transferencia a", "transferiste"]),
]

INCOME_RULES: list[tuple[str, list[str]]] = [
    (INTERNAL_TRANSFERS, ["recarga desde cuenta", "recarga desde tarjeta", "recarga desde agente",
                          "pago recibido - tarjeta", "transferencia a billetera"]),
    ("Salario", ["planilla", "sueldo", "salario", "haberes", "remuneracion", "nomina"]),
    ("Reembolsos", ["devolucion", "reembolso", "extorno"]),
    ("Transferencias recibidas", ["recibiste", "transferencia recibida", "te envio", "abono de",
                                  "deposito", "transferencia de"]),
    ("Intereses y otros", ["interes", "rendimiento", "dividendo"]),
]


def _ordered_unique(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


EXPENSE_CATEGORIES = _ordered_unique([c for c, _ in EXPENSE_RULES] + [DEFAULT_EXPENSE])
INCOME_CATEGORIES = _ordered_unique([c for c, _ in INCOME_RULES] + [DEFAULT_INCOME])
ALL_CATEGORIES = _ordered_unique(EXPENSE_CATEGORIES + INCOME_CATEGORIES)


def categorize(description: str, merchant: Optional[str], tx_type: str) -> tuple[str, Optional[str]]:
    """Devuelve (categoría, palabra clave que la justificó o None)."""
    text = normalize(f"{description or ''} {merchant or ''}") + " "
    rules = INCOME_RULES if tx_type == "income" else EXPENSE_RULES
    for category, keywords in rules:
        for keyword in keywords:
            if keyword in text:
                return category, keyword
    return (DEFAULT_INCOME if tx_type == "income" else DEFAULT_EXPENSE), None
