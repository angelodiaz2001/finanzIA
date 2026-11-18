# Spec 005 · Gastos recurrentes y tarjeta de alertas en el Panel principal

## 1. Objetivo e historia de usuario
Como usuario de FinanzIA, quiero ver en el Panel principal qué comercios me generan cobros recurrentes mes a mes (suscripciones, servicios o pagos periódicos) junto con las alertas de gastos atípicos del periodo seleccionado, para anticipar compromisos fijos y detectar desvíos de un vistazo.

- **Alcance:** Ambos (`backend/app/**`, `backend/tests/**`, `docs/api-contracts.md`, `frontend/src/**`).
- **Rama:** `feat/005-gastos-recurrentes-y-alertas-panel`

## 2. Criterios de aceptación verificables
- **CA-1 (Detección determinista de gastos recurrentes):** `GET /api/analytics/recurring?limit=8` agrupa gastos con `merchant` no nulo (excluyendo `is_duplicate == True`, `Transferencias internas` y `Transferencias enviadas`) y devuelve aquellos presentes en **al menos 2 meses calendario distintos (`months_active >= 2`)**, con `merchant`, `category`, `months_active`, `occurrences`, `average_amount`, `total_amount` y `last_charged_at` (`YYYY-MM-DD`), ordenados por `months_active` descendente y `average_amount` descendente. `limit < 1` o `limit > 30` responde `422`.
- **CA-2 (Herramienta estricta en el asistente de IA):** `backend/app/ai/assistant.py` añade `get_recurring_expenses` con `"strict": True` y `"additionalProperties": False`, delegando en `analytics.recurring_expenses`.
- **CA-3 (Tarjeta en el Panel principal):** `frontend/src/api.js` expone `anomalies(params)` y `recurring(limit)`. `Dashboard.jsx` los carga en el mismo `Promise.all` existente y ubica `RecurringAndAlerts.jsx` junto a `TopMerchants.jsx` en la cuadrícula `.grid-2`, mostrando tanto los cobros recurrentes como los gastos atípicos del periodo (con textos claros en español cuando cualquiera de las dos listas esté vacía).
- **CA-4 (Calidad y contrato):** `docs/api-contracts.md` actualizado, cero colores hexadecimales fijos en JSX y suite completa de backend y frontend en verde con cobertura `>= 80 %`.

## 3. Restricciones
- No ejecutar SQL directo en `routers/analytics.py` (`test_architecture.py`).
- Reutilizar las clases existentes de `frontend/src/styles.css` (`card`, `grid-2`, `pill`, `small`, `num`) y variables CSS para conservar los temas claro y oscuro.
