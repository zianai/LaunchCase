# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.spec.ts >> real API full internal workflow 1440px
- Location: tests/workbench.spec.ts:15:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('img')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('img') with timeout 5000ms
  - waiting for getByRole('img')

```

```yaml
- alert
- link "跳至主要内容":
  - /url: "#main"
- complementary:
  - button "LC LaunchCase 产品开发工作台"
  - text: 产品工作区
  - navigation "主导航":
    - button "产品项目"
    - button "审核收件箱 2"
    - button "来源与知识"
    - button "图片与素材"
    - button "能力与设置"
  - text: 默认离线
  - paragraph: 先核实，再决策。 概念不等于产品事实。
  - button "退出本地会话 ↗"
- main:
  - text: "工作台 / [SYNTHETIC] US Pet Furniture: Easier Assembly 本地连接 | 亚马逊美国站 · 差异化开发"
  - paragraph: 产品项目
  - 'heading "[SYNTHETIC] US Pet Furniture: Easier Assembly" [level=1]'
  - text: 合成数据 / 功能测试 需求第 1 版 · 第 10 次修订
  - button "↻ 刷新"
  - paragraph: 当前阶段 · G4
  - heading "验证样品" [level=2]
  - paragraph: 可以先整理内部交接资料，真实样品验证仍需完成。
  - button "准备内部交接资料 →"
  - tablist "项目内容":
    - tab "总览"
    - tab "证据来源"
    - tab "用户反馈研究"
    - tab "产品机会"
    - tab "产品方案与规格"
    - tab "图片与素材" [selected]
    - tab "成本与风险"
    - tab "样品与交接"
    - tab "内部交接资料"
    - tab "变更记录"
  - tabpanel "图片与素材":
    - region "SKU 原图与授权":
      - paragraph: 原始素材 → 真实产品事实 → 严格保真
      - heading "SKU 原图与授权" [level=3]
      - paragraph: 原图、概念图与生成图分别保存。图片审核、样品确认和内部交接是独立决定；这里不授权发布。 当前为合成测试项目，不能升级为真实 SKU。
      - group:
        - text: 上传产品照片或透明抠图 SKU / 样品编号
        - textbox "SKU / 样品编号"
        - text: 原图用途
        - combobox "原图用途":
          - option "产品原始照片" [selected]
          - option "透明抠图（保持产品结构）"
          - option "授权 Logo"
        - text: 图片文件
        - button "图片文件"
        - paragraph: 上限 1 MiB / 800 万像素。浏览器计算原始文件哈希，服务端校验解码内容；预览移除图片元数据。
        - text: 权利证明来源
        - combobox "权利证明来源":
          - option "先在「证据来源」导入素材权利证明" [selected]
        - text: 权利原文摘录
        - textbox "权利原文摘录"
        - text: 权利复核截止时间
        - textbox "权利复核截止时间"
        - checkbox "我有权导入此原图，且权利证明允许向本地图片服务传输；这不批准发布"
        - text: 我有权导入此原图，且权利证明允许向本地图片服务传输；这不批准发布
        - button "保存原始素材，等待独立审核" [disabled]
      - heading "严格保真商品素材计划" [level=4]
      - paragraph: 当前样品：未确认 · 事实快照：未确认 · 仅确定性复用或合成。
      - text: 本次适用规则
      - combobox "本次适用规则":
        - option "选择已复核规则" [selected]
      - status: 需要当前 G2、G4、事实快照、适用规则及已审核透明抠图。缺项时不会改用概念生成。
      - button "创建严格保真计划（仍待计划审批）" [disabled]
    - paragraph: 概念图片 · 仅内部使用
    - heading "把想法看清，别把图像当事实。" [level=2]
    - button "＋ 创建概念图片计划"
    - paragraph: 仅内部使用 · 模拟制作 · 不产生费用 · 计划批准与图片审核分别进行
    - article:
      - text: 制作中
      - 'heading "Internal concept exploration: Keyed panels and captive connectors to reduce alignment steps. No verified product performance claims." [level=3]'
      - group: 技术信息
      - button "刷新制作进度"
  - text: LaunchCase 证据、推断、假设和决定，各有边界。 内部工作区
