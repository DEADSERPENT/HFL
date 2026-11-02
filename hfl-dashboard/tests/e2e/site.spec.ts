import { expect, test } from "@playwright/test";

const ROUTES = ["/", "/research/", "/architecture/", "/datasets/", "/privacy/", "/results/", "/experiments/", "/reproducibility/", "/limitations/", "/publication/", "/accessibility/"];

test.describe("public pages", () => {
  for (const route of ROUTES) {
    test(`${route} renders, has one h1, no overflow, no external requests`, async ({ page, baseURL }) => {
      const external: string[] = [];
      const errors: string[] = [];
      page.on("request", (r) => {
        const u = new URL(r.url());
        if (!["127.0.0.1", "localhost"].includes(u.hostname) && u.protocol.startsWith("http")) external.push(r.url());
      });
      page.on("pageerror", (e) => errors.push(e.message));
      const res = await page.goto(route);
      expect(res?.status()).toBe(200);
      await expect(page.locator("h1")).toHaveCount(1);
      await page.waitForLoadState("networkidle");
      expect(external, `external requests from ${baseURL}${route}`).toEqual([]);
      expect(errors).toEqual([]);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow).toBeLessThanOrEqual(1);
    });
  }

  test("unknown routes show the custom 404", async ({ page }) => {
    const res = await page.goto("/repository/");
    expect(res?.status()).toBe(404);
    await expect(page.getByRole("heading", { name: /not part of the Observatory/ })).toBeVisible();
  });

  test("limitations are discoverable from the header and footer", async ({ page, isMobile }) => {
    await page.goto("/");
    if (isMobile) await page.getByRole("button", { name: "Open menu" }).click();
    await page.getByRole("navigation", { name: isMobile ? "Mobile" : "Primary" }).getByRole("link", { name: "Limitations" }).click();
    await expect(page).toHaveURL(/\/limitations\/$/);
    await expect(page.getByRole("contentinfo").getByRole("link", { name: "Limitations" })).toBeVisible();
  });
});

test.describe("results explorer", () => {
  test("filters update charts and text, and the drawer restores focus", async ({ page }) => {
    await page.goto("/results/");
    await page.getByLabel("Metric").selectOption("update-delivery");
    await page.getByRole("radio", { name: "eICU" }).click();
    await expect(page.getByText("Showing 1 result for Update delivery, eICU.")).toBeVisible();
    const bar = page.getByRole("button", { name: /Update delivery, eICU.*97.83%/ });
    await bar.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('[data-status="target-not-met"]')).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(bar).toBeFocused();
  });

  test("table view keeps the energy caveat", async ({ page }) => {
    await page.goto("/results/?metric=energy&view=table");
    await expect(page.getByRole("table")).toContainText("CloudSim Plus simulation");
  });

  test("deep link opens a result", async ({ page }) => {
    await page.goto("/results/?detail=utility-eicu-end-to-end");
    await expect(page.getByRole("dialog")).toContainText("3.91 AUROC points");
  });
});

test.describe("architecture", () => {
  test("switch between 3D and 2D, step through the story, pause flow", async ({ page }) => {
    await page.goto("/architecture/");
    await page.getByRole("radio", { name: "2D diagram" }).click();
    await expect(page.getByRole("group", { name: /Two-dimensional diagram/ })).toBeVisible();
    await page.getByRole("button", { name: "Start the story" }).click();
    await expect(page.getByRole("heading", { name: "Local computation" })).toBeVisible();
    await page.getByRole("button", { name: "Next step" }).click();
    await expect(page.getByRole("heading", { name: "Privacy mechanism" })).toBeVisible();
    const flow = page.getByRole("button", { name: /flow$/ }).first();
    const before = await flow.textContent();
    await flow.click();
    await expect(flow).not.toHaveText(before ?? "");
    await page.getByRole("radio", { name: "8 edges" }).click();
    await expect(page.getByText(/minimum 99.49%/)).toBeVisible();
  });

  test("keyboard reaches layer selection", async ({ page }) => {
    await page.goto("/architecture/");
    const edge = page.getByRole("radio", { name: "Edge", exact: true });
    await edge.focus();
    await page.keyboard.press("Enter");
    await expect(edge).toHaveAttribute("aria-checked", "true");
  });
});

test("pause motion persists", async ({ page, isMobile }) => {
  test.skip(isMobile, "control is in the menu on mobile");
  await page.goto("/");
  await page.getByRole("banner").getByRole("button", { name: "Pause motion" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "paused");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "paused");
});
