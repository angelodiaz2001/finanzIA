# Spec 001 · API de presupuestos mensuales por categoría de gasto

## 1. Objetivo e historia de usuario
Como usuario de FinanzIA, quiero definir topes mensuales de gasto por categoría y consultar cuánto llevo gastado, cuánto saldo disponible me queda y qué categorías están en alerta o excedidas en un mes (`YYYY-MM`), para vigilar mi presupuesto mensual y consultarlo también desde el asistente conversacional.

- **Alcance:** Backend (`backend/app/**`, `backend/tests/**`, `docs/api-contracts.md`).
- **Rama:** `feat/001-presupuestos-mensuales-api`

## 2. Criterios de aceptación verificables
- **CA-1 (Creación y actualización idempotente):** `PUT /api/budgets` con `{ "month": "2026-10", "category": "Alimentación", "limit_amount": 500.0 }` guarda el tope mensual y devuelve `id`, `month`, `category`, `limit_amount`, `spent`, `remaining`, `usage_ratio`, `status` y `currency`. Si ya existe presupuesto para ese `(month, category)`, actualiza `limit_amount` sin duplicar filas.
- **CA-2 (Cálculo determinista y exclusiones de dominio):** `GET /api/budgets?month=2026-10` devuelve `BudgetMonthSummary` (`month`, `currency`, `total_budgeted`, `total_spent`, `items` ordenados de mayor a menor `usage_ratio`). El cálculo de `spent` suma únicamente gastos (`type == "expense"`) de ese mes calendario, excluyendo `is_duplicate == True`, `Transferencias internas` y `Transferencias enviadas`. El campo `status` vale `"ok"` (`usage_ratio < 0.8`), `"warning"` (`0.8 <= usage_ratio <= 1.0` con `spent <= limit_amount`) o `"exceeded"` (`spent > limit_amount`).
- **CA-3 (Validación de entrada en español):** `limit_amount <= 0` responde `422`; un `month` que no cumpla `YYYY-MM` válido responde `400` con mensaje en español; intentar presupuestar una categoría de ingreso, inexistente o de transferencia (`Transferencias internas` / `Transferencias enviadas`) responde `400` con mensaje en español.
- **CA-4 (Eliminación y mes vacío):** `DELETE /api/budgets/{id}` elimina el presupuesto y responde `204`; si el `id` no existe responde `404` (`"Presupuesto no encontrado"`). Consultar un mes sin presupuestos responde `200` con `items: []`, `total_budgeted: 0.0` y `total_spent: 0.0`.
- **CA-5 (Herramienta estricta para el asistente de IA):** `backend/app/ai/assistant.py` expone la herramienta `get_budgets_status` con `"strict": True` y `"additionalProperties": False`, delegando el cálculo en `budgets_service.list_budgets_status` sin que el LLM calcule montos.

## 3. Restricciones
- No alterar columnas de tablas existentes en `models.py` (crear únicamente la tabla nueva `category_budgets` compatible con `init_db()`).
- No ejecutar consultas SQL directas dentro de `routers/budgets.py` (respetar `backend/tests/test_architecture.py`).
- No modificar `frontend/**`, `services/**`, `docker-compose.yml` ni `.env`.
