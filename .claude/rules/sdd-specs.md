---
paths:
  - "specs/**/*.md"
---

# Reglas para especificaciones SDD en `specs/`

Cada funcionalidad desarrollada con SDD vive en una subcarpeta `specs/NNN-nombre-corto/` y debe contener estos tres artefactos coherentes entre sí:

1. `spec.md`: objetivo para el usuario de FinanzIA, alcance (backend, frontend o ambos), criterios de aceptación numerados y verificables (`CA-1`, `CA-2`...) y restricciones de dominio/arquitectura.
2. `plan.md`: decisiones técnicas justificadas, contrato HTTP involucrado (referencia a `docs/api-contracts.md`), lista exacta de archivos a crear o modificar y estrategia de pruebas por capa.
3. `tasks.md`: pasos ordenados en fases con casillas `- [ ]` / `- [X]`, identificando el agente responsable (`test-backend`, `dev-backend`, `test-frontend`, `dev-frontend`, `verificador-e2e`, `revisor-calidad`, `auditor-convergencia`) y asegurando siempre tareas Red antes que tareas Green.
