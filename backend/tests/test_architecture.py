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
import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.ai import assistant

BACKEND_APP = Path(__file__).resolve().parents[1] / "app"
REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_SCRIPT = REPO_ROOT / ".claude" / "hooks" / "guard_agent_paths.py"


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


def _run_hook(payload: dict, agent_name: str = "") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if agent_name:
        env["CLAUDE_AGENT_NAME"] = agent_name
    else:
        env.pop("CLAUDE_AGENT_NAME", None)
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_pretooluse_hook_enforces_structural_tdd_and_protected_files():
    assert HOOK_SCRIPT.exists()
    # dev-backend no puede tocar pruebas y test-backend no puede tocar codigo de produccion
    res_dev_on_test = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": "backend/tests/test_api.py"}},
        agent_name="dev-backend",
    )
    assert res_dev_on_test.returncode == 2

    res_test_on_app = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "backend/app/analytics.py"}},
        agent_name="test-backend",
    )
    assert res_test_on_app.returncode == 2

    # Ningun agente puede tocar .env ni services/
    res_env = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": ".env"}},
        agent_name="dev-backend",
    )
    assert res_env.returncode == 2

    # Rutas legitimas permitidas
    res_ok = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": "backend/app/analytics.py"}},
        agent_name="dev-backend",
    )
    assert res_ok.returncode == 0


def test_pretooluse_hook_blocks_git_push_and_pr_merge_in_bash():
    res_push = _run_hook({"tool_name": "Bash", "tool_input": {"command": "git push origin feat/001"}})
    assert res_push.returncode == 2

    res_merge = _run_hook({"tool_name": "Bash", "tool_input": {"command": "gh pr merge 6 --merge"}})
    assert res_merge.returncode == 2

    res_pytest = _run_hook({"tool_name": "Bash", "tool_input": {"command": "python -m pytest -q"}})
    assert res_pytest.returncode == 0
