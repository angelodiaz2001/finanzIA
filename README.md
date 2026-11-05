# FinanzIA · Taller 4: memoria del proyecto, skills y modo plan

Diplomado en Ingeniería de Software con IA y Sistemas Agénticos · FET · Grupo 6

**Integrantes:** Elian Danilo Romero Herrera · Angelo David Díaz Cortés · André Ricardo Rodríguez Fernández

**Herramienta:** Claude Code v2.1.318 (Opus 5.5, plan Claude Pro), usado en la terminal de VS Code en Windows con PowerShell

**Proyecto:** FinanzIA es un monorepo, con el backend en [`backend/`](backend/) (Python + FastAPI) y el frontend en [`frontend/`](frontend/) (React + Vite). Por eso la memoria y las skills van por carpeta, como si fueran dos repositorios.

## De qué trata el taller

Un agente de código empieza cada sesión sin saber nada del proyecto. En este taller dejamos funcionando en FinanzIA las tres piezas que lo cambian: la memoria que lee al iniciar, las skills que carga cuando las necesita y un plan que revisamos antes de que toque el código. Con eso implementamos dos solicitudes de principio a fin, cada una en su rama y con su pull request fusionado en `main`.

| Parte | Qué quedó en `main` | Pull request |
|---|---|---|
| 1. Memoria del proyecto | `CLAUDE.md` en la raíz, en `backend/` y en `frontend/` | [#1](https://github.com/angelodiaz2001/finanzIA/pull/1) |
| 2. Skills | `finanzia-nuevo-endpoint` en el backend y `vercel-react-best-practices` en el frontend | [#1](https://github.com/angelodiaz2001/finanzIA/pull/1) |
| 3. Solicitud 1 | Endpoint `GET /api/analytics/top-merchants` | [#2](https://github.com/angelodiaz2001/finanzIA/pull/2) |
| 3. Solicitud 2 | Tarjeta "Comercios donde más gastas" en el Panel | [#3](https://github.com/angelodiaz2001/finanzIA/pull/3) |

## 1. Memoria del proyecto

Trabajamos solo con Claude Code, así que escogimos `CLAUDE.md`, que es el archivo propio de esa herramienta. Como es un monorepo hicimos tres: Claude Code carga el de la raíz al iniciar y el de cada carpeta cuando trabaja con sus archivos.

| Archivo | Qué tiene |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Mapa del repo, comandos en PowerShell, flujo de Git (ramas `feat/`, `fix/`, `chore/` y `docs/`, commits en español, todo por PR) y lo que el agente no debe tocar: el `.env`, los puertos de `docker-compose.yml` y las dependencias nuevas sin avisar |
| [`backend/CLAUDE.md`](backend/CLAUDE.md) | Capas permitidas (router, analytics y schemas), reglas de negocio de todo indicador, que no hay migraciones, que el `.venv` está en la raíz y cómo probar con los fixtures de pytest |
| [`frontend/CLAUDE.md`](frontend/CLAUDE.md) | JavaScript sin TypeScript, `api.js` como único cliente HTTP, colores solo con variables CSS por el modo oscuro y `npm run build` como verificación |

No dejamos el borrador de `/init`: los escribimos a partir del código y dejamos solo lo que el agente no deduciría leyendo los archivos.

## 2. Skills

| Skill | Dónde está | Origen | Revisión de seguridad |
|---|---|---|---|
| [`finanzia-nuevo-endpoint`](backend/.claude/skills/finanzia-nuevo-endpoint/SKILL.md) | `backend/.claude/skills/` | La creamos nosotros | Solo instrucciones en Markdown, sin scripts |
| [`vercel-react-best-practices`](frontend/.claude/skills/vercel-react-best-practices/SKILL.md) | `frontend/.claude/skills/` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | 70 reglas en Markdown, sin scripts; no descarga archivos ni envía datos, y su SKILL.md declara licencia MIT |

Se invocan con `/nombre-de-la-skill`, o el agente las carga solo cuando la tarea coincide con su descripción. De Vercel descartamos `web-design-guidelines`, porque descarga sus reglas de una URL en cada uso y no se puede revisar una sola vez.

## 3. Solicitudes con modo plan

Las dos siguieron el mismo camino:

1. Rama `feat/...` creada desde `main`.
2. Prompt con la fórmula base (qué quiero, para quién, contexto, formato, criterios de aceptación y restricciones) en modo plan.
3. Revisión del plan: archivos que toca, arquitectura y pruebas. Las correcciones se las pedimos al agente, sin editar el plan a mano.
4. Plan final guardado tal cual (`plan-1-grupo6.md` y `plan-2-grupo6.md`, entregados aparte).
5. Implementación, revisión del diff contra el plan, pull request y merge.

### Solicitud 1 · Comercios con mayor gasto (backend)

*Como usuario de FinanzIA, quiero saber en qué comercios gasto más dinero en un periodo, para identificar dónde puedo recortar gastos.*

`GET /api/analytics/top-merchants?date_from=&date_to=&limit=` devuelve los comercios ordenados por total, con `merchant`, `total`, `count` y `share`, sin contar duplicados ni transferencias internas. Al revisar el plan vimos que los envíos de dinero a personas se guardan con el nombre de la persona como comercio, así que le pedimos al agente excluir también la categoría "Transferencias enviadas" y agregar una prueba para eso. Quedaron 9 pruebas nuevas en `backend/tests/test_top_merchants.py` y la suite pasó de 24 a 33 pruebas en verde. PR [#2](https://github.com/angelodiaz2001/finanzIA/pull/2).

### Solicitud 2 · Tarjeta "Comercios donde más gastas" (frontend)

*Como usuario de FinanzIA, quiero ver en el Panel los 5 comercios donde más gasto en el periodo seleccionado, para entender mis hábitos de consumo de un vistazo.*

La tarjeta muestra la posición, el nombre, el número de compras, el monto y una barra proporcional a su participación, y se actualiza al cambiar el periodo o al sincronizar. El primer intento corrió en auto mode y no en modo plan, así que lo descartamos y lo repetimos en modo plan. El cambio toca 4 archivos (`api.js`, `TopMerchants.jsx`, `Dashboard.jsx` y `styles.css`), no agrega dependencias y compila con `npm run build`. PR [#3](https://github.com/angelodiaz2001/finanzIA/pull/3).

## El proyecto FinanzIA

Prototipo académico de finanzas personales. Junta en una sola base de datos los movimientos de tres APIs **simuladas** (banco, billetera digital y notificaciones), calcula los indicadores con código convencional y los muestra en un panel web con un asistente de IA que los explica. Todo funciona con datos ficticios: no maneja dinero real ni se conecta con entidades financieras. El contrato de cada API está en [`docs/api-contracts.md`](docs/api-contracts.md) y el entorno del equipo en [`docs/entorno-de-trabajo.md`](docs/entorno-de-trabajo.md).

### Cómo ejecutarlo (Windows, PowerShell, desde la raíz)

```powershell
# entorno de Python y dependencias
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt -r services\requirements.txt
cd frontend; npm install; cd ..

# levantar todo (una ventana por servicio)
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1

# pruebas del backend y de los servicios simulados
.venv\Scripts\python -m pytest

# verificación del frontend
cd frontend; npm run build; cd ..
```

| Componente | URL |
|---|---|
| Interfaz web | http://localhost:5173 |
| Backend (Swagger) | http://localhost:8000/docs |
| Banco, billetera y notificaciones | http://localhost:8001/docs · http://localhost:8002/docs · http://localhost:8003/docs |

Abre la interfaz y pulsa **Sincronizar fuentes** para cargar los movimientos. Sin archivo `.env` el backend usa SQLite y el asistente de IA queda desactivado; para MySQL y la clave de Anthropic mira `.env.example`.

## Licencia y uso

Proyecto académico con fines educativos. Los nombres de comercios, bancos y personas son ficticios.
