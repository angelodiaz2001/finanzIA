// Cliente HTTP del backend principal. En desarrollo, Vite redirige /api al puerto 8000.
const BASE = "/api";

function qs(params = {}) {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return entries.length ? "?" + new URLSearchParams(entries).toString() : "";
}

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health: () => request("/health"),
  sync: () => request("/sync", { method: "POST" }),
  summary: (params) => request("/analytics/summary" + qs(params)),
  byCategory: (params) => request("/analytics/by-category" + qs(params)),
  monthly: (months) => request("/analytics/monthly" + qs({ months })),
  transactions: (params) => request("/transactions" + qs(params)),
  updateCategory: (id, category) =>
    request(`/transactions/${id}/category`, { method: "PATCH", body: JSON.stringify({ category }) }),
  categories: () => request("/categories"),
  accounts: () => request("/accounts"),
  chat: (message, conversationId) =>
    request("/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
    }),
  resetChat: (conversationId) => request(`/assistant/chat/${conversationId}`, { method: "DELETE" }),
  categorize: (payload) => request("/assistant/categorize", { method: "POST", body: JSON.stringify(payload) }),
};

export function formatMoney(value, currency = "PEN") {
  try {
    return new Intl.NumberFormat("es-PE", { style: "currency", currency, maximumFractionDigits: 2 }).format(value ?? 0);
  } catch {
    return `${currency} ${Number(value ?? 0).toFixed(2)}`;
  }
}

export function formatDate(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
}

export const SOURCE_LABELS = { bank: "Banco", wallet: "Billetera", notification: "Notificación" };
