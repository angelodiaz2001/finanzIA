---
name: sdd-flujo-finanzia
description: Guía el desarrollo guiado por especificaciones (SDD) en FinanzIA desde la creación de spec.md, plan.md y tasks.md hasta la ejecución coordinada con el orquestador y la apertura del Pull Request.
---

# Flujo SDD del monorepo FinanzIA

Usa esta skill cuando vayas a construir una funcionalidad nueva en FinanzIA mediante desarrollo guiado por especificaciones.

## 1. Preparar la rama y la carpeta `specs/NNN-nombre/`
1. Crea desde `main` actualizado una rama `feat/NNN-nombre`.
2. Crea la carpeta `specs/NNN-nombre/` con numeración consecutiva de tres dígitos (`001`, `002`...).

## 2. Redactar y revisar los tres artefactos antes de escribir código
1. **`spec.md`:** qué problema resuelve, para quién, alcance (`Backend`, `Frontend` o `Ambos`), criterios de aceptación numerados y verificables (`CA-1`, `CA-2`...) y restricciones de FinanzIA (exclusión de duplicados y transferencias, sin cálculos en el LLM, variables CSS si hay UI).
2. **`plan.md`:** invoca primero al subagente `arquitecto` si hay dudas abiertas o cambios en `models.py`. Documenta contrato HTTP (`docs/api-contracts.md`), archivos exactos a crear o editar y casos de prueba por capa. Detente para aprobación humana antes de pasar a tareas.
3. **`tasks.md`:** divide el trabajo en fases cortas con casillas `- [ ]`, asignando el subagente responsable de cada paso y ubicando siempre las tareas **Red** (`test-backend` / `test-frontend`) antes de las tareas **Green** (`dev-backend` / `dev-frontend`), seguidas por `verificador-e2e`, `revisor-calidad` y `auditor-convergencia`.

## 3. Ejecutar con el sistema de agentes y cerrar el PR
1. Invoca al agente `orquestador` indicando la ruta `specs/NNN-nombre/`.
2. Al recibir `converged`, ejecuta opcionalmente `/mutacion-backend` si tocaste módulos de cálculo y corre `/review-pr` antes de abrir el Pull Request hacia `main`.
