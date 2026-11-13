/**
 * Pruebas E2E del Core. Necesitan el sistema levantado con los datos de demo:
 *     docker compose up -d --build
 * Después, desde esta carpeta:
 *     npm install
 *     npx playwright install chromium
 *     npx playwright test
 */
import {defineConfig, devices} from "@playwright/test";

export default defineConfig({
    testDir: "./tests",
    timeout: 90_000,
    expect: {timeout: 10_000},
    // El flujo es una sola historia: los pasos van en orden, sin paralelismo
    fullyParallel: false,
    workers: 1,
    retries: process.env.CI ? 1 : 0,
    reporter: [["list"], ["html", {open: "never"}]],
    use: {
        baseURL: process.env.E2E_URL ?? "http://localhost:8081",
        locale: "es-AR",
        screenshot: "only-on-failure",
        trace: "retain-on-failure",
    },
    projects: [{name: "chromium", use: {...devices["Desktop Chrome"], viewport: {width: 1366, height: 900}}}],
});