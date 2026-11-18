# Spec 003 · Detección determinista de gastos atípicos por categoría

## 1. Objetivo e historia de usuario
Como usuario de FinanzIA, quiero identificar automáticamente qué gastos de un periodo superan de manera inusual el gasto promedio histórico de su misma categoría, para detectar cobros fuera de lo común o picos de consumo y consultarlos también desde el asistente de IA.

- **Alcance:** Backend (`backend/app/**`, `backend/tests/**`, `docs/api-contracts.md`).
- **Rama:** `feat/003-deteccion-gastos-atipicos`

## 2. Criterios de aceptación verificables
- **CA-1 (Regla estadística determinista y muestra mínima):** `GET /api/analytics/anomalies?date_from=&date_to=&multiplier=2.0&limit=10` evalúa gastos dentro del rango frente al promedio histórico de cada categoría (`category_average`). Una categoría solo genera alertas si acumula **al menos 3 gastos válidos** (`count >= 3`), evitando falsos positivos en categorías recién estrenadas. Se marca como atípico todo gasto cuyo `amount >= category_average * multiplier`.
- **CA-2 (Ordenamiento, campos y exclusiones contables):** cada elemento devuelve `id`, `occurred_at`, `description`, `merchant`, `category`, `source`, `currency`, `amount`, `category_average` y `ratio` (`amount / category_average` redondeado a 2 decimales), ordenados de mayor a menor `ratio` y desempate por `amount` descendente. Excluye siempre `is_duplicate == True`, `Transferencias internas`, `Transferencias enviadas` e ingresos (`type == "income"`).
- **CA-3 (Validación de parámetros):** `date_from > date_to` devuelve `400` (`"date_from no puede ser posterior a date_to"`); `multiplier < 1.2`, `multiplier > 10.0`, `limit < 1` o `limit > 50` devuelven `422`. Si no hay anomalías o movimientos, devuelve `200 []`.
- **CA-4 (Integración estricta con el asistente de IA):** `backend/app/ai/assistant.py` registra la herramienta `get_spending_anomalies` con `"strict": True` y `"additionalProperties": False`, delegando en `analytics.spending_anomalies`.

## 3. Restricciones
- Toda la lógica numérica vive en `backend/app/analytics.py`; `routers/analytics.py` solo valida parámetros y serializa con `SpendingAnomaly` (`test_architecture.py`).
- No modificar `frontend/**`, `services/**` ni `models.py`.
