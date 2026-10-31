import { test, expect } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
const seedDir = process.env.LAUNCHCASE_P8_SEED!;
const seed = JSON.parse(
  readFileSync(path.join(seedDir, "manifest.json"), "utf8"),
);
const out = process.env.LAUNCHCASE_SCREENSHOT_DIR!;

test("SKU originals, rights, strict HTTP composition, independent review and internal pack", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await page
    .getByLabel("本地身份凭证")
    .fill(readFileSync(path.join(seedDir, "token"), "utf8"));
  await page.getByRole("button", { name: "进入工作区 →" }).click();
  await page.locator(".case-row").first().click();
  await page.getByRole("tab", { name: "用户反馈研究", exact: true }).click();
  await page
    .getByText("核验洞察来源与运行版本", { exact: true })
    .first()
    .click();
  await expect(
    page.getByText("来源定位有效 · 人工判断仍待评审").first(),
  ).toBeVisible();
  await expect(page.getByText(/deterministic-sdk-test/).first()).toBeVisible();
  await page.screenshot({
    path: path.join(out, "provenance-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: "图片与素材", exact: true }).click();
  const rights = page.getByLabel(
    "我有权导入此原图，且权利证明允许向本地图片服务传输；这不批准发布",
  );
  await expect(rights).not.toBeChecked();
  await expect(
    page.getByRole("button", { name: "创建严格保真计划（仍待计划审批）" }),
  ).toBeDisabled();
  for (const [filename, kind] of [
    ["TEST-ONLY-original.png", "product_photo"],
    ["TEST-ONLY-cutout.png", "cutout"],
  ]) {
    const form = page.locator(".sku-form");
    if (!(await form.isVisible()))
      await page.getByText("上传产品照片或透明抠图", { exact: true }).click();
    await page
      .getByLabel("SKU / 样品编号", { exact: true })
      .fill(seed.upload.sku);
    await page.getByLabel("原图用途").selectOption(kind);
    await page
      .getByLabel("图片文件", { exact: true })
      .setInputFiles(path.join(seedDir, filename));
    await page
      .getByLabel("权利证明来源")
      .selectOption(seed.upload.rights.source_id);
    await page
      .getByLabel("权利原文摘录")
      .fill(seed.upload.rights.exact_excerpt);
    await page
      .getByLabel("权利复核截止时间")
      .fill(seed.upload.rights.expires_at_utc.slice(0, 16));
    await rights.check();
    await page
      .getByRole("button", { name: "保存原始素材，等待独立审核" })
      .click();
    const article = page.locator(".sku-source").filter({ hasText: filename });
    await expect(article).toBeVisible();
    await expect(rights).not.toBeChecked();
    await article.getByRole("button", { name: "审核原始素材" }).click();
    await expect(article.getByLabel("原图审核决定")).toHaveValue("rejected");
    await article.getByLabel("原图审核决定").selectOption("approved");
    await article
      .getByLabel("原图审核理由")
      .fill(
        "TEST ONLY fictional original and rights review; no business or publication approval.",
      );
    await article.getByRole("button", { name: "记录原图决定" }).click();
    await expect(
      article.getByText("原图审核有效；仍需样品、事实和规则"),
    ).toBeVisible();
    await article.getByLabel("用于严格保真计划").check();
  }
  await page.getByLabel("本次适用规则").selectOption(seed.rule.id);
  await page
    .getByRole("button", { name: "创建严格保真计划（仍待计划审批）" })
    .click();
  await page.getByRole("button", { name: "审核计划", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("理由与适用边界")
    .fill(
      "TEST ONLY deterministic strict composition, no paid API, no publication.",
    );
  await page.getByRole("button", { name: "记录人工决定" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByRole("button", { name: "执行已批准计划" }).click();
  for (
    let i = 0;
    i < 20 &&
    !(await page.getByRole("button", { name: "审核这张图片" }).count());
    i++
  ) {
    const refresh = page.getByRole("button", { name: "刷新制作进度" });
    if (await refresh.count()) await refresh.click();
    await page.waitForTimeout(250);
  }
  await expect(page.getByText("原图确定性合成 · 仅内部")).toBeVisible();
  await page.getByRole("button", { name: "审核这张图片" }).click();
  await page
    .getByRole("dialog")
    .getByLabel("理由与适用边界")
    .fill(
      "TEST ONLY asset-byte review for internal use, not product or publication approval.",
    );
  await page.getByRole("button", { name: "记录人工决定" }).click();
  await expect(
    page.getByText("已批准内部使用", { exact: false }),
  ).toBeVisible();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    await page.screenshot({
      path: path.join(out, `sku-${width}.png`),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  const a11y = await page.evaluate(async () => (window as any).axe.run());
  writeFileSync(
    path.join(out, "accessibility.json"),
    JSON.stringify(a11y.violations, null, 2),
  );
  expect(
    a11y.violations.filter((x: any) =>
      ["critical", "serious"].includes(x.impact),
    ),
  ).toEqual([]);
  await page.getByRole("tab", { name: "内部交接资料", exact: true }).click();
  await page
    .getByRole("button", { name: "生成内部交接资料", exact: true })
    .click();
  await expect(page.getByRole("link", { name: "下载 JSON ↗" })).toBeVisible();
  const pack = await page.request.get(
    (await page
      .getByRole("link", { name: "下载 JSON ↗" })
      .getAttribute("href"))!,
  );
  expect(pack.status()).toBe(200);
  expect((await pack.json()).publishable).not.toBe(true);
  writeFileSync(
    path.join(out, "scope.json"),
    JSON.stringify(
      {
        scope:
          "E1 TEST ONLY real-mode contracts, fictional image; no business review",
        case_id: seed.case_id,
        viewport_widths: [1440, 390],
        paid_calls: 0,
        design_approval: "pending",
      },
      null,
      2,
    ),
  );
  expect(errors).toEqual([]);
});
