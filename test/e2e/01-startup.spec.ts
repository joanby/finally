import { test, expect } from "@playwright/test";
import { DEFAULT_TICKERS, watchlistRow, expectLive } from "./helpers";

test.describe("Arranque limpio (PLAN §12)", () => {
  test("watchlist por defecto, saldo $10k, conexión y precios en vivo", async ({ page }) => {
    await page.goto("/");

    // 10 tickers por defecto visibles.
    for (const t of DEFAULT_TICKERS) {
      await expect(watchlistRow(page, t)).toBeVisible();
    }

    // Saldo de efectivo inicial.
    await expect(page.getByText("$10,000.00").first()).toBeVisible();

    // Indicador de conexión en LIVE.
    await expectLive(page);

    // El SSE actualiza precios: el precio de un ticker cambia con el tiempo.
    const priceCell = watchlistRow(page, "AAPL").getByRole("cell").nth(2);
    const first = await priceCell.textContent();
    await expect
      .poll(async () => priceCell.textContent(), { timeout: 15_000, intervals: [500] })
      .not.toBe(first);
  });
});
