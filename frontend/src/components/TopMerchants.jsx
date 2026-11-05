import { formatMoney } from "../api.js";

// Comercios con mayor gasto del periodo. Los totales y la participación vienen
// calculados del backend (analytics.top_merchants); aquí solo se muestran.
export default function TopMerchants({ data, currency }) {
  return (
    <section className="card">
      <h2>Comercios donde más gastas</h2>
      <p className="small">
        Los 5 comercios con mayor gasto del periodo; la barra indica su participación en el gasto total con comercio.
      </p>
      {data?.length ? (
        <ol className="merchant-list">
          {data.map((m, i) => {
            const pct = m.share * 100;
            return (
              <li className="merchant-row" key={m.merchant}>
                <span className="merchant-rank">{i + 1}</span>
                <span>
                  {m.merchant}{" "}
                  <span className="small">
                    · {m.count} {m.count === 1 ? "compra" : "compras"}
                  </span>
                </span>
                <span className="num">{formatMoney(m.total, currency)}</span>
                <div
                  className="merchant-bar"
                  role="img"
                  aria-label={`${pct.toFixed(1)} % del gasto con comercio`}
                  title={`${pct.toFixed(1)} % del gasto con comercio`}
                >
                  <div className="merchant-bar-fill" style={{ width: `${pct}%` }} />
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="small">Sin gastos con comercio en el periodo.</p>
      )}
    </section>
  );
}
