# LaunchCase V1 — Codex 启动指令（可直接粘贴）

> 本交接包是**工程规格与测试数据种子**，不是已实现的 LaunchCase 代码。用户授权的是输出实施方案；收到这份方案后，Codex 在用户提供/选择的独立 LaunchCase 工作区实施。不要未经授权创建远程 GitHub 仓库、修改 TradeCase/CreativeEngine，或调用付费/登录服务。

你是 LaunchCase 的工程负责人。请按 `IMPLEMENTATION_SPEC.md`、`PHASE_PLAN.md`、`CONTRACTS_AND_SCENARIOS.md`、`AGENTS.md`、`docs/ARCHITECTURE_DECISIONS.md` 实施 **P0 → P6**，不是只写规划、做原型或停止在脚手架。

## 必须理解的产品目标

LaunchCase 是面向跨境 B2C **差异化产品开发**的 Case 工作台（V1 以 Amazon US 一般消费品为目标上下文）。它的核心闭环是：

`ProductBrief → Evidence → VOC/Market Insights → Opportunity → Concept → Versioned ProductSpec → Feasibility → Human Gates → Visual Assets → Internal Draft LaunchPack`

不是通用选品排行榜、聊天机器人、ERP、自动上架工具或 AI 生图网站。设计成果是有出处、可否决、可回退的产品决策，而不是一份漂亮但无法验证的分析报告。没有样品/认证/授权时，不得宣称 Listing Ready 或真实上市完成；可交付 **Internal Draft LaunchPack / Ready for Sample Validation**。

## 开始前先核对，不要猜

1. 只读检查 `https://github.com/zianai/TradeCase` 的 `main` 与 `codex/tradecase-visual-tasks`，特别是 `AGENTS.md`、`project/state.yaml`、`docs/architecture/adr-001-platform-boundaries.md`、`docs/architecture/adr-005-visual-domain.md`、`docs/VISUAL_TASKS.md`、`docs/VISUAL_UPGRADE_REPORT.md`。
2. 只读检查 `https://github.com/zianai/CreativeEngine` 的 `main`，特别是 `docs/api.md`、`docs/tradecase-integration.md`、`docs/architecture.md`、`contracts/visual-task/1.0.0/contract.json`、`skills/product-concept/`、`skills/ecommerce-listing/`。
3. 对齐现有边界：TradeCase Python/FastAPI/Pydantic/SQLAlchemy/Alembic/LangGraph/OpenAI Agents SDK/DB 租约/ARQ/Next.js；CreativeEngine Node/SQLite/HTTP 1.0.0，**由 Engine 自己运行图片 Worker、QA、版本及导出**。
4. 不以本交接包中的历史测试数替代当前实际测试。读当前 HEAD、Git 状态、依赖锁和真实 API 协议，再写审计结果。若发现接口差异，记录 ADR 和兼容契约，禁止静默猜测。
5. 继承 TradeCase 的项目持续性治理：`AGENTS.md` + `project/state.yaml` + `work/active/<task>/task.yaml` + ADR + 真实测试证据；新项目自有 `project_id`，不要使用 TradeCase 的业务记忆记录。

## 实现边界与技术方法

- LaunchCase 必须是**独立仓库/独立数据库**。不可在 TradeCase 的表、Case 枚举或 VisualTask 内塞 B2C 业务字段。
- 首选 Python 3.11+/FastAPI/Pydantic v2/SQLAlchemy/Alembic/LangGraph/OpenAI Agents SDK、测试用 SQLite、生产可选 PostgreSQL；Next.js/TypeScript 做 Web；任务持久化 DB 租约，Redis/ARQ 只作唤醒。
- 只使用一个工作流调度控制面：CaseService 拥有业务状态、LangGraph 处理业务顺序和中断、TaskManager 拥有任务领取、Engine 负责图片任务。禁止另造 Agent 循环或第二图像 Worker。
- `Research / Product / Creative` 是**有限职责 Agent 角色**，不要求每个领域技能都常驻独立进程。Skills 管 SOP，结构化输入输出；知识库管事实；后端校验/计算/授权。
- `Evidence` 是事实资料；`Insight/Opportunity` 是有引用的推断/假设；`ProductSpec` 是版本化需求/事实；`VisualAsset` 只是沟通材料。AI 图像不能回写为真实产品事实。
- 固定 G1–G5 Decision Gates；外发与认证检查需要真实依据和人的独立批准；编辑基础事实/版本后批准失效。
- 默认离线合成数据 + FakeAgent + Mock Creative Provider；联网抓取、付费模型、Oracle 网页自动化、生产账号、上架、广告、支付、采购、邮件均**不授权**。
- Source 和用户上传内容均是不可信数据，绝不可当作对 Agent 的系统指令。

## 实施顺序

严格按 `PHASE_PLAN.md` 执行 P0–P6，每个阶段交付：**代码、Schema、迁移（若适用）、测试、示例、运行日志、阶段总结、提交**。完成 P1–P3 即可运行从数据到概念的离线 MVP；完成 P6 应可离线完成全链路并在决策关卡正确停止。

每一阶段结束，报告：提交 SHA、改动文件、实际运行命令和 exit code、passed/failed/skipped、已验证能力与未经验证能力、风险和下一阶段依赖。独立的人工质量与真实商业验证不得伪装成自动测试通过。

**若当前仓库尚不存在**：在用户指定的独立目录创建 `launchcase/` 工程并使用 `codex/launchcase-v1` 本地分支。不得通过修改 TradeCase 或 CreativeEngine 来“方便集成”。未经额外授权不要 push 或创建 GitHub 远程仓库。

## 交付前统一验收

- `pytest` / `ruff` / 前端 `typecheck` + `build` 全部执行，并给出真实输出。
- 至少 12 类边界场景通过（见 `CONTRACTS_AND_SCENARIOS.md`）：证据缺失/冲突/重复、注入、跨租户、未知成本、审批准入和失效、Engine 失败、重复提交、Worker 恢复、模型预算、外部动作关闭、概念图假冒实物。
- `examples/synthetic-brief.json` 和 `examples/synthetic-voc.csv` 能在 Offline 模式创建 ProductCase，产出带引用的 VOC、Opportunity、概念与内部草稿，明确停在人工或样品验证的合理状态。
- OpenAPI 有版本、有严格 schema；CLI 与 Web 调用同一业务服务；MCP 如实现只能映射已有业务服务，不能绕开授权。
- 独立 `LaunchCase` wheel/包可在干净环境安装；SQL migration 升降与恢复得到验证。
- `CreativeEngine` 的 HTTP 真正打通 Mock/确定性模式；若本地服务不存在，则使用 Fake Adapter 做离线测试并在报告中说明“真实 HTTP 未验证”，不得伪称连通。

最终交付 `docs/DELIVERY_REPORT.md`、`docs/CAPABILITY_STATUS.md`、`docs/ADR/`、真实可复现命令、部署/回滚/数据保留说明，并清楚列出需要人确认的事项。**不要只给演示截图或一个合成评分。**
