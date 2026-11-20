---
name: sdd-flujo-finanzia
description: Mapa de referencia del flujo SDD en FinanzIA mediante los comandos atómicos /sdd-specify, /sdd-plan, /sdd-tasks y /sdd-implement con aprobación humana entre cada artefacto.
---

# Flujo SDD del monorepo FinanzIA

FinanzIA ejecuta el desarrollo guiado por especificaciones (SDD) mediante **cuatro comandos independientes**, deteniendo el flujo al terminar cada documento para evitar arrastrar errores en cadena sin revisión humana:

| Orden | Comando en Claude Code | Qué produce | Puerta humana antes de seguir |
|---|---|---|---|
| 1 | `/sdd-specify <necesidad>` | Rama `feat/NNN-nombre` y `specs/NNN-nombre/spec.md` (apoyado en `/interview`) | El desarrollador revisa y aprueba `spec.md` (qué y por qué). |
| 2 | `/sdd-plan [specs/NNN-nombre]` | `specs/NNN-nombre/plan.md` tras consultar al subagente `arquitecto` | El desarrollador valida contratos HTTP, impacto en `models.py` y archivos por capa. |
| 3 | `/sdd-tasks [specs/NNN-nombre]` | `specs/NNN-nombre/tasks.md` con tareas **Red** antes que **Green** por subagente | El desarrollador aprueba la secuencia de tareas antes de escribir código. |
| 4 | `/sdd-implement` (o `claude --agent orquestador`) | Código, pruebas >= 80 %, verificación E2E, revisión y convergencia (`converged`) | El desarrollador corre opcionalmente `/mutacion-backend`, ejecuta `/review-pr` y abre el Pull Request hacia `main`. |
