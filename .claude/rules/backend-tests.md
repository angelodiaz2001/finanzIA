---
paths:
  - "backend/tests/**/*.py"
---

# Reglas para pruebas del backend

- Usa los fixtures `client` y `db_session` de `backend/tests/conftest.py` (SQLite en memoria, sin leer `.env` ni llamar a la API real de Anthropic ni levantar los puertos 8001 a 8003).
- Cada prueba debe verificar comportamiento observable contra los criterios de aceptación de `spec.md`, nunca repetir de forma literal la preparación del mock.
- Para cada endpoint nuevo de indicadores o presupuestos cubre como mínimo:
  1. Caso feliz con montos y orden exactos sobre datos conocidos.
  2. Exclusión comprobada de duplicados (`is_duplicate=True`) y transferencias (`INTERNAL_TRANSFERS` y, cuando aplique, `SENT_TRANSFERS`).
  3. Validación de parámetros inválidos (`400` con mensaje en español o `422`).
  4. Respuesta controlada cuando no existen datos en el periodo (`200` con lista o resumen en cero).
- Mantén la cobertura de `backend.app` en al menos 80 % (`pytest --cov=backend.app --cov-fail-under=80`).
