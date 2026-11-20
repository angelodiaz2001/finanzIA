---
name: review-pr
description: Revisa la rama actual antes de abrir un Pull Request hacia main delegando el diff al subagente revisor-calidad y clasificando cada hallazgo en Aceptar, Cuestionar o Descartar para decisión del desarrollador.
argument-hint: "[rama base, por defecto main]"
---

# Revisión asistida de Pull Request en FinanzIA (`/review-pr`)

La IA actúa como **primer revisor**; la decisión final sobre cada observación corresponde siempre al desarrollador humano. Responde siempre en español.

## Pasos obligatorios
1. **Alcance del cambio:** toma la rama base del argumento recibido o usa `main` por defecto. Ejecuta `git diff --name-only <base>...HEAD` y `git diff --stat <base>...HEAD`. Si no hay cambios frente a la base, infórmalo y termina.
2. **Delegación independiente:** delega en el subagente `revisor-calidad` (solo lectura, modelo `opus`) pasándole el diff `<base>...HEAD`, la lista de archivos modificados y la carpeta `specs/NNN-nombre/` correspondiente.
3. **Propuesta de clasificación:** para cada observación (incluidos comentarios de revisores automáticos en GitHub si existen), propón una de estas tres decisiones:
   - **Aceptar:** hay evidencia verificable de que incumple `specs/constitution.md`, `CLAUDE.md` o un criterio `CA-*` de `spec.md`, o falla una prueba, una guardia arquitectónica, un mutante superviviente o una regla WCAG 2.2 AA.
   - **Cuestionar:** es plausible pero carece de evidencia reproducible o contradice una decisión aprobada en `plan.md`; se solicita evidencia concreta antes de modificar código.
   - **Descartar:** es preferencia subjetiva de estilo no recogida en las normas del repositorio, falso positivo comprobado en el código o complejidad innecesaria fuera de `spec.md`.
4. **Confirmación humana:** presenta la tabla (`ID`, severidad, `archivo:línea`, observación, decisión propuesta y motivo) y pregunta al desarrollador con `AskUserQuestion` si confirma la clasificación.
5. **Resultado sin edición directa:** entrega la lista de acciones aceptadas y el resumen listo para documentar en el Pull Request. **No edites código dentro de esta skill.**

## Traza en el chat
```text
➡️ [DELEGA -> revisor-calidad] diff <base>...HEAD · <n> archivos
⬅️ [RESPUESTA <- revisor-calidad] <ESTADO> · <n> hallazgos
🧭 [CLASIFICACIÓN] <n> aceptar · <n> cuestionar · <n> descartar (propuesta al desarrollador)
```
