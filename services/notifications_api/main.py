"""API de notificaciones financieras simulada de FinanzIA.

A diferencia de las otras dos APIs, esta NO devuelve transacciones ya
estructuradas: recibe eventos sin procesar (texto de SMS, correos o push de
prueba) y extrae de ellos información relevante (importe, descripción, tipo
de movimiento, comercio). El backend principal decide luego si ese evento
representa una transacción nueva o un duplicado de otra fuente.

Puerto sugerido: 8003  ->  uvicorn services.notifications_api.main:app --port 8003
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from .parser import parse_notification

app = FastAPI(
    title="FinanzIA - Notificaciones Financieras (simulada)",
    version="0.1.0",
    description=(
        "Recibe eventos de notificación de prueba (SMS/EMAIL/PUSH) y los "
        "transforma en información estructurada. Los mensajes son ficticios."
    ),
)

Channel = Literal["SMS", "EMAIL", "PUSH"]


# --------------------------------------------------------------------------- #
# Modelos
# --------------------------------------------------------------------------- #
class RawEvent(BaseModel):
    channel: Channel
    sender: str = Field(min_length=1, max_length=80, description="Remitente ficticio, p. ej. BancoSim")
    received_at: Optional[datetime] = Field(default=None, description="Si se omite, se usa la hora actual")
    raw_text: str = Field(min_length=5, max_length=1000)


class ParsedInfo(BaseModel):
    amount: Optional[float]
    currency: Optional[str]
    movement_type: Literal["expense", "income", "unknown"]
    description: str
    merchant: Optional[str]
    card_last4: Optional[str]
    event_date: Optional[date]
    confidence: float = Field(ge=0, le=1)
    signals: list[str]


class ProcessedEvent(BaseModel):
    event_id: str
    channel: Channel
    sender: str
    received_at: datetime
    raw_text: str
    parsed: ParsedInfo
    processed_at: datetime


EVENTS: dict[str, ProcessedEvent] = {}


def _process(raw: RawEvent, event_id: Optional[str] = None) -> ProcessedEvent:
    received = raw.received_at or datetime.now().replace(microsecond=0)
    parsed = parse_notification(raw.raw_text, received_on=received.date())
    return ProcessedEvent(
        event_id=event_id or "NTF-" + uuid.uuid4().hex[:10].upper(),
        channel=raw.channel, sender=raw.sender, received_at=received,
        raw_text=raw.raw_text, parsed=ParsedInfo(**parsed.__dict__),
        processed_at=datetime.now().replace(microsecond=0),
    )


# --------------------------------------------------------------------------- #
# Eventos de prueba (relativos a hoy). Algunos coinciden con movimientos de la
# API bancaria o de la billetera para demostrar la deduplicación.
# --------------------------------------------------------------------------- #
def _seed_events(today: Optional[date] = None) -> None:
    today = today or date.today()

    def dmy(offset: int) -> str:
        d = today + timedelta(days=offset)
        return f"{d.day:02d}/{d.month:02d}"

    seeds = [
        (-3, "SMS", "BancoSim",
         f"BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA el {dmy(-3)} con tarjeta ****0001. "
         "Si no reconoces esta operacion llama al 0800-00-SIM."),
        (-1, "PUSH", "BancoSim",
         "Compra aprobada por S/ 45.50 en FARMACIA VIDA ****0001"),
        (-4, "SMS", "BilleteraSim",
         "Enviaste S/ 35.00 a Carlos R. Tu nuevo saldo es S/ 410.50"),
        (-5, "EMAIL", "BancoSim",
         f"Se acreditó un abono de S/ 150.00 por DEVOLUCION TIENDA DE ROPA URBANA el {dmy(-5)}."),
        (-6, "SMS", "BancoSim",
         "Retiro en cajero por S/ 100.00 en ATM AV. PRINCIPAL ****0001"),
        (-7, "EMAIL", "MusicaSim",
         "Tu pago de suscripcion Musica Sim Premium por US$ 5.99 fue procesado correctamente."),
        (-2, "PUSH", "ConectaSim",
         f"Recordatorio: tu recibo de internet de S/ 129.00 vence el {dmy(3)}."),
        (-10, "SMS", "BancoSim",
         "Compra aprobada por S/ 72.40 en LIBRERIA CENTRAL ****4321"),
    ]
    for offset, channel, sender, text in seeds:
        received = datetime.combine(today + timedelta(days=offset), time(14, 10))
        event_id = "NTF-SEED-" + f"{abs(offset):02d}" + channel[:1] + f"{len(text):03d}"
        EVENTS[event_id] = _process(RawEvent(channel=channel, sender=sender, received_at=received,
                                             raw_text=text), event_id=event_id)


_seed_events()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["sistema"])
def health() -> dict:
    return {"status": "ok", "service": "notifications-api", "simulated": True}


@app.post("/events", response_model=ProcessedEvent, status_code=status.HTTP_201_CREATED, tags=["eventos"])
def ingest_event(raw: RawEvent) -> ProcessedEvent:
    """Recibe un evento sin procesar, lo analiza y lo almacena."""
    ev = _process(raw)
    EVENTS[ev.event_id] = ev
    return ev


@app.post("/events/parse", response_model=ParsedInfo, tags=["eventos"])
def parse_only(raw: RawEvent) -> ParsedInfo:
    """Analiza el texto sin almacenarlo (vista previa de la extracción)."""
    return _process(raw).parsed


@app.get("/events", response_model=list[ProcessedEvent], tags=["eventos"])
def list_events(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    min_confidence: float = Query(0.0, ge=0, le=1),
    limit: int = Query(500, ge=1, le=2000),
) -> list[ProcessedEvent]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="El parámetro from no puede ser posterior a to")
    out = [
        e for e in EVENTS.values()
        if (from_date is None or e.received_at.date() >= from_date)
        and (to_date is None or e.received_at.date() <= to_date)
        and e.parsed.confidence >= min_confidence
    ]
    out.sort(key=lambda e: e.received_at, reverse=True)
    return out[:limit]


@app.get("/events/{event_id}", response_model=ProcessedEvent, tags=["eventos"])
def get_event(event_id: str) -> ProcessedEvent:
    ev = EVENTS.get(event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return ev


@app.post("/events/reset", tags=["eventos"])
def reset() -> dict:
    """Regenera los eventos de prueba."""
    EVENTS.clear()
    _seed_events()
    return {"ok": True, "events": len(EVENTS)}
