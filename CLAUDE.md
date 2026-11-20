# FinanzIA

Prototipo académico de finanzas personales. Consolida movimientos de tres APIs **simuladas** (banco, billetera, notificaciones), los guarda normalizados y los muestra en un panel web con un asistente de IA. Todo con datos ficticios.

Es un **monorepo**: `backend/` (FastAPI) y `frontend/` (React + Vite) tienen cada uno su propio `CLAUDE.md` con lo específico de esa parte. Este archivo concentra las normas y el arnés común.

## Constitución del proyecto (fuente única de verdad)

@specs/constitution.md

La constitución importada arriba rige toda conversación, haya o no un comando SDD activo; ante cualquier conflicto con otras notas, prevalece `specs/constitution.md`. Si una solicitud contradice alguno de sus principios, adviértelo al desarrollador antes de tocar archivos.

## Mapa del repositorio y del arnés

- `backend/app/` backend principal (puerto 8000) -> ver `backend/CLAUDE.md`
- `frontend/src/` interfaz React (puerto 5173) -> ver `frontend/CLAUDE.md`
- `services/` las tres APIs simuladas (8001 banco, 8002 billetera, 8003 notificaciones). Son fixtures de datos: no las modifiques.
- `docs/api-contracts.md` contrato de cada API y estructura común de transacción. **Si cambias un endpoint o un esquema, actualiza este archivo en la misma entrega.**
- `specs/` constitución (`specs/constitution.md`) y especificaciones SDD (`specs/NNN-nombre/{spec.md, plan.md, tasks.md}`).
- `.claude/agents/` sistema único de 9 agentes (`orquestador`, `arquitecto`, `test-backend`, `dev-backend`, `test-frontend`, `dev-frontend`, `verificador-e2e`, `revisor-calidad`, `auditor-convergencia`).
- `.claude/rules/` reglas automáticas por ruta (`paths:`) para Python, pytest, React y especificaciones SDD.
- `.claude/skills/` comandos SDD y de calidad (`/interview`, `/sdd-specify`, `/sdd-plan`, `/sdd-tasks`, `/sdd-implement`, `/sdd-flujo-finanzia`, `/review-pr`, `/mutacion-backend`), junto a las skills por capa en `backend/.claude/skills/` y `frontend/.claude/skills/`.
- `.claude/settings.json` y `.claude/hooks/guard_agent_paths.py` bloqueo determinista de secretos, aislamiento de carpetas por subagente y bloqueo de `git push` / `gh pr merge` desde agentes.
- `.github/workflows/ci.yml` pipeline de integración continua para cada Pull Request hacia `main`.

## Entorno y verificación (PowerShell, desde la raíz)

```powershell
# instalar dependencias
.venv\Scripts\python -m pip install -r backend\requirements.txt -r services\requirements.txt
cd frontend; npm install; cd ..

# levantar todo (una ventana por servicio)
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1

# calidad backend (ruff + pytest + arquitectura + cobertura >= 80%)
.venv\Scripts\ruff check backend services
.venv\Scripts\python -m pytest --cov=backend.app --cov-report=term-missing --cov-fail-under=80

# calidad frontend (eslint + jsx-a11y + guardias + vitest >= 80% + build)
cd frontend; npm run lint; npm run test:coverage; npm run build; cd ..

# auditoría de mutación AST bajo demanda
.venv\Scripts\python scripts\run_mutation_check.py --per-file 6
```

## Flujo SDD y de Git

- Nunca trabajes ni hagas commit directo en `main`. Crea una rama por solicitud desde `main` actualizado (`feat/<tema>`, `fix/<tema>`, `chore/<tema>`, `docs/<tema>`).
- Toda funcionalidad nueva se construye paso a paso con parada humana entre artefactos: `/sdd-specify` (`spec.md`) -> aprobación -> `/sdd-plan` (`plan.md`) -> aprobación -> `/sdd-tasks` (`tasks.md`) -> aprobación -> `/sdd-implement` o `claude --agent orquestador` (`Red -> Green -> Refactor` y convergencia).
- Commits pequeños y en **español**, sin trailers de coautoría automática. Solo el desarrollador humano ejecuta `git push` y fusiona el Pull Request tras ver el CI en verde.

## Lo que no debes hacer

- No leas, edites ni subas `.env` (contiene `ANTHROPIC_API_KEY`). Documenta variables nuevas solo en `.env.example`.
- No cambies credenciales ni puertos de `docker-compose.yml`, `vite.config.js` ni `services/**`.
- No hagas que la IA calcule cifras: todo monto, porcentaje o detección numérica se calcula en código determinista del backend; el modelo solo interpreta herramientas con `"strict": True`.
- No consultes `context7` por rutina: úsalo únicamente cuando el código del repositorio, `CLAUDE.md` y `docs/api-contracts.md` no resuelvan una duda puntual sobre una API externa (una consulta por duda).
- No agregues dependencias nuevas (pip o npm) sin justificarlo en `plan.md`.
- No borres ni relajes pruebas existentes para forzar que pasen.
