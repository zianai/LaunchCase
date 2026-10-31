# 给 Codex 的直接执行消息

你现在负责独立实施 **LaunchCase V1**。请完整阅读并以当前目录内的文件作为实施规格，按顺序执行 P0→P6：

1. `README_FOR_CODEX.md` — 任务边界、最新仓库基线、实施纪律与验收口径。
2. `IMPLEMENTATION_SPEC.md` — 产品目标、核心业务对象、完整架构、工作流、Agent/Skills、CreativeEngine 接口、审查权限和最终 DoD。
3. `PHASE_PLAN.md` — 每个 P 阶段的具体工作包与退出条件。
4. `CONTRACTS_AND_SCENARIOS.md`、`ACCEPTANCE_MATRIX.csv`、`contracts/`、`examples/` — 契约种子与测试输入。
5. `AGENTS.md`、`docs/ARCHITECTURE_DECISIONS.md`、`docs/REFERENCES.md` — 项目持续性、架构决策和源仓库验证。

**要求：**
- 新建或仅在用户指定的 LaunchCase 独立工作区实施；不修改 TradeCase/CreativeEngine，不创建或推送远程仓库。
- 首先只读核查现有 TradeCase `main` 和 `codex/tradecase-visual-tasks`，以及 CreativeEngine `main` 的最新代码与真实 HTTP/OpenAPI 契约；生成 baseline audit，不能照抄报告中的历史测试数字充当本轮结果。
- 保留设计哲学：**Skills 管方法；Agent SDK 管限域研究；LangGraph 管业务流程；DB TaskManager 管任务、幂等与恢复；普通代码管 Schema、数据与经济计算；CreativeEngine 管图片执行；人类管关键决策。**
- V1 仅 Mode B：Amazon US、差异化非高风险消费品、合法授权/合成数据导入。禁止自动上架、购买、供应商联系、付费调用、未经授权爬取、无来源的市场/法规/认证声称。
- 完成 ProductCase→Evidence→VOC→Opportunity→Concept/ProductSpec→Feasibility→VisualTask→**Internal Draft LaunchPack** 的持久化离线闭环；若没有真实样品，**G4/G5 保持阻断**，不要假装上市准备已被批准。
- 每阶段必须真实运行测试/构建/迁移/示例，报告实际 exit code、passed/failed/skipped、提交 SHA 与未验证部分；修复问题后继续下一阶段。不要求每完成一个小任务就停下来询问；只有涉及额外权限、不可逆外部操作或重大产品定义冲突才需申请用户决定。
- 最终交付 README、API/CLI、可运行 Web、严格校验的合成 Case、端到端演示脚本、阶段与总验收报告。不得只做文档和 TODO。

从 **P0 仓库核查与基线建立** 开始，然后实施，不要自行改变此方案的目标边界。
