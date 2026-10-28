import { useEffect, useState } from "react";
import { api, formatMoney, SOURCE_LABELS } from "../api.js";
import CategoryBars from "./CategoryBars.jsx";
import MonthlyChart from "./MonthlyChart.jsx";

export default function Dashboard({ range, version }) {
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.summary(range), api.byCategory({ ...range, type: "expense" }), api.monthly(6), api.accounts()])
      .then(([s, c, m, a]) => {
        if (cancelled) return;
        setSummary(s);
        setCategories(c);
        setMonthly(m);
        setAccounts(a);
        setError("");
      })
      .catch((e) => !cancelled && setError(`No se pudieron cargar los indicadores: ${e.message}`))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [range, version]);

  if (error) return <div className="notice error">{error}</div>;
  const currency = summary?.currency ?? "PEN";
  const empty = summary && summary.count === 0;

  return (
    <div className={`stack ${loading ? "is-loading" : ""}`}>
      {empty && (
        <div className="notice">
          Aún no hay movimientos en este periodo. Pulsa <strong>Sincronizar fuentes</strong> para consumir las tres
          APIs simuladas.
        </div>
      )}

      <section className="tiles" aria-label="Resumen">
        <StatTile label="Ingresos" value={formatMoney(summary?.income, currency)} caption="sin transferencias internas" />
        <StatTile label="Gastos" value={formatMoney(summary?.expenses, currency)} caption="sin transferencias internas" />
        <StatTile
          label="Balance neto"
          value={formatMoney(summary?.net, currency)}
          caption={
            summary ? (
              <span className={summary.net >= 0 ? "delta-up" : "delta-down"}>
                <span aria-hidden="true">{summary.net >= 0 ? "▲" : "▼"}</span>{" "}
                {summary.net >= 0 ? "ingresos superan gastos" : "gastos superan ingresos"}
              </span>
            ) : (
              ""
            )
          }
        />
        <StatTile
          label="Movimientos"
          value={summary?.count ?? 0}
          caption={`${summary?.duplicates_detected ?? 0} duplicados detectados · ${formatMoney(
            summary?.internal_transfers,
            currency
          )} en transferencias internas`}
        />
      </section>

      <div className="grid-2">
        <section className="card">
          <h2>Distribución de gastos por categoría</h2>
          <p className="small">Participación de cada categoría en el total de gastos del periodo.</p>
          <CategoryBars data={categories} currency={currency} />
        </section>
        <section className="card">
          <h2>Ingresos y gastos por mes</h2>
          <p className="small">Últimos 6 meses, excluyendo transferencias internas y duplicados.</p>
          <MonthlyChart data={monthly} currency={currency} />
        </section>
      </div>

      <div className="grid-2">
        <section className="card">
          <h2>Cuentas y saldos</h2>
          {accounts.length === 0 ? (
            <p className="small">Sin cuentas sincronizadas todavía.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Cuenta</th>
                  <th>Fuente</th>
                  <th>Tipo</th>
                  <th className="num">Saldo</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.id}>
                    <td>{a.name}</td>
                    <td>
                      <span className={`pill src-${a.source}`}>{SOURCE_LABELS[a.source] ?? a.source}</span>
                    </td>
                    <td>{a.account_type}</td>
                    <td className="num">{formatMoney(a.balance, a.currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
        <section className="card">
          <h2>Movimientos por fuente</h2>
          {summary?.by_source?.length ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Fuente</th>
                  <th className="num">Movimientos</th>
                  <th className="num">Ingresos</th>
                  <th className="num">Gastos</th>
                </tr>
              </thead>
              <tbody>
                {summary.by_source.map((s) => (
                  <tr key={s.source}>
                    <td>
                      <span className={`pill src-${s.source}`}>{SOURCE_LABELS[s.source] ?? s.source}</span>
                    </td>
                    <td className="num">{s.count}</td>
                    <td className="num">{formatMoney(s.income, currency)}</td>
                    <td className="num">{formatMoney(s.expenses, currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="small">Sin datos en el periodo.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function StatTile({ label, value, caption }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value">{value}</div>
      {caption && <div className="tile-caption">{caption}</div>}
    </div>
  );
}
