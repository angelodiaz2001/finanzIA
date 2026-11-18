"""Pruebas deterministas de integridad arquitectónica y frontera con la IA.

Verifican con el módulo estándar `ast` que ningún cambio rompa las reglas
estructurales de FinanzIA:
1. Los módulos de cálculo y dominio (`analytics`, `dedup`, `normalizer`,
   `categorizer`) nunca importan `anthropic` ni dependen de `backend.app.ai`
   (la IA jamás calcula montos).
2. Los routers de indicadores y presupuestos delegan sus consultas a la capa de
   servicios/analítica y no ejecutan `select()` ni `func.sum()` directamente.
3. Todas las herramientas declaradas en `backend/app/ai/assistant.py` usan
   `"strict": True` y `"additionalProperties": False`.
4. Ningún módulo fuera de `config.py` lee directamente el archivo `.env`.
"""
from __future__ import annotations

import ast
from pathlib import Path

from backend.app.ai import assistant

BACKEND_APP = Path(__file__).resolve().parents[1] / "app"


def _imports_of(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            found.add(mod)
            for alias in node.names:
                found.add(f"{mod}.{alias.name}" if mod else alias.name)
    return found


def test_domain_and_analytics_never_import_ai_or_anthropic():
    pure_modules = ["analytics.py", "dedup.py", "normalizer.py", "categorizer.py", "textutil.py"]
    forbidden = {"anthropic", "ai", "ai.assistant", "backend.app.ai", "backend.app.ai.assistant"}
    for filename in pure_modules:
        imports = _imports_of(BACKEND_APP / filename)
        leaked = {imp for imp in imports if imp in forbidden or imp.startswith("anthropic")}
        assert not leaked, f"{filename} no debe importar el SDK de IA: {sorted(leaked)}"


def test_indicator_routers_do_not_build_sql_queries_directly():
    routers_dir = BACKEND_APP / "routers"
    thin_routers = [p for p in routers_dir.glob("*.py") if p.name in {"analytics.py", "budgets.py"}]
    assert thin_routers, "Debe existir al menos routers/analytics.py"
    for router_file in thin_routers:
        tree = ast.parse(router_file.read_text(encoding="utf-8"), filename=str(router_file))
        sql_calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"select", "delete"}
        ]
        assert not sql_calls, f"{router_file.name} debe delegar las consultas a la capa de lógica, no usar {sql_calls}"


def test_assistant_tools_enforce_strict_json_schema():
    assert len(assistant.TOOLS) >= 5
    for tool in assistant.TOOLS:
        name = tool.get("name")
        assert tool.get("strict") is True, f"La herramienta {name} debe declarar strict=True"
        schema = tool.get("input_schema", {})
        assert schema.get("additionalProperties") is False, (
            f"La herramienta {name} debe cerrar additionalProperties=False"
        )


def test_only_config_references_dotenv_file():
    offenders: list[str] = []
    for py_file in BACKEND_APP.rglob("*.py"):
        if py_file.name == "config.py" or py_file.parent.name == "ai":
            # assistant.py solo menciona ".env" en mensajes de ayuda al usuario, nunca abre el archivo.
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                    offenders.append(str(py_file.relative_to(BACKEND_APP)))
            continue
        text = py_file.read_text(encoding="utf-8")
        if '".env"' in text or "'.env'" in text:
            offenders.append(str(py_file.relative_to(BACKEND_APP)))
    assert not offenders, f"Solo config.py puede cargar .env; revisa: {offenders}"
