import { test, expect, type Page } from "@playwright/test";

async function createDraft(page: Page) {
  await page.goto("/assessments");
  await page.getByRole("button", { name: "New assessment", exact: true }).click();
  await page.getByLabel("Assessment name", { exact: true }).fill("Demo review");
  await page.getByLabel("What should be assessed?").fill("Discover registered services without starting a live scan.");
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByLabel("Lab hostname", { exact: true }).fill("demo.lab.example");
  await page.getByLabel("IPv4 with /32").fill("192.0.2.44/32");
  await page.getByLabel("Permission reference", { exact: true }).fill("DEMO-0044");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByRole("button", { name: "Create assessment", exact: true }).click();
  await expect(page).toHaveURL(/\/assessments\/AST-003\/plan$/);
}

async function openAssistant(page: Page) {
  await page.getByRole("button", { name: "Ask assistant", exact: true }).click();
  return page.getByRole("dialog");
}

test("dashboard shows synthetic evidence and distinct decision counts", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await expect(page.getByText("Synthetic preview", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Finding priorities" })).toBeVisible();
  await expect(page.getByTestId("pending-count")).toHaveText("1");
  await expect(page.getByTestId("failed-count")).toHaveText("1");
});

test("source destinations and deep links render on refresh", async ({ page }) => {
  for (const [path, heading] of [["/assessments", "Assessments"], ["/approvals", "Approvals"], ["/findings", "Findings"], ["/reports", "Reports"], ["/settings", "Settings"], ["/assessments/AST-001/scope", "Customer portal review"]]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    await expect(page.getByText("Synthetic preview", { exact: true }).first()).toBeVisible();
  }
});

test("creation validates exact scope and starts with no actions or findings", async ({ page }) => {
  await page.goto("/assessments");
  await page.getByRole("button", { name: "New assessment", exact: true }).click();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "assessment name" })).toBeVisible();
  await page.getByLabel("Assessment name", { exact: true }).fill("Validated draft");
  await page.getByLabel("What should be assessed?").fill("Review the demo scope.");
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByLabel("Lab hostname", { exact: true }).fill("valid.lab.example");
  await page.getByLabel("IPv4 with /32").fill("999.0.2.44/32");
  await page.getByLabel("Permission reference", { exact: true }).fill("DEMO");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("valid IPv4");
  await page.getByLabel("IPv4 with /32").fill("192.0.2.44/32");
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByLabel("Allowed TCP ports", { exact: true }).fill("443.5");
  await page.getByRole("button", { name: "Create assessment", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("integer TCP ports");
  await page.getByLabel("Allowed TCP ports", { exact: true }).fill("443");
  await page.getByRole("button", { name: "Create assessment", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Start with a scoped proposal" })).toBeVisible();
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Findings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No findings match" })).toBeVisible();
});

test("approval records a decision without scanner execution or invented results", async ({ page }) => {
  await createDraft(page);
  await page.getByRole("button", { name: "Generate preview proposal", exact: true }).click();
  await page.getByRole("button", { name: /Service discovery on demo.lab.example/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("button", { name: "Record approval" })).toBeDisabled();
  await dialog.getByLabel("Decision rationale").fill("Review only. No execution in preview.");
  await dialog.getByRole("button", { name: "Record approval" }).click();
  const action = page.getByRole("button", { name: /Service discovery on demo.lab.example/ });
  await expect(action).toContainText("Approved");
  await expect(action).not.toContainText("Done");
  await action.click();
  await expect(page.getByRole("button", { name: "Start scan / In development" })).toBeDisabled();
  await page.keyboard.press("Escape");
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Findings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No findings match" })).toBeVisible();
});

test("messages stay assessment-specific and generation is explicit and deduplicated", async ({ page }) => {
  await createDraft(page);
  let dialog = await openAssistant(page);
  await dialog.getByLabel("Message", { exact: true }).fill("Discover services on demo.lab.example");
  await dialog.getByRole("button", { name: "Send message" }).click();
  await expect(dialog.getByLabel("Message", { exact: true })).toHaveValue("");
  await expect(dialog.getByRole("log")).toContainText("No proposal, model call, or scan was started");
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Start with a scoped proposal" })).toBeVisible();
  dialog = await openAssistant(page);
  await dialog.getByRole("button", { name: "Generate preview proposal" }).click();
  await expect(dialog.getByRole("log")).toContainText("Deterministic preview proposal generated");
  await dialog.getByRole("button", { name: "Generate preview proposal" }).click();
  await expect(dialog.getByRole("log")).toContainText("No duplicate proposal added");
  await dialog.getByLabel("Assessment context").selectOption("AST-001");
  await expect(dialog.getByRole("log")).not.toContainText("Discover services on demo.lab.example");
  await dialog.getByLabel("Assessment context").selectOption("AST-003");
  await expect(dialog.getByRole("log")).toContainText("Discover services on demo.lab.example");
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await expect(page.getByRole("button", { name: /Service discovery on demo.lab.example/ })).toHaveCount(1);
});

test("requests for another assessment target are rejected without adding work", async ({ page }) => {
  await page.goto("/assessments/AST-002/plan");
  const dialog = await openAssistant(page);
  await dialog.getByLabel("Message", { exact: true }).fill("Discover services on web.lab.example");
  await dialog.getByRole("button", { name: "Send message" }).click();
  await dialog.getByRole("button", { name: "Generate preview proposal" }).click();
  await expect(dialog.getByRole("log")).toContainText("Request rejected");
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await expect(page.getByRole("button", { name: /Service discovery on port 443/ })).toHaveCount(1);
  await page.getByRole("link", { name: "Audit trail", exact: true }).click();
  await expect(page.getByText("Preview request rejected", { exact: true })).toBeVisible();
});

test("unsupported active validation cannot be approved but can be declined", async ({ page }) => {
  await page.goto("/approvals");
  await page.getByRole("button", { name: "Review", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Decision rationale").fill("Unsupported capability; do not execute.");
  await expect(dialog.getByRole("button", { name: "Record approval" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Decline proposal" }).click();
  await expect(page.getByRole("heading", { name: "No decisions waiting" })).toBeVisible();
  await expect(page.getByText("Failed", { exact: true })).toBeVisible();
});

test("retry preserves the failed attempt and creates a distinct pending proposal", async ({ page }) => {
  await page.goto("/assessments/AST-002/plan");
  await page.getByRole("button", { name: /Service discovery on port 443/ }).click();
  await page.getByRole("button", { name: "Create retry proposal" }).click();
  await expect(page.getByRole("dialog").getByRole("heading")).toContainText("Retry proposal");
  await expect(page.getByRole("dialog").getByText("Pending", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: /^1 Service discovery/ })).toContainText("Failed");
  await expect(page.getByRole("button", { name: /Retry proposal: Service discovery/ })).toContainText("Pending");
});

test("retry respects disabled preview tools", async ({ page }) => {
  await page.goto("/settings");
  await page.getByLabel("Nmap enabled", { exact: true }).uncheck();
  await page.getByRole("button", { name: "Save preferences", exact: true }).first().click();
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Assessments", exact: true }).click();
  await page.getByRole("link", { name: /Staging API check/ }).click();
  await page.getByRole("button", { name: /Service discovery on port 443/ }).click();
  await expect(page.getByRole("button", { name: "Create retry proposal" })).toBeDisabled();
});

test("finding review retains source evidence and never confirms a suspected banner", async ({ page }) => {
  await page.goto("/findings");
  await page.getByRole("button", { name: /Outdated nginx 1.18.0 version banner/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Suspected", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Unknown / no score or vector supplied")).toBeVisible();
  await expect(dialog.getByText("Synthetic fixture", { exact: true })).toHaveCount(3);
  await dialog.getByLabel("Analyst disposition", { exact: true }).selectOption("Accepted");
  await dialog.getByLabel("Review rationale").fill("Accept for review; vendor patch level remains unknown.");
  await dialog.getByRole("button", { name: "Save review" }).click();
  const row = page.getByRole("button", { name: /Outdated nginx 1.18.0 version banner/ });
  await expect(row).toContainText("Accepted");
  await expect(row).toContainText("Suspected");
  await page.getByLabel("Filter by severity").selectOption("Low");
  await expect(page.getByRole("button", { name: /Session cookie without HttpOnly/ })).toBeVisible();
  await expect(row).toHaveCount(0);
});

test("local files are hashed and escaped without claiming native parsing", async ({ page }) => {
  await page.goto("/assessments/AST-002/plan");
  await page.getByRole("button", { name: "Attach results", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Recorded output file").setInputFiles({ name: "synthetic.xml", mimeType: "text/xml", buffer: Buffer.from('<script>window.evidenceExecuted=true</script><sample/>') });
  await dialog.getByRole("button", { name: "Attach to preview" }).click();
  await expect(page.getByRole("heading", { name: "Preview attachments" })).toBeVisible();
  await page.getByText("View escaped excerpt", { exact: true }).click();
  await expect(page.locator("pre")).toContainText("<script>window.evidenceExecuted=true</script>");
  expect(await page.evaluate(() => (window as unknown as Record<string, unknown>).evidenceExecuted)).toBeUndefined();
  await expect(page.getByText(/^SHA-256 [a-f0-9]{64}$/)).toBeVisible();
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Findings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No findings match" })).toBeVisible();
});

test("sample report remains frozen after later finding review and supports print layout", async ({ page }) => {
  await page.goto("/assessments/AST-001/plan");
  await page.getByRole("button", { name: /Lab-only validation of outdated/ }).click();
  await page.getByLabel("Decision rationale").fill("Unsupported; synthetic report may disclose unvalidated findings.");
  await page.getByRole("button", { name: "Decline proposal" }).click();
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Report", exact: true }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Generate sample draft" }).click();
  let dialog = page.getByRole("dialog");
  for (const section of ["7.1 Executive summary", "7.2 Scope and methodology", "7.3 Severity distribution", "7.4 Detailed findings and evidence", "7.5 Impact and remediation", "7.6 Limitations and review history"]) await expect(dialog.getByRole("heading", { name: section, exact: true })).toBeVisible();
  const frozenText = await dialog.locator(".report-copy").innerText();
  await page.emulateMedia({ media: "print" });
  await expect(dialog.getByRole("heading", { name: "Vulnerability assessment report", exact: true })).toBeVisible();
  await expect(page.locator(".app-shell")).toBeHidden();
  await page.pdf({ path: "test-results/reknyx-synthetic-sample.pdf", format: "A4", printBackground: true });
  await page.emulateMedia({ media: "screen" });
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Findings", exact: true }).click();
  await page.getByRole("button", { name: /Outdated nginx 1.18.0 version banner/ }).click();
  await page.getByLabel("Review rationale").fill("A review after the report snapshot was created.");
  await page.getByRole("button", { name: "Save review" }).click();
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Reports", exact: true }).click();
  await page.getByRole("button", { name: /Preview/ }).first().click();
  dialog = page.getByRole("dialog");
  expect(await dialog.locator(".report-copy").innerText()).toBe(frozenText);
});

test("search and notifications open the correct assessment context", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Quick search", exact: true }).click();
  await page.keyboard.press("Escape");
  await page.keyboard.press("/");
  await page.getByLabel("Search workspace").fill("HttpOnly");
  await page.getByRole("dialog").getByRole("button", { name: /Session cookie without HttpOnly/ }).click();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Session cookie without HttpOnly", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Notifications", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("heading")).toHaveText("Notifications");
  await page.getByRole("button", { name: /Unsupported validation proposal/ }).click();
  await expect(page.getByRole("dialog").getByRole("heading")).toContainText("Lab-only validation");
});

test("keyboard dialogs trap focus and restore it on Escape", async ({ page }) => {
  await page.goto("/assessments");
  const opener = page.getByRole("button", { name: "New assessment", exact: true });
  await opener.click();
  await expect(page.getByLabel("Assessment name", { exact: true })).toBeFocused();
  for (let i = 0; i < 10; i++) {
    await page.keyboard.press("Tab");
    expect(await page.evaluate(() => Boolean(document.activeElement?.closest("dialog")))).toBe(true);
  }
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(opener).toBeFocused();
});

test("preferences persist while existing scope and preview assessments remain isolated", async ({ page }) => {
  await page.goto("/settings");
  await page.getByLabel("Analyst name", { exact: true }).fill("Demo Analyst");
  await page.getByLabel("Allowed TCP ports", { exact: true }).fill("8443");
  await page.getByLabel("Theme", { exact: true }).selectOption("dark");
  await page.getByRole("button", { name: "Save preferences", exact: true }).first().click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Assessments", exact: true }).click();
  await page.getByRole("link", { name: /Customer portal review/ }).click();
  await page.getByRole("navigation", { name: "Assessment views" }).getByRole("link", { name: "Scope", exact: true }).click();
  await expect(page.locator("dd").filter({ hasText: /^80, 443$/ })).toBeVisible();
  await page.goto("/settings");
  await expect(page.getByLabel("Analyst name", { exact: true })).toHaveValue("Demo Analyst");
  await expect(page.getByLabel("Allowed TCP ports", { exact: true })).toHaveValue("8443");
  await page.getByRole("button", { name: "Reset preferences", exact: true }).click();
  await expect(page.getByLabel("Analyst name", { exact: true })).toHaveValue("Long");
});

test("storage failure is visible and does not prevent session preferences", async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => { throw new DOMException("Storage disabled", "QuotaExceededError"); };
  });
  await page.goto("/settings");
  await page.getByLabel("Analyst name", { exact: true }).fill("Session Analyst");
  await page.getByRole("button", { name: "Save preferences", exact: true }).first().click();
  await expect(page.getByRole("alert").filter({ hasText: "Browser storage is unavailable" })).toBeVisible();
  await expect(page.getByLabel("Analyst name", { exact: true })).toHaveValue("Session Analyst");
});

test("desktop and mobile layouts fit viewport and support navigation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/");
  await page.screenshot({ path: "test-results/reknyx-dashboard-desktop.png", fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/reknyx-dashboard-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("link", { name: "Findings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Findings", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: /Outdated nginx 1.18.0 version banner/ }).click();
  const box = await page.getByRole("dialog").boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.width).toBeLessThanOrEqual(390);
  await page.keyboard.press("Escape");
  for (const [path, heading] of [["/assessments", "Assessments"], ["/approvals", "Approvals"], ["/reports", "Reports"], ["/settings", "Settings"], ["/assessments/AST-001/plan", "Customer portal review"]]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), path).toBe(true);
  }
});

test("unknown routes and reload of an ephemeral draft explain recovery", async ({ page }) => {
  await page.goto("/missing-view");
  await expect(page.getByRole("heading", { name: "Page not found", exact: true })).toBeVisible();
  await createDraft(page);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Assessment unavailable in this session", exact: true })).toBeVisible();
});

test("preview makes no scanner, provider, API, or external requests", async ({ page }) => {
  const unexpected: string[] = [];
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.origin !== "http://127.0.0.1:3100" || url.pathname.startsWith("/api/")) unexpected.push(request.url());
  });
  await page.goto("/");
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Assessments", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Assessments", exact: true })).toBeVisible();
  await page.getByRole("link", { name: /Staging API check/ }).click();
  const dialog = await openAssistant(page);
  await dialog.getByLabel("Message", { exact: true }).fill("Discover services on api.lab.example");
  await dialog.getByRole("button", { name: "Send message" }).click();
  await dialog.getByRole("button", { name: "Generate preview proposal" }).click();
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  expect(unexpected).toEqual([]);
  expect(errors).toEqual([]);
});
