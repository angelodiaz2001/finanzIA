# Informe de Auditoría de Mutación AST del Backend

Ejecutado mediante la skill bajo demanda `/mutacion-backend` (`scripts/run_mutation_check.py --per-file 6`) sobre los cuatro módulos de lógica determinista de `backend/app/`: `analytics.py`, `dedup.py`, `categorizer.py` y `normalizer.py`.

## 1. Resumen antes y después del endurecimiento de pruebas

| Corrida | Mutantes totales | Eliminados (`killed`) | Supervivientes (`survived`) | Puntaje de mutación |
|---|---:|---:|---:|---:|
| Primera corrida (tras cerrar Specs 001 a 005) | 24 | 20 | 4 | **83.3 %** |
| Segunda corrida (tras agregar `test_mutation_hardening.py`) | 24 | 23 | 1 | **95.8 %** |

## 2. Clasificación de los cuatro supervivientes iniciales

| ID | Archivo y línea | Cambio aplicado | Clasificación | Acción tomada |
|---|---|---|---|---|
| `M-03` | `backend/app/analytics.py:127` (`if month == 0:`) | `Eq -> NotEq` | **Prueba débil** | Las pruebas previas de `monthly()` solo corrían en octubre sin cruzar enero -> diciembre. Se agregó `test_monthly_crosses_year_boundary_and_computes_exact_net` en `backend/tests/test_mutation_hardening.py` (mutante eliminado). |
| `M-04` | `backend/app/analytics.py:146` (`v["income"] - v["expenses"]`) | `Sub -> Add` | **Prueba débil** | No había una aserción directa sobre `net` cuando el mismo mes tenía ingresos y gastos mayores que cero. Cubierto en `test_mutation_hardening.py` (mutante eliminado). |
| `M-06` | `backend/app/analytics.py:221` (`amt >= avg * multiplier`) | `Mult -> Div` | **Prueba débil** | Faltaba en el mismo mes una compra normal situada entre `avg / multiplier` y `avg * multiplier`. Se agregó `test_anomalies_does_not_flag_normal_purchase_near_average` (mutante eliminado). |
| `M-07` | `backend/app/dedup.py:29` (`normalize(a_merchant) == normalize(b_merchant)`) | `Eq -> NotEq` | **Atajo redundante / cuasi-equivalente** | Cuando dos movimientos de fuentes distintas comparten comercio, la comparación Jaccard por tokens de la línea siguiente ya supera el umbral `0.5` sobre los datos consolidados. Se conserva el atajo por claridad y velocidad sin agregar pruebas artificiales. |

El detalle completo por mutante queda disponible en [`reporte-mutacion-backend.json`](reporte-mutacion-backend.json) y como artefacto descargable en cada ejecución del workflow `.github/workflows/ci.yml`.
