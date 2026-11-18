# Backend de FinanzIA

API REST en **Python 3.13 + FastAPI**, SQLAlchemy 2 (estilo `Mapped`/`select`), Pydantic v2. Base de datos MySQL 8 (Docker) o SQLite local si no hay `DATABASE_URL`. Las tablas se crean al arrancar con `init_db()`: **no hay migraciones** (no Alembic), así que un cambio de columnas sobre tablas existentes en MySQL obliga a recrear la tabla; avísalo siempre en `plan.md`.

El paquete se importa como `backend.app`, por eso todo se ejecuta **desde la raíz del repositorio**, nunca desde `backend/`.

## Comandos (PowerShell, desde la raíz)

```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload
.venv\Scripts\ruff check backend services
.venv\Scripts\python -m pytest --cov=backend.app --cov-report=term-missing --cov-fail-under=80
.venv\Scripts\python scripts\run_mutation_check.py --per-file 6
```

## Capas y dependencias permitidas

Flujo de datos: `clients/` -> `normalizer.py` -> `dedup.py` -> `categorizer.py` -> `models.py` (BD) -> `analytics.py` / servicios de dominio -> `routers/` -> frontend.

- `routers/` valida parámetros HTTP, delega en `analytics.py` (o en el servicio de presupuestos/sincronización) y envuelve el resultado en un esquema de `schemas.py`. `backend/tests/test_architecture.py` verifica que los routers de indicadores y presupuestos no ejecuten consultas SQL directas.
- `analytics.py` concentra las consultas y cálculos financieros devolviendo `dict`/`list[dict]` con montos redondeados a 2 decimales y proporciones a 4 decimales.
- `ai/assistant.py` expone herramientas con `"strict": True` y `"additionalProperties": False` que delegan en funciones deterministas; nunca calcula montos por su cuenta.
- Prefijo `/api` y registro de routers en `main.py`.

## Reglas de negocio obligatorias

- Excluir siempre `Transaction.is_duplicate == True`.
- Excluir `INTERNAL_TRANSFERS` ("Transferencias internas") de ingresos, gastos y presupuestos.
- Excluir `SENT_TRANSFERS` ("Transferencias enviadas") en rankings de comercios, anomalías de consumo y gastos recurrentes.
- `amount` siempre es positivo; el sentido está en `type` (`income` | `expense`).
- Filtros de fecha con `_range_conditions(date_from, date_to)` y validación `date_from <= date_to` con error `400` en español.

## Pruebas y estilo

- `pytest` en `backend/tests/` con fixtures `client` y `db_session` de `conftest.py` (SQLite en memoria, sin `.env` ni llamadas reales a Anthropic).
- En flujo SDD/TDD, `test-backend` escribe primero las pruebas en rojo y `dev-backend` implementa el código mínimo hasta pasar en verde manteniendo cobertura >= 80 %.
- `from __future__ import annotations` al inicio, type hints con `Optional[...]`, identificadores en inglés y mensajes/docstrings en español.
