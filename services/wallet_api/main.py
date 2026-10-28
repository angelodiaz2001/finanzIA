"""API de billetera digital simulada de FinanzIA.

Imita una billetera móvil: saldo, movimientos de entrada/salida y operaciones
ficticias (transferencias y recargas). Los nombres de campos son distintos a
los de la API bancaria a propósito: el backend principal debe normalizarlos.

Puerto sugerido: 8002  ->  uvicorn services.wallet_api.main:app --port 8002
"""
from __future__ import annotations

import hashlib
import random
import uuid
from datetime import date, datetime, time, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

CURRENCY = "PEN"
SEED = 7
DAYS_OF_HISTORY = 60

app = FastAPI(
    title="FinanzIA - Billetera Digital (simulada)",
    version="0.1.0",
    description=(
        "Billetera digital ficticia: consulta de saldo y movimientos, y "
        "operaciones de prueba (transferencias, recargas). No mueve dinero real."
    ),
)


# --------------------------------------------------------------------------- #
# Modelos
# --------------------------------------------------------------------------- #
class Wallet(BaseModel):
    wallet_id: str
    owner: str
    phone_masked: str
    currency: str
    balance: float


class Movement(BaseModel):
    movement_id: str
    created_at: datetime
    direction: Literal["IN", "OUT"]
    amount: float = Field(gt=0)
    concept: str
    counterparty: Optional[str] = None
    kind: Literal["TOPUP", "PAYMENT", "TRANSFER", "REFUND", "WITHDRAWAL"]
    reference: Optional[str] = None


class TransferRequest(BaseModel):
    to: str = Field(min_length=2, description="Nombre o teléfono del destinatario (ficticio)")
    amount: float = Field(gt=0)
    concept: str = Field(default="Transferencia", max_length=120)


class TopupRequest(BaseModel):
    amount: float = Field(gt=0)
    source: Literal["BANK", "CASH", "CARD"] = "BANK"


class OperationResult(BaseModel):
    ok: bool
    movement: Movement
    new_balance: float


# --------------------------------------------------------------------------- #
# Datos ficticios
# --------------------------------------------------------------------------- #
WALLET = Wallet(wallet_id="WLT-DEMO-001", owner="Usuario Demo",
                phone_masked="***-***-4455", currency=CURRENCY, balance=0.0)
INITIAL_BALANCE = 150.00

PAYMENT_PLACES = [
    ("Bodega San Martín", (5.0, 40.0)),
    ("Delivery Rápido", (18.0, 65.0)),
    ("Movilidad Urbana App", (6.0, 28.0)),
    ("Juguería La Fresca", (6.0, 18.0)),
    ("Lavandería Express", (15.0, 35.0)),
    ("Recarga celular Telco Sim", (10.0, 30.0)),
]
PEOPLE = ["María L.", "Carlos R.", "Lucía T.", "Jorge M.", "Ana P."]

# Movimientos fijos relativos a hoy (algunos coinciden con notificaciones y
# con la API bancaria para demostrar la deduplicación entre fuentes).
FIXED_RELATIVE = [
    (-2, "IN", 200.00, "Recarga desde cuenta bancaria ****0001", "Banco Sim", "TOPUP"),
    (-4, "OUT", 35.00, "Envío a Carlos R.", "Carlos R.", "TRANSFER"),
    (-8, "IN", 50.00, "Recibiste de Lucía T. - cuota almuerzo", "Lucía T.", "TRANSFER"),
    (-12, "IN", 22.50, "Devolución Delivery Rápido", "Delivery Rápido", "REFUND"),
]


def _mv_id(when: datetime, concept: str, amount: float, direction: str) -> str:
    raw = f"{when.isoformat()}|{concept}|{amount:.2f}|{direction}"
    return "WLT-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


