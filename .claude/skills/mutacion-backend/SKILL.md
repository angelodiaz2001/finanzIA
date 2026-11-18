---
name: mutacion-backend
description: Ejecuta bajo demanda pruebas de mutación AST sobre los módulos financieros del backend (analytics, dedup, categorizer y normalizer) y clasifica los mutantes supervivientes sin bloquear el bucle TDD.
---

# Auditoría de mutación del backend (bajo demanda)

Usa esta skill fuera del bucle principal del `orquestador` cuando hayas modificado lógica de cálculo o clasificación en `backend/app/` y quieras medir la fortaleza real de las aserciones de `pytest`.

## Por qué va como skill independiente
Ejecutar mutación dentro de cada iteración de subagentes detiene la sesión varios minutos y consume cuota innecesaria. Además, en Windows nativo `mutmut` no arranca por depender de `os.fork()`, por lo que FinanzIA incluye `scripts/run_mutation_check.py` (basado en el módulo estándar `ast`, compatible con Windows PowerShell y con Linux en GitHub Actions).

## Cómo ejecutarla (desde la raíz del repositorio)
```powershell
.venv\Scripts\python scripts\run_mutation_check.py --per-file 6
```

## Cómo interpretar y documentar el resultado
Lee `docs/evidencias/reporte-mutacion-backend.json` y clasifica cualquier mutante con estado `"survived"` en una de estas tres categorías:
1. **Prueba débil:** falta una aserción sobre un borde numérico o condición; pide a `test-backend` agregar el caso que lo elimine.
2. **Mutante equivalente:** el cambio sintáctico produce exactamente el mismo resultado observable (por ejemplo, un empate irrelevante cuando el denominador ya es cero); documéntalo sin inflar pruebas artificiales.
3. **Código sobrante:** rama defensiva inalcanzable; pide a `dev-backend` simplificarla.
