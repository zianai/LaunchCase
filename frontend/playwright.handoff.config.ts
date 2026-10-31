import { defineConfig } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
const root = path.resolve(__dirname, "..");
const seed = JSON.parse(
  readFileSync(
    path.join(root, ".launchcase/handoff-e2e/manifest.json"),
    "utf8",
  ),
);
export default defineConfig({
  testDir: "./tests",
  testMatch: "handoff.spec.ts",
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: "http://127.0.0.1:3312",
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "uv run uvicorn launchcase.api:app --host 127.0.0.1 --port 8812 --no-access-log",
      cwd: root,
      url: "http://127.0.0.1:8812/health",
      env: {
        LAUNCHCASE_DATA_DIR: seed.data_dir,
        LAUNCHCASE_DATABASE_URL: `sqlite:///${seed.database}`,
      },
    },
    {
      command:
        "node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3312",
      url: "http://127.0.0.1:3312",
      env: { LAUNCHCASE_API_URL: "http://127.0.0.1:8812" },
    },
  ],
  outputDir: "test-results/handoff",
  reporter: [["list"]],
});
