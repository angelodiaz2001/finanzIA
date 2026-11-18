# Plan técnico · Spec 005: Gastos recurrentes y alertas en el Panel

## 1. Decisiones técnicas (`arquitecto` + `vercel-react-best-practices`)
- **Criterio de recurrencia sin heurísticas opacas:** un comercio se considera recurrente cuando registra gastos válidos en `>= 2` meses distintos (`YYYY-MM`), tomando como categoría representativa la más frecuente de ese comercio.
- **Carga paralela en `Dashboard.jsx`:** `api.recurring(5)` y `api.anomalies({ ...range, limit: 5 })` se incorporan al `Promise.all` ya existente en `Dashboard.jsx` para evitar cascadas de red (*waterfalls*). La tarjeta `RecurringAndAlerts.jsx` ocupa la segunda columna del `<div className="grid-2">` junto a `TopMerchants.jsx`.

## 2. Contrato HTTP (`docs/api-contracts.md`)
- `GET /api/analytics/recurring?limit=8` -> `200 list[RecurringExpense]`:
  `[{ "merchant": "Streaming Sim", "category": "Entretenimiento", "months_active": 3, "occurrences": 3, "average_amount": 39.9, "total_amount": 119.7, "last_charged_at": "2026-10-15" }]`

## 3. Archivos a crear o modificar
- Crear `backend/tests/test_recurring.py` (fase Red backend)
- Crear `frontend/src/__tests__/RecurringAndAlerts.test.jsx` y actualizar mocks en `AppAndDashboard.test.jsx` (fase Red frontend)
- Modificar `backend/app/analytics.py`, `backend/app/schemas.py`, `backend/app/routers/analytics.py`, `backend/app/ai/assistant.py` y `docs/api-contracts.md`
- Crear `frontend/src/components/RecurringAndAlerts.jsx` y modificar `frontend/src/api.js` y `frontend/src/components/Dashboard.jsx`
