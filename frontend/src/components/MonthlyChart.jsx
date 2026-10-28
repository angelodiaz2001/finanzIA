import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMoney } from "../api.js";
import useChartTheme from "./useChartTheme.js";

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

function monthLabel(key) {
  const [y, m] = key.split("-");
  return `${MONTHS[Number(m) - 1]} ${y.slice(2)}`;
}

export default function MonthlyChart({ data, currency }) {
  const theme = useChartTheme();
  const [showTable, setShowTable] = useState(false);
  if (!data || data.length === 0) return <p className="small">Sin datos mensuales.</p>;

  const rows = data.map((d) => ({ ...d, label: monthLabel(d.month) }));

  return (
    <div>
      <div className="chart-toolbar">
        <button className="btn ghost small" onClick={() => setShowTable((v) => !v)}>
          {showTable ? "Ver gráfico" : "Ver tabla"}
        </button>
      </div>
      {showTable ? (
        <table className="table">
          <thead>
            <tr>
              <th>Mes</th>
              <th className="num">Ingresos</th>
              <th className="num">Gastos</th>
              <th className="num">Neto</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.month}>
                <td>{r.label}</td>
                <td className="num">{formatMoney(r.income, currency)}</td>
                <td className="num">{formatMoney(r.expenses, currency)}</td>
                <td className="num">{formatMoney(r.net, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={{ width: "100%", height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 4, left: 8 }} barGap={2} barCategoryGap={16}>
              <CartesianGrid vertical={false} stroke={theme["--grid"]} />
              <XAxis dataKey="label" tick={{ fill: theme["--muted"], fontSize: 12 }} axisLine={{ stroke: theme["--axis"] }} tickLine={false} />
              <YAxis
                tick={{ fill: theme["--muted"], fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={64}
                tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v)}
              />
              <Tooltip
                cursor={{ fill: theme["--grid"], opacity: 0.5 }}
                content={({ active, payload, label }) =>
                  active && payload?.length ? (
                    <div className="tooltip">
                      <div className="tooltip-title">{label}</div>
                      {payload.map((p) => (
                        <div key={p.dataKey}>
                          <span className="swatch" style={{ background: p.fill }} aria-hidden="true" /> {p.name}:{" "}
                          {formatMoney(p.value, currency)}
                        </div>
                      ))}
                      <div className="small">Neto: {formatMoney(payload[0].payload.net, currency)}</div>
                    </div>
                  ) : null
                }
              />
              <Legend wrapperStyle={{ fontSize: 12, color: theme["--text"] }} iconType="circle" iconSize={8} />
              <Bar dataKey="income" name="Ingresos" fill={theme["--series-1"]} barSize={18} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="expenses" name="Gastos" fill={theme["--series-2"]} barSize={18} radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
