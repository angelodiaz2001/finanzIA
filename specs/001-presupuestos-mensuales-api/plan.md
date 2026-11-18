# Plan técnico · Spec 001: API de presupuestos mensuales por categoría

## 1. Análisis de diseño (`arquitecto`)
- **Impacto en base de datos (`models.py`):** FinanzIA no usa Alembic sino `Base.metadata.create_all` en `init_db()`. Agregamos una tabla nueva independiente `category_budgets` (`CategoryBudget`) con restricción única `(month, category)`. Esto no modifica las tablas existentes (`accounts`, `transactions`, `sync_runs`), por lo que es seguro tanto en SQLite local como en MySQL 8 sin recrear datos previos.
- **Separación de capas:** toda la consulta SQL y el cálculo de `spent`, `remaining`, `usage_ratio` y `status` viven en un módulo nuevo `backend/app/budgets_service.py`. El router `backend/app/routers/budgets.py` queda delgado (solo recibe parámetros, traduce errores de dominio a `HTTPException` 400/404 y devuelve esquemas de `schemas.py`), cumpliendo `test_architecture.py`.
- **Frontera con el asistente de IA:** se registra `get_budgets_status` en `TOOLS` de `backend/app/ai/assistant.py` con `"strict": True` y `required: ["month"]`, delegando en `budgets_service.list_budgets_status`.

## 2. Contrato HTTP (`docs/api-contracts.md`)
- `GET /api/budgets?month=YYYY-MM` -> `200 BudgetMonthSummary`:
  `{ "month": "2026-10", "currency": "PEN", "total_budgeted": 800.0, "total_spent": 620.5, "items": [{ "id": 1, "month": "2026-10", "category": "Alimentación", "limit_amount": 500.0, "spent": 450.5, "remaining": 49.5, "usage_ratio": 0.901, "status": "warning", "currency": "PEN" }] }`
- `PUT /api/budgets` (`{ "month": "2026-10", "category": "Alimentación", "limit_amount": 500.0 }`) -> `200 BudgetStatusOut`
- `DELETE /api/budgets/{budget_id}` -> `204` | `404 {"detail": "Presupuesto no encontrado"}`
- Errores de dominio: `400` si `month` no cumple `YYYY-MM` válido o si `category` no es una categoría de gasto presupuestable; `422` si `limit_amount <= 0`.

## 3. Archivos a crear o modificar
- Crear `backend/tests/test_budgets.py` (fase Red)
- Modificar `backend/app/models.py` (`CategoryBudget`)
- Crear `backend/app/budgets_service.py` (lógica determinista y acceso a BD)
- Modificar `backend/app/schemas.py` (`BudgetUpsert`, `BudgetStatusOut`, `BudgetMonthSummary`)
- Crear `backend/app/routers/budgets.py` y registrarlo en `backend/app/main.py`
- Modificar `backend/app/ai/assistant.py` (herramienta `get_budgets_status`)
- Modificar `docs/api-contracts.md` (documentación de endpoints de presupuestos y herramienta IA)

## 4. Estrategia de pruebas
- Suite dedicada `backend/tests/test_budgets.py` cubriendo `CA-1` a `CA-5`: creación, actualización sin duplicar, estados `ok`/`warning`/`exceeded`, exclusión de `is_duplicate`, `INTERNAL_TRANSFERS` y `SENT_TRANSFERS`, errores `400`/`404`/`422`, mes vacío y ejecución de `execute_tool(..., "get_budgets_status", ...)`.
