---
name: finanzia-nuevo-endpoint
description: Crear o modificar un endpoint REST del backend de FinanzIA (FastAPI) siguiendo sus capas, reglas de negocio y pruebas. Usar cuando la tarea pida un endpoint nuevo, un indicador o consulta nueva en /api, o cambiar la respuesta de uno existente.
---

# Nuevo endpoint en el backend de FinanzIA

Sigue estos pasos en orden. No te saltes las pruebas ni la documentación.

## 1. Ubicar la lógica

- Cálculos o consultas sobre transacciones → función nueva en `backend/app/analytics.py`.
  - Firma: `def nombre(db: Session, date_from: Optional[date], date_to: Optional[date], ...) -> list[dict[str, Any]]` (o `dict`).
  - Filtra siempre con `Transaction.is_duplicate.is_(False)`, `Transaction.category != INTERNAL_TRANSFERS` (si suma ingresos o gastos) y `*_range_conditions(date_from, date_to)`.
  - Redondea montos con `round(x, 2)` y convierte con `float(...)`.
  - Usa `select(...)`, `func.sum`, `func.count`, `group_by` de SQLAlchemy 2; nada de SQL en texto.
- Nunca pongas esta lógica en el router.

## 2. Esquema de salida

- Agrega la clase Pydantic en `backend/app/schemas.py` (montos `float`, conteos `int`, nombres de campo en `snake_case` inglés).

## 3. Router

- Usa el router que corresponda en `backend/app/routers/` (indicadores → `analytics.py`, con prefijo `/analytics`). Si creas un router nuevo, regístralo en `main.py` con `prefix=API_PREFIX`.
- Parámetros con `Query(...)` y límites (`ge`, `le`, `pattern`). Fechas con `_check_range` → error 400 en español.
- `response_model=` siempre declarado.

## 4. Pruebas (obligatorio)

En `backend/tests/` (usa el fixture `client` de `conftest.py` y datos insertados con `db_session` o una sincronización con fuentes falsas como en `test_api.py`):

1. Caso feliz con valores esperados exactos.
2. Que los duplicados y las transferencias internas **no** se cuenten.
3. Un error de validación (400 o 422).

Ejecuta: `.venv\Scripts\python -m pytest` desde la raíz. Todo en verde antes de terminar.

## 5. Documentación y cierre

- Agrega el endpoint (método, ruta, parámetros, ejemplo de respuesta) en `docs/api-contracts.md`.
- Si el frontend lo va a consumir, indica el método que habría que añadir en `frontend/src/api.js`, pero no toques el frontend salvo que la tarea lo pida.
- Resume al final: archivos tocados, pruebas añadidas y resultado de pytest.