```

# Test source

```ts
  33  |     let dialog = page.getByRole("dialog");
  34  |     await dialog.getByRole("button", { name: "载入合成宠物家具示例" }).click();
  35  |     await dialog.getByRole("button", { name: "创建项目", exact: true }).click();
  36  |     await expect(page.getByRole("tab", { name: "证据来源" })).toHaveAttribute(
  37  |       "aria-selected",
  38  |       "true",
  39  |     );
  40  |     await page.getByLabel("我有权导入并用于内部研究").check();
  41  |     for (const [file, type] of [
  42  |       ["synthetic-voc.csv", "review"],
  43  |       ["synthetic-competitors.csv", "competitor"],
  44  |       ["synthetic-quote.json", "quote"],
  45  |     ]) {
  46  |       await page.getByLabel("资料类型").selectOption(type);
  47  |       await page
  48  |         .getByLabel("导入来源文件")
  49  |         .setInputFiles(path.join(fixture, file));
  50  |       await expect(page.getByText(file, { exact: true })).toBeVisible();
  51  |     }
  52  |     await page
  53  |       .getByRole("button")
  54  |       .filter({ hasText: "The screws were hard to align during assembly." })
  55  |       .first()
  56  |       .click();
  57  |     await expect(page.locator("blockquote")).toHaveText(
  58  |       "The screws were hard to align during assembly.",
  59  |     );
  60  |     await page.getByRole("tab", { name: "用户反馈研究" }).click();
  61  |     await page.getByRole("button", { name: "运行研究", exact: true }).click();
  62  |     await expect(
  63  |       page.getByText("用户反馈存在分歧", { exact: true }),
  64  |     ).toBeVisible();
  65  |     await page.getByRole("tab", { name: "产品机会", exact: true }).click();
  66  |     await page
  67  |       .locator("article.opportunity")
  68  |       .filter({ hasText: "Reduce assembly friction" })
  69  |       .getByRole("button", { name: "审核机会" })
  70  |       .click();
  71  |     dialog = page.getByRole("dialog");
  72  |     await dialog
  73  |       .getByLabel("理由与适用边界")
  74  |       .fill(
  75  |         "SYNTHETIC TEST ONLY: investigate assembly hypothesis; no commercial approval.",
  76  |       );
  77  |     await dialog.getByRole("button", { name: "记录人工决定" }).click();
  78  |     await expect(dialog).not.toBeVisible();
  79  |     await page
  80  |       .getByRole("button", { name: "从选中机会生成产品方案 →" })
  81  |       .click();
  82  |     await expect(page.getByRole("status")).toContainText("G2");
  83  |     await page.getByRole("tab", { name: "产品方案与规格" }).click();
  84  |     await expect(page.locator("article.concept")).toHaveCount(2);
  85  |     await page
  86  |       .locator("article.concept")
  87  |       .first()
  88  |       .getByRole("button", { name: "审核方案" })
  89  |       .click();
  90  |     await page
  91  |       .getByRole("dialog")
  92  |       .getByLabel("理由与适用边界")
  93  |       .fill(
  94  |         "SYNTHETIC TEST ONLY: choose proposal, dimensions and performance remain unknown.",
  95  |       );
  96  |     await page
  97  |       .getByRole("dialog")
  98  |       .getByRole("button", { name: "记录人工决定" })
  99  |       .click();
  100 |     await expect(page.getByRole("dialog")).not.toBeVisible();
  101 |     await page.getByRole("tab", { name: "成本与风险", exact: true }).click();
  102 |     await page.getByRole("button", { name: "核算成本", exact: true }).click();
  103 |     await expect(page.getByText("资料不足，无法计算")).toBeVisible();
  104 |     await page
  105 |       .getByRole("button", { name: "审核成本与样品验证", exact: true })
  106 |       .click();
  107 |     await page
  108 |       .getByRole("dialog")
  109 |       .getByLabel("理由与适用边界")
  110 |       .fill(
  111 |         "SYNTHETIC TEST ONLY: sample investigation only, no viability conclusion.",
  112 |       );
  113 |     await page
  114 |       .getByRole("dialog")
  115 |       .getByRole("button", { name: "记录人工决定" })
  116 |       .click();
  117 |     await expect(page.getByRole("dialog")).not.toBeVisible();
  118 |     await page.getByRole("tab", { name: "图片与素材", exact: true }).click();
  119 |     await page.getByRole("button", { name: "＋ 创建概念图片计划" }).click();
  120 |     await page.getByRole("button", { name: "审核计划", exact: true }).click();
  121 |     await page
  122 |       .getByRole("dialog")
  123 |       .getByLabel("理由与适用边界")
  124 |       .fill(
  125 |         "SYNTHETIC TEST ONLY: zero-budget Mock, internal visual exploration.",
  126 |       );
  127 |     await page
  128 |       .getByRole("dialog")
  129 |       .getByRole("button", { name: "记录人工决定" })
  130 |       .click();
  131 |     await expect(page.getByRole("dialog")).not.toBeVisible();
  132 |     await page.getByRole("button", { name: "执行已批准计划" }).click();
