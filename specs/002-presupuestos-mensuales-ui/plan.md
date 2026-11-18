# Plan técnico · Spec 002: Vista interactiva de presupuestos mensuales

## 1. Decisiones técnicas (`arquitecto` + `vercel-react-best-practices`)
- **Consumo del contrato de Spec 001:** `BudgetsView.jsx` consume exactamente el esquema `BudgetMonthSummary` documentado en `docs/api-contracts.md` (`month`, `currency`, `total_budgeted`, `total_spent`, `items` con `id`, `category`, `limit_amount`, `spent`, `remaining`, `usage_ratio`, `status`).
- **Carga en paralelo sin cascadas:** `useEffect` dispara `Promise.all([api.budgets(month), api.categories()])` con bandera `cancelled` en el cleanup, dependiendo de `[month, version]`.
- **Estilos compatibles con modo oscuro:** en `frontend/src/styles.css` se añaden únicamente las reglas mínimas `.budget-bar-fill.ok` (`var(--good)`), `.budget-bar-fill.warning` (`var(--series-2)`) y `.budget-bar-fill.exceeded` (`var(--critical)`).
- **Filtro global de periodo en `App.jsx`:** igual que ocurre en la pestaña *Asistente IA*, cuando `tab === "budgets"` se oculta la fila de presets rápidos de días porque la vista trabaja sobre un mes calendario exacto (`YYYY-MM`).

## 2. Archivos a crear o modificar
- Crear `frontend/src/__tests__/BudgetsView.test.jsx` (fase Red)
- Modificar `frontend/src/api.js` (`budgets`, `saveBudget`, `deleteBudget`)
- Crear `frontend/src/components/BudgetsView.jsx`
- Modificar `frontend/src/App.jsx` (pestaña `"Presupuestos"`)
- Modificar `frontend/src/styles.css` (clases de barra de presupuesto con variables CSS)

## 3. Estrategia de pruebas (`test-frontend`)
- Pruebas con Vitest + React Testing Library sobre `BudgetsView` y `App`: renderizado de estados `ok`/`warning`/`exceeded`, creación mediante formulario accesible, eliminación por botón con `aria-label`, estado vacío en español y aviso `role="alert"` cuando falla `api.budgets`.
