import { test, expect } from "@playwright/test";

test.describe("Chat IA con LLM_MOCK (PLAN §12)", () => {
  test("'buy 1 AAPL' devuelve respuesta y ejecuta el trade inline", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("LIVE", { exact: true })).toBeVisible({ timeout: 15_000 });

    const chat = page.locator("section", {
      has: page.getByText("AI Copilot", { exact: true }),
    });

    // Enviar la instrucción mock determinista.
    await page.getByRole("textbox", { name: "Message FinAlly" }).fill("buy 1 AAPL");
    await page.getByRole("button", { name: "Send", exact: true }).click();

    // El mensaje del usuario aparece.
    await expect(chat.getByText("buy 1 AAPL")).toBeVisible({ timeout: 10_000 });

    // El recibo de acción inline muestra el trade ejecutado (pill "BUY 1 AAPL",
    // distinta del eco del usuario "buy 1 AAPL" → exact case-sensitive).
    await expect(chat.getByText("BUY 1 AAPL", { exact: true })).toBeVisible({ timeout: 15_000 });

    // La posición AAPL se refleja en la tabla de posiciones.
    const positions = page.locator("section", {
      has: page.getByText("Positions", { exact: true }),
    });
    await expect(positions.getByRole("cell", { name: "AAPL" })).toBeVisible({ timeout: 10_000 });
  });
});
