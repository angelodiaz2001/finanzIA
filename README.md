# FinanzIA: Asistente inteligente de finanzas personales

Prototipo académico de aplicación web que centraliza movimientos financieros de distintas fuentes (un banco, una billetera digital y notificaciones financieras), los normaliza en una sola base de datos y los presenta con estadísticas y un asistente de IA generativa que explica los hábitos de consumo en lenguaje natural.

> **Aviso de alcance.** Las tres APIs de fuentes son **simuladas** y trabajan con datos ficticios. FinanzIA no administra dinero real, no realiza transferencias reales ni accede a cuentas bancarias auténticas. No existen integraciones con entidades financieras reales; esa integración se considera una posible mejora futura.

## Arquitectura

```
┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────────────┐
│  API bancaria (sim) │   │ Billetera digital   │   │ Notificaciones (sim)     │
│  cuentas, saldos,   │   │ (sim) movimientos,  │   │ recibe eventos crudos y  │
│  transacciones      │   │ transferencias,     │   │ extrae importe, tipo,    │
│  :8001              │   │ recargas  :8002     │   │ comercio…  :8003         │
└──────────┬──────────┘   └──────────┬──────────┘   └────────────┬─────────────┘
           └──────────────────────────┼─────────────────────────┘
                                      ▼
                   ┌──────────────────────────────────────┐
                   │  Backend principal (Python + FastAPI) │
                   │  consume → valida → normaliza →       │
                   │  deduplica → categoriza → persiste    │
                   │  indicadores (ingresos, gastos, …)    │──── MySQL (docker)
                   │  asistente IA con tool use  :8000     │     o SQLite local
                   └──────────────────┬───────────────────┘
                                      │  /api            ┌──────────────────┐
                   ┌──────────────────▼───────────────┐   │ Claude (API de   │
                   │  Frontend (React + Vite)  :5173   │   │ Anthropic)       │
                   │  panel, historial, gráficos, chat │   │ interpreta datos │
                   └──────────────────────────────────┘   └──────────────────┘
```

Principio de diseño: **los cálculos financieros, las validaciones y la consolidación se hacen con código convencional** en el backend. La IA solo interpreta y explica información ya procesada: el modelo obtiene las cifras mediante herramientas que consultan la base de datos, lo que reduce el riesgo de montos inventados.

### Estructura del repositorio

```
backend/app/            Backend principal (FastAPI)
  config.py             Configuración por variables de entorno / .env
  database.py, models.py  SQLAlchemy (MySQL o SQLite)
  normalizer.py         Validación y transformación a la estructura común
  dedup.py              Detección de duplicados exactos y entre fuentes
  categorizer.py        Categorización por reglas
  analytics.py          Indicadores: ingresos, gastos, neto, por categoría, mensual
  sync_service.py       Orquestación de la sincronización
  clients/              Clientes HTTP de las tres fuentes
  ai/assistant.py       Asistente (Claude + tool use) y sugerencia de categoría
  routers/              Endpoints REST
backend/tests/          Pruebas (pytest)
services/bank_api/      API bancaria simulada
services/wallet_api/    Billetera digital simulada
services/notifications_api/  Notificaciones: parser de eventos crudos
frontend/               React + Vite + Recharts
docs/api-contracts.md   Contrato de cada API, integración y alcance de la IA
docs/entorno-de-trabajo.md  Editores, control de versiones y suscripciones de IA del equipo
scripts/start_all.ps1   Arranca todos los servicios en Windows
docker-compose.yml      MySQL 8
```

## Requisitos

- Python 3.11 o superior (probado con 3.13)
- Node.js 18 o superior (probado con 24)
- Docker Desktop (opcional, solo para MySQL; sin Docker se usa SQLite)
- Una clave de API de Anthropic (opcional, solo para el asistente de IA)

El detalle del entorno de trabajo del equipo (editores de código, herramienta de control de versiones y suscripciones de modelos de IA) está en [docs/entorno-de-trabajo.md](docs/entorno-de-trabajo.md).

## Instalación (Windows, PowerShell)

```powershell
# 1. Entorno Python con todas las dependencias (backend + servicios simulados)
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt -r services\requirements.txt

# 2. Dependencias del frontend
cd frontend
npm install
cd ..

# 3. Configuración (opcional). Sin .env el backend usa SQLite y la IA queda desactivada.
copy .env.example .env
```

En Linux/macOS los comandos equivalentes son `python3 -m venv .venv`, `.venv/bin/python -m pip install ...` y `cp .env.example .env`.

