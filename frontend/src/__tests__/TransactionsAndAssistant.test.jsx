import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TransactionsTable from "../components/TransactionsTable.jsx";
import Assistant from "../components/Assistant.jsx";
import { api } from "../api.js";

vi.mock("../api.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      transactions: vi.fn(),
      categories: vi.fn(),
      updateCategory: vi.fn(),
      categorize: vi.fn(),
      chat: vi.fn(),
      resetChat: vi.fn(),
    },
  };
});

describe("TransactionsTable y Assistant", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.categories.mockResolvedValue({
      expense: ["Alimentación", "Salud", "Transporte"],
      income: ["Salario"],
    });
    api.transactions.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [
        {
          id: 10,
          occurred_at: "2026-10-20T14:00:00",
          description: "Compra en botica",
          merchant: "Farmacia Sim",
          source: "bank",
          category: "Alimentación",
          category_source: "rules",
          type: "expense",
          amount: 45.5,
          currency: "PEN",
          is_duplicate: false,
        },
      ],
    });
  });

  it("lista transacciones, actualiza categoría manual y pide sugerencia de categoría", async () => {
    const user = userEvent.setup();
    api.updateCategory.mockResolvedValue({
      id: 10,
      occurred_at: "2026-10-20T14:00:00",
      description: "Compra en botica",
      merchant: "Farmacia Sim",
      source: "bank",
      category: "Salud",
      category_source: "manual",
      type: "expense",
      amount: 45.5,
      currency: "PEN",
      is_duplicate: false,
    });
    api.categorize.mockResolvedValue({
      category: "Salud",
      reason: "Palabra clave botica",
      confidence: 0.9,
      source: "rules",
    });

    render(<TransactionsTable range={{}} version={0} />);
    expect(await screen.findByText("Compra en botica")).toBeInTheDocument();

    const catSelect = screen.getByLabelText("Categoría de Compra en botica");
    await user.selectOptions(catSelect, "Salud");
    expect(await screen.findByRole("status")).toHaveTextContent(/actualizada manualmente a Salud/);

    await user.click(screen.getByRole("button", { name: "Sugerir categoría" }));
    await waitFor(() => expect(api.categorize).toHaveBeenCalledWith({ transaction_id: 10, apply: true }));
  });

  it("envía preguntas al asistente, muestra herramientas consultadas y reinicia conversación", async () => {
    const user = userEvent.setup();
    api.chat.mockResolvedValue({
      reply: "En octubre tus gastos sumaron S/ 1,100.00.",
      conversation_id: "conv-1",
      model: "claude-haiku-4-5",
      tools_used: [{ name: "get_summary", input: { from_date: "2026-10-01", to_date: "2026-10-31" } }],
      configured: true,
    });
    api.resetChat.mockResolvedValue(null);

    render(<Assistant aiConfigured={false} />);
    expect(screen.getByText(/El asistente de IA no está configurado/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText("Mensaje"), "¿Cuánto gasté en octubre?");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(/En octubre tus gastos sumaron/i)).toBeInTheDocument();
    expect(screen.getByText("get_summary")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Nueva conversación" }));
    expect(api.resetChat).toHaveBeenCalledWith("conv-1");
  });
});
