import { test, expect } from "@playwright/test";
import { watchlistRow, readCash } from "./helpers";

test.describe("Trading vía barra de operaciones (PLAN §12)", () => {
  test("comprar baja el efectivo y crea la posición; vender lo revierte", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("LIVE", { exact: true })).toBeVisible({ timeout: 15_000 });

    const cashBefore = await readCash(page);
    expect(cashBefore).toBeGreaterThan(0);

    // Comprar 2 MSFT.
    await page.getByRole("textbox", { name: "Trade ticker" }).fill("MSFT");
    await page.getByRole("textbox", { name: "Trade quantity" }).fill("2");
    await page.getByRole("button", { name: "Buy", exact: true }).click();

    // La posición aparece en la tabla de posiciones.
    const positions = page.locator("section", {
      has: page.getByText("Positions", { exact: true }),
    });
    await expect(positions.getByRole("cell", { name: "MSFT" })).toBeVisible({ timeout: 10_000 });

    // El efectivo baja respecto al inicial.
    await expect
      .poll(async () => readCash(page), { timeout: 10_000 })
      .toBeLessThan(cashBefore);
    const cashAfterBuy = await readCash(page);

    // Vender 2 MSFT: la posición desaparece y el efectivo sube de nuevo.
    await page.getByRole("textbox", { name: "Trade ticker" }).fill("MSFT");
    await page.getByRole("textbox", { name: "Trade quantity" }).fill("2");
    await page.getByRole("button", { name: "Sell", exact: true }).click();

    await expect(positions.getByRole("cell", { name: "MSFT" })).toHaveCount(0, { timeout: 10_000 });
    await expect
      .poll(async () => readCash(page), { timeout: 10_000 })
      .toBeGreaterThan(cashAfterBuy);
  });
});
