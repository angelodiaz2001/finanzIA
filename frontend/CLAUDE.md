# Frontend de FinanzIA

SPA en **React 18 + Vite 6** con **JavaScript (JSX), sin TypeScript**. Gráficos con **Recharts**. Sin router, sin librería de estado, sin framework CSS: todo el estilo vive en `src/styles.css`.

## Comandos (PowerShell, desde `frontend/`)

```powershell
npm install
npm run dev      # http://localhost:5173 (necesita el backend en :8000)
npm run build    # única verificación automática del frontend: debe compilar sin errores
```

En desarrollo Vite redirige `/api` a `http://127.0.0.1:8000` (`vite.config.js`). Para ver datos hay que levantar el backend y pulsar **Sincronizar fuentes** en la interfaz.

No hay pruebas automáticas ni linter en el frontend. La verificación es `npm run build` más una prueba manual en el navegador, en tema claro **y** oscuro.

## Organización

- `src/App.jsx` cabecera, pestañas (Panel, Transacciones, Asistente IA), filtro de periodo y estado de servicios. Pasa `range` (`{date_from, date_to}`) y `version` (se incrementa al sincronizar) a las vistas.
- `src/api.js` **único** lugar que llama al backend. Todo endpoint nuevo se agrega como método del objeto `api`; los componentes nunca usan `fetch` directo. También tiene `formatMoney`, `formatDate` y `SOURCE_LABELS`.
- `src/components/` una vista o gráfico por archivo, `PascalCase.jsx`, `export default function`.
- `src/components/useChartTheme.js` lee las variables CSS para dar color a Recharts; úsalo en cualquier gráfico nuevo.

## Convenciones

- Carga de datos con `useEffect` + bandera `cancelled` y dependencias `[range, version]`, como en `Dashboard.jsx`. Errores en `<div className="notice error">` con texto en español.
- Reutiliza las clases existentes de `styles.css` (`card`, `grid-2`, `tiles`/`tile`, `table`, `num`, `pill`, `small`, `notice`, `chip`, `btn`) antes de crear nuevas.
- Colores **solo** con variables CSS (`--series-1`, `--text-2`, `--good`, `--critical`…); nunca valores hexadecimales en los componentes, o se rompe el modo oscuro.
- Montos con `formatMoney(valor, currency)` y fechas con `formatDate`; nunca `toFixed` a mano.
- Textos de la interfaz en español; accesibilidad básica (`aria-label` en controles sin texto, `role="alert"` en errores).

## Lo que no debes hacer

- No cambies el puerto 5173 ni el proxy de `vite.config.js`.
- No agregues dependencias npm (UI kits, axios, etc.) sin justificarlo en el plan.
- No edites `package-lock.json` a mano.
