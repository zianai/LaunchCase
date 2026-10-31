import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testMatch: "p8-p10.spec.ts",
  timeout: 90000,
  workers: 1,
  use: {
    baseURL: process.env.LAUNCHCASE_WEB_URL,
    headless: true,
    trace: "retain-on-failure",
  },
  reporter: [["list"]],
  outputDir: "test-results/p8-p10",
});
