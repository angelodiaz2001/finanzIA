# Spec 002 · Vista interactiva de presupuestos mensuales en el frontend

## 1. Objetivo e historia de usuario
Como usuario de FinanzIA, quiero gestionar mis presupuestos mensuales desde una pestaña «Presupuestos» en la aplicación web (crear o editar topes por categoría, eliminarlos y ver barras de avance por estado) para vigilar mi gasto sin salir del navegador.

- **Alcance:** Frontend (`frontend/src/**`).
- **Rama:** `feat/002-presupuestos-mensuales-ui`

## 2. Criterios de aceptación verificables
- **CA-1 (Cliente HTTP y navegación):** `frontend/src/api.js` agrega `budgets(month)`, `saveBudget(payload)` y `deleteBudget(id)`. `frontend/src/App.jsx` incorpora la pestaña `"Presupuestos"` en la barra principal de pestañas y le pasa `version` para refrescar datos tras pulsar *Sincronizar fuentes*.
- **CA-2 (Resumen, barras y estados en español):** `frontend/src/components/BudgetsView.jsx` consulta en paralelo (`Promise.all`) `api.budgets(month)` y `api.categories()`, muestra tarjetas de total presupuestado, total gastado y saldo global, y por cada categoría renderiza monto gastado, tope, restante (`formatMoney`), porcentaje y estado legible (`En orden`, `En alerta` o `Excedido`). Si no hay presupuestos en el mes, muestra `"Aún no definiste presupuestos para este mes."`.
- **CA-3 (Formulario accesible de guardado y eliminación):** incluye selector de mes (`input type="month"` con `<label>`), selector de categoría de gasto (excluyendo `Transferencias internas` y `Transferencias enviadas`) y campo numérico de tope mensual, permitiendo guardar con `api.saveBudget` y eliminar cualquier presupuesto con `api.deleteBudget` (`aria-label` descriptivo por categoría).
- **CA-4 (Temas claro/oscuro y manejo de errores):** las barras de estado usan clases en `frontend/src/styles.css` basadas exclusivamente en variables CSS (`--good`, `--series-2`, `--critical`, `--surface-2`), con cero literales hexadecimales en JSX, y cualquier fallo de red se informa en `<div className="notice error" role="alert">`.
- **CA-5 (Calidad automática):** `npm run lint`, `npm run test:coverage` (`>= 80 %`) y `npm run build` terminan sin errores.

## 3. Restricciones
- No modificar `backend/**`, `services/**` ni `frontend/vite.config.js`.
- No agregar dependencias npm nuevas ni llamar `fetch(` fuera de `frontend/src/api.js`.
