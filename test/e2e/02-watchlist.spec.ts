import { test, expect } from "@playwright/test";
import { watchlistRow } from "./helpers";

test.describe("Watchlist CRUD vía UI (PLAN §12)", () => {
  test("añadir un ticker nuevo y eliminarlo", async ({ page }) => {
    await page.goto("/");

    // Añadir PYPL (no está en la watchlist por defecto). Enter envía el form.
    const add = page.getByRole("textbox", { name: "Add ticker" });
    await add.fill("PYPL");
    await add.press("Enter");

    await expect(watchlistRow(page, "PYPL")).toBeVisible({ timeout: 10_000 });

    // Eliminar GOOGL (ticker por defecto). El botón aparece al hover sobre la fila.
    const googlRow = watchlistRow(page, "GOOGL");
    await googlRow.hover();
    await googlRow.getByRole("button", { name: "Remove GOOGL" }).click();

    await expect(watchlistRow(page, "GOOGL")).toHaveCount(0, { timeout: 10_000 });

    // PYPL sigue presente tras la eliminación.
    await expect(watchlistRow(page, "PYPL")).toBeVisible();
  });
});
