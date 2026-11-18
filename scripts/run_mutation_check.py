"""Ejecutor determinista de pruebas de mutación AST sobre el dominio financiero.

En Windows nativo (PowerShell sin WSL) `mutmut` no arranca porque depende de
`os.fork()` (exclusivo de sistemas Unix). Este script aplica mutaciones
controladas con el módulo `ast` sobre una copia temporal de los módulos de
cálculo (`analytics.py`, `dedup.py`, `categorizer.py`, `normalizer.py`), corre
`pytest backend/tests` por cada mutante y genera el informe JSON y Markdown de
mutantes eliminados y supervivientes.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    "backend/app/analytics.py",
    "backend/app/dedup.py",
    "backend/app/categorizer.py",
    "backend/app/normalizer.py",
]

COMPARE_SWAPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Gt: ast.LtE,
    ast.GtE: ast.Lt,
    ast.Lt: ast.GtE,
    ast.LtE: ast.Gt,
}

BINOP_SWAPS: dict[type[ast.operator], type[ast.operator]] = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Div,
    ast.Div: ast.Mult,
}


class _Collector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.candidates: list[tuple[int, str, str]] = []

    def visit_Compare(self, node: ast.Compare) -> None:
        if len(node.ops) == 1 and type(node.ops[0]) in COMPARE_SWAPS:
            op_t = type(node.ops[0])
            self.candidates.append((node.lineno, "compare", f"{op_t.__name__} -> {COMPARE_SWAPS[op_t].__name__}"))
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        op_t = type(node.op)
        if op_t in BINOP_SWAPS:
            # Ignorar concatenación de cadenas para no mutar textos estáticos
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                return
            self.candidates.append((node.lineno, "binop", f"{op_t.__name__} -> {BINOP_SWAPS[op_t].__name__}"))
        self.generic_visit(node)


class _SingleMutator(ast.NodeTransformer):
    def __init__(self, target_index: int) -> None:
        self.target_index = target_index
        self.current = 0

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if len(node.ops) == 1 and type(node.ops[0]) in COMPARE_SWAPS:
            idx = self.current
            self.current += 1
            if idx == self.target_index:
                node.ops[0] = COMPARE_SWAPS[type(node.ops[0])]()
                return node
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        op_t = type(node.op)
        if op_t in BINOP_SWAPS:
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                return node
            idx = self.current
            self.current += 1
            if idx == self.target_index:
                node.op = BINOP_SWAPS[op_t]()
                return node
        return self.generic_visit(node)


def collect_mutants(rel_path: str, limit_per_file: int) -> list[dict[str, Any]]:
    full = ROOT / rel_path
    src = full.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=rel_path)
    collector = _Collector()
    collector.visit(tree)
    total_found = len(collector.candidates)
    if total_found == 0:
        return []
    step = max(1, total_found // limit_per_file)
    picked_indices = list(range(0, total_found, step))[:limit_per_file]
    mutants: list[dict[str, Any]] = []
    lines = src.splitlines()
    for idx in picked_indices:
        lineno, kind, desc = collector.candidates[idx]
        m_tree = ast.parse(src, filename=rel_path)
        _SingleMutator(idx).visit(m_tree)
        ast.fix_missing_locations(m_tree)
        mutated_code = ast.unparse(m_tree)
        snippet = lines[lineno - 1].strip() if 1 <= lineno <= len(lines) else ""
        mutants.append(
            {
                "file": rel_path,
                "line": lineno,
                "kind": kind,
                "change": desc,
                "original_line": snippet,
                "mutated_code": mutated_code,
            }
        )
    return mutants


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta pruebas de mutación sobre los módulos financieros.")
    parser.add_argument("--per-file", type=int, default=6, help="Máximo de mutantes muestreados por archivo")
    parser.add_argument("--output-dir", type=str, default="docs/evidencias", help="Carpeta de salida del reporte")
    args = parser.parse_args()

    all_mutants: list[dict[str, Any]] = []
    for rel in TARGET_FILES:
        if (ROOT / rel).exists():
            all_mutants.extend(collect_mutants(rel, args.per_file))

    results: list[dict[str, Any]] = []
    killed = 0
    survived = 0

    with tempfile.TemporaryDirectory(prefix="finanzia_mut_") as tmp:
        tmp_root = Path(tmp)
        for folder in ("backend", "services"):
            shutil.copytree(
                ROOT / folder,
                tmp_root / folder,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".claude"),
            )
        shutil.copy2(ROOT / "pytest.ini", tmp_root / "pytest.ini")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_root)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        for i, m in enumerate(all_mutants, 1):
            target = tmp_root / m["file"]
            original_bytes = target.read_bytes()
            try:
                target.write_text(m["mutated_code"], encoding="utf-8")
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "backend/tests", "-q", "-x", "--tb=no"],
                    cwd=str(tmp_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                is_killed = proc.returncode != 0
            except subprocess.TimeoutExpired:
                is_killed = True
            finally:
                target.write_bytes(original_bytes)

            status = "killed" if is_killed else "survived"
            if is_killed:
                killed += 1
            else:
                survived += 1
            results.append(
                {
                    "id": f"M-{i:02d}",
                    "file": m["file"],
                    "line": m["line"],
                    "change": m["change"],
                    "original_line": m["original_line"],
                    "status": status,
                }
            )
            print(f"[{i:02d}/{len(all_mutants):02d}] {status.upper():8s} {m['file']}:{m['line']} ({m['change']})")

    total = len(results)
    score = round((killed / total) * 100, 1) if total else 100.0
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_mutants": total,
        "killed": killed,
        "survived": survived,
        "mutation_score_pct": score,
        "mutants": results,
    }

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "reporte-mutacion-backend.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen de mutación: {killed}/{total} eliminados ({score}%), {survived} supervivientes -> {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
