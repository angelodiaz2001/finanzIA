---
name: sdd-tasks
description: Genera únicamente specs/NNN-nombre/tasks.md a partir de spec.md y plan.md aprobados, ordenando tareas Red antes que Green por subagente y deteniéndose para aprobación humana.
argument-hint: "[specs/NNN-nombre]"
---

# Fase 3 SDD: Dividir en tareas (`/sdd-tasks`)

Construye la lista ejecutable de tareas (`tasks.md`) a partir de `spec.md` y `plan.md` previamente aprobados por el desarrollador.

## Pasos obligatorios
1. **Verificación de artefactos previos:** localiza `specs/NNN-nombre/` y comprueba que tanto `spec.md` como `plan.md` existen. Si falta alguno, detente e indica el comando previo correspondiente (`/sdd-specify` o `/sdd-plan`).
2. **Estructura obligatoria de `specs/NNN-nombre/tasks.md`:**
   - Organiza los pasos con casillas `- [ ] T01`, `- [ ] T02`... agrupados por fases claras.
   - Indica en cada tarea el subagente responsable (`test-backend`, `dev-backend`, `test-frontend`, `dev-frontend`, `verificador-e2e`, `revisor-calidad`, `auditor-convergencia`) y las rutas concretas involucradas.
   - **Regla TDD no negociable:** en cada capa, las tareas de pruebas que fallan (**Red**: `test-backend` o `test-frontend`) preceden siempre a las tareas de implementación (**Green**: `dev-backend` o `dev-frontend`).
   - **Orden entre capas:** cuando una funcionalidad crea o cambia un endpoint, ubica la pareja del backend (`test-backend` -> `dev-backend` + actualización de `docs/api-contracts.md`) antes de la pareja del frontend (`test-frontend` -> `dev-frontend`). Marca con `[P]` solo tareas de subagentes distintos cuyos archivos y contratos no dependan entre sí.
   - Cierra siempre con las tareas de control de calidad (`verificador-e2e`, `revisor-calidad` y `auditor-convergencia`).
3. **Parada obligatoria para revisión humana:**
   - **No ejecutes las tareas ni modifiques código en este comando.**
   - Muestra el resumen de fases y detén el flujo para que el desarrollador apruebe `tasks.md` antes de lanzar `/sdd-implement` o `claude --agent orquestador`.
