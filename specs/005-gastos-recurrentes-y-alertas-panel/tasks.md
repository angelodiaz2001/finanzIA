# Tareas · Spec 005: Gastos recurrentes y alertas en el Panel

## Fase 1: Pruebas desde criterios de aceptación (Red)
- [X] **T1.1 (`test-backend`):** Crear `backend/tests/test_recurring.py` cubriendo `CA-1` y `CA-2` (comercios con cobros en >= 2 meses distintos, exclusión de duplicados y transferencias, validación `422` y herramienta `get_recurring_expenses`) y confirmar fallo inicial en `pytest`.
- [X] **T1.2 (`test-frontend`):** Crear `frontend/src/__tests__/RecurringAndAlerts.test.jsx` y actualizar mocks en `AppAndDashboard.test.jsx` verificando `CA-3` (renderizado de recurrentes, alertas de gastos atípicos y estados vacíos) y confirmar fallo inicial en `vitest`.

## Fase 2: Implementación Backend y Frontend (Green + Refactor)
- [X] **T2.1 (`dev-backend`):** Implementar `recurring_expenses` en `backend/app/analytics.py`, `RecurringExpense` en `schemas.py`, `GET /api/analytics/recurring` en `routers/analytics.py`, herramienta en `assistant.py` y `docs/api-contracts.md`.
- [X] **T2.2 (`dev-frontend`):** Agregar `anomalies` y `recurring` en `frontend/src/api.js`, crear `frontend/src/components/RecurringAndAlerts.jsx` e integrarlo en `frontend/src/components/Dashboard.jsx`.

## Fase 3: Verificación, accesibilidad y convergencia
- [X] **T3.1 (`test-backend` + `test-frontend`):** Ejecutar `ruff`, `pytest --cov >= 80 %`, `npm run lint`, `npm run test:coverage >= 80 %` y `npm run build`.
- [X] **T3.2 (`verificador-e2e`):** Validar el Panel principal en temas claro y oscuro con datos reales.
- [X] **T3.3 (`revisor-calidad` + `auditor-convergencia`):** Auditar cumplimiento íntegro de `spec.md` (`converged`).
