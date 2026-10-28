# Contratos de las APIs de FinanzIA

Este documento fija el contrato de cada API (endpoints, parámetros, estructura de respuestas y códigos de error), las decisiones de integración y el alcance real de la IA. Las tres APIs de fuentes son **simuladas**: devuelven datos ficticios y no se conectan a ninguna entidad financiera.

Todas las APIs son FastAPI y publican su documentación interactiva en `/docs` (OpenAPI).

| Servicio | Puerto | Módulo |
|---|---|---|
| API bancaria (simulada) | 8001 | `services/bank_api` |
| Billetera digital (simulada) | 8002 | `services/wallet_api` |
| Notificaciones financieras (simulada) | 8003 | `services/notifications_api` |
| Backend principal FinanzIA | 8000 | `backend/app` |

Convenciones comunes:

- Fechas y horas en ISO 8601 (`2026-10-24T12:30:00`), sin zona horaria (hora local).
- Importes siempre **positivos** con dos decimales; el sentido del movimiento lo indica otro campo (`type`, `direction`, `movement_type`).
- Errores con el formato de FastAPI: `{"detail": "mensaje"}`. Los errores de validación de parámetros devuelven `422` con el detalle de Pydantic.

---

## 1. API bancaria (simulada) — puerto 8001

Representa un banco: cuentas, saldos y transacciones.

### `GET /health`
`200` → `{"status": "ok", "service": "bank-api", "simulated": true}`

### `GET /accounts`
Lista de cuentas del titular.

```json
[
  {"account_id": "ACC-0001", "account_type": "AHORROS", "alias": "Cuenta Sueldo",
   "holder": "USUARIO DEMO", "currency": "PEN", "balance": 2635.40}
]
```
`account_type`: `AHORROS | CORRIENTE | CREDITO`. En tarjetas de crédito `balance` es el crédito disponible.

### `GET /accounts/{account_id}`
`200` cuenta · `404 {"detail": "Cuenta no encontrada"}`

### `GET /accounts/{account_id}/transactions?from=YYYY-MM-DD&to=YYYY-MM-DD&limit=500`
### `GET /transactions?from=&to=&limit=1000`
Transacciones (más recientes primero). `limit` entre 1 y 2000 (5000 en `/transactions`).

```json
{"transaction_id": "BNK-3F2A91C0D4", "account_id": "ACC-0001", "posted_at": "2026-10-24T12:30:00",
 "amount": 189.90, "type": "DEBIT", "description": "Supermercado La Canasta",
 "merchant": "Supermercado La Canasta", "channel": "POS", "status": "POSTED", "currency": "PEN"}
```
- `type`: `DEBIT` (salida) | `CREDIT` (entrada)
- `channel`: `POS | ATM | WEB | APP | TRANSFER | PAYROLL`
- `status`: `POSTED | PENDING`
- Errores: `400` si `from` > `to`; `404` cuenta inexistente; `422` parámetros inválidos.

Los identificadores se derivan del contenido (hash), por lo que son estables entre reinicios.

---

## 2. Billetera digital (simulada) — puerto 8002

Imita una billetera móvil. Los nombres de campos difieren a propósito de los del banco (`created_at`/`direction`/`concept`) para que el backend tenga que normalizarlos.

### `GET /health`
### `GET /wallet`
```json
{"wallet_id": "WLT-DEMO-001", "owner": "Usuario Demo", "phone_masked": "***-***-4455",
 "currency": "PEN", "balance": 410.50}
```

### `GET /wallet/movements?from=&to=&direction=IN|OUT&limit=500`
```json
{"movement_id": "WLT-8A1F0C22B9", "created_at": "2026-10-23T18:45:00", "direction": "OUT",
 "amount": 35.00, "concept": "Envío a Carlos R.", "counterparty": "Carlos R.",
 "kind": "TRANSFER", "reference": null}
```
`kind`: `TOPUP | PAYMENT | TRANSFER | REFUND | WITHDRAWAL`. `400` si `from` > `to`.

### `POST /wallet/transfer` (operación ficticia)
Cuerpo: `{"to": "María L.", "amount": 20.0, "concept": "Almuerzo"}`
`201` → `{"ok": true, "movement": {...}, "new_balance": 390.50}`
`400 {"detail": "Saldo insuficiente"}` · `422` si `amount <= 0` o `to` vacío.

