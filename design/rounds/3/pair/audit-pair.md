# 自动检查对照（A / B）

每格为 级别 + 数量；fail 是硬伤，warn 需要看，info 只是清单。

## 1440x900-default

| 检查 | A | B |
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
| off-token-colors | warn 23 | warn 23 |
| spacing-off-grid | warn 12 | warn 12 |
| gradients | ok | ok |

## 390x844-default

| 检查 | A | B |
|---|---|---|
| console-errors | ok | ok |
| failed-requests | ok | ok |
| horizontal-overflow | ok | ok |
| clipped-text | ok | ok |
| touch-target | warn 10 | ok |
| primary-action | warn 2 | warn 2 |
| focus-visible | ok | ok |
| focus-hidden-stop | ok | ok |
| a11y-axe | info 0 | info 0 |
| font-families | ok | ok |
| off-token-colors | warn 18 | warn 18 |
| spacing-off-grid | warn 12 | warn 12 |
| gradients | ok | ok |

并排图：
- 1440x900-default-first.png
- 1440x900-default-full.png
- 390x844-default-first.png
- 390x844-default-full.png