def generate_movements(today: date | None = None) -> list[Movement]:
    today = today or date.today()
    rng = random.Random(SEED)
    out: list[Movement] = []
    start = today - timedelta(days=DAYS_OF_HISTORY)

    for offset in range(DAYS_OF_HISTORY + 1):
        day = start + timedelta(days=offset)
        # Recarga semanal desde el banco (lunes)
        if day.weekday() == 0:
            when = datetime.combine(day, time(8, 15))
            amt = float(rng.choice([100.0, 150.0, 200.0]))
            concept = "Recarga desde cuenta bancaria ****0001"
            out.append(Movement(movement_id=_mv_id(when, concept, amt, "IN"), created_at=when,
                                direction="IN", amount=amt, concept=concept,
                                counterparty="Banco Sim", kind="TOPUP"))
        n = rng.choices([0, 1, 2], weights=[45, 40, 15])[0]
        for _ in range(n):
            when = datetime.combine(day, time(rng.randint(7, 22), rng.randint(0, 59)))
            if rng.random() < 0.7:
                place, rng_amt = rng.choice(PAYMENT_PLACES)
                amt = round(rng.uniform(*rng_amt), 2)
                concept = f"Pago en {place}"
                out.append(Movement(movement_id=_mv_id(when, concept, amt, "OUT"), created_at=when,
                                    direction="OUT", amount=amt, concept=concept,
                                    counterparty=place, kind="PAYMENT"))
            else:
                person = rng.choice(PEOPLE)
                amt = float(rng.choice([10.0, 15.0, 20.0, 25.0, 30.0, 50.0]))
                concept = f"Envío a {person}"
                out.append(Movement(movement_id=_mv_id(when, concept, amt, "OUT"), created_at=when,
                                    direction="OUT", amount=amt, concept=concept,
                                    counterparty=person, kind="TRANSFER"))

    for rel, direction, amt, concept, party, kind in FIXED_RELATIVE:
        when = datetime.combine(today + timedelta(days=rel), time(18, 45))
        out.append(Movement(movement_id=_mv_id(when, concept, amt, direction), created_at=when,
                            direction=direction, amount=amt, concept=concept,
                            counterparty=party, kind=kind))

    out.sort(key=lambda m: m.created_at)
    return out


MOVEMENTS: list[Movement] = []


def _recompute_balance() -> None:
    bal = INITIAL_BALANCE
    for m in MOVEMENTS:
        bal += m.amount if m.direction == "IN" else -m.amount
    WALLET.balance = round(bal, 2)


def reset_data() -> None:
    MOVEMENTS.clear()
    MOVEMENTS.extend(generate_movements())
    _recompute_balance()


reset_data()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["sistema"])
def health() -> dict:
    return {"status": "ok", "service": "wallet-api", "simulated": True}


@app.get("/wallet", response_model=Wallet, tags=["billetera"])
def get_wallet() -> Wallet:
    return WALLET


@app.get("/wallet/movements", response_model=list[Movement], tags=["movimientos"])
def list_movements(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    direction: Literal["IN", "OUT"] | None = None,
    limit: int = Query(500, ge=1, le=2000),
) -> list[Movement]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="El parámetro from no puede ser posterior a to")
    out = [
        m for m in MOVEMENTS
        if (from_date is None or m.created_at.date() >= from_date)
        and (to_date is None or m.created_at.date() <= to_date)
        and (direction is None or m.direction == direction)
    ]
    out.sort(key=lambda m: m.created_at, reverse=True)
    return out[:limit]


@app.post("/wallet/transfer", response_model=OperationResult, status_code=status.HTTP_201_CREATED,
          tags=["operaciones"])
def transfer(req: TransferRequest) -> OperationResult:
    """Transferencia ficticia a otra persona. Falla con 400 si no hay saldo."""
    if req.amount > WALLET.balance:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    now = datetime.now().replace(microsecond=0)
    mv = Movement(movement_id="WLT-" + uuid.uuid4().hex[:10].upper(), created_at=now,
                  direction="OUT", amount=round(req.amount, 2),
                  concept=f"Envío a {req.to} - {req.concept}", counterparty=req.to,
                  kind="TRANSFER", reference=uuid.uuid4().hex[:8])
    MOVEMENTS.append(mv)
    _recompute_balance()
    return OperationResult(ok=True, movement=mv, new_balance=WALLET.balance)


@app.post("/wallet/topup", response_model=OperationResult, status_code=status.HTTP_201_CREATED,
          tags=["operaciones"])
def topup(req: TopupRequest) -> OperationResult:
    """Recarga ficticia de saldo."""
    now = datetime.now().replace(microsecond=0)
    source_label = {"BANK": "cuenta bancaria ****0001", "CASH": "agente en efectivo", "CARD": "tarjeta ****4321"}
    mv = Movement(movement_id="WLT-" + uuid.uuid4().hex[:10].upper(), created_at=now,
                  direction="IN", amount=round(req.amount, 2),
                  concept=f"Recarga desde {source_label[req.source]}", counterparty="Banco Sim",
                  kind="TOPUP", reference=uuid.uuid4().hex[:8])
    MOVEMENTS.append(mv)
    _recompute_balance()
    return OperationResult(ok=True, movement=mv, new_balance=WALLET.balance)


@app.post("/wallet/reset", tags=["operaciones"])
def reset() -> dict:
    """Regenera los datos de prueba (útil para demostraciones)."""
    reset_data()
    return {"ok": True, "movements": len(MOVEMENTS), "balance": WALLET.balance}
