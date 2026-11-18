---
paths:
  - "frontend/src/**/*.{js,jsx,css}"
---

# Reglas para el frontend React

- El proyecto usa React 18 + Vite 6 en JavaScript (JSX) sin TypeScript: verifica siempre los nombres exactos de propiedades contra `docs/api-contracts.md`.
- `frontend/src/api.js` es el único archivo autorizado para invocar `fetch(`. Todo endpoint nuevo se expone como método del objeto `api`.
- Prohibido usar colores hexadecimales fijos (`#...`) dentro de `frontend/src/components/*.jsx`; emplea únicamente las variables CSS definidas en `frontend/src/styles.css` (`--series-1`, `--series-2`, `--good`, `--critical`, `--surface-2`, `--text-2`, etc.) para conservar el tema claro y el tema oscuro.
- Formatea importes con `formatMoney(valor, currency)` y fechas con `formatDate(iso)` de `src/api.js`.
- En efectos de carga asíncrona usa bandera `let cancelled = false` en el cleanup y recarga cuando cambien `range` o `version`.
- Accesibilidad obligatoria: mensajes de error dentro de un contenedor con `role="alert"` en español, controles sin texto visible con `aria-label` y etiquetas `<label>` asociadas a cada campo de formulario.
