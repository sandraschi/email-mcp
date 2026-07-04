import { expect, test } from "@playwright/test";

const AUTH = {
  Authorization: `Basic ${Buffer.from("sandra:vienna2026").toString("base64")}`,
};

test.describe("Email-MCP Webapp", () => {
  test("Dashboard loads with KPIs", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Email Hub Dashboard" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Unread Messages" }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Services" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Drafts" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Bridge Status" }),
    ).toBeVisible();
  });

  test("Inbox page loads", async ({ page }) => {
    await page.goto("/inbox");
    await expect(
      page.getByRole("heading", { name: "Inbox", exact: true }),
    ).toBeVisible();
  });

  test("Compose page loads with AI Improve and Expander", async ({ page }) => {
    await page.goto("/compose");
    await expect(
      page.getByRole("heading", { name: "Compose Email" }),
    ).toBeVisible();
    await page.fill(
      'textarea[placeholder*="Write your email"]',
      "Test email body for AI",
    );
    await expect(page.getByText("AI Improve")).toBeVisible();
    await expect(page.getByText("Expander")).toBeVisible();
  });

  test("Services page has Quick Setup chips", async ({ page }) => {
    await page.goto("/services");
    await expect(page.getByText("Quick Setup")).toBeVisible();
    await expect(page.getByText("Gmail").first()).toBeVisible();
    await page.getByText("Outlook").first().click();
    await expect(page.getByPlaceholder("your@email.com")).toBeVisible();
  });

  test("Settings page loads", async ({ page }) => {
    await page.goto("/settings");
    await expect(
      page.getByRole("heading", { name: "AI Provider" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Email Service Credentials" }),
    ).toBeVisible();
  });

  test("AI Chat page loads with workflow presets", async ({ page }) => {
    await page.goto("/chat");
    await expect(
      page.getByRole("heading", { name: "Email AI Expert" }),
    ).toBeVisible();
    await page.waitForTimeout(1000);
    await expect(page.getByText("Creative Workflows")).toBeVisible();
  });

  test("Mail Lab page loads", async ({ page }) => {
    await page.goto("/lab");
    await expect(page.getByRole("heading", { name: "Mail Lab" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "SMTP Server" }),
    ).toBeVisible();
  });

  test("Contacts page loads", async ({ page }) => {
    await page.goto("/contacts");
    await expect(page.getByRole("heading", { name: "Contacts" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Import" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Add" })).toBeVisible();
  });

  test("Help page has 6 tabs", async ({ page }) => {
    await page.goto("/help");
    await expect(page.getByRole("tab", { name: "Quick Start" })).toBeVisible();
    await expect(
      page.getByRole("tab", { name: "Email Systems" }),
    ).toBeVisible();
    await expect(
      page.getByRole("tab", { name: "Configuration" }),
    ).toBeVisible();
    await expect(page.getByRole("tab", { name: "Tools" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Safety" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "SOTA" })).toBeVisible();
    await page.getByRole("tab", { name: "Safety" }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText("Two-layer defense").first()).toBeVisible();
  });

  test("Topbar health check shows online", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(3000);
    await expect(page.getByText("System Online")).toBeVisible();
  });

  test("Sidebar navigation works", async ({ page }) => {
    await page.goto("/");
    const navItems = [
      "Inbox",
      "Search",
      "Compose",
      "AI Chat",
      "Mail Lab",
      "Services",
      "Contacts",
    ];
    for (const item of navItems) {
      await page.getByRole("link", { name: item }).click();
      await page.waitForTimeout(300);
      await expect(page.locator("h2").first()).toBeVisible();
    }
  });
});

test.describe("REST API", () => {
  test("GET /api/status returns connected", async ({ request }) => {
    const resp = await request.get("http://localhost:10813/api/status", {
      headers: AUTH,
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.status).toBe("connected");
  });

  test("GET /api/services returns service list", async ({ request }) => {
    const resp = await request.get("http://localhost:10813/api/services", {
      headers: AUTH,
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data).toHaveProperty("services");
  });

  test("POST /api/services/quick rejects invalid provider", async ({
    request,
  }) => {
    const resp = await request.post(
      "http://localhost:10813/api/services/quick",
      {
        headers: AUTH,
        data: {
          provider: "nonexistent",
          email: "test@test.com",
          password: "pass",
        },
      },
    );
    expect(resp.status()).toBe(422);
  });

  test("POST /api/improve rejects empty text", async ({ request }) => {
    const resp = await request.post("http://localhost:10813/api/improve", {
      headers: AUTH,
      data: { text: "", style: "professional" },
    });
    expect(resp.status()).toBe(422);
  });

  test("GET /api/watcher/status returns without crashing", async ({
    request,
  }) => {
    const resp = await request.get(
      "http://localhost:10813/api/watcher/status",
      { headers: AUTH },
    );
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data).toHaveProperty("running");
  });

  test("POST /api/workflow love-letter returns text", async ({ request }) => {
    const resp = await request.post("http://localhost:10813/api/workflow", {
      headers: AUTH,
      data: {
        workflow: "love-letter",
        recipient: "Test",
        tone: "sincere",
        mood: "warm",
        format: "text",
      },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.success).toBe(true);
    expect(data.workflow).toBe("love-letter");
    expect(data.response.length).toBeGreaterThan(10);
  });
});
