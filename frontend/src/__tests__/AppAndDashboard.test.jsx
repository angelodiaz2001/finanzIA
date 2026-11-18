import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App.jsx";
import Dashboard from "../components/Dashboard.jsx";
import { api } from "../api.js";

vi.mock("../api.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      health: vi.fn(),
      sync: vi.fn(),
      summary: vi.fn(),
      byCategory: vi.fn(),
      monthly: vi.fn(),
      accounts: vi.fn(),
      topMerchants: vi.fn(),
      anomalies: vi.fn(),
      recurring: vi.fn(),
      transactions: vi.fn(),
      categories: vi.fn(),
      updateCategory: vi.fn(),
      categorize: vi.fn(),
      chat: vi.fn(),
      resetChat: vi.fn(),
    },
  };
});

const SAMPLE_SUMMARY = {
  currency: "PEN",
  income: 3200,
  expenses: 1100,
  net: 2100,
  internal_transfers: 200,
  count: 8,
  duplicates_detected: 1,
  by_source: [{ source: "bank", count: 8, income: 3200, expenses: 1100 }],
};

describe("App y Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.health.mockResolvedValue({
      status: "ok",
      database: "ok",
      sources: { bank: "ok", wallet: "ok", notification: "ok" },
      ai_configured: true,
    });
    api.summary.mockResolvedValue(SAMPLE_SUMMARY);
    api.byCategory.mockResolvedValue([
      { category: "Alimentación", type: "expense", total: 600, count: 4, share: 0.5455 },
      { category: "Salud", type: "expense", total: 500, count: 4, share: 0.4545 },
    ]);
    api.monthly.mockResolvedValue([{ month: "2026-10", income: 3200, expenses: 1100, net: 2100 }]);
    api.accounts.mockResolvedValue([
      { id: 1, name: "Cuenta Sueldo", source: "bank", account_type: "AHORROS", currency: "PEN", balance: 2500 },
    ]);
    api.topMerchants.mockResolvedValue([
      { merchant: "Supermercado La Canasta", total: 450, count: 3, share: 0.6 },
    ]);
    api.anomalies.mockResolvedValue([]);
    api.recurring.mockResolvedValue([
      {
        merchant: "Streaming Sim",
        category: "Entretenimiento",
        months_active: 3,
        occurrences: 3,
        average_amount: 39.9,
        total_amount: 119.7,
        last_charged_at: "2026-10-15",
      },
    ]);
  });

  it("renderiza indicadores del panel, comercios principales, cambio de tabla y tema", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByText("Supermercado La Canasta")).toBeInTheDocument();
    expect(screen.getByText("Cuenta Sueldo")).toBeInTheDocument();

    const tableButtons = screen.getAllByRole("button", { name: "Ver tabla" });
    await user.click(tableButtons[0]);
    expect(screen.getByText("Alimentación")).toBeInTheDocument();
    await user.click(tableButtons[1]);
    expect(screen.getByText(/oct 26/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cambiar tema" }));
    expect(document.documentElement.getAttribute("data-theme")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: /Últimos 30 días/i }));
    await waitFor(() => expect(api.summary).toHaveBeenCalledTimes(2));
  });

  it("ejecuta sincronización y muestra alerta accesible si el backend falla en Dashboard", async () => {
    const user = userEvent.setup();
    api.sync.mockResolvedValue({
      status: "ok",
      inserted: { bank: 3, wallet: 2, notification: 1 },
      duplicates_exact: 0,
      duplicates_cross: 1,
      skipped: 0,
      rejected: 0,
      errors: [],
      warnings: [],
    });

    const { unmount } = render(<App />);
    await screen.findByText("Supermercado La Canasta");
    await user.click(screen.getByRole("button", { name: "Sincronizar fuentes" }));
    expect(await screen.findByText(/Sincronización completada/i)).toBeInTheDocument();
    unmount();

    api.summary.mockRejectedValueOnce(new Error("Servidor no disponible"));
    render(<Dashboard range={{}} version={0} />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/Servidor no disponible/);
  });
});
