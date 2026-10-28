from datetime import datetime

from backend.app.categorizer import INTERNAL_TRANSFERS, categorize
from backend.app.dedup import find_cross_source_duplicate, similarity
from backend.app.models import Transaction
from backend.app.normalizer import NormalizedTx


def test_similarity_detects_same_merchant_in_different_wording():
    score = similarity("BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA el 21/10", "Supermercado La Canasta",
                       "Supermercado La Canasta", "Supermercado La Canasta")
    assert score == 1.0


def test_similarity_is_low_for_unrelated_descriptions():
    assert similarity("Pago alquiler departamento", None, "Consumo POS CINE ESTELAR", "Cine Estelar") < 0.3


def test_cross_source_duplicate_found_within_window(db_session):
    db_session.add(Transaction(source="bank", external_id="BNK-1", occurred_at=datetime(2026, 10, 21, 12, 30),
                               amount=189.9, type="expense", currency="PEN", description="Supermercado La Canasta",
                               merchant="Supermercado La Canasta", category="Alimentación"))
    db_session.commit()
    incoming = NormalizedTx(source="notification", external_id="NTF-1", occurred_at=datetime(2026, 10, 21, 14, 10),
                            amount=189.9, type="expense", currency="PEN",
                            description="Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA", merchant="Supermercado La Canasta")
    match = find_cross_source_duplicate(db_session, incoming, window_hours=36, threshold=0.5)
    assert match is not None and match.external_id == "BNK-1"


def test_cross_source_duplicate_ignores_different_amount(db_session):
    db_session.add(Transaction(source="bank", external_id="BNK-1", occurred_at=datetime(2026, 10, 21, 12, 30),
                               amount=189.9, type="expense", currency="PEN", description="Supermercado La Canasta",
                               merchant="Supermercado La Canasta", category="Alimentación"))
    db_session.commit()
    incoming = NormalizedTx(source="notification", external_id="NTF-1", occurred_at=datetime(2026, 10, 21, 14, 10),
                            amount=190.0, type="expense", currency="PEN", description="Supermercado La Canasta",
                            merchant="Supermercado La Canasta")
    assert find_cross_source_duplicate(db_session, incoming, 36, 0.5) is None


def test_rules_categorize_common_movements():
    assert categorize("Abono planilla - Empresa Ficticia SAC", None, "income")[0] == "Salario"
    assert categorize("Consumo POS SUPERMERCADO LA CANASTA", "Supermercado La Canasta", "expense")[0] == "Alimentación"
    assert categorize("Pago alquiler departamento", None, "expense")[0] == "Vivienda"
    assert categorize("Recarga desde cuenta bancaria ****0001", "Banco Sim", "income")[0] == INTERNAL_TRANSFERS
    assert categorize("Transferencia a billetera digital", None, "expense")[0] == INTERNAL_TRANSFERS
    assert categorize("Recarga celular Telco Sim", None, "expense")[0] == "Servicios"
    assert categorize("Envío a María L.", "María L.", "expense")[0] == "Transferencias enviadas"
    assert categorize("Algo sin pista alguna", None, "expense")[0] == "Otros gastos"
