import { Page, expect } from "@playwright/test";

const DEFAULT_TICKERS = [
  "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
  "NVDA", "META", "JPM", "V", "NFLX",
];

export { DEFAULT_TICKERS };

/** Fila de la watchlist por símbolo (la primera celda contiene el ticker en mono). */
export function watchlistRow(page: Page, ticker: string) {
  return page
    .locator("section", { has: page.getByText("Watchlist", { exact: true }) })
    .getByRole("row", { name: new RegExp(`\\b${ticker}\\b`) })
    .first();
}

/** Lee el valor "Cash" del header como número (quita $ y comas). */
export async function readCash(page: Page): Promise<number> {
  const cash = page
    .locator("div", { hasText: /^Cash$/ })
    .locator("xpath=following-sibling::div[1]")
    .first();
  const text = (await cash.textContent())?.trim() ?? "";
  return Number(text.replace(/[$,\s]/g, ""));
}

/** Espera a que el indicador de conexión muestre LIVE. */
export async function expectLive(page: Page) {
  await expect(page.getByText("LIVE", { exact: true })).toBeVisible({ timeout: 15_000 });
}
