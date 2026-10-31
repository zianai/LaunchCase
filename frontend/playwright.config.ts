import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testIgnore: "handoff.spec.ts",
  timeout: 90000,
  workers: 1,
  use: {
    baseURL: process.env.LAUNCHCASE_WEB_URL || "http://127.0.0.1:3310",
    headless: true,
    trace: "retain-on-failure",
  },
  reporter: [["list"]],
  outputDir: "test-results",
});
