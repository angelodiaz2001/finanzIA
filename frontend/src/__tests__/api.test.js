import { api, formatDate, formatMoney, SOURCE_LABELS } from "../api.js";

describe("Cliente HTTP api.js y formateadores", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("formatea montos y fechas en español y expone las etiquetas de origen", () => {
    expect(formatMoney(150.5, "PEN")).toMatch(/150/);
    expect(formatMoney(50, "INVALID_CODE")).toBe("INVALID_CODE 50.00");
    expect(formatDate("2026-10-24T12:30:00")).toMatch(/2026/);
    expect(formatDate("no-es-fecha")).toBe("no-es-fecha");
    expect(SOURCE_LABELS).toEqual({ bank: "Banco", wallet: "Billetera", notification: "Notificación" });
  });

  it("construye query strings omitiendo vacíos y devuelve JSON en respuestas exitosas", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ merchant: "Cine Sim", total: 30, count: 1, share: 1 }],
    });

    const res = await api.topMerchants({ date_from: "2026-10-01", date_to: "", limit: 5 });
    expect(res).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/analytics/top-merchants?date_from=2026-10-01&limit=5",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } })
    );
  });

  it("maneja respuestas 204 y propaga detail en español ante errores HTTP", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({ ok: true, status: 204, json: async () => null })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: "Bad Request",
        json: async () => ({ detail: "date_from no puede ser posterior a date_to" }),
      });

    expect(await api.resetChat("abc")).toBeNull();
    await expect(api.summary({ date_from: "2026-10-31", date_to: "2026-10-01" })).rejects.toThrow(
      "date_from no puede ser posterior a date_to"
    );
  });
});