> 133 |     await expect(page.getByRole("img")).toBeVisible();
      |                                         ^ Error: expect(locator).toBeVisible() failed
  134 |     await expect(page.getByText("人工审核：待独立审核")).toBeVisible();
  135 |     await page.getByRole("button", { name: "审核这张图片" }).click();
  136 |     await page
  137 |       .getByRole("dialog")
  138 |       .getByLabel("理由与适用边界")
  139 |       .fill(
  140 |         "SYNTHETIC TEST ONLY: fixed Mock raster approved for internal fixture pack.",
  141 |       );
  142 |     await page
  143 |       .getByRole("dialog")
  144 |       .getByRole("button", { name: "记录人工决定" })
  145 |       .click();
  146 |     await expect(page.getByRole("dialog")).not.toBeVisible();
  147 |     await expect(page.getByText("人工审核：已批准内部使用")).toBeVisible();
  148 |     await page.screenshot({
  149 |       path: path.join(screenshotDir, `visual-${viewport.width}.png`),
  150 |       fullPage: true,
  151 |     });
  152 |     await page.getByRole("tab", { name: "内部交接资料", exact: true }).click();
  153 |     await page.getByRole("button", { name: "生成内部交接资料" }).click();
  154 |     await expect(page.getByText("不可发布", { exact: true })).toBeVisible();
  155 |     const url = await page
  156 |       .getByRole("link", { name: "下载 JSON ↗" })
  157 |       .getAttribute("href");
  158 |     const response = await page.request.get(url!);
  159 |     expect(response.ok()).toBeTruthy();
  160 |     const pack = await response.json();
  161 |     expect(pack.publishable).toBe(false);
  162 |     expect(pack.manifest.assets).toHaveLength(1);
  163 |     expect(pack.cost_model.unit_contribution).toBeNull();
  164 |     expect(pack.blockers.some((b: string) => b.includes("G4"))).toBe(true);
  165 |     await page.screenshot({
  166 |       path: path.join(screenshotDir, `pack-${viewport.width}.png`),
  167 |       fullPage: true,
  168 |     });
  169 |     await page.getByRole("tab", { name: "总览", exact: true }).click();
  170 |     await page.screenshot({
  171 |       path: path.join(screenshotDir, `overview-${viewport.width}.png`),
  172 |       fullPage: true,
  173 |     });
  174 |     expect(
  175 |       await page.evaluate(
  176 |         () => document.documentElement.scrollWidth <= window.innerWidth,
  177 |       ),
  178 |     ).toBe(true);
  179 |     await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  180 |     const a11y = await page.evaluate(
  181 |       async () =>
  182 |         await (window as any).axe.run(document, {
  183 |           runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
  184 |         }),
  185 |     );
  186 |     expect(
  187 |       a11y.violations.map((v: any) => ({
  188 |         id: v.id,
  189 |         description: v.description,
  190 |         nodes: v.nodes.length,
  191 |       })),
  192 |     ).toEqual([]);
  193 |     expect(errors).toEqual([]);
  194 |   });
  195 | }
  196 | test("server proxy rejects missing session and cross-origin writes", async ({
  197 |   request,
  198 | }) => {
  199 |   expect((await request.get("/api/product-cases")).status()).toBe(401);
  200 |   expect(
  201 |     (
  202 |       await request.post("/api/session", { data: { token: "invalid" } })
  203 |     ).status(),
  204 |   ).toBe(403);
  205 | });
  206 | 
```