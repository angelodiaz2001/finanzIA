import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BudgetsView from "../components/BudgetsView.jsx";
import { api } from "../api.js";

vi.mock("../api.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      ...actual.api,
      budgets: vi.fn(),
      saveBudget: vi.fn(),
      deleteBudget: vi.fn(),
      categories: vi.fn(),
    },
  };
});

describe("BudgetsView (Spec 002)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.categories.mockResolvedValue({
      expense: ["Alimentación", "Salud", "Transporte", "Transferencias internas", "Transferencias enviadas"],
      income: ["Salario"],
    });
  });

  it("muestra totales, estados en español y permite guardar y eliminar presupuestos", async () => {
    const user = userEvent.setup();
    api.budgets.mockResolvedValue({
      month: "2026-10",
      currency: "PEN",
      total_budgeted: 800,
      total_spent: 615,
      items: [
        {
          id: 1,
          month: "2026-10",
          category: "Salud",
          limit_amount: 100,
          spent: 150,
          remaining: -50,
          usage_ratio: 1.5,
          status: "exceeded",
          currency: "PEN",
        },
        {
          id: 2,
          month: "2026-10",
          category: "Alimentación",
          limit_amount: 500,
          spent: 425,
          remaining: 75,
          usage_ratio: 0.85,
          status: "warning",
          currency: "PEN",
        },
        {
          id: 3,
          month: "2026-10",
          category: "Transporte",
          limit_amount: 200,
          spent: 40,
          remaining: 160,
          usage_ratio: 0.2,
          status: "ok",
          currency: "PEN",
        },
      ],
    });
    api.saveBudget.mockResolvedValue({ id: 4 });
    api.deleteBudget.mockResolvedValue(null);

    render(<BudgetsView version={0} initialMonth="2026-10" />);

    expect(await screen.findByText("Excedido")).toBeInTheDocument();
    expect(screen.getByText("En alerta")).toBeInTheDocument();
    expect(screen.getByText("En orden")).toBeInTheDocument();

    // Las categorías de transferencia no aparecen en el selector presupuestable
    const catSelect = screen.getByLabelText("Categoría de gasto");
    expect(catSelect).not.toHaveTextContent("Transferencias internas");
    expect(catSelect).not.toHaveTextContent("Transferencias enviadas");

    await user.selectOptions(catSelect, "Transporte");
    const limitInput = screen.getByLabelText("Tope mensual");
    await user.clear(limitInput);
    await user.type(limitInput, "250");
    await user.click(screen.getByRole("button", { name: "Guardar presupuesto" }));

    await waitFor(() =>
      expect(api.saveBudget).toHaveBeenCalledWith({
        month: "2026-10",
        category: "Transporte",
        limit_amount: 250,
      })
    );

    await user.click(screen.getByRole("button", { name: "Eliminar presupuesto de Salud" }));
    await waitFor(() => expect(api.deleteBudget).toHaveBeenCalledWith(1));
  });

  it("muestra estado vacío en español y alerta accesible cuando falla la red", async () => {
    api.budgets.mockResolvedValueOnce({
      month: "2026-11",
      currency: "PEN",
      total_budgeted: 0,
      total_spent: 0,
      items: [],
    });

    const { unmount } = render(<BudgetsView version={0} initialMonth="2026-11" />);
    expect(await screen.findByText("Aún no definiste presupuestos para este mes.")).toBeInTheDocument();
    unmount();

    api.budgets.mockRejectedValueOnce(new Error("Fallo de conexión"));
    render(<BudgetsView version={0} initialMonth="2026-11" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Fallo de conexión/);
  });
});
