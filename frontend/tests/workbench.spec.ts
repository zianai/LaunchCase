import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import path from "node:path";
const root = path.resolve(__dirname, "../..");
const fixture = path.join(root, "fixtures/scenarios/pet-furniture-us");
const screenshotDir = path.resolve(
  root,
  process.env.LAUNCHCASE_SCREENSHOT_DIR || "docs/evidence/browser",
);
mkdirSync(screenshotDir, { recursive: true });
for (const viewport of [
  { width: 1440, height: 1000 },
  { width: 390, height: 844 },
]) {
  test(`real API full internal workflow ${viewport.width}px`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/");
    await page
      .getByLabel("本地身份凭证")
      .fill(
        readFileSync(
          process.env.LAUNCHCASE_TOKEN_FILE ||
            path.join(root, ".launchcase/browser-token"),
          "utf8",
        ).trim(),
      );
    await page.getByRole("button", { name: "进入工作区 →" }).click();
    await page.getByRole("button", { name: "＋ 创建产品项目" }).click();
    let dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: "载入合成宠物家具示例" }).click();
    await dialog.getByRole("button", { name: "创建项目", exact: true }).click();
    await expect(page.getByRole("tab", { name: "证据来源" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await page.getByLabel("我有权导入并用于内部研究").check();
    for (const [file, type] of [
      ["synthetic-voc.csv", "review"],
      ["synthetic-competitors.csv", "competitor"],
      ["synthetic-quote.json", "quote"],
    ]) {
      await page.getByLabel("资料类型").selectOption(type);
      await page
        .getByLabel("导入来源文件")
        .setInputFiles(path.join(fixture, file));
      await expect(page.getByText(file, { exact: true })).toBeVisible();
    }
    await page
      .getByRole("button")
      .filter({ hasText: "The screws were hard to align during assembly." })
      .first()
      .click();
    await expect(page.locator("blockquote")).toHaveText(
      "The screws were hard to align during assembly.",
    );
    await page.getByRole("tab", { name: "用户反馈研究" }).click();
    await page.getByRole("button", { name: "运行研究", exact: true }).click();
    await expect(
      page.getByText("用户反馈存在分歧", { exact: true }),
    ).toBeVisible();
    await page.getByRole("tab", { name: "产品机会", exact: true }).click();
    await page
      .locator("article.opportunity")
      .filter({ hasText: "Reduce assembly friction" })
      .getByRole("button", { name: "审核机会" })
      .click();
    dialog = page.getByRole("dialog");
    await dialog
      .getByLabel("理由与适用边界")
      .fill(
        "SYNTHETIC TEST ONLY: investigate assembly hypothesis; no commercial approval.",
      );
    await dialog.getByRole("button", { name: "记录人工决定" }).click();
    await expect(dialog).not.toBeVisible();
    await page
      .getByRole("button", { name: "从选中机会生成产品方案 →" })
      .click();
    await expect(page.getByRole("status")).toContainText("G2");
    await page.getByRole("tab", { name: "产品方案与规格" }).click();
    await expect(page.locator("article.concept")).toHaveCount(2);
    await page
      .locator("article.concept")
      .first()
      .getByRole("button", { name: "审核方案" })
      .click();
    await page
      .getByRole("dialog")
      .getByLabel("理由与适用边界")
      .fill(
        "SYNTHETIC TEST ONLY: choose proposal, dimensions and performance remain unknown.",
      );
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "记录人工决定" })
      .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await page.getByRole("tab", { name: "成本与风险", exact: true }).click();
    await page.getByRole("button", { name: "核算成本", exact: true }).click();
    await expect(page.getByText("资料不足，无法计算")).toBeVisible();
    await page
      .getByRole("button", { name: "审核成本与样品验证", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByLabel("理由与适用边界")
      .fill(
        "SYNTHETIC TEST ONLY: sample investigation only, no viability conclusion.",
      );
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "记录人工决定" })
      .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await page.getByRole("tab", { name: "概念图片", exact: true }).click();
    await page.getByRole("button", { name: "＋ 创建概念图片计划" }).click();
    await page.getByRole("button", { name: "审核计划", exact: true }).click();
    await page
      .getByRole("dialog")
      .getByLabel("理由与适用边界")
      .fill(
        "SYNTHETIC TEST ONLY: zero-budget Mock, internal visual exploration.",
      );
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "记录人工决定" })
      .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await page.getByRole("button", { name: "执行已批准计划" }).click();
    await expect(page.getByRole("img")).toBeVisible();
    await expect(page.getByText("人工审核：待独立审核")).toBeVisible();
    await page.getByRole("button", { name: "审核这张图片" }).click();
    await page
      .getByRole("dialog")
      .getByLabel("理由与适用边界")
      .fill(
        "SYNTHETIC TEST ONLY: fixed Mock raster approved for internal fixture pack.",
      );
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "记录人工决定" })
      .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await expect(page.getByText("人工审核：已批准内部使用")).toBeVisible();
    await page.screenshot({
      path: path.join(screenshotDir, `visual-${viewport.width}.png`),
      fullPage: true,
    });
    await page.getByRole("tab", { name: "内部交接资料", exact: true }).click();
    await page.getByRole("button", { name: "生成内部交接资料" }).click();
    await expect(page.getByText("不可发布", { exact: true })).toBeVisible();
    const url = await page
      .getByRole("link", { name: "下载 JSON ↗" })
      .getAttribute("href");
    const response = await page.request.get(url!);
    expect(response.ok()).toBeTruthy();
    const pack = await response.json();
    expect(pack.publishable).toBe(false);
    expect(pack.manifest.assets).toHaveLength(1);
    expect(pack.cost_model.unit_contribution).toBeNull();
    expect(pack.blockers.some((b: string) => b.includes("G4"))).toBe(true);
    await page.screenshot({
      path: path.join(screenshotDir, `pack-${viewport.width}.png`),
      fullPage: true,
    });
    await page.getByRole("tab", { name: "总览", exact: true }).click();
    await page.screenshot({
      path: path.join(screenshotDir, `overview-${viewport.width}.png`),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
    const a11y = await page.evaluate(
      async () =>
        await (window as any).axe.run(document, {
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        }),
    );
    expect(
      a11y.violations.map((v: any) => ({
        id: v.id,
        description: v.description,
        nodes: v.nodes.length,
      })),
    ).toEqual([]);
    expect(errors).toEqual([]);
  });
}
test("server proxy rejects missing session and cross-origin writes", async ({
  request,
}) => {
  expect((await request.get("/api/product-cases")).status()).toBe(401);
  expect(
    (
      await request.post("/api/session", { data: { token: "invalid" } })
    ).status(),
  ).toBe(403);
});
