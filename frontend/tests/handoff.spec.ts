import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
const root = path.resolve(__dirname, "../..");
const handoffDir =
  process.env.LAUNCHCASE_HANDOFF_DIR ||
  path.join(root, ".launchcase/handoff-e2e");
const seed = JSON.parse(
  readFileSync(path.join(handoffDir, "manifest.json"), "utf8"),
);
const refs = JSON.parse(
  readFileSync(
    path.join(root, "fixtures/public-references/manifest.json"),
    "utf8",
  ),
);
const output = path.resolve(
  root,
  process.env.LAUNCHCASE_SCREENSHOT_DIR || "docs/evidence/g4-g5",
);
mkdirSync(output, { recursive: true });
test("G4 and G5 forms, exact approvals, receipt and responsive states", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await page
    .getByLabel("本地身份凭证")
    .fill(readFileSync(path.join(handoffDir, "token"), "utf8").trim());
  await page.getByRole("button", { name: "进入工作区 →" }).click();
  await page.locator(".case-row").first().click();
  await page.getByRole("tab", { name: "样品与交接", exact: true }).click();
  await page
    .getByLabel("样品原始记录")
    .selectOption(seed.sample.facts[0].source_id);
  await page
    .getByLabel("样品编号 / SKU / 批次")
    .fill(seed.sample.sample_identifier);
  await page.getByLabel("测试方法与判定范围").fill(seed.sample.test_method);
  await page.getByLabel("第 1 条事实名称").fill("width");
  await page.getByLabel("第 1 条实测值").fill("40 cm");
  await page
    .getByLabel("第 1 条原文摘录")
    .fill(seed.sample.facts[0].exact_excerpt);
  await page.getByLabel("测试时间", { exact: true }).fill("2026-10-01T10:00");
  await page
    .getByLabel("测试负责人", { exact: true })
    .fill("TEST ONLY operator");
  await page
    .getByLabel("限制、未测项目与不通过项")
    .fill(seed.sample.limitations);
  // A second row must be validated on its own before anything is submitted.
  await page.getByRole("button", { name: "＋ 增加一条事实" }).click();
  await page.getByLabel("第 2 条事实名称").fill("宽度复测");
  await page.getByLabel("第 2 条实测值").fill("41 cm");
  await page
    .getByLabel("第 2 条原文摘录")
    .fill(seed.sample.facts[0].exact_excerpt);
  await page.getByRole("button", { name: "保存样品记录，等待审核" }).click();
  await expect(page.getByText("原文摘录必须包含这个实测值")).toBeVisible();
  await page.getByLabel("第 2 条实测值").fill("40 cm");
  await expect(page.getByText("原文摘录必须包含这个实测值")).toHaveCount(0);
  await page.getByRole("button", { name: "保存样品记录，等待审核" }).click();
  await expect(page.getByText("宽度复测: 40 cm")).toBeVisible();
  await page.getByRole("button", { name: "审核样品记录" }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("combobox", { name: "决定", exact: true }),
  ).toHaveValue("hold");
  await page
    .getByRole("dialog")
    .getByRole("combobox", { name: "决定", exact: true })
    .selectOption("verify_sample");
  await page
    .getByLabel("理由与适用边界")
    .fill("TEST ONLY isolated contract approval, no real business evidence.");
  await page.getByRole("button", { name: "记录人工决定" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByRole("tab", { name: "证据来源", exact: true }).click();
  await page.getByLabel("资料类型").selectOption("rule");
  await page.getByLabel("这是合成测试资料").uncheck();
  await page.getByLabel("我有权导入并用于内部研究").check();
  await page
    .getByLabel("来源 URL（规则必填；样品原始记录留空）")
    .fill(refs.references[0].url);
  await page
    .getByLabel("导入来源文件")
    .setInputFiles(
      path.join(root, "fixtures/public-references", refs.references[0].file),
    );
  await expect(
    page.getByText(refs.references[0].file, { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "样品与交接", exact: true }).click();
  const select = page.getByLabel("官方规则来源");
  await select.selectOption({ label: refs.references[0].file });
  await page
    .getByLabel("规则版本", { exact: true })
    .fill("TEST ONLY reviewed reference");
  await page
    .getByLabel("规则原文摘录", { exact: true })
    .fill(
      readFileSync(
        path.join(root, "fixtures/public-references", refs.references[0].file),
        "utf8",
      ).trim(),
    );
  await page.getByLabel("生效时间", { exact: true }).fill("2026-10-01T10:00");
  await page.getByLabel("复核截止时间").fill("2027-01-01T10:00");
  await page
    .getByLabel("对本品类的适用理由与未覆盖范围")
    .fill(
      "TEST ONLY: internal advertising claim review; product compliance is not established.",
    );
  await page.getByRole("button", { name: "记录规则适用性复核" }).click();
  await expect(
    page.getByText("TEST ONLY reviewed reference", { exact: false }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "内部交接资料", exact: true }).click();
  await page
    .getByRole("button", { name: "生成内部交接资料", exact: true })
    .click();
  await expect(page.getByRole("link", { name: "下载 JSON ↗" })).toBeVisible();
  await page.getByRole("tab", { name: "样品与交接", exact: true }).click();
  await page.getByLabel("交接包版本").selectOption({ index: 1 });
  await page.getByLabel(/TEST ONLY reviewed reference/).check();
  await page
    .getByLabel("交接负责人", { exact: true })
    .fill("TEST ONLY handoff owner");
  await page
    .getByLabel("成本缺口、风险处置、责任人与后续行动")
    .fill(
      "TEST ONLY owner must obtain all real quotes, validate all costs and investigate all risks before business use.",
    );
  await page
    .getByLabel("未验证及禁止对外使用的声明")
    .fill(
      "No real sample exists. No claims of safety, performance, demand or certification are approved.",
    );
  await page
    .getByLabel("本次仅内部交接；模拟素材不具有外部使用权，不批准发布")
    .check();
  await page.getByRole("button", { name: "保存交接材料，等待审核" }).click();
  await page.getByRole("button", { name: "审核内部交接" }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("combobox", { name: "决定", exact: true }),
  ).toHaveValue("needs_changes");
  await page
    .getByRole("dialog")
    .getByRole("combobox", { name: "决定", exact: true })
    .selectOption("internal_handoff");
  await page
    .getByLabel("理由与适用边界")
    .fill(
      "TEST ONLY isolated software approval. Publication remains unavailable.",
    );
  await page.getByRole("button", { name: "记录人工决定" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("link", { name: "查看内部交接批准回执 ↗" }),
  ).toBeVisible();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    await page
      .getByRole("heading", { name: "把实测事实与交接责任放在一起。" })
      .scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(output, `handoff-${width}.png`),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  const a11y = await page.evaluate(async () => (window as any).axe.run());
  writeFileSync(
    path.join(output, "accessibility.json"),
    JSON.stringify(a11y.violations, null, 2),
  );
  expect(
    a11y.violations.filter((v: any) =>
      ["critical", "serious"].includes(v.impact),
    ),
  ).toEqual([]);
  const html = await page.evaluate(() => {
    const clone = document.documentElement.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("script,link").forEach((e) => e.remove());
    const style = document.createElement("style");
    style.textContent = Array.from(document.styleSheets)
      .map((s) =>
        Array.from(s.cssRules)
          .map((r) => r.cssText)
          .join("\n"),
      )
      .join("\n");
    clone.querySelector("head")!.append(style);
    return "<!doctype html>" + clone.outerHTML;
  });
  writeFileSync(path.join(output, "handoff-render.html"), html);
  const link = await page
    .getByRole("link", { name: "查看内部交接批准回执 ↗" })
    .getAttribute("href");
  const receipt = await page.request.get(link!);
  expect(receipt.status()).toBe(200);
  expect((await receipt.json()).publishable).toBe(false);
  const download = await page
    .getByRole("link", { name: "下载完整内部交接包 ZIP ↗" })
    .getAttribute("href");
  const bundle = await page.request.get(download!);
  expect(bundle.status()).toBe(200);
  expect(bundle.headers()["content-type"]).toContain("application/zip");
  expect(errors).toEqual([]);
});
