import { useEffect, useState } from "react";
import { api, formatDate, formatMoney, SOURCE_LABELS } from "../api.js";

const PAGE_SIZE = 25;

export default function TransactionsTable({ range, version }) {
  const [filters, setFilters] = useState({ source: "", type: "", category: "", q: "", include_duplicates: false });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [categories, setCategories] = useState({ expense: [], income: [] });
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [hint, setHint] = useState("");

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setPage(1);
  }, [range, filters]);

  useEffect(() => {
    let cancelled = false;
    api
      .transactions({ ...range, ...filters, page, page_size: PAGE_SIZE })
      .then((d) => !cancelled && (setData(d), setError("")))
      .catch((e) => !cancelled && setError(`No se pudieron cargar las transacciones: ${e.message}`));
    return () => {
      cancelled = true;
    };
  }, [range, filters, page, version]);

  const allCategories = [...new Set([...categories.expense, ...categories.income])];
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  function update(field, value) {
    setFilters((f) => ({ ...f, [field]: value }));
  }

  async function changeCategory(tx, category) {
    setBusyId(tx.id);
    try {
      const updated = await api.updateCategory(tx.id, category);
      setData((d) => ({ ...d, items: d.items.map((t) => (t.id === tx.id ? updated : t)) }));
      setHint(`Categoría de "${tx.description}" actualizada manualmente a ${category}.`);
    } catch (e) {
      setError(`No se pudo actualizar la categoría: ${e.message}`);
    } finally {
      setBusyId(null);
    }
  }

  async function suggestCategory(tx) {
    setBusyId(tx.id);
    try {
      const result = await api.categorize({ transaction_id: tx.id, apply: true });
      setData((d) => ({
        ...d,
        items: d.items.map((t) => (t.id === tx.id ? { ...t, category: result.category, category_source: result.source } : t)),
      }));
      setHint(
        `${result.source === "ai" ? "IA" : "Reglas"}: ${result.category} (confianza ${(result.confidence * 100).toFixed(0)}%). ${result.reason}`
      );
    } catch (e) {
      setError(`No se pudo sugerir la categoría: ${e.message}`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="stack">
      <div className="card">
        <div className="filters">
          <label>
            Fuente
            <select value={filters.source} onChange={(e) => update("source", e.target.value)}>
              <option value="">Todas</option>
              <option value="bank">Banco</option>
              <option value="wallet">Billetera</option>
              <option value="notification">Notificación</option>
            </select>
          </label>
          <label>
            Tipo
            <select value={filters.type} onChange={(e) => update("type", e.target.value)}>
              <option value="">Todos</option>
              <option value="income">Ingreso</option>
              <option value="expense">Gasto</option>
            </select>
          </label>
          <label>
            Categoría
            <select value={filters.category} onChange={(e) => update("category", e.target.value)}>
              <option value="">Todas</option>
              {allCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label className="grow">
            Buscar
            <input
              type="search"
              placeholder="Descripción o comercio"
              value={filters.q}
              onChange={(e) => update("q", e.target.value)}
            />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={filters.include_duplicates}
              onChange={(e) => update("include_duplicates", e.target.checked)}
            />
            Mostrar duplicados
          </label>
        </div>
      </div>

      {error && <div className="notice error">{error}</div>}
      {hint && (
        <div className="notice" role="status">
          {hint}
        </div>
      )}

      <div className="card">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Fuente</th>
                <th>Categoría</th>
                <th className="num">Monto</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="small">
                    No hay transacciones con estos filtros.
                  </td>
                </tr>
              )}
              {data.items.map((tx) => (
                <tr key={tx.id} className={tx.is_duplicate ? "row-duplicate" : ""}>
                  <td className="nowrap">{formatDate(tx.occurred_at)}</td>
                  <td>
                    <div>{tx.description}</div>
                    {tx.merchant && tx.merchant !== tx.description && <div className="small">{tx.merchant}</div>}
                    {tx.is_duplicate && (
                      <div className="small">
                        <span className="pill dup">Duplicado</span> de la transacción #{tx.duplicate_of_id}
                      </div>
                    )}
                  </td>
                  <td>
                    <span className={`pill src-${tx.source}`}>{SOURCE_LABELS[tx.source] ?? tx.source}</span>
                  </td>
                  <td>
                    <select
                      value={tx.category}
                      disabled={busyId === tx.id}
                      onChange={(e) => changeCategory(tx, e.target.value)}
                      aria-label={`Categoría de ${tx.description}`}
                    >
                      {[...new Set([tx.category, ...(tx.type === "income" ? categories.income : categories.expense)])].map(
                        (c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        )
                      )}
                    </select>
                    <div className="small">origen: {tx.category_source}</div>
                  </td>
                  <td className={`num ${tx.type === "income" ? "amount-in" : "amount-out"}`}>
                    {tx.type === "income" ? "+" : "−"} {formatMoney(tx.amount, tx.currency)}
                  </td>
                  <td>
                    <button className="btn ghost small" disabled={busyId === tx.id} onClick={() => suggestCategory(tx)}>
                      Sugerir categoría
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pager">
          <span className="small">
            {data.total} transacciones · página {page} de {pages}
          </span>
          <div>
            <button className="btn ghost small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Anterior
            </button>
            <button className="btn ghost small" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
