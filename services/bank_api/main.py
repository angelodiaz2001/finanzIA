"""API bancaria simulada de FinanzIA.

Servicio ficticio que expone cuentas, saldos y transacciones de un "banco".
NO se conecta a ninguna entidad financiera real: todos los datos se generan en
memoria a partir de una semilla fija, de modo que las respuestas sean
reproducibles entre reinicios (los identificadores se derivan del contenido).

Puerto sugerido: 8001  ->  uvicorn services.bank_api.main:app --port 8001
"""
from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, time, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

CURRENCY = "PEN"
SEED = 2026
DAYS_OF_HISTORY = 90

app = FastAPI(
    title="FinanzIA - API Bancaria (simulada)",
    version="0.1.0",
    description=(
        "Fuente de datos ficticia que imita a un banco: cuentas, saldos y "
        "transacciones. Los datos son generados y no corresponden a ninguna "
        "entidad financiera real."
    ),
)


# --------------------------------------------------------------------------- #
# Modelos (contrato de respuesta)
# --------------------------------------------------------------------------- #
class Account(BaseModel):
    account_id: str
    account_type: Literal["AHORROS", "CORRIENTE", "CREDITO"]
    alias: str
    holder: str
    currency: str
    balance: float = Field(description="Saldo disponible. En tarjetas de crédito es el crédito disponible.")


class BankTransaction(BaseModel):
    transaction_id: str
    account_id: str
    posted_at: datetime
    amount: float = Field(gt=0, description="Monto siempre positivo; el sentido lo indica el campo type.")
    type: Literal["DEBIT", "CREDIT"]
    description: str
    merchant: Optional[str] = None
    channel: Literal["POS", "ATM", "WEB", "APP", "TRANSFER", "PAYROLL"]
    status: Literal["POSTED", "PENDING"]
    currency: str


# --------------------------------------------------------------------------- #
# Generación de datos ficticios
# --------------------------------------------------------------------------- #
ACCOUNTS: dict[str, Account] = {
    "ACC-0001": Account(
        account_id="ACC-0001", account_type="AHORROS", alias="Cuenta Sueldo",
        holder="USUARIO DEMO", currency=CURRENCY, balance=0.0,
    ),
    "ACC-0002": Account(
        account_id="ACC-0002", account_type="CREDITO", alias="Tarjeta Visa Sim ****4321",
        holder="USUARIO DEMO", currency=CURRENCY, balance=0.0,
    ),
}
INITIAL_BALANCE = {"ACC-0001": 2500.00, "ACC-0002": 5000.00}  # para CREDITO: línea disponible

# (comercio, canal, rango de montos, cuenta preferida)
MERCHANTS = [
    ("Supermercado La Canasta", "POS", (80.0, 260.0), "ACC-0001"),
    ("Minimarket Don Pepe", "POS", (8.0, 45.0), "ACC-0001"),
    ("Restaurante El Fogón", "POS", (35.0, 120.0), "ACC-0002"),
    ("Pollería Doña Rosa", "POS", (28.0, 75.0), "ACC-0001"),
    ("Café Aroma", "POS", (9.0, 25.0), "ACC-0001"),
    ("Grifo Ruta Norte", "POS", (60.0, 150.0), "ACC-0002"),
    ("Movilidad Urbana App", "APP", (7.0, 30.0), "ACC-0001"),
    ("Farmacia Vida", "POS", (15.0, 90.0), "ACC-0001"),
    ("Cine Estelar", "WEB", (20.0, 60.0), "ACC-0002"),
    ("Tienda de Ropa Urbana", "POS", (60.0, 220.0), "ACC-0002"),
    ("Librería Central", "POS", (25.0, 120.0), "ACC-0001"),
    ("Veterinaria Patitas", "POS", (40.0, 160.0), "ACC-0002"),
]

# (día del mes, descripción, tipo, monto o rango, canal, cuenta)
MONTHLY_ITEMS = [
    (1, "Abono planilla - Empresa Ficticia SAC", "CREDIT", 4200.00, "PAYROLL", "ACC-0001"),
    (3, "Pago alquiler departamento", "DEBIT", 1100.00, "TRANSFER", "ACC-0001"),
    (10, "Recibo de luz - Electro Sim", "DEBIT", (90.0, 140.0), "WEB", "ACC-0001"),
    (12, "Recibo de agua - Agua Sim", "DEBIT", (40.0, 70.0), "WEB", "ACC-0001"),
    (15, "Internet y cable - Conecta Sim", "DEBIT", 129.00, "WEB", "ACC-0001"),
    (18, "Suscripción Video Streaming Sim", "DEBIT", 29.90, "WEB", "ACC-0002"),
    (20, "Pensión diplomado - Instituto Sim", "DEBIT", 450.00, "WEB", "ACC-0001"),
    (25, "Pago tarjeta de crédito ****4321", "DEBIT", 900.00, "TRANSFER", "ACC-0001"),
    (25, "Pago recibido - tarjeta ****4321", "CREDIT", 900.00, "TRANSFER", "ACC-0002"),
]

