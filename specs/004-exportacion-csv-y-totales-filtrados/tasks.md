# Tareas · Spec 004: Totales filtrados y exportación CSV

## Fase 1: Pruebas desde criterios de aceptación (Red)
- [X] **T1.1 (`test-backend`):** Crear `backend/tests/test_transactions_export.py` cubriendo `CA-1` y `CA-2` (`filtered_income`, `filtered_expenses` sin duplicados ni transferencias internas, rango invertido `400`, descarga CSV UTF-8 BOM y neutralización de celdas con fórmulas) y confirmar fallo inicial en `pytest`.
- [X] **T1.2 (`test-frontend`):** Ampliar `frontend/src/__tests__/TransactionsAndAssistant.test.jsx` verificando `CA-3` (resumen `Ingresos filtrados`, `Gastos filtrados` y enlace `"Exportar CSV"` sincronizado con los filtros) y confirmar fallo inicial en `vitest`.

## Fase 2: Implementación Backend y Frontend (Green + Refactor)
- [ ] **T2.1 (`dev-backend`):** Añadir `filtered_income` y `filtered_expenses` en `TransactionPage` (`schemas.py`), validación de rango y ruta `GET /api/transactions/export` en `routers/transactions.py`, y actualizar `docs/api-contracts.md`.
- [ ] **T2.2 (`dev-frontend`):** Agregar `exportTransactionsUrl` en `frontend/src/api.js` y mostrar el resumen filtrado junto al enlace de descarga en `frontend/src/components/TransactionsTable.jsx`.

## Fase 3: Verificación, accesibilidad y convergencia
- [ ] **T3.1 (`test-backend` + `test-frontend`):** Comprobar `ruff`, `pytest --cov >= 80 %`, `npm run lint`, `npm run test:coverage >= 80 %` y `npm run build`.
- [ ] **T3.2 (`verificador-e2e`):** Verificar descarga real en `/api/transactions/export` y visualización en temas claro y oscuro.
- [ ] **T3.3 (`revisor-calidad` + `auditor-convergencia`):** Revisar diff completo y cerrar en estado `converged`.
