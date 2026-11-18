# Frontend de FinanzIA

SPA en **React 18 + Vite 6** con **JavaScript (JSX), sin TypeScript**. Gráficos con **Recharts**. Sin router externo, sin librería global de estado y sin framework CSS: todo el estilo vive en `src/styles.css`.

## Comandos (PowerShell, desde `frontend/`)

```powershell
npm install
npm run dev            # http://localhost:5173 (redirige /api a :8000)
npm run lint           # ESLint (react-hooks + jsx-a11y) + guardias anti-hex y anti-fetch
npm test               # Vitest + React Testing Library (jsdom)
npm run test:coverage  # Cobertura v8 con umbral >= 80 % de líneas
npm run build          # Compilación de producción con Vite
```

## Organización

- `src/App.jsx` cabecera, pestañas (`Panel`, `Presupuestos`, `Transacciones`, `Asistente IA`), filtro de periodo y estado de servicios. Pasa `range` (`{date_from, date_to}`) y `version` (se incrementa al sincronizar) a las vistas.
- `src/api.js` **único** módulo autorizado para invocar `fetch(`. También exporta `formatMoney`, `formatDate` y `SOURCE_LABELS`.
- `src/components/` una vista o tarjeta por archivo (`PascalCase.jsx`, `export default function`).
- `src/__tests__/` pruebas de comportamiento con Vitest y React Testing Library.

## Convenciones y guardias automáticas

- Carga asíncrona con `useEffect` + bandera `cancelled` y dependencias `[range, version]` (usando `Promise.all` para peticiones independientes según `vercel-react-best-practices`).
- Errores siempre en `<div className="notice error" role="alert">` con mensaje en español.
- Colores **solo** con variables CSS de `src/styles.css` (`--series-1`, `--series-2`, `--good`, `--critical`, `--surface-2`, `--text-2`); `scripts/check_frontend_guards.mjs` bloquea cualquier literal `#hex` en `src/components/*.jsx`.
- Montos con `formatMoney(valor, currency)` y fechas con `formatDate`; etiquetas `<label>` o `aria-label` en cada control interactivo.

## Lo que no debes hacer

- No cambies el puerto 5173 ni el proxy `/api` de `vite.config.js`.
- No edites `src/__tests__/**` desde `dev-frontend` ni `package-lock.json` a mano.
