# Tareas · Spec 001: API de presupuestos mensuales por categoría

## Fase 1: Pruebas desde criterios de aceptación (Red)
- [X] **T1.1 (`test-backend`):** Crear `backend/tests/test_budgets.py` cubriendo `CA-1` a `CA-5` (upsert idempotente, cálculo exacto y orden por `usage_ratio`, exclusión de duplicados y transferencias, errores 400/404/422, mes vacío y herramienta `get_budgets_status`) y confirmar fallo inicial en `pytest`.

## Fase 2: Implementación y contrato (Green + Refactor)
- [ ] **T2.1 (`dev-backend`):** Agregar modelo `CategoryBudget` en `backend/app/models.py` y esquemas `BudgetUpsert`, `BudgetStatusOut` y `BudgetMonthSummary` en `backend/app/schemas.py`.
- [ ] **T2.2 (`dev-backend`):** Implementar `backend/app/budgets_service.py`, crear `backend/app/routers/budgets.py` y registrar el router en `backend/app/main.py`.
- [ ] **T2.3 (`dev-backend`):** Exponer herramienta estricta `get_budgets_status` en `backend/app/ai/assistant.py` y documentar el contrato en `docs/api-contracts.md`.

## Fase 3: Verificación, revisión y convergencia
- [ ] **T3.1 (`test-backend`):** Verificar suite completa y cobertura `pytest --cov=backend.app --cov-fail-under=80` (incluyendo `test_architecture.py`).
- [ ] **T3.2 (`verificador-e2e`):** Comprobar respuestas HTTP `200`, `400`, `404` y `204` en `/api/budgets`.
- [ ] **T3.3 (`revisor-calidad` + `auditor-convergencia`):** Revisar diff contra `spec.md`, `plan.md` y `docs/api-contracts.md`.