### `POST /wallet/topup`
Cuerpo: `{"amount": 100.0, "source": "BANK" | "CASH" | "CARD"}` → `201` igual que transfer.

### `POST /wallet/reset`
Regenera los datos de prueba. `200 {"ok": true, "movements": n, "balance": x}`

---

## 3. Notificaciones financieras (simulada) — puerto 8003

Función distintiva: **recibe un evento sin procesar** (texto de SMS, correo o push) y lo transforma en información estructurada. No devuelve transacciones ya hechas; devuelve una interpretación con nivel de confianza.

### `GET /health`

### `POST /events` → `201`
Cuerpo (`RawEvent`):
```json
{"channel": "SMS", "sender": "BancoSim", "received_at": "2026-10-24T14:10:00",
 "raw_text": "BancoSim: Consumo de S/ 189.90 en SUPERMERCADO LA CANASTA el 24/10 con tarjeta ****0001."}
```
Respuesta (`ProcessedEvent`):
```json
{"event_id": "NTF-7B3C...", "channel": "SMS", "sender": "BancoSim", "received_at": "...",
 "raw_text": "...", "processed_at": "...",
 "parsed": {"amount": 189.90, "currency": "PEN", "movement_type": "expense",
            "description": "BancoSim: Consumo de S/ 189.90 en ...", "merchant": "SUPERMERCADO LA CANASTA",
            "card_last4": "0001", "event_date": "2026-10-24", "confidence": 1.0,
            "signals": ["amount:currency_prefix", "type:expense_keyword", "merchant:pattern", "date:pattern"]}}
```
- `movement_type`: `expense | income | unknown` (p. ej. un recordatorio de vencimiento es `unknown`).
- `confidence` ∈ [0, 1]: 0.4 importe + 0.3 tipo + 0.2 comercio + 0.1 fecha.
- `422` si `raw_text` tiene menos de 5 caracteres o `channel` no es `SMS|EMAIL|PUSH`.

### `POST /events/parse`
Igual cuerpo que `/events`; devuelve solo `parsed` sin almacenar (vista previa).

### `GET /events?from=&to=&min_confidence=0&limit=500`
Eventos procesados, más recientes primero.

### `GET /events/{event_id}` → `200` | `404 {"detail": "Evento no encontrado"}`
### `POST /events/reset`

---

## 4. Backend principal FinanzIA — puerto 8000 (prefijo `/api`)

Responsable de **consumir** las tres APIs, **normalizar** y **validar** los movimientos, **detectar duplicados**, **almacenar** en MySQL y **calcular indicadores**. La IA solo interpreta información ya procesada.

### Estructura común (tabla `transactions`)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | int | clave primaria |
| `source` | `bank\|wallet\|notification` | fuente de origen |
| `external_id` | str | id en la fuente (`UNIQUE(source, external_id)`) |
| `occurred_at` | datetime | fecha y hora del movimiento |
| `amount` | decimal(14,2) | siempre positivo |
| `type` | `income\|expense` | sentido |
| `currency` | char(3) | ISO 4217 |
| `description` | str | descripción normalizada |
| `merchant` | str? | comercio o contraparte |
| `category` | str | categoría asignada |
| `category_source` | `rules\|ai\|manual` | quién asignó la categoría |
| `is_duplicate` | bool | marcado como duplicado de otra fuente |
| `duplicate_of_id` | int? | transacción primaria |
| `raw` | JSON | carga original de la fuente |

Mapeo por fuente:

| Campo común | Banco | Billetera | Notificación |
|---|---|---|---|
| `external_id` | `transaction_id` | `movement_id` | `event_id` |
| `occurred_at` | `posted_at` | `created_at` | `parsed.event_date` (12:00) o `received_at` |
| `type` | `DEBIT→expense`, `CREDIT→income` | `OUT→expense`, `IN→income` | `parsed.movement_type` |
| `description` | `description` | `concept` | `parsed.description` |
| `merchant` | `merchant` | `counterparty` | `parsed.merchant` |
| `currency` | `currency` | moneda de la billetera | `parsed.currency` o la moneda por defecto |

