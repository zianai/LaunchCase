# UI 检查报告

- 目标：design/rounds/3/workbench-render.html
- 时间：2026-10-31T04:12:17.628Z
- 浏览器：playwright-chromium 156.0.8078.4
- 结论：**warn**（fail 0，warn 6）

| 检查 | 1440x900 · default | 390x844 · default |
|---|---|---|
| console-errors | ok | ok |
| failed-requests | ok | ok |
| horizontal-overflow | ok | ok |
| clipped-text | ok | ok |
| touch-target | ok | ok |
| primary-action | warn 2 | warn 2 |
| focus-visible | ok | ok |
| focus-hidden-stop | ok | ok |
| a11y-axe | info 0 | info 0 |
| font-families | ok | ok |
| off-token-colors | warn 23 | warn 18 |
| spacing-off-grid | warn 12 | warn 12 |
| gradients | ok | ok |

## 明细（只列非 ok 项，每项最多 8 条）

### 1440x900 · default

截图：1440x900-default.png，1440x900-default-full.png

**primary-action**（warn） heuristic: 实心且与周围背景对比 ≥ 3 的按钮；首屏内 2 个
- div.app-shell > aside.sidebar > nav > button.active「◫ 产品 Cases」 @16,192,200,55 fill=rgb(233, 234, 220) contrastWithSurround=10
- section.tab-content > div.next-step > div.actions > button.primary「查看真实样品验证待办 →」 @1096,401,185,44 fill=rgb(24, 60, 52) contrastWithSurround=10.9

**a11y-axe**（info） 另有 4 处对比度 axe 无法判断（渐变/图片背景、被遮挡等），需人工看：.active > span[aria-hidden="true"]；button:nth-child(2) > span[aria-hidden="true"]；button:nth-child(3) > span[aria-hidden="true"]

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(206, 217, 207) ×9（color）例：div.app-shell > aside.sidebar > nav > button；aside.sidebar > nav > button > span；aside.sidebar > nav > button > b
- rgb(202, 208, 196) ×8（border）例：div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral
- rgb(170, 183, 165) ×8（border）例：div.overview-grid > div.gate-rail > div.gate-step > b.current-gate；div.overview-grid > div.gate-rail > div.gate-step > b.current-gate；div.overview-grid > div.gate-rail > div.gate-step > b.current-gate
- rgb(119, 142, 124) ×4（border）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram
- rgb(118, 138, 124) ×4（border）例：aside.sidebar > nav > button > b；aside.sidebar > nav > button > b；aside.sidebar > nav > button > b
- rgb(227, 213, 183) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber
- rgb(174, 184, 169) ×4（border）例：main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary
- rgb(183, 198, 187) ×3（color）例：aside.sidebar > button.brand > span > small；body > div.app-shell > aside.sidebar > div.workspace-label；div.app-shell > aside.sidebar > div.workspace-label > span

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 26px ×5 例：section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}；section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}；section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}
- 18px ×4 例：main#main > div.case-heading > button.secondary {paddingRight}；main#main > div.case-heading > button.secondary {paddingLeft}；section.tab-content > div.next-step > div.actions > button.primary {paddingRight}
- 6px ×2 例：section.tab-content > div.next-step > div.actions > button.text-button {paddingTop}；section.tab-content > div.next-step > div.actions > button.text-button {paddingBottom}
- 19.92px ×1 例：section.tab-content > div.overview-grid > div.paper.brief-paper > h2 {marginBottom}

清单：字体 Helvetica Neue、Georgia；字号/字重 8px/400 10px/700 10px/400 11px/400 11px/500 11px/700 12px/400 12px/600 13px/500 13px/400 14px/400 19px/400 20px/500 22px/400 23px/400 24px/400 24px/500 32px/500；颜色 31 种（不在 token 里 23 种）；圆角 4px

### 390x844 · default

截图：390x844-default.png，390x844-default-full.png

**primary-action**（warn） heuristic: 实心且与周围背景对比 ≥ 3 的按钮；首屏内 2 个
- div.app-shell > aside.sidebar > nav > button.active「◫ 产品 Cases」 @16,84,94,44 fill=rgb(233, 234, 220) contrastWithSurround=10
- section.tab-content > div.next-step > div.actions > button.primary「查看真实样品验证待办 →」 @20,617,185,44 fill=rgb(24, 60, 52) contrastWithSurround=10.9

**a11y-axe**（info） 另有 10 处对比度 axe 无法判断（渐变/图片背景、被遮挡等），需人工看：.active > span[aria-hidden="true"]；button:nth-child(2) > span[aria-hidden="true"]；button:nth-child(3) > span[aria-hidden="true"]

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(206, 217, 207) ×9（color）例：div.app-shell > aside.sidebar > nav > button；aside.sidebar > nav > button > span；div.app-shell > aside.sidebar > nav > button
- rgb(202, 208, 196) ×8（border）例：div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral
- rgb(170, 183, 165) ×8（border）例：div.overview-grid > div.gate-rail > div.gate-step > b.current-gate；div.overview-grid > div.gate-rail > div.gate-step > b.current-gate；div.overview-grid > div.gate-rail > div.gate-step > b.current-gate
- rgb(119, 142, 124) ×4（border）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram
- rgb(227, 213, 183) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber
- rgb(174, 184, 169) ×4（border）例：main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary
- rgb(255, 255, 255) ×3（color）例：div.overview-grid > div.gate-rail > div.gate-step > b.complete；div.overview-grid > div.gate-rail > div.gate-step > b.complete；div.overview-grid > div.gate-rail > div.gate-step > b.complete
- rgb(255, 248, 230) ×2（color）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 26px ×5 例：section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}；section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}；section.tab-content > div.overview-grid > div.gate-rail > div.gate-step {paddingBottom}
- 6px ×4 例：main#main > div.case-heading > div > div.heading-badges {rowGap}；main#main > div.case-heading > div > div.heading-badges {columnGap}；section.tab-content > div.next-step > div.actions > button.text-button {paddingTop}
- 18px ×2 例：section.tab-content > div.next-step > div.actions > button.primary {paddingRight}；section.tab-content > div.next-step > div.actions > button.primary {paddingLeft}
- 19.92px ×1 例：section.tab-content > div.overview-grid > div.paper.brief-paper > h2 {marginBottom}

清单：字体 Helvetica Neue、Georgia；字号/字重 7px/400 9px/400 10px/400 10px/700 11px/400 11px/500 11px/700 12px/600 12px/400 13px/500 13px/400 14px/400 15px/400 18px/500 20px/400 22px/400 24px/500；颜色 26 种（不在 token 里 18 种）；圆角 4px

## 未覆盖

- 只测加载后的静态状态和键盘焦点；hover、按下、拖拽和真实任务流程没有测。
- 触点的间距豁免是近似计算；SVG 图标颜色不在颜色清单里。
- 渐变或图片上的文字对比度由 axe 标为“无法判断”的部分需要人工看。
- 这些检查只能说明“有没有错”，不能说明“好不好看”。
