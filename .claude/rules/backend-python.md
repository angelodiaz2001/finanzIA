---
paths:
  - "backend/app/**/*.py"
---

# Reglas para código Python del backend

- Incluye `from __future__ import annotations` al inicio y anotaciones de tipos en funciones públicas (`Optional[...]` consistente con el resto del módulo).
- Respeta las capas: `routers/` valida parámetros HTTP, delega en `analytics.py` o en el módulo de servicio correspondiente y devuelve esquemas de `schemas.py`; no pongas consultas `select()` ni agregaciones en routers de indicadores o presupuestos.
- En todo cálculo financiero excluye `Transaction.is_duplicate.is_(False)` y `INTERNAL_TRANSFERS`; cuando se analicen comercios o patrones de consumo, excluye además `SENT_TRANSFERS`. Redondea montos a 2 decimales y proporciones (`share`) a 4 decimales.
- Nunca importes `anthropic` ni `backend.app.ai` desde `analytics.py`, `dedup.py`, `normalizer.py` o `categorizer.py`.
- En `backend/app/ai/assistant.py`, cada entrada de `TOOLS` debe incluir `"strict": True` y `"additionalProperties": False`.
- No hay migraciones con Alembic (`init_db()` crea tablas al arrancar): si agregas un modelo nuevo en `models.py`, regístralo limpio sobre `Base`; evita renombrar o borrar columnas de tablas existentes sin advertirlo en `plan.md`.
- Si creas o cambias un endpoint o esquema de respuesta, actualiza `docs/api-contracts.md` en la misma tarea.
