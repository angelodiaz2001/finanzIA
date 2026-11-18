import { useCallback, useEffect, useState } from "react";
import { api, formatMoney } from "../api.js";

const EXCLUDED_CATEGORIES = new Set(["Transferencias internas", "Transferencias enviadas"]);

const STATUS_LABELS = {
  ok: "En orden",
  warning: "En alerta",
  exceeded: "Excedido",
};

function currentYearMonth() {
  return new Date().toISOString().slice(0, 7);
}

export default function BudgetsView({ version, initialMonth }) {
  const [month, setMonth] = useState(() => initialMonth || currentYearMonth());
  const [summary, setSummary] = useState(null);
  const [expenseCategories, setExpenseCategories] = useState([]);
  const [category, setCategory] = useState("");
  const [limitAmount, setLimitAmount] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const loadData = useCallback(() => {
    let cancelled = false;
    Promise.all([api.budgets(month), api.categories()])
      .then(([budgetRes, cats]) => {
        if (cancelled) return;
        const allowed = (cats?.expense || []).filter((c) => !EXCLUDED_CATEGORIES.has(c));
        setSummary(budgetRes);
        setExpenseCategories(allowed);
        setCategory((prev) => (prev && allowed.includes(prev) ? prev : allowed[0] || ""));
        setError("");
      })
      .catch((e) => {
        if (!cancelled) setError(`No se pudieron cargar los presupuestos: ${e.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

  useEffect(() => {
    return loadData();
  }, [loadData, version]);

  async function handleSubmit(e) {
    e.preventDefault();
    const numeric = Number(limitAmount);
    if (!category || !Number.isFinite(numeric) || numeric <= 0) {
      setError("Ingresa un tope mensual mayor que cero.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api.saveBudget({ month, category, limit_amount: numeric });
      setLimitAmount("");
      loadData();
    } catch (err) {
      setError(`No se pudo guardar el presupuesto: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(item) {
    setError("");
    try {
      await api.deleteBudget(item.id);
      loadData();
    } catch (err) {
      setError(`No se pudo eliminar el presupuesto: ${err.message}`);
    }
  }

  const currency = summary?.currency || "PEN";
  const totalBudgeted = summary?.total_budgeted ?? 0;
  const totalSpent = summary?.total_spent ?? 0;
  const totalRemaining = totalBudgeted - totalSpent;

  return (
    <div className="stack">
      <section className="card">
        <h2>Presupuestos mensuales por categoría</h2>
        <p className="small">
          Define cuánto planeas gastar como máximo en cada categoría durante el mes seleccionado (sin contar
          duplicados ni transferencias).
        </p>

        <form className="filters" onSubmit={handleSubmit}>
          <label>
            Mes
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
          </label>
          <label>
            Categoría de gasto
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {expenseCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Tope mensual
            <input
              type="number"
              min="1"
              step="0.01"
              placeholder="Ej. 500"
              value={limitAmount}
              onChange={(e) => setLimitAmount(e.target.value)}
            />
          </label>
          <button className="btn primary" type="submit" disabled={saving || !category}>
            {saving ? "Guardando…" : "Guardar presupuesto"}
          </button>
        </form>
      </section>

      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}

      <section className="tiles" aria-label="Resumen de presupuestos">
        <div className="tile">
          <div className="tile-label">Total presupuestado</div>
          <div className="tile-value">{formatMoney(totalBudgeted, currency)}</div>
          <div className="tile-caption">mes {month}</div>
        </div>
        <div className="tile">
          <div className="tile-label">Gastado en categorías con tope</div>
          <div className="tile-value">{formatMoney(totalSpent, currency)}</div>
          <div className="tile-caption">calculado por el backend</div>
        </div>
        <div className="tile">
          <div className="tile-label">Disponible global</div>
          <div className="tile-value">{formatMoney(totalRemaining, currency)}</div>
          <div className="tile-caption">
            <span className={totalRemaining >= 0 ? "delta-up" : "delta-down"}>
              {totalRemaining >= 0 ? "dentro del total mensual" : "supera el total presupuestado"}
            </span>
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Avance por categoría</h2>
        {!summary?.items?.length ? (
          <p className="small">Aún no definiste presupuestos para este mes.</p>
        ) : (
          <ul className="budget-list">
            {summary.items.map((it) => {
              const pct = Math.min(100, Math.round(it.usage_ratio * 100));
              const rawPct = (it.usage_ratio * 100).toFixed(1);
              return (
                <li key={it.id} className="budget-row">
                  <div className="budget-row-head">
                    <div>
                      <strong>{it.category}</strong>{" "}
                      <span className={`pill status-${it.status}`}>{STATUS_LABELS[it.status] || it.status}</span>
                    </div>
                    <div className="budget-row-actions">
                      <span className="num">
                        {formatMoney(it.spent, it.currency)} / {formatMoney(it.limit_amount, it.currency)} ({rawPct}%)
                      </span>
                      <button
                        type="button"
                        className="btn ghost small"
                        aria-label={`Eliminar presupuesto de ${it.category}`}
                        onClick={() => handleDelete(it)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                  <div
                    className="budget-bar"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={pct}
                    aria-label={`Ejecución de ${it.category}`}
                  >
                    <div className={`budget-bar-fill ${it.status}`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className="small">
                    {it.remaining >= 0
                      ? `Disponible: ${formatMoney(it.remaining, it.currency)}`
                      : `Excedido por: ${formatMoney(Math.abs(it.remaining), it.currency)}`}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
