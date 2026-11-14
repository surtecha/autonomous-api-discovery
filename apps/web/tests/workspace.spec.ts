import { test, expect } from "@playwright/test";

test("authorized target session produces visible evidence", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Explore the contract." })).toBeVisible();
  await expect(page.getByLabel("Authorized target")).toBeEnabled();
  await page.getByLabel("Authorized target").selectOption("ecommerce");
  await page.getByRole("button", { name: "Start discovery" }).click();
  await expect(page.locator(".error[role=alert]")).toHaveCount(0);
  await expect(page.locator("details.operation").first()).toBeVisible({ timeout: 150000 });
  await page.locator("details.operation summary").first().click();
  await expect(page.getByRole("heading", { name: "Evidence references" }).first()).toBeVisible();
  await page.getByRole("tab", { name: "Resource graph" }).click();
  await expect(page.getByRole("heading", { name: "Observed state transitions" })).toBeVisible();
  await page.getByRole("tab", { name: "Artifacts" }).click();
  await expect(page.getByRole("link", { name: "Download openapi" })).toBeVisible({ timeout: 30000 });
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download openapi" }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("openapi.json");
  expect(await download.failure()).toBeNull();
  await page.getByRole("tab", { name: "Evaluation" }).click();
  await expect(page.getByRole("heading", { name: "Measured execution" })).toBeVisible();
  await page.reload();
  await expect(page.locator("details.operation").first()).toBeVisible();
  await page.screenshot({ path: "../../.runtime/verification/workspace-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Start discovery" })).toBeVisible();
  await page.screenshot({ path: "../../.runtime/verification/workspace-mobile.png", fullPage: true });
});

test("authentication and cross-origin writes are rejected", async ({ playwright, baseURL }) => {
  const anonymous = await playwright.request.newContext({ baseURL,
    httpCredentials: { username: "unauthorized", password: "invalid" }, // pragma: allowlist secret - rejected test input
  });
  expect((await anonymous.get("/")).status()).toBe(401);
  await anonymous.dispose();
  const authorized = await playwright.request.newContext({ baseURL, httpCredentials: {
    username: process.env.WEB_USERNAME ?? "", password: process.env.WEB_PASSWORD ?? "",
  } });
  expect((await authorized.post("/api/backend/discovery-sessions", {
    headers: { Origin: "https://unrelated.invalid" }, data: { target: "ecommerce" },
  })).status()).toBe(403);
  expect((await authorized.post("/api/backend/discovery-sessions", {
    headers: { Origin: baseURL! }, data: { target: "unauthorized" },
  })).status()).toBe(422);
  await authorized.dispose();
});
