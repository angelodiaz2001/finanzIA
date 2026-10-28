from datetime import datetime

import pytest

from backend.app.normalizer import NormalizationError, SkippedEvent, from_bank, from_notification, from_wallet


def test_bank_debit_becomes_expense():
    tx = from_bank({
        "transaction_id": "BNK-1", "account_id": "ACC-0001", "posted_at": "2026-10-20T12:30:00",
        "amount": 189.9, "type": "DEBIT", "description": "Supermercado La Canasta",
        "merchant": "Supermercado La Canasta", "channel": "POS", "status": "POSTED", "currency": "PEN",
    })
    assert tx.source == "bank"
    assert tx.type == "expense"
    assert tx.amount == 189.9
    assert tx.occurred_at == datetime(2026, 10, 20, 12, 30)


def test_bank_rejects_invalid_amount():
    with pytest.raises(NormalizationError):
        from_bank({"transaction_id": "BNK-2", "posted_at": "2026-10-20T12:30:00", "amount": -5,
                   "type": "DEBIT", "description": "x", "currency": "PEN"})


def test_bank_rejects_missing_fields():
    with pytest.raises(NormalizationError):
        from_bank({"transaction_id": "BNK-3", "amount": 10, "type": "DEBIT"})


def test_wallet_in_becomes_income_with_wallet_currency():
    tx = from_wallet({"movement_id": "WLT-1", "created_at": "2026-10-21T18:45:00", "direction": "IN",
                      "amount": 200, "concept": "Recarga desde cuenta bancaria", "counterparty": "Banco Sim",
                      "kind": "TOPUP"}, currency="PEN")
    assert tx.type == "income"
    assert tx.currency == "PEN"
    assert tx.merchant == "Banco Sim"


def test_notification_with_low_confidence_is_skipped():
    with pytest.raises(SkippedEvent):
        from_notification({"event_id": "NTF-1", "received_at": "2026-10-21T14:10:00",
                           "parsed": {"movement_type": "expense", "amount": 10, "confidence": 0.2}},
                          min_confidence=0.6, default_currency="PEN")


def test_notification_unknown_type_is_skipped():
    with pytest.raises(SkippedEvent):
        from_notification({"event_id": "NTF-2", "received_at": "2026-10-21T14:10:00",
                           "parsed": {"movement_type": "unknown", "amount": 129, "confidence": 0.9}},
                          min_confidence=0.6, default_currency="PEN")


def test_notification_uses_event_date_and_titlecases_merchant():
    tx = from_notification({
        "event_id": "NTF-3", "received_at": "2026-10-24T14:10:00", "raw_text": "...",
        "parsed": {"movement_type": "expense", "amount": 189.9, "currency": "PEN", "confidence": 1.0,
                   "description": "Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA el 21/10",
                   "merchant": "SUPERMERCADO LA CANASTA", "event_date": "2026-10-21"},
    }, min_confidence=0.6, default_currency="PEN")
    assert tx.occurred_at.date().isoformat() == "2026-10-21"
    assert tx.merchant == "Supermercado La Canasta"