# Movimientos fijos relativos a HOY. Varios de ellos también aparecen como
# notificaciones en la API de notificaciones para demostrar la detección de
# duplicados entre fuentes en el backend principal.
FIXED_RELATIVE = [
    (-1, "Farmacia Vida", "DEBIT", 45.50, "POS", "ACC-0001", "Farmacia Vida"),
    (-2, "Transferencia a billetera digital", "DEBIT", 200.00, "APP", "ACC-0001", None),
    (-3, "Supermercado La Canasta", "DEBIT", 189.90, "POS", "ACC-0001", "Supermercado La Canasta"),
    (-5, "Devolución Tienda de Ropa Urbana", "CREDIT", 150.00, "POS", "ACC-0002", "Tienda de Ropa Urbana"),
    (-6, "Retiro cajero ATM Av. Principal", "DEBIT", 100.00, "ATM", "ACC-0001", None),
    (-9, "Transferencia recibida de Ana P.", "CREDIT", 80.00, "TRANSFER", "ACC-0001", None),
]


def _tx_id(account_id: str, when: datetime, description: str, amount: float) -> str:
    """Identificador estable derivado del contenido (no cambia entre reinicios)."""
    raw = f"{account_id}|{when.date().isoformat()}|{description}|{amount:.2f}"
    return "BNK-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


def _amount(rng: random.Random, spec) -> float:
    if isinstance(spec, tuple):
        return round(rng.uniform(*spec), 2)
    return float(spec)


def generate_transactions(today: date | None = None) -> list[BankTransaction]:
    today = today or date.today()
    rng = random.Random(SEED)
    txs: list[BankTransaction] = []
    start = today - timedelta(days=DAYS_OF_HISTORY)

    for offset in range(DAYS_OF_HISTORY + 1):
        day = start + timedelta(days=offset)

        # Cargos y abonos fijos del mes
        for dom, desc, ttype, spec, channel, acc in MONTHLY_ITEMS:
            if day.day == dom:
                when = datetime.combine(day, time(9, 0))
                amt = _amount(rng, spec)
                txs.append(BankTransaction(
                    transaction_id=_tx_id(acc, when, desc, amt), account_id=acc,
                    posted_at=when, amount=amt, type=ttype, description=desc,
                    merchant=None, channel=channel, status="POSTED", currency=CURRENCY,
                ))

        # Consumos variables (0 a 3 por día)
        n = rng.choices([0, 1, 2, 3], weights=[45, 35, 15, 5])[0]
        for _ in range(n):
            merchant, channel, rng_amt, acc = rng.choice(MERCHANTS)
            when = datetime.combine(day, time(rng.randint(8, 21), rng.randint(0, 59)))
            amt = _amount(rng, rng_amt)
            desc = f"Consumo {channel} {merchant.upper()}"
            txs.append(BankTransaction(
                transaction_id=_tx_id(acc, when, desc, amt), account_id=acc,
                posted_at=when, amount=amt, type="DEBIT", description=desc,
                merchant=merchant, channel=channel, status="POSTED", currency=CURRENCY,
            ))

    for rel, desc, ttype, amt, channel, acc, merchant in FIXED_RELATIVE:
        when = datetime.combine(today + timedelta(days=rel), time(12, 30))
        txs.append(BankTransaction(
            transaction_id=_tx_id(acc, when, desc, amt), account_id=acc,
            posted_at=when, amount=amt, type=ttype, description=desc,
            merchant=merchant, channel=channel,
            status="PENDING" if rel == -1 else "POSTED", currency=CURRENCY,
        ))

    txs.sort(key=lambda t: t.posted_at)
    return txs


TRANSACTIONS: list[BankTransaction] = generate_transactions()


def _refresh_balances() -> None:
    for acc_id, account in ACCOUNTS.items():
        bal = INITIAL_BALANCE[acc_id]
        for t in TRANSACTIONS:
            if t.account_id != acc_id:
                continue
            bal += t.amount if t.type == "CREDIT" else -t.amount
        account.balance = round(bal, 2)


_refresh_balances()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
def _filter(items: list[BankTransaction], from_date: date | None, to_date: date | None,
            limit: int) -> list[BankTransaction]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="El parámetro from no puede ser posterior a to")
    out = [
        t for t in items
        if (from_date is None or t.posted_at.date() >= from_date)
        and (to_date is None or t.posted_at.date() <= to_date)
    ]
    out.sort(key=lambda t: t.posted_at, reverse=True)
    return out[:limit]


@app.get("/health", tags=["sistema"])
def health() -> dict:
    return {"status": "ok", "service": "bank-api", "simulated": True}


@app.get("/accounts", response_model=list[Account], tags=["cuentas"])
def list_accounts() -> list[Account]:
    return list(ACCOUNTS.values())


@app.get("/accounts/{account_id}", response_model=Account, tags=["cuentas"])
def get_account(account_id: str) -> Account:
    account = ACCOUNTS.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return account


@app.get("/accounts/{account_id}/transactions", response_model=list[BankTransaction], tags=["transacciones"])
def account_transactions(
    account_id: str,
    from_date: date | None = Query(None, alias="from", description="Fecha inicial (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="Fecha final (YYYY-MM-DD)"),
    limit: int = Query(500, ge=1, le=2000),
) -> list[BankTransaction]:
    if account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return _filter([t for t in TRANSACTIONS if t.account_id == account_id], from_date, to_date, limit)


@app.get("/transactions", response_model=list[BankTransaction], tags=["transacciones"])
def all_transactions(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    limit: int = Query(1000, ge=1, le=5000),
) -> list[BankTransaction]:
    """Transacciones de todas las cuentas del titular (más recientes primero)."""
    return _filter(TRANSACTIONS, from_date, to_date, limit)
