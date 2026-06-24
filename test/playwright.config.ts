import { defineConfig, devices } from "@playwright/test";

/**
 * Apunta a la app FinAlly ya en marcha (contenedor con LLM_MOCK=true).
 * Override con BASE_URL; por defecto el puerto host alternativo 8012
 * (el 8000 del host está ocupado por otro contenedor).
 */
const baseURL = process.env.BASE_URL ?? "http://localhost:8012";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
