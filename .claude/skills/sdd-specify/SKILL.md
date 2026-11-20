---
name: sdd-specify
description: Crea la rama de funcionalidad y redacta únicamente specs/NNN-nombre/spec.md a partir de una necesidad en lenguaje natural, deteniéndose al terminar para aprobación humana.
argument-hint: "<descripción de la funcionalidad: qué problema resuelve y por qué>"
---

# Fase 1 SDD: Especificar (`/sdd-specify`)

Convierte una necesidad del usuario de FinanzIA en una especificación verificable (`spec.md`). Define **qué se construye y por qué**, sin adelantar código ni detalles internos de implementación.

## Pasos obligatorios
1. **Contexto previo:** lee `specs/constitution.md` y revisa las carpetas existentes en `specs/` para asignar el siguiente número consecutivo de tres dígitos (`NNN`, por ejemplo `006-nombre-corto`).
2. **Entrevista de aclaración:** lee y aplica `.claude/skills/interview/SKILL.md`. Si la solicitud deja dudas de negocio (umbrales, categorías excluidas, periodo por defecto o comportamiento sin datos), pregunta al desarrollador con `AskUserQuestion` antes de escribir el archivo.
3. **Rama y carpeta:** desde `main` actualizado, crea la rama `feat/NNN-nombre-corto` (si aún estás en `main`) y el directorio `specs/NNN-nombre-corto/`.
4. **Redacción de `specs/NNN-nombre-corto/spec.md`:** incluye:
   - Problema y valor para la persona usuaria de FinanzIA.
   - Alcance de capas (`Backend`, `Frontend` o `Ambos`) y lo que queda explícitamente fuera del alcance.
   - Criterios de aceptación numerados y comprobables (`CA-1`, `CA-2`...) con entradas, resultados exactos y casos de error en español.
   - Restricciones obligatorias de FinanzIA aplicables (exclusión de `is_duplicate == True`, exclusión de `INTERNAL_TRANSFERS` y `SENT_TRANSFERS` según corresponda, cero cálculos numéricos en el LLM y uso de variables CSS en UI).
5. **Parada obligatoria para revisión humana:**
   - **No crees `plan.md`, no crees `tasks.md` y no edites código ni pruebas** en este comando.
   - Entrega la ruta `specs/NNN-nombre-corto/spec.md` y detén la ejecución para que el desarrollador revise, ajuste o apruebe la especificación antes de lanzar `/sdd-plan`.
