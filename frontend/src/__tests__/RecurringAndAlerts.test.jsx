import { render, screen } from "@testing-library/react";
import RecurringAndAlerts from "../components/RecurringAndAlerts.jsx";

describe("RecurringAndAlerts (Spec 005)", () => {
  it("muestra cobros recurrentes y alertas de gastos atípicos formateados", () => {
    render(
      <RecurringAndAlerts
        currency="PEN"
        recurring={[
          {
            merchant: "Streaming Sim",
            category: "Entretenimiento",
            months_active: 3,
            occurrences: 3,
            average_amount: 39.9,
            total_amount: 119.7,
            last_charged_at: "2026-10-15",
          },
        ]}
        anomalies={[
          {
            id: 99,
            occurred_at: "2026-10-20T18:00:00",
            description: "Cena especial",
            merchant: "Restaurante Gourmet",
            category: "Alimentación",
            amount: 450,
            category_average: 150,
            ratio: 3.0,
          },
        ]}
      />
    );

    expect(screen.getByText("Streaming Sim")).toBeInTheDocument();
    expect(screen.getByText(/3 meses/i)).toBeInTheDocument();
    expect(screen.getByText("Restaurante Gourmet")).toBeInTheDocument();
    expect(screen.getByText(/3\.0x/i)).toBeInTheDocument();
  });

  it("muestra textos vacíos claros cuando no hay recurrentes ni alertas", () => {
    render(<RecurringAndAlerts currency="PEN" recurring={[]} anomalies={[]} />);
    expect(screen.getByText("Sin cobros recurrentes detectados.")).toBeInTheDocument();
    expect(screen.getByText("Sin gastos atípicos en el periodo.")).toBeInTheDocument();
  });
});
