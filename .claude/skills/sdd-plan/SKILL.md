---
name: sdd-plan
description: Genera únicamente specs/NNN-nombre/plan.md a partir de un spec.md aprobado, apoyándose en el subagente arquitecto y deteniéndose para validación humana.
argument-hint: "[specs/NNN-nombre]"
---

# Fase 2 SDD: Planificar (`/sdd-plan`)

Traduce un `spec.md` ya revisado por el desarrollador en el diseño técnico (`plan.md`) alineado con `specs/constitution.md` y `docs/api-contracts.md`.

## Pasos obligatorios
1. **Verificación de entrada:** identifica la carpeta activa `specs/NNN-nombre/` (por argumento o por el nombre de la rama `feat/NNN-nombre`) y confirma que `spec.md` existe y no tiene preguntas pendientes. Si falta `spec.md`, detente e indica ejecutar primero `/sdd-specify`.
2. **Investigación técnica (Fase 0):** delega en el subagente `arquitecto` (solo lectura) el análisis de contratos HTTP en `docs/api-contracts.md`, el impacto en `backend/app/models.py` (recuerda que el proyecto usa `init_db()` sin Alembic) y la correspondencia de campos con `frontend/src/api.js`.
3. **Decisiones abiertas:** si el informe de `arquitecto` plantea alternativas con compromisos de diseño, consulta al desarrollador siguiendo `.claude/skills/interview/SKILL.md` antes de fijar el plan.
4. **Redacción de `specs/NNN-nombre/plan.md`:** documenta:
   - Verificación explícita de los 6 principios de `specs/constitution.md`.
   - Decisiones técnicas tomadas (privilegiando simplicidad y reutilización de módulos existentes).
   - Esquema exacto de rutas, parámetros, respuestas JSON y errores `400/404/422` que se reflejarán en `docs/api-contracts.md`.
   - Lista exacta de archivos a crear o modificar por capa (`backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/src/__tests__/`, `docs/api-contracts.md`).
   - Estrategia de pruebas unitarias, de integración/contrato y de interfaz vinculada a cada `CA-*`.
5. **Parada obligatoria para revisión humana:**
   - **No crees `tasks.md` ni escribas código de producción o pruebas** en este comando.
   - Presenta el resumen del plan y detén la ejecución para que el desarrollador valide o ajuste `plan.md` antes de ejecutar `/sdd-tasks`.
