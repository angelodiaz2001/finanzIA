---
name: interview
description: Guía la entrevista estructurada al desarrollador con AskUserQuestion para resolver ambigüedades de alcance o diseño una por una antes de redactar una spec o un plan en FinanzIA.
---

# Entrevista estructurada al desarrollador en FinanzIA

Analiza la solicitud recibida antes de generar `spec.md` o `plan.md` y resuelve las dudas abiertas con el desarrollador hasta lograr un acuerdo completo y sin supuestos implícitos.

## Reglas obligatorias
1. **Explora antes de preguntar:** si una duda se responde leyendo el código del repositorio, `CLAUDE.md`, `specs/constitution.md` o `docs/api-contracts.md`, verifícalo directamente y no lo preguntes al desarrollador.
2. **Una decisión por turno:** recorre las dudas abiertas en orden lógico de dependencia; no avances a la siguiente hasta resolver la actual.
3. **Usa `AskUserQuestion` en español:** antes de invocar la herramienta, escribe en el chat un contexto corto (2 a 3 oraciones explicando qué se decide, por qué importa en FinanzIA y cuál es la opción recomendada citando evidencia del código).
4. **Formato de opciones:**
   - La primera opción lleva la etiqueta `(Recomendada)` junto con su beneficio principal y su compromiso o límite.
   - Agrega entre 1 y 2 alternativas viables con pros y contras concretos, privilegiando siempre la opción más simple (sin dependencias nuevas innecesarias).
   - Incluye siempre una opción abierta final (`Otra: escribir respuesta propia`) para que el desarrollador ajuste libremente el criterio.
5. **Cierre explícito:** cuando no queden ambigüedades de negocio ni de contrato, confirma en español el resumen de acuerdos tomados y continúa con el comando que invocó la entrevista.
