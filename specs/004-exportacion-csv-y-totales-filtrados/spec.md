# Spec 004 · Totales filtrados y exportación CSV en el historial de transacciones

## 1. Objetivo e historia de usuario
Como usuario de FinanzIA, cuando aplico filtros en la pestaña «Transacciones» (fuente, tipo, categoría, texto o periodo), quiero conocer al instante cuánto suman los ingresos y gastos del subconjunto filtrado y descargar todas las filas coincidentes en un archivo CSV legible en hojas de cálculo en español.

- **Alcance:** Ambos (`backend/app/**`, `backend/tests/**`, `docs/api-contracts.md`, `frontend/src/**`).
- **Rama:** `feat/004-exportacion-csv-y-totales-filtrados`

## 2. Criterios de aceptación verificables
- **CA-1 (Totales del subconjunto filtrado):** `GET /api/transactions` añade a `TransactionPage` los campos `filtered_income` y `filtered_expenses` (2 decimales), calculados sobre el total de registros que cumplen el filtro (no solo la página actual) y excluyendo siempre `is_duplicate == True` y `Transferencias internas` de ambos subtotales. Si `date_from > date_to`, responde `400` en español.
- **CA-2 (Descarga CSV segura con UTF-8 BOM):** `GET /api/transactions/export` recibe los mismos filtros de consulta y responde `200` (`text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="transacciones_finanzia.csv"`) con marca BOM `\ufeff`, columnas `id,fecha,fuente,tipo,categoria,comercio,descripcion,monto,moneda,duplicado` y saneamiento contra inyección de fórmulas en hojas de cálculo si un texto empieza por `=`, `+`, `-` o `@`.
- **CA-3 (Banda de resumen y acción en React):** `frontend/src/api.js` incorpora `exportTransactionsUrl(params)` y `TransactionsTable.jsx` muestra los totales filtrados (`Ingresos filtrados` y `Gastos filtrados` con `formatMoney`) junto al enlace accesible `"Exportar CSV"` sincronizado con el periodo y los filtros activos.
- **CA-4 (Calidad integral):** `docs/api-contracts.md` actualizado y puertas de backend y frontend en verde con cobertura `>= 80 %`.

## 3. Restricciones
- Declarar `/export` antes de `/{transaction_id}` en `backend/app/routers/transactions.py` para evitar colisión de rutas en FastAPI.
- Cero colores hexadecimales fijos en `TransactionsTable.jsx` y cero dependencias externas nuevas.
