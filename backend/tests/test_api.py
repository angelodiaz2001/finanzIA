"""Pruebas de integración del backend con fuentes simuladas en memoria."""
from datetime import date, datetime, timedelta

from backend.app.clients import SourceUnavailable
from backend.app.routers import sync as sync_router
from backend.app.sync_service import run_sync

TODAY = date.today()


def _iso(days_ago: int, hour: int = 12) -> str:
    return datetime.combine(TODAY - timedelta(days=days_ago), datetime.min.time()).replace(hour=hour).isoformat()


def fake_bank(_settings):
    return {
        "accounts": [{"account_id": "ACC-0001", "account_type": "AHORROS", "alias": "Cuenta Sueldo",
                      "holder": "DEMO", "currency": "PEN", "balance": 2500.0}],
        "transactions": [
            {"transaction_id": "BNK-1", "account_id": "ACC-0001", "posted_at": _iso(1), "amount": 3200.0,
             "type": "CREDIT", "description": "Abono planilla - Empresa Ficticia SAC", "merchant": None,
             "channel": "PAYROLL", "status": "POSTED", "currency": "PEN"},
            {"transaction_id": "BNK-2", "account_id": "ACC-0001", "posted_at": _iso(2), "amount": 189.9,
             "type": "DEBIT", "description": "Supermercado La Canasta", "merchant": "Supermercado La Canasta",
             "channel": "POS", "status": "POSTED", "currency": "PEN"},
            {"transaction_id": "BNK-3", "account_id": "ACC-0001", "posted_at": _iso(3), "amount": 200.0,
             "type": "DEBIT", "description": "Transferencia a billetera digital", "merchant": None,
             "channel": "APP", "status": "POSTED", "currency": "PEN"},
            {"transaction_id": "BNK-BAD", "account_id": "ACC-0001", "posted_at": _iso(3), "amount": 0,
             "type": "DEBIT", "description": "Importe inválido", "channel": "APP", "status": "POSTED", "currency": "PEN"},
        ],
    }


def fake_wallet(_settings):
    return {
        "wallet": {"wallet_id": "WLT-DEMO-001", "owner": "Usuario Demo", "phone_masked": "***", "currency": "PEN",
                   "balance": 410.5},
        "movements": [
            {"movement_id": "WLT-1", "created_at": _iso(3, 18), "direction": "IN", "amount": 200.0,
             "concept": "Recarga desde cuenta bancaria ****0001", "counterparty": "Banco Sim", "kind": "TOPUP"},
            {"movement_id": "WLT-2", "created_at": _iso(4, 18), "direction": "OUT", "amount": 35.0,
             "concept": "Envío a Carlos R.", "counterparty": "Carlos R.", "kind": "TRANSFER"},
        ],
    }


def fake_notifications(_settings):
    return {"events": [
        {"event_id": "NTF-1", "channel": "SMS", "sender": "BancoSim", "received_at": _iso(2, 14),
         "raw_text": "BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA",
         "parsed": {"amount": 189.9, "currency": "PEN", "movement_type": "expense", "confidence": 0.9,
                    "description": "BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA",
                    "merchant": "SUPERMERCADO LA CANASTA", "card_last4": "0001", "event_date": None, "signals": []}},
        {"event_id": "NTF-2", "channel": "SMS", "sender": "BilleteraSim", "received_at": _iso(4, 14),
         "raw_text": "Enviaste S/ 35.00 a Carlos R.",
         "parsed": {"amount": 35.0, "currency": "PEN", "movement_type": "expense", "confidence": 0.9,
                    "description": "Enviaste S/ 35.00 a Carlos R.", "merchant": "Carlos R.", "card_last4": None,
                    "event_date": None, "signals": []}},
        {"event_id": "NTF-3", "channel": "EMAIL", "sender": "MusicaSim", "received_at": _iso(7, 14),
         "raw_text": "Tu pago de suscripcion Musica Sim por US$ 5.99 fue procesado",
         "parsed": {"amount": 5.99, "currency": "USD", "movement_type": "expense", "confidence": 0.7,
                    "description": "Tu pago de suscripcion Musica Sim por US$ 5.99 fue procesado",
                    "merchant": None, "card_last4": None, "event_date": None, "signals": []}},
        {"event_id": "NTF-4", "channel": "PUSH", "sender": "ConectaSim", "received_at": _iso(2, 14),
         "raw_text": "Recordatorio: tu recibo vence pronto",
         "parsed": {"amount": 129.0, "currency": "PEN", "movement_type": "unknown", "confidence": 0.4,
                    "description": "Recordatorio", "merchant": None, "card_last4": None, "event_date": None, "signals": []}},
    ]}


