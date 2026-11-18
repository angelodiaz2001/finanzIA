# Plan técnico · Spec 003: Detección determinista de gastos atípicos

## 1. Decisiones técnicas (`arquitecto`)
- **Línea base histórica frente a ventana consultada:** el promedio de referencia de cada categoría se calcula sobre todos los gastos válidos no duplicados de la base consolidada (con mínimo 3 registros por categoría), mientras que los candidatos reportados se filtran por `date_from` y `date_to`. Así un periodo corto como `"Este mes"` conserva una referencia estable aunque solo tenga una compra en esa semana.
- **Sin cambios en base de datos:** reutiliza la tabla `transactions` existente y sus índices sobre `type`, `category` y `occurred_at`.

## 2. Contrato HTTP (`docs/api-contracts.md`)
- `GET /api/analytics/anomalies?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&multiplier=2.0&limit=10` -> `200 list[SpendingAnomaly]`:
  `[{ "id": 14, "occurred_at": "2026-10-22T19:00:00", "description": "Cena aniversario", "merchant": "Restaurante Sim", "category": "Alimentación", "source": "bank", "currency": "PEN", "amount": 360.0, "category_average": 115.0, "ratio": 3.13 }]`

## 3. Archivos a crear o modificar
- Crear `backend/tests/test_anomalies.py` (fase Red)
- Modificar `backend/app/analytics.py` (`spending_anomalies`)
- Modificar `backend/app/schemas.py` (`SpendingAnomaly`)
- Modificar `backend/app/routers/analytics.py` (`GET /api/analytics/anomalies`)
- Modificar `backend/app/ai/assistant.py` (herramienta `get_spending_anomalies`)
- Modificar `docs/api-contracts.md`
