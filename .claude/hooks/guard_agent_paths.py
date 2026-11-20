"""Hook PreToolUse determinista para aislar subagentes y proteger Git/entorno.

Lee por stdin el JSON del evento `PreToolUse` en Claude Code:
1. En llamadas a `Bash`, impide que cualquier sesión o subagente ejecute
   `git push`, `gh pr merge` o borrados destructivos (`git reset --hard`),
   reservando la publicación y fusión en GitHub al desarrollador humano.
2. En llamadas a `Edit` o `Write`, bloquea siempre cualquier escritura sobre
   `.env`, `docker-compose.yml`, `services/` o `frontend/vite.config.js`, y
   verifica que `file_path` pertenezca a las carpetas permitidas del subagente
   indicado en `CLAUDE_AGENT_NAME`.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ALWAYS_FORBIDDEN_PREFIXES = (
    ".env",
    "docker-compose.yml",
    "services/",
    "frontend/vite.config.js",
)

FORBIDDEN_BASH_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:^|[;&|]\s*)git\s+push\b", re.IGNORECASE), "git push está reservado al desarrollador humano."),
    (re.compile(r"(?:^|[;&|]\s*)gh\s+pr\s+merge\b", re.IGNORECASE), "gh pr merge está reservado al desarrollador humano."),
    (re.compile(r"(?:^|[;&|]\s*)git\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard está bloqueado por seguridad."),
)

AGENT_ALLOWED_PREFIXES: dict[str, tuple[str, ...]] = {
    "orquestador": ("specs/",),
    "auditor-convergencia": ("specs/",),
    "test-backend": ("backend/tests/",),
    "dev-backend": ("backend/app/", "docs/api-contracts.md", "backend/requirements.txt", ".env.example"),
    "test-frontend": ("frontend/src/__tests__/",),
    "dev-frontend": ("frontend/src/", "frontend/index.html"),
}


def _normalize_rel(raw_path: str) -> str:
    try:
        resolved = Path(raw_path).resolve()
        rel = resolved.relative_to(ROOT.resolve())
        return rel.as_posix()
    except Exception:
        return raw_path.replace("\\", "/").lstrip("./")


def _check_bash_command(command: str) -> int:
    for pattern, reason in FORBIDDEN_BASH_PATTERNS:
        if pattern.search(command):
            sys.stderr.write(f"Bloqueado por hook PreToolUse: {reason}\n")
            return 2
    return 0


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}

    if tool_name == "Bash" or ("command" in tool_input and "file_path" not in tool_input and "path" not in tool_input):
        cmd = str(tool_input.get("command") or "")
        return _check_bash_command(cmd)

    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    rel = _normalize_rel(str(file_path))

    if rel == ".env.example":
        pass
    elif any(rel == p.rstrip("/") or rel.startswith(p) for p in ALWAYS_FORBIDDEN_PREFIXES):
        sys.stderr.write(f"Bloqueado por regla del repositorio: no se permite modificar '{rel}'.\n")
        return 2

    agent = os.environ.get("CLAUDE_AGENT_NAME", "").strip()
    if not agent or agent not in AGENT_ALLOWED_PREFIXES:
        return 0

    if agent == "dev-frontend" and rel.startswith("frontend/src/__tests__/"):
        sys.stderr.write("Bloqueado: dev-frontend no tiene permiso sobre frontend/src/__tests__/.\n")
        return 2

    allowed = AGENT_ALLOWED_PREFIXES[agent]
    if not any(rel == p.rstrip("/") or rel.startswith(p) for p in allowed):
        sys.stderr.write(f"Bloqueado: el agente '{agent}' no puede escribir en '{rel}'. Permitido: {allowed}\n")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