### Base de datos MySQL (opcional)

```powershell
docker compose up -d        # levanta MySQL 8 con la base finanzia (usuario finanzia / finanzia)
```

El archivo `.env.example` ya apunta a esa instancia (`DATABASE_URL=mysql+pymysql://finanzia:finanzia@localhost:3306/finanzia`). Las tablas se crean automáticamente al arrancar el backend. Si prefieres no usar Docker, elimina la línea `DATABASE_URL` del `.env` y se usará `finanzia.db` (SQLite) en la raíz del proyecto.

### Asistente de IA (opcional)

Edita `.env` y define `ANTHROPIC_API_KEY`. El modelo por defecto es `claude-opus-5-5` (`ANTHROPIC_MODEL`). Sin clave, el resto de la aplicación funciona y el asistente indica que no está configurado.

## Ejecución

Opción rápida (abre una ventana por servicio):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1
```

Opción manual, desde la raíz del repositorio, cada comando en su propia terminal:

```powershell
.venv\Scripts\python -m uvicorn services.bank_api.main:app --port 8001 --reload
.venv\Scripts\python -m uvicorn services.wallet_api.main:app --port 8002 --reload
.venv\Scripts\python -m uvicorn services.notifications_api.main:app --port 8003 --reload
.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload
cd frontend; npm run dev
```

| Componente | URL |
|---|---|
| Interfaz web | http://localhost:5173 |
| Backend (Swagger) | http://localhost:8000/docs |
| API bancaria | http://localhost:8001/docs |
| Billetera digital | http://localhost:8002/docs |
| Notificaciones | http://localhost:8003/docs |

Flujo de demostración:

1. Abre la interfaz y pulsa **Sincronizar fuentes**. El backend consume las tres APIs, normaliza los movimientos, detecta duplicados (p. ej. una compra que aparece en el banco y en un SMS) y los guarda.
2. El **Panel** muestra ingresos, gastos, balance neto, distribución por categorías y la serie mensual.
3. **Transacciones** permite filtrar el historial, corregir categorías manualmente y pedir una sugerencia de categoría.
4. **Asistente IA** responde preguntas como "¿en qué categoría gasté más en los últimos 30 días?" y muestra qué datos consultó.

Para probar la tercera API con un evento propio:

```bash
curl -X POST http://localhost:8003/events -H "Content-Type: application/json" -d "{\"channel\":\"SMS\",\"sender\":\"BancoSim\",\"raw_text\":\"Compra aprobada por S/ 72.40 en LIBRERIA CENTRAL ****4321\"}"
```

y vuelve a sincronizar.

## Pruebas

```powershell
.venv\Scripts\python -m pytest
```

Cubren la normalización de cada fuente, el rechazo de datos inválidos, la detección de duplicados, las reglas de categorización, el parser de notificaciones y los endpoints del backend con fuentes simuladas en memoria.

## Decisiones de integración

- **Quién consume las APIs:** únicamente el backend principal (`sync_service.py`), de forma explícita mediante `POST /api/sync`.
- **Quién normaliza:** `normalizer.py` convierte cada fuente a la estructura común documentada en `docs/api-contracts.md`; los registros inválidos se rechazan y se reportan.
- **Cómo se almacena:** tabla `transactions` con restricción única `(source, external_id)`, carga original en JSON y marcas de duplicado; `accounts` con saldos; `sync_runs` con el reporte de cada ejecución.
- **Duplicados:** exactos por identificador y entre fuentes por importe, tipo, ventana de tiempo y similitud de texto. Las fuentes primarias (banco, billetera) prevalecen sobre las notificaciones.
- **Transferencias internas** (recargas de la billetera desde el banco, pago de la tarjeta propia) no se cuentan como ingreso ni gasto.
- **Alcance de la IA:** asistente conversacional con herramientas y sugerencia de categoría con salida estructurada. Mejoras futuras: categorización masiva automática, detección de anomalías, metas de ahorro persistentes.

## Trabajo con Git

El repositorio tiene configurada a nivel local la identidad del perfil educativo (`git config user.name` / `user.email` con el correo *noreply* de GitHub), de modo que los commits realizados desde esta carpeta se atribuyen a esa cuenta sin depender de la configuración global de la máquina. Comprueba la identidad activa con:

```bash
git config user.name && git config user.email
```

## Licencia y uso

Proyecto académico con fines educativos. Los nombres de comercios, bancos y personas son ficticios.