Reglas de validación: importe > 0 y finito, moneda de 3 letras, descripción e identificador no vacíos, fecha válida. Un registro inválido se **rechaza** y se informa en el reporte de sincronización. Un evento de notificación con `movement_type = unknown`, sin importe o con `confidence < NOTIFICATION_MIN_CONFIDENCE` (0.6) se **omite**.

Deduplicación:
1. **Exacta**: misma fuente y mismo `external_id` → no se vuelve a insertar.
2. **Entre fuentes**: mismo tipo, mismo importe (±0.005), fecha dentro de `DEDUP_WINDOW_HOURS` (36 h) y similitud de descripción/comercio ≥ `DEDUP_SIMILARITY_THRESHOLD` (0.5). El registro de la fuente primaria (banco o billetera) prevalece; la notificación queda marcada `is_duplicate = true` con `duplicate_of_id`. Los duplicados se conservan para auditoría pero se excluyen de los indicadores.

Transferencias internas (recargas de billetera desde el banco, pago de tarjeta propia) se categorizan como `Transferencias internas` y no cuentan como ingreso ni gasto.

### Endpoints

| Método y ruta | Descripción |
|---|---|
| `GET /api/health` | Estado de BD, de las tres fuentes y de la IA |
| `POST /api/sync` | Ejecuta la sincronización completa y devuelve el reporte |
| `GET /api/sync/runs?limit=20` | Historial de sincronizaciones |
| `GET /api/transactions` | Historial paginado. Filtros: `source`, `type`, `category`, `q`, `date_from`, `date_to`, `include_duplicates`, `page`, `page_size` |
| `GET /api/transactions/{id}` | Detalle incluyendo `raw` |
| `PATCH /api/transactions/{id}/category` | Corrección manual `{"category": "..."}` |
| `GET /api/accounts` | Cuentas y saldos consolidados |
| `GET /api/categories` | Catálogo de categorías |
| `GET /api/analytics/summary?date_from&date_to` | Ingresos, gastos, neto, transferencias internas, conteos |
| `GET /api/analytics/by-category?type=expense\|income&date_from&date_to` | Distribución por categoría con participación |
| `GET /api/analytics/monthly?months=6` | Serie mensual de ingresos/gastos/neto |
| `POST /api/assistant/chat` | `{"message": "...", "conversation_id": null}` → respuesta en lenguaje natural |
| `DELETE /api/assistant/chat/{conversation_id}` | Reinicia la conversación |
| `POST /api/assistant/categorize` | `{"transaction_id": 1, "apply": false}` o `{"description": "...", "type": "expense"}` → categoría sugerida |

Reporte de `POST /api/sync`:
```json
{"run_id": 1, "started_at": "...", "finished_at": "...", "status": "ok|partial|error",
 "fetched": {"bank": 230, "wallet": 85, "notification": 8},
 "inserted": {"bank": 230, "wallet": 85, "notification": 3},
 "duplicates_exact": 0, "duplicates_cross": 4, "skipped": 1, "rejected": 0, "errors": [], "warnings": []}
```
`status = partial` cuando alguna fuente no respondió (`errors`; el resto se sincroniza igual); `error` cuando ninguna respondió. Los registros rechazados por validación se listan en `warnings` y no cambian el estado.

Errores: `400` rango de fechas invertido · `404` transacción inexistente · `422` validación.

---

## 5. Alcance real de la IA

Implementado en el prototipo:

- **Asistente conversacional** (`POST /api/assistant/chat`): el modelo (Claude, SDK oficial de Anthropic) recibe herramientas que consultan los datos consolidados (`get_summary`, `get_by_category`, `get_monthly_trend`, `search_transactions`, `list_categories`). Las cifras las calcula el backend; el modelo interpreta, explica patrones y sugiere ajustes. Cada respuesta indica qué herramientas consultó.
- **Sugerencia de categoría** (`POST /api/assistant/categorize`): salida estructurada restringida al catálogo de categorías; si la IA no está configurada o falla, se usa la categorización por reglas.

Sin clave de API el asistente responde que no está configurado y todo lo demás funciona.

Queda como mejora futura: categorización masiva automática en cada sincronización, detección de anomalías, metas de ahorro persistentes y memoria de conversación en base de datos.
