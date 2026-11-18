# Tareas · Spec 002: Vista interactiva de presupuestos mensuales

## Fase 1: Pruebas de comportamiento desde criterios (Red)
- [X] **T1.1 (`test-frontend`):** Crear `frontend/src/__tests__/BudgetsView.test.jsx` verificando `CA-1` a `CA-4` (estados `En orden` / `En alerta` / `Excedido`, formulario de creación, eliminación accesible, estado vacío y error `role="alert"`) y confirmar fallo inicial en `npm test`.

## Fase 2: Implementación de cliente HTTP, vista y estilos (Green + Refactor)
- [ ] **T2.1 (`dev-frontend`):** Agregar métodos `budgets`, `saveBudget` y `deleteBudget` en `frontend/src/api.js`.
- [ ] **T2.2 (`dev-frontend`):** Implementar `frontend/src/components/BudgetsView.jsx` con `Promise.all`, etiquetas accesibles y clases basadas en variables CSS.
- [ ] **T2.3 (`dev-frontend`):** Conectar pestaña `"Presupuestos"` en `frontend/src/App.jsx` y añadir estilos de barra de presupuesto en `frontend/src/styles.css`.

## Fase 3: Verificación, accesibilidad y convergencia
- [ ] **T3.1 (`test-frontend`):** Comprobar `npm run lint`, `npm run test:coverage` (`>= 80 %`) y `npm run build`.
- [ ] **T3.2 (`verificador-e2e`):** Verificar navegación en pestaña Presupuestos en temas claro y oscuro.
- [ ] **T3.3 (`revisor-calidad` + `auditor-convergencia`):** Auditar cumplimiento de `spec.md` y cero hexadecimales en JSX.
