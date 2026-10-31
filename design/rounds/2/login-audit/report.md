# UI 检查报告

- 目标：http://127.0.0.1:3310
- 时间：2026-10-31T04:01:36.431Z
- 浏览器：playwright-chromium 156.0.8078.4
- 结论：**warn**（fail 0，warn 4）

| 检查 | 1440x900 · default | 390x844 · default |
|---|---|---|
| console-errors | ok | ok |
| failed-requests | ok | ok |
| horizontal-overflow | ok | ok |
| clipped-text | ok | ok |
| touch-target | ok | ok |
| primary-action | ok | ok |
| focus-visible | ok | ok |
| focus-hidden-stop | ok | ok |
| a11y-axe | info 0 | ok |
| font-families | ok | ok |
| off-token-colors | warn 3 | warn 3 |
| spacing-off-grid | warn 7 | warn 5 |
| gradients | info 1 | ok |

## 明细（只列非 ok 项，每项最多 8 条）

### 1440x900 · default

截图：1440x900-default.png，1440x900-default-full.png

**a11y-axe**（info） 另有 10 处对比度 axe 无法判断（渐变/图片背景、被遮挡等），需人工看：.monogram；span:nth-child(2)；.login-copy > .eyebrow

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(119, 142, 124) ×4（border）例：body > main.login-shell > div.login-brand > span.monogram；body > main.login-shell > div.login-brand > span.monogram；body > main.login-shell > div.login-brand > span.monogram
- rgb(171, 183, 167) ×4（border）例：main.login-shell > form.login-form > label > input；main.login-shell > form.login-form > label > input；main.login-shell > form.login-form > label > input
- rgb(255, 254, 246) ×1（color）例：body > main.login-shell > form.login-form > button.primary

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 115.2px ×2 例：html > body > main.login-shell {paddingRight}；html > body > main.login-shell {paddingLeft}
- 10px ×2 例：main.login-shell > form.login-form > label > input {paddingTop}；main.login-shell > form.login-form > label > input {paddingBottom}
- 18px ×2 例：body > main.login-shell > form.login-form > button.primary {paddingRight}；body > main.login-shell > form.login-form > button.primary {paddingLeft}
- 19.92px ×1 例：body > main.login-shell > form.login-form > h2 {marginBottom}

**gradients**（info）
- html > body > main.login-shell「LC LAUNCHCASE PRODUCT DEVELOPMENT / AMAZ」 @0,0,1440,900 value=linear-gradient(90deg, rgb(228, 232, 220) 54%, rgb(245, 243, 237) 54%)

清单：字体 Helvetica Neue、Georgia；字号/字重 10px/700 10px/400 12px/500 12px/400 13px/400 13px/500 14px/400 23px/400 24px/500 64px/500；颜色 7 种（不在 token 里 3 种）；圆角 4px

### 390x844 · default

截图：390x844-default.png，390x844-default-full.png

**off-token-colors**（warn） token 来源：page :root，9 个颜色 token
- rgb(119, 142, 124) ×4（border）例：body > main.login-shell > div.login-brand > span.monogram；body > main.login-shell > div.login-brand > span.monogram；body > main.login-shell > div.login-brand > span.monogram
- rgb(171, 183, 167) ×4（border）例：main.login-shell > form.login-form > label > input；main.login-shell > form.login-form > label > input；main.login-shell > form.login-form > label > input
- rgb(255, 254, 246) ×1（color）例：body > main.login-shell > form.login-form > button.primary

**spacing-off-grid**（warn） 栅格 4px，≤2px 视为光学微调不计
- 10px ×2 例：main.login-shell > form.login-form > label > input {paddingTop}；main.login-shell > form.login-form > label > input {paddingBottom}
- 18px ×2 例：body > main.login-shell > form.login-form > button.primary {paddingRight}；body > main.login-shell > form.login-form > button.primary {paddingLeft}
- 19.92px ×1 例：body > main.login-shell > form.login-form > h2 {marginBottom}

清单：字体 Helvetica Neue、Georgia；字号/字重 10px/700 10px/400 12px/500 12px/400 13px/400 13px/500 20px/400 24px/500 48px/500；颜色 9 种（不在 token 里 3 种）；圆角 4px

## 未覆盖

- 只测加载后的静态状态和键盘焦点；hover、按下、拖拽和真实任务流程没有测。
- 触点的间距豁免是近似计算；SVG 图标颜色不在颜色清单里。
- 渐变或图片上的文字对比度由 axe 标为“无法判断”的部分需要人工看。
- 这些检查只能说明“有没有错”，不能说明“好不好看”。
