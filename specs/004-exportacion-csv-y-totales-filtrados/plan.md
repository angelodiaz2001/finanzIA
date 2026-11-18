# Plan técnico · Spec 004: Totales filtrados y exportación CSV

## 1. Coordinación transversal (`orquestador` + `arquitecto`)
- **Secuencia entre stacks:** al modificar el esquema `TransactionPage` y crear una ruta nueva en `/api/transactions/export`, el `orquestador` ejecuta primero la pareja del backend (`test-backend` -> `dev-backend`) actualizando `docs/api-contracts.md`, y luego la pareja del frontend (`test-frontend` -> `dev-frontend`).
- **Prevención de inyección CSV:** se usa el módulo estándar `csv` de Python con `io.StringIO` y una función `_safe_csv_cell` que antepone apóstrofo `'` si una cadena comienza con `=`, `+`, `-` o `@`.

## 2. Contrato HTTP (`docs/api-contracts.md`)
- `GET /api/transactions` -> `TransactionPage`: `{ items, total, page, page_size, filtered_income, filtered_expenses }`
- `GET /api/transactions/export?source=&type=&category=&q=&date_from=&date_to=&include_duplicates=false` -> `200 text/csv`

## 3. Archivos a crear o modificar
- Crear `backend/tests/test_transactions_export.py` (fase Red backend)
- Modificar `backend/app/schemas.py` (`TransactionPage`)
- Modificar `backend/app/routers/transactions.py` (filtros compartidos, validación de rango, subtotales y ruta `/export`)
- Modificar `docs/api-contracts.md`
- Modificar `frontend/src/__tests__/TransactionsAndAssistant.test.jsx` (fase Red frontend)
- Modificar `frontend/src/api.js` (`exportTransactionsUrl`) y `frontend/src/components/TransactionsTable.jsx`
