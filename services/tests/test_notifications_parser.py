from datetime import date

from fastapi.testclient import TestClient

from services.notifications_api.main import app
from services.notifications_api.parser import parse_notification


def test_bank_consumption_sms():
    info = parse_notification(
        "BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA el 21/10 con tarjeta ****0001.",
        received_on=date(2026, 10, 24),
    )
    assert info.amount == 189.9
    assert info.currency == "PEN"
    assert info.movement_type == "expense"
    assert info.merchant == "SUPERMERCADO LA CANASTA"
    assert info.card_last4 == "0001"
    assert info.event_date == date(2026, 10, 21)
    assert info.confidence == 1.0


def test_wallet_transfer_sms():
    info = parse_notification("Enviaste S/ 35.00 a Carlos R. Tu nuevo saldo es S/ 410.50")
    assert info.amount == 35.0
    assert info.movement_type == "expense"
    assert info.merchant == "Carlos R"


def test_income_email_with_thousands_separator():
    info = parse_notification("Se acreditó un abono de S/ 1,500.00 por PLANILLA EMPRESA FICTICIA SAC.")
    assert info.amount == 1500.0
    assert info.movement_type == "income"


def test_usd_subscription():
    info = parse_notification("Tu pago de suscripcion Musica Sim Premium por US$ 5.99 fue procesado.")
    assert info.amount == 5.99
    assert info.currency == "USD"
    assert info.movement_type == "expense"


def test_reminder_is_not_a_movement():
    info = parse_notification("Recordatorio: tu recibo de internet de S/ 129.00 vence el 30/10.")
    assert info.movement_type == "unknown"
    assert info.confidence < 0.6


def test_api_ingests_and_lists_events():
    client = TestClient(app)
    created = client.post("/events", json={"channel": "SMS", "sender": "BancoSim",
                                           "raw_text": "Compra aprobada por S/ 72.40 en LIBRERIA CENTRAL ****4321"})
    assert created.status_code == 201
    body = created.json()
    assert body["parsed"]["amount"] == 72.4
    assert body["parsed"]["merchant"] == "LIBRERIA CENTRAL"

    listed = client.get("/events", params={"min_confidence": 0.6}).json()
    assert any(e["event_id"] == body["event_id"] for e in listed)
    assert client.get("/events/NO-EXISTE").status_code == 404
