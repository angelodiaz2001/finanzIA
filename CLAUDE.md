# FinanzIA

Prototipo académico de finanzas personales. Consolida movimientos de tres APIs **simuladas** (banco, billetera, notificaciones), los guarda normalizados y los muestra en un panel web con un asistente de IA. Todo con datos ficticios.

Es un **monorepo**: `backend/` (FastAPI) y `frontend/` (React + Vite) tienen cada uno su propio `CLAUDE.md` con lo específico de esa parte. Este archivo tiene solo lo común.

## Mapa del repositorio

- `backend/app/` backend principal (puerto 8000) → ver `backend/CLAUDE.md`
- `frontend/src/` interfaz React (puerto 5173) → ver `frontend/CLAUDE.md`
- `services/` las tres APIs simuladas (8001 banco, 8002 billetera, 8003 notificaciones). Son fixtures de datos, no las modifiques salvo que la tarea lo pida.
- `docs/api-contracts.md` contrato de cada API y estructura común de transacción. **Si cambias un endpoint o un esquema, actualiza este archivo en el mismo commit.**
- `scripts/start_all.ps1` arranca todo en Windows.

## Entorno del equipo

Windows 10 + PowerShell, Python 3.13 en `.venv` de la **raíz** (no hay venv dentro de `backend/`), Node 24. Todos los comandos se ejecutan desde la raíz del repositorio salvo que se indique otra cosa.

```powershell
# instalar
.venv\Scripts\python -m pip install -r backend\requirements.txt -r services\requirements.txt
cd frontend; npm install; cd ..

# levantar todo (una ventana por servicio)
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1

# pruebas (backend y servicios; pytest.ini está en la raíz)
.venv\Scripts\python -m pytest
```

## Flujo de Git

- Nunca trabajes ni hagas commit directo en `main`. Una rama por solicitud, creada desde `main` actualizado: `feat/<tema>`, `fix/<tema>`, `chore/<tema>`, `docs/<tema>`.
- Commits pequeños y en **español**: título corto en infinitivo ("Agregar endpoint de comercios principales") y, si hace falta, un cuerpo con el qué y el porqué.
- Antes de cada commit: `.venv\Scripts\python -m pytest` en verde y, si tocaste el frontend, `cd frontend; npm run build` sin errores.
- Todo llega a `main` por pull request.

## Lo que no debes hacer

- No leas, edites ni subas `.env` (tiene la `ANTHROPIC_API_KEY`). Las variables nuevas se documentan en `.env.example` sin valores secretos.
- No cambies credenciales ni puertos de `docker-compose.yml` ni las URLs/puertos de los servicios.
- No hagas que la IA calcule cifras: los montos y totales se calculan con código en `backend/app/analytics.py`; la IA solo los interpreta (principio de diseño del proyecto).
- No agregues dependencias nuevas (pip o npm) sin decirlo explícitamente en el plan.
- No borres ni reescribas pruebas existentes para que pasen; si una falla, explica por qué.