FAKE_FETCHERS = {"bank": fake_bank, "wallet": fake_wallet, "notification": fake_notifications}


def test_sync_normalizes_dedups_and_persists(client, db_session, monkeypatch):
    monkeypatch.setattr(sync_router, "run_sync", lambda db, settings: run_sync(db, settings, FAKE_FETCHERS))

    report = client.post("/api/sync").json()
    assert report["status"] == "ok"
    assert report["fetched"] == {"bank": 4, "wallet": 2, "notification": 4}
    assert report["inserted"] == {"bank": 3, "wallet": 2, "notification": 1}
    assert report["duplicates_cross"] == 2       # NTF-1 ~ BNK-2, NTF-2 ~ WLT-2
    assert report["skipped"] == 1                # NTF-4 (tipo desconocido)
    assert report["rejected"] == 1               # BNK-BAD (importe 0)
    assert report["errors"] == [] and len(report["warnings"]) == 1

    # Segunda sincronización: todo ya existe
    report2 = client.post("/api/sync").json()
    assert report2["inserted"] == {"bank": 0, "wallet": 0, "notification": 0}
    assert report2["duplicates_exact"] == 8

    page = client.get("/api/transactions", params={"page_size": 50}).json()
    assert page["total"] == 6
    dup_page = client.get("/api/transactions", params={"include_duplicates": True, "page_size": 50}).json()
    assert dup_page["total"] == 8
    dups = [t for t in dup_page["items"] if t["is_duplicate"]]
    assert {d["source"] for d in dups} == {"notification"}

    summary = client.get("/api/analytics/summary").json()
    assert summary["income"] == 3200.0
    assert summary["expenses"] == round(189.9 + 35.0 + 5.99, 2)
    assert summary["internal_transfers"] == 400.0   # 200 salida banco + 200 entrada billetera
    assert summary["duplicates_detected"] == 2

    cats = client.get("/api/analytics/by-category").json()
    assert cats[0]["category"] == "Alimentación"
    assert abs(sum(c["share"] for c in cats) - 1.0) < 0.01

    monthly = client.get("/api/analytics/monthly", params={"months": 3}).json()
    assert len(monthly) == 3
    assert sum(m["income"] for m in monthly) == 3200.0

    accounts = client.get("/api/accounts").json()
    assert {a["source"] for a in accounts} == {"bank", "wallet"}


def test_sync_reports_unavailable_sources(client, monkeypatch):
    def boom(_settings):
        raise SourceUnavailable("No se pudo conectar con http://localhost:8001/accounts (ConnectError)")

    fetchers = {"bank": boom, "wallet": fake_wallet, "notification": fake_notifications}
    monkeypatch.setattr(sync_router, "run_sync", lambda db, settings: run_sync(db, settings, fetchers))
    report = client.post("/api/sync").json()
    assert report["status"] == "partial"
    assert any(e.startswith("bank:") for e in report["errors"])
    assert report["inserted"]["wallet"] == 2


def test_manual_category_update_and_rules_fallback(client, monkeypatch):
    monkeypatch.setattr(sync_router, "run_sync", lambda db, settings: run_sync(db, settings, FAKE_FETCHERS))
    client.post("/api/sync")
    tx = client.get("/api/transactions", params={"q": "Canasta"}).json()["items"][0]

    updated = client.patch(f"/api/transactions/{tx['id']}/category", json={"category": "Compras"}).json()
    assert updated["category"] == "Compras" and updated["category_source"] == "manual"

    # Sin credenciales de IA, la sugerencia proviene de las reglas
    suggestion = client.post("/api/assistant/categorize", json={"transaction_id": tx["id"]}).json()
    assert suggestion["source"] == "rules" and suggestion["category"] == "Alimentación"

    chat = client.post("/api/assistant/chat", json={"message": "¿En qué gasté más?"}).json()
    assert chat["configured"] is False and "ANTHROPIC_API_KEY" in chat["reply"]


def test_health_reports_sources(client, monkeypatch):
    from backend.app import main as main_module

    monkeypatch.setattr(main_module, "ping", lambda url, timeout=2.0: "down")
    body = client.get("/api/health").json()
    assert body["database"] == "ok"
    assert body["sources"] == {"bank": "down", "wallet": "down", "notification": "down"}
    assert body["status"] == "degraded"
