---
name: review-pr
description: Revisa el diff completo de la rama actual frente a main usando el subagente revisor-calidad y clasifica cada observación bajo los criterios Aceptar, Cuestionar o Descartar antes de abrir o fusionar un Pull Request.
---

# Revisión asistida de Pull Request en FinanzIA

Invoca esta skill antes de abrir un Pull Request hacia `main` o al evaluar comentarios de revisión sobre una rama activa.

## Pasos
1. Inspecciona los archivos modificados frente a `main` con `git status` y `git diff main...HEAD`.
2. Lanza el subagente `revisor-calidad` pasándole el diff y la carpeta `specs/NNN-*/` correspondiente (si aplica).
3. Clasifica cada punto reportado (incluidos comentarios de revisores automáticos en GitHub si existen) aplicando estas tres decisiones explícitas:
   - **Aceptar:** incumple una regla de `CLAUDE.md`, `specs/constitution.md` o `spec.md`, o produce un fallo reproducible en pruebas, seguridad o accesibilidad.
   - **Cuestionar:** contradice una decisión aprobada en `plan.md` o carece de evidencia verificable; se consulta con el equipo antes de tocar código.
   - **Descartar:** es preferencia subjetiva de estilo o agrega abstracciones innecesarias fuera del alcance de `spec.md`.
4. Resume la tabla final de observaciones aceptadas y descartadas para dejar constancia en la descripción o comentarios del Pull Request.
