# UI 检查报告

- 目标：docs/evidence/g4-g5/handoff-render.html
- 时间：2026-10-31T05:04:51.131Z
- 浏览器：playwright-chromium 156.0.8078.4
- 结论：**fail**（fail 4，warn 4）

| 检查 | 1440x900 · default | 390x844 · default |
|---|---|---|
| console-errors | ok | ok |
| failed-requests | ok | ok |
| horizontal-overflow | ok | ok |
| clipped-text | ok | ok |
| touch-target | fail 2 | fail 2 |
| primary-action | ok | ok |
| focus-visible | ok | ok |
| focus-hidden-stop | ok | ok |
| a11y-axe | fail 2 | fail 2 |
| font-families | ok | ok |
| off-token-colors | warn 23 | warn 18 |
| spacing-off-grid | warn 17 | warn 17 |
| gradients | ok | ok |

## 明细（只列非 ok 项，每项最多 8 条）

### 1440x900 · default

截图：1440x900-default.png，1440x900-default-full.png

**touch-target**（fail） 小于 24px 且与相邻控件过近（WCAG 2.2 AA 2.5.8）
- div#g4-sample > details > summary「录入新的样品记录」 @305,750,1062,20 size=1062×20
- div#g4-sample > details > summary「导入完整样品确认 JSON（多条事实）」 @305,769,1062,20 size=1062×20

**a11y-axe**（fail） 另有 4 处对比度 axe 无法判断（渐变/图片背景、被遮挡等），需人工看：.active > span[aria-hidden="true"]；button:nth-child(2) > span[aria-hidden="true"]；button:nth-child(3) > span[aria-hidden="true"]
- target-size（serious，2 处）：All touch targets must be 24px large, or leave sufficient space — #g4-sample > details:nth-child(3) > summary；details:nth-child(4) > summary

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(174, 184, 169) ×24（border）例：main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary
- rgb(206, 217, 207) ×9（color）例：div.app-shell > aside.sidebar > nav > button；aside.sidebar > nav > button > span；aside.sidebar > nav > button > b
- rgb(119, 142, 124) ×4（border）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram
- rgb(118, 138, 124) ×4（border）例：aside.sidebar > nav > button > b；aside.sidebar > nav > button > b；aside.sidebar > nav > button > b
- rgb(227, 213, 183) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber
- rgb(202, 208, 196) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral
- rgb(183, 198, 187) ×3（color）例：aside.sidebar > button.brand > span > small；body > div.app-shell > aside.sidebar > div.workspace-label；div.app-shell > aside.sidebar > div.workspace-label > span
- rgb(255, 248, 230) ×2（color）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 18px ×12 例：main#main > div.case-heading > button.secondary {paddingRight}；main#main > div.case-heading > button.secondary {paddingLeft}；div#g4-sample > article > button.secondary {paddingRight}
- 18.62px ×4 例：div#g4-sample > article > h4 {marginTop}；div#g4-sample > article > h4 {marginBottom}；section.tab-content > div.paper.handoff-section > article > h4 {marginTop}
- 19.92px ×1 例：main#main > section.tab-content > h2 {marginBottom}

清单：字体 Helvetica Neue、Georgia；字号/字重 8px/400 10px/700 10px/400 11px/400 12px/400 12px/600 13px/500 14px/400 14px/700 19px/400 20px/500 23px/400 24px/400 24px/500 32px/500；颜色 30 种（不在 token 里 23 种）；圆角 4px

### 390x844 · default

截图：390x844-default.png，390x844-default-full.png

**touch-target**（fail） 小于 24px 且与相邻控件过近（WCAG 2.2 AA 2.5.8）
- div#g4-sample > details > summary「录入新的样品记录」 @45,1049,300,20 size=300×20
- div#g4-sample > details > summary「导入完整样品确认 JSON（多条事实）」 @45,1068,300,20 size=300×20

**a11y-axe**（fail） 另有 11 处对比度 axe 无法判断（渐变/图片背景、被遮挡等），需人工看：.active > span[aria-hidden="true"]；button:nth-child(2) > span[aria-hidden="true"]；button:nth-child(3) > span[aria-hidden="true"]
- target-size（serious，2 处）：All touch targets must be 24px large, or leave sufficient space — #g4-sample > details:nth-child(3) > summary；details:nth-child(4) > summary

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(174, 184, 169) ×24（border）例：main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary；main#main > div.case-heading > button.secondary
- rgb(206, 217, 207) ×9（color）例：div.app-shell > aside.sidebar > nav > button；aside.sidebar > nav > button > span；div.app-shell > aside.sidebar > nav > button
- rgb(119, 142, 124) ×4（border）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span.monogram
- rgb(227, 213, 183) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber；div.case-heading > div > div.heading-badges > span.badge.amber
- rgb(202, 208, 196) ×4（border）例：div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral；div.case-heading > div > div.heading-badges > span.badge.neutral
- rgb(255, 248, 230) ×2（color）例：div.app-shell > aside.sidebar > button.brand > span.monogram；div.app-shell > aside.sidebar > button.brand > span
- rgb(183, 198, 187) ×1（color）例：aside.sidebar > button.brand > span > small
- rgb(233, 234, 220) ×1（background）例：div.app-shell > aside.sidebar > nav > button.active

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 18px ×6 例：div#g4-sample > article > button.secondary {paddingRight}；div#g4-sample > article > button.secondary {paddingLeft}；section.tab-content > div.paper.handoff-section > article > button.secondary {paddingRight}
- 18.62px ×4 例：div#g4-sample > article > h4 {marginTop}；div#g4-sample > article > h4 {marginBottom}；section.tab-content > div.paper.handoff-section > article > h4 {marginTop}
- 10px ×4 例：section.tab-content > div.paper.handoff-section > p > a.download {paddingTop}；section.tab-content > div.paper.handoff-section > p > a.download {paddingBottom}；main#main > section.tab-content > div.paper.handoff-section > a.download {paddingTop}
- 6px ×2 例：main#main > div.case-heading > div > div.heading-badges {rowGap}；main#main > div.case-heading > div > div.heading-badges {columnGap}
- 19.92px ×1 例：main#main > section.tab-content > h2 {marginBottom}

清单：字体 Helvetica Neue、Georgia；字号/字重 7px/400 9px/400 10px/400 10px/700 11px/400 11px/500 12px/400 12px/600 13px/500 14px/400 14px/700 15px/400 20px/400 20px/500 22px/400 24px/500；颜色 25 种（不在 token 里 18 种）；圆角 4px

## 未覆盖

- 只测加载后的静态状态和键盘焦点；hover、按下、拖拽和真实任务流程没有测。
- 触点的间距豁免是近似计算；SVG 图标颜色不在颜色清单里。
- 渐变或图片上的文字对比度由 axe 标为“无法判断”的部分需要人工看。
- 这些检查只能说明“有没有错”，不能说明“好不好看”。
