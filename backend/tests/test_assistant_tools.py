"""Pruebas del ejecutor de herramientas del asistente (sin llamar a la API de IA)."""
import json
from datetime import datetime

import pytest

from backend.app.ai.assistant import TOOLS, execute_tool
from backend.app.config import Settings
from backend.app.models import Transaction

UNSUPPORTED_IN_STRICT_SCHEMAS = {"minimum", "maximum", "minLength", "maxLength", "pattern", "format"}


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_tool_schemas_only_use_keywords_supported_in_strict_mode():
    for tool in TOOLS:
        assert tool["strict"] is True
        schema = tool["input_schema"]
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"].keys())
        for node in _walk(schema):
            assert not (set(node.keys()) & UNSUPPORTED_IN_STRICT_SCHEMAS), f"{tool['name']}: {node}"


@pytest.fixture
def seeded(db_session):
    db_session.add_all([
        Transaction(source="bank", external_id="B1", occurred_at=datetime(2026, 10, 1, 9), amount=4200,
                    type="income", currency="PEN", description="Abono planilla", category="Salario"),
        Transaction(source="bank", external_id="B2", occurred_at=datetime(2026, 10, 3, 9), amount=1100,
                    type="expense", currency="PEN", description="Pago alquiler", category="Vivienda"),
        Transaction(source="wallet", external_id="W1", occurred_at=datetime(2026, 10, 5, 9), amount=40,
                    type="expense", currency="PEN", description="Pago en Bodega San Martín",
                    merchant="Bodega San Martín", category="Alimentación"),
    ])
    db_session.commit()
    return db_session


def test_execute_tools_return_grounded_json(seeded):
    settings = Settings(_env_file=None)
    summary = json.loads(execute_tool(seeded, settings, "get_summary", {"from_date": "2026-10-01", "to_date": "2026-10-31"}))
    assert summary["income"] == 4200 and summary["expenses"] == 1140

    cats = json.loads(execute_tool(seeded, settings, "get_by_category", {"from_date": None, "to_date": None, "type": "expense"}))
    assert cats[0]["category"] == "Vivienda"

    found = json.loads(execute_tool(seeded, settings, "search_transactions",
                                    {"query": "bodega", "category": None, "type": "cualquiera",
                                     "from_date": None, "to_date": None, "limit": 500}))
    assert len(found) == 1 and found[0]["merchant"] == "Bodega San Martín"

    catalog = json.loads(execute_tool(seeded, settings, "list_categories", {}))
    assert "Vivienda" in catalog["expense_categories"]

    with pytest.raises(ValueError):
        execute_tool(seeded, settings, "herramienta_inexistente", {})
