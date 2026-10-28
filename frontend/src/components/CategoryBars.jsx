import { useState } from "react";
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMoney } from "../api.js";
import useChartTheme from "./useChartTheme.js";

const MAX_BARS = 8;

export default function CategoryBars({ data, currency }) {
  const theme = useChartTheme();
  const [showTable, setShowTable] = useState(false);

  if (!data || data.length === 0) return <p className="small">Sin gastos en el periodo.</p>;

  // Más de 8 categorías se agrupan en "Otras" para mantener el gráfico legible.
  let rows = data;
  if (data.length > MAX_BARS) {
    const head = data.slice(0, MAX_BARS - 1);
    const tail = data.slice(MAX_BARS - 1);
    rows = [
      ...head,
      {
        category: "Otras",
        total: tail.reduce((a, r) => a + r.total, 0),
        count: tail.reduce((a, r) => a + r.count, 0),
        share: tail.reduce((a, r) => a + r.share, 0),
      },
    ];
  }
  const height = 36 * rows.length + 40;

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
              <th>Categoría</th>
              <th className="num">Movimientos</th>
              <th className="num">Total</th>
              <th className="num">% del gasto</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.category}>
                <td>{r.category}</td>
                <td className="num">{r.count}</td>
                <td className="num">{formatMoney(r.total, currency)}</td>
                <td className="num">{(r.share * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={{ width: "100%", height }}>
          <ResponsiveContainer>
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 96, bottom: 4, left: 8 }} barCategoryGap={8}>
              <CartesianGrid horizontal={false} stroke={theme["--grid"]} />
              <XAxis
                type="number"
                tick={{ fill: theme["--muted"], fontSize: 12 }}
                axisLine={{ stroke: theme["--axis"] }}
                tickLine={false}
                tickFormatter={(v) => formatMoney(v, currency).replace(/\.00$/, "")}
              />
              <YAxis
                type="category"
                dataKey="category"
                width={150}
                tick={{ fill: theme["--text"], fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: theme["--grid"], opacity: 0.5 }}
                content={({ active, payload }) =>
                  active && payload?.length ? (
                    <div className="tooltip">
                      <div className="tooltip-title">{payload[0].payload.category}</div>
                      <div>{formatMoney(payload[0].value, currency)}</div>
                      <div className="small">
                        {payload[0].payload.count} movimientos · {(payload[0].payload.share * 100).toFixed(1)}% del gasto
                      </div>
                    </div>
                  ) : null
                }
              />
              <Bar dataKey="total" fill={theme["--series-1"]} barSize={16} radius={[0, 4, 4, 0]} isAnimationActive={false}>
                <LabelList
                  dataKey="share"
                  position="right"
                  formatter={(v) => `${(v * 100).toFixed(0)}%`}
                  style={{ fill: theme["--muted"], fontSize: 12 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
