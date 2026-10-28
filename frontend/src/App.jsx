import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Dashboard from "./components/Dashboard.jsx";
import TransactionsTable from "./components/TransactionsTable.jsx";
import Assistant from "./components/Assistant.jsx";

const TABS = [
  { id: "panel", label: "Panel" },
  { id: "transactions", label: "Transacciones" },
  { id: "assistant", label: "Asistente IA" },
];

function isoDaysAgo(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

const PRESETS = [
  { id: "30d", label: "Últimos 30 días", range: () => ({ date_from: isoDaysAgo(30), date_to: isoDaysAgo(0) }) },
  { id: "90d", label: "Últimos 90 días", range: () => ({ date_from: isoDaysAgo(90), date_to: isoDaysAgo(0) }) },
  {
    id: "month",
    label: "Este mes",
    range: () => ({ date_from: new Date().toISOString().slice(0, 8) + "01", date_to: isoDaysAgo(0) }),
  },
  { id: "all", label: "Todo", range: () => ({}) },
];

function readTheme() {
  try {
    return localStorage.getItem("finanzia-theme") || "";
  } catch {
    return "";
  }
}

export default function App() {
  const [tab, setTab] = useState("panel");
  const [preset, setPreset] = useState("90d");
  const [range, setRange] = useState(() => PRESETS[1].range());
  const [health, setHealth] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncReport, setSyncReport] = useState(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0); // fuerza recarga de datos tras sincronizar
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    if (theme) document.documentElement.setAttribute("data-theme", theme);
    else document.documentElement.removeAttribute("data-theme");
    try {
      if (theme) localStorage.setItem("finanzia-theme", theme);
      else localStorage.removeItem("finanzia-theme");
    } catch {
      /* almacenamiento no disponible */
    }
  }, [theme]);

  const loadHealth = useCallback(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "down", sources: {}, database: "?" }));
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  function choosePreset(id) {
    setPreset(id);
    setRange(PRESETS.find((p) => p.id === id).range());
  }

  async function runSync() {
    setSyncing(true);
    setError("");
    try {
      const report = await api.sync();
      setSyncReport(report);
      setVersion((v) => v + 1);
      loadHealth();
    } catch (e) {
      setError(`No se pudo sincronizar: ${e.message}`);
    } finally {
      setSyncing(false);
    }
  }

  function toggleTheme() {
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    const current = theme || (prefersDark ? "dark" : "light");
    setTheme(current === "dark" ? "light" : "dark");
  }

  const inserted = syncReport ? Object.values(syncReport.inserted).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1 className="brand">FinanzIA</h1>
          <p className="tagline">Asistente inteligente de finanzas personales · prototipo con datos ficticios</p>
        </div>
        <div className="topbar-actions">
          <HealthBadges health={health} />
          <button className="btn ghost" onClick={toggleTheme} aria-label="Cambiar tema">
            Tema
          </button>
          <button className="btn primary" onClick={runSync} disabled={syncing}>
            {syncing ? "Sincronizando…" : "Sincronizar fuentes"}
          </button>
        </div>
      </header>

      {syncReport && (
        <div className={`notice ${syncReport.status === "ok" ? "" : "warn"}`} role="status">
          <strong>Sincronización {syncReport.status === "ok" ? "completada" : "parcial"}:</strong>{" "}
          {inserted} movimientos nuevos · {syncReport.duplicates_exact} ya existentes ·{" "}
          {syncReport.duplicates_cross} duplicados entre fuentes · {syncReport.skipped} eventos omitidos ·{" "}
          {syncReport.rejected} rechazados.
          {syncReport.errors.length > 0 && <div className="small">{syncReport.errors.join(" · ")}</div>}
          {syncReport.warnings.length > 0 && <div className="small">{syncReport.warnings.join(" · ")}</div>}
        </div>
      )}
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab !== "assistant" && (
        <div className="filter-row" aria-label="Periodo">
          <span className="filter-label">Periodo</span>
          {PRESETS.map((p) => (
            <button
              key={p.id}
              className={`chip ${preset === p.id ? "active" : ""}`}
              onClick={() => choosePreset(p.id)}
            >
              {preset === p.id ? "✓ " : ""}
              {p.label}
            </button>
          ))}
        </div>
      )}

      <main>
        {tab === "panel" && <Dashboard range={range} version={version} />}
        {tab === "transactions" && <TransactionsTable range={range} version={version} />}
        {tab === "assistant" && <Assistant aiConfigured={health?.ai_configured} />}
      </main>

      <footer className="footer">
        Las APIs bancaria y de billetera son simuladas: no existen integraciones reales con entidades financieras y
        no se administra dinero real.
      </footer>
    </div>
  );
}

function HealthBadges({ health }) {
  if (!health) return <span className="small">Comprobando servicios…</span>;
  const items = [
    ["Base de datos", health.database === "ok"],
    ["Banco", health.sources?.bank === "ok"],
    ["Billetera", health.sources?.wallet === "ok"],
    ["Notificaciones", health.sources?.notification === "ok"],
    ["IA", Boolean(health.ai_configured)],
  ];
  return (
    <ul className="badges" aria-label="Estado de servicios">
      {items.map(([label, ok]) => (
        <li key={label} className={`badge ${ok ? "ok" : "off"}`} title={ok ? "Disponible" : "No disponible"}>
          <span aria-hidden="true">{ok ? "●" : "○"}</span> {label}
        </li>
      ))}
    </ul>
  );
}
