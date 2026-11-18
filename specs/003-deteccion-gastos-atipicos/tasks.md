# Tareas · Spec 003: Detección determinista de gastos atípicos

## Fase 1: Pruebas desde criterios de aceptación (Red)
- [X] **T1.1 (`test-backend`):** Crear `backend/tests/test_anomalies.py` cubriendo `CA-1` a `CA-4` (cálculo exacto de promedio y ratio, umbral de al menos 3 movimientos por categoría, exclusión de duplicados y transferencias, validaciones 400/422 y herramienta `get_spending_anomalies`) y verificar fallo inicial en `pytest`.

## Fase 2: Implementación y contrato (Green + Refactor)
- [X] **T2.1 (`dev-backend`):** Implementar `spending_anomalies` en `backend/app/analytics.py` y esquema `SpendingAnomaly` en `backend/app/schemas.py`.
- [X] **T2.2 (`dev-backend`):** Exponer `GET /api/analytics/anomalies` en `backend/app/routers/analytics.py`.
- [X] **T2.3 (`dev-backend`):** Registrar herramienta `get_spending_anomalies` en `backend/app/ai/assistant.py` y documentar en `docs/api-contracts.md`.

## Fase 3: Verificación, revisión y convergencia
- [X] **T3.1 (`test-backend`):** Ejecutar `ruff` y `pytest --cov=backend.app --cov-fail-under=80`.
- [X] **T3.2 (`verificador-e2e`):** Comprobar endpoint `/api/analytics/anomalies` con códigos 200, 400 y 422.
- [X] **T3.3 (`revisor-calidad` + `auditor-convergencia`):** Verificar `test_architecture.py` y cierre `converged`.
