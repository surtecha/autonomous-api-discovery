import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 180_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    httpCredentials: {
      username: process.env.WEB_USERNAME ?? "",
      password: process.env.WEB_PASSWORD ?? "",
    },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: process.env.E2E_EXTERNAL_SERVER === "1" ? undefined : {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
  },
});
