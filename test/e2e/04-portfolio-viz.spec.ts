import { test, expect } from "@playwright/test";

test.describe("Visualización de cartera (PLAN §12)", () => {
  test("el treemap se renderiza con una posición y el gráfico de P&L acumula puntos", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText("LIVE", { exact: true })).toBeVisible({ timeout: 15_000 });

    const allocation = page.locator("section", {
      has: page.getByText("Allocation", { exact: true }),
    });
    const pnl = page.locator("section", {
      has: page.getByText("Portfolio Value", { exact: true }),
    });

    // Sin posiciones, el treemap muestra el estado vacío.
    await expect(allocation.getByText("No open positions.")).toBeVisible();

    // Dos compras: cada trade registra un snapshot inmediato → el gráfico tendrá >1 punto.
    const buy = async (ticker: string, qty: string) => {
      await page.getByRole("textbox", { name: "Trade ticker" }).fill(ticker);
      await page.getByRole("textbox", { name: "Trade quantity" }).fill(qty);
      await page.getByRole("button", { name: "Buy", exact: true }).click();
    };
    await buy("NVDA", "3");
    await buy("AAPL", "2");

    // El treemap ahora muestra celdas de posición (botones por ticker), no el vacío.
    await expect(allocation.getByRole("button", { name: /NVDA/ })).toBeVisible({ timeout: 10_000 });
    await expect(allocation.getByText("No open positions.")).toHaveCount(0);

    // El gráfico de P&L deja de mostrar el placeholder y dibuja la línea (svg).
    await expect(pnl.getByText("Recording portfolio value")).toHaveCount(0, { timeout: 15_000 });
    await expect(pnl.locator("svg").first()).toBeVisible();
  });
});
