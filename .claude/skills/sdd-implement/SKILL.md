---
name: sdd-implement
description: Ejecuta de forma orquestada las tareas aprobadas en specs/NNN-nombre/tasks.md delegando el ciclo TDD (Red, Green, verificación E2E, revisión y convergencia) en los ocho subagentes.
argument-hint: "[specs/NNN-nombre]"
---

# Fase 4 SDD: Implementar con orquestación (`/sdd-implement`)

Ejecuta las tareas aprobadas en `specs/NNN-nombre/tasks.md` actuando bajo las mismas reglas del agente `orquestador` (o desde una sesión iniciada con `claude --agent orquestador`).

## Pasos obligatorios
1. **Comprobación previa:** verifica que `spec.md`, `plan.md` y `tasks.md` existen en `specs/NNN-nombre/` y que el árbol de trabajo esté en la rama `feat/NNN-nombre`. Si falta alguno de los tres documentos, detente sin tocar código.
2. **Rol estricto de orquestador:**
   - Solo puedes editar `specs/NNN-nombre/tasks.md` para marcar `[X]` las tareas completadas o añadir tareas puntuales de revisión/convergencia.
   - Nunca edites directamente `backend/**`, `frontend/**`, `services/**` ni `docs/**`; delega cada bloque en el subagente asignado.
3. **Delegación ordenada y TDD estructural:**
   - Ejecuta siempre el bloque **Red** (`test-backend` / `test-frontend`) y confirma la evidencia del fallo esperado antes de delegar el bloque **Green** (`dev-backend` / `dev-frontend`).
   - Si cambia la API HTTP, completa primero backend y la actualización de `docs/api-contracts.md` antes de delegar frontend.
   - Al cerrar las tareas de implementación, verifica cobertura >= 80 %, delega en `verificador-e2e` y luego en `revisor-calidad` (máximo **2 vueltas** de corrección por bucle; si persiste, consulta al desarrollador con `AskUserQuestion`).
4. **Convergencia final:** cuando todas las tareas estén en `[X]`, delega en `auditor-convergencia` hasta obtener `RESULTADO: converged` (máximo 2 vueltas).
5. **Traza visible en el chat:**
   ```text
   🎬 [ORQUESTADOR] Inicio · specs/NNN-nombre · <n> tareas pendientes
   ➡️ [DELEGA -> <subagente>] <tareas> · <motivo Red/Green/Control>
   ⬅️ [RESPUESTA <- <subagente>] <ESTADO> · <resumen de evidencia>
   🔁 [CONVERGENCIA] Vuelta <k> · <converged | tasks_appended>
   🏁 [ORQUESTADOR] Fin · Converged · listo para /mutacion-backend (opcional) y /review-pr
   ```
