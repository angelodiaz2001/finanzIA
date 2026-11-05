# Backend de FinanzIA

API REST en **Python 3.13 + FastAPI**, SQLAlchemy 2 (estilo `Mapped`/`select`), Pydantic v2. Base de datos MySQL 8 (Docker) o SQLite local si no hay `DATABASE_URL`. Las tablas se crean al arrancar con `init_db()`: **no hay migraciones** (no Alembic), así que un cambio en `models.py` en MySQL obliga a recrear la tabla; avísalo en el plan.

El paquete se importa como `backend.app`, por eso todo se ejecuta **desde la raíz del repositorio**, nunca desde `backend/`.

## Comandos (PowerShell, desde la raíz)

```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload   # Swagger en http://localhost:8000/docs
.venv\Scripts\python -m pytest                                              # todas las pruebas
.venv\Scripts\python -m pytest backend\tests\test_api.py -k nombre          # una prueba
docker compose up -d                                                        # MySQL (opcional)
```

## Capas y dependencias permitidas

Flujo de datos: `clients/` → `normalizer.py` → `dedup.py` → `categorizer.py` → `models.py` (BD) → `analytics.py` → `routers/` → frontend.

- `routers/` solo valida parámetros HTTP, llama a una función de `analytics.py` (o `sync_service.py`) y envuelve el resultado en un esquema de `schemas.py`. **Sin lógica de negocio ni consultas complejas en el router.**
- `analytics.py` hace las consultas y cálculos y devuelve `dict`/`list[dict]` planos, con montos redondeados a 2 decimales.
- `schemas.py` tiene todos los modelos Pydantic de entrada/salida.
- `ai/assistant.py` usa las funciones de `analytics.py` como herramientas del modelo. Una función nueva de indicadores puede exponerse ahí, pero solo si la tarea lo pide.
- Prefijo `/api` y registro de routers en `main.py`.

## Reglas de negocio que cualquier indicador debe respetar

- Excluir siempre `Transaction.is_duplicate == True`.
- Excluir la categoría `INTERNAL_TRANSFERS` ("Transferencias internas", de `categorizer.py`) de ingresos y gastos.
- `amount` siempre es positivo; el sentido está en `type` (`income` | `expense`).
- Filtros de fecha con `_range_conditions(date_from, date_to)` de `analytics.py` y validación `date_from <= date_to` con `_check_range` del router (error 400).
- Moneda por defecto: `settings.default_currency` (PEN). Textos de error y `detail` en español.

## Pruebas

- pytest en `backend/tests/`. `conftest.py` da los fixtures `client` (TestClient con BD SQLite en memoria) y `db_session`; las pruebas **nunca** usan la API real de Anthropic ni el `.env`.
- Las fuentes se simulan con funciones `fake_bank`/`fake_wallet`/... y `monkeypatch` (ver `test_api.py`); no levantes los servicios para probar.
- Todo endpoint nuevo lleva al menos: un caso feliz, un caso que excluya duplicados/transferencias internas y un caso de error de validación.

## Estilo

`from __future__ import annotations` al inicio, type hints en todas las funciones, `Optional[...]` como en el resto del código, nombres de funciones y variables en inglés, docstrings y mensajes al usuario en español.
