import { formatDate, formatMoney } from "../api.js";

// Suscripciones/cobros recurrentes y alertas de gastos atípicos calculados por el backend.
export default function RecurringAndAlerts({ recurring = [], anomalies = [], currency = "PEN" }) {
  return (
    <section className="card">
      <h2>Cobros recurrentes y alertas del periodo</h2>
      <p className="small">
        Comercios con cargos en dos o más meses distintos y gastos individuales que duplican o más el promedio de su
        categoría.
      </p>

      <div style={{ marginTop: 10 }}>
        <strong className="small">Cobros periódicos detectados</strong>
        {recurring?.length ? (
          <ul className="budget-list" style={{ marginTop: 6 }}>
            {recurring.map((r) => (
              <li key={r.merchant} className="budget-row">
                <div className="budget-row-head" style={{ marginBottom: 2 }}>
                  <span>
                    <strong>{r.merchant}</strong> <span className="pill">{r.category}</span>
                  </span>
                  <span className="num">{formatMoney(r.average_amount, currency)} / cargo</span>
                </div>
                <div className="small">
                  {r.months_active} meses activos ({r.occurrences} cargos) · último: {formatDate(r.last_charged_at)}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="small" style={{ marginTop: 4 }}>
            Sin cobros recurrentes detectados.
          </p>
        )}
      </div>

      <div style={{ marginTop: 12 }}>
        <strong className="small">Gastos atípicos en el periodo</strong>
        {anomalies?.length ? (
          <ul className="budget-list" style={{ marginTop: 6 }}>
            {anomalies.map((a) => (
              <li key={a.id} className="budget-row">
                <div className="budget-row-head" style={{ marginBottom: 2 }}>
                  <span>
                    <strong>{a.merchant || a.description}</strong>{" "}
                    <span className="pill status-warning">{a.ratio.toFixed(1)}x prom.</span>
                  </span>
                  <span className="num">{formatMoney(a.amount, a.currency || currency)}</span>
                </div>
                <div className="small">
                  {a.category} (promedio habitual {formatMoney(a.category_average, a.currency || currency)}) ·{" "}
                  {formatDate(a.occurred_at)}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="small" style={{ marginTop: 4 }}>
            Sin gastos atípicos en el periodo.
          </p>
        )}
      </div>
    </section>
  );
}
