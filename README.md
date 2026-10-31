# LaunchCase V1

证据驱动的 Amazon US 差异化消费品开发工作台。独立工作区：
`/Users/a/workspaces/AForeign Trade/LaunchCase`。

已经实现 ProductCase → 原始证据/VOC → Opportunity → Concept/Spec → Feasibility →
Mock VisualTask → **Internal Draft LaunchPack**。默认只运行合成测试、Agents SDK Fake Model
和 CreativeEngine Mock。没有样品时停在 G4；不能把草稿当作可上市产品。

## 本地启动

需要 Python 3.12（项目允许 3.11+，本机验证为 3.12.13）、uv、Node 24+、npm。
第一次依赖安装需要软件包仓库；业务演示不需要 API Key。

```bash
cd '/Users/a/workspaces/AForeign Trade/LaunchCase'
uv sync --frozen --extra dev
uv run launchcase init-db
uv run launchcase doctor
umask 077
uv run launchcase auth create --tenant local --name 'Local owner' --role owner > .launchcase/identity.json
uv run uvicorn launchcase.api:app --host 127.0.0.1 --port 8810
```

第二个终端：

```bash
cd '/Users/a/workspaces/AForeign Trade/LaunchCase/frontend'
npm ci
npm run build
npm run start
```

打开 <http://127.0.0.1:3310>，使用本地 `.launchcase/identity.json` 中的 token 登录。
该文件是凭证，不要提交、截图或发送。环境变量不会自动从 `.env` 加载。
Web 的服务端 `LAUNCHCASE_API_URL` 默认为 `http://127.0.0.1:8810`。

本次交付的浏览器演示单独使用 `.launchcase/browser`，凭证在
`.launchcase/browser-token`（权限 600）。与上面的默认新环境互相独立。

## 无人值守合成演示

```bash
uv run launchcase demo --fixture fixtures/scenarios/pet-furniture-us --out .launchcase/demo-new
uv run launchcase validate --case .launchcase/demo-new --strict
```

输出目录必须不存在。该命令仅为合成 Case/合成身份执行测试审批，不能替真实用户批准。
输出包含 3 个来源、28 条去重证据、4 个机会、2 个概念、版本化规格、缺失成本、
经过内部测试审核的 Mock 图片，以及 JSON/Markdown/ZIP 草稿；G4/G5 未获真实批准。
原始 24 条评论中保留 23 条，另有 4 条竞品证据和 1 条缺失报价记录。

Web 操作顺序：创建 Brief → 导入 fixture 的 3 个文件（分别选择 review/competitor/quote，
明确勾选合成与导入权利）→ VOC 研究 → G1 选择 → 概念生成/G2 → 可行性/G3 →
概念计划审核 → 执行 Mock → 独立审核图片 → 生成内部草稿。

## 验证与运维

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python ops/verify_migrations.py
uv build
uv run python ops/verify_install.py
npm run typecheck --prefix frontend
```

`verify_install.py` 使用新虚拟环境和缓存进行离线安装；首次缺缓存可显式加
`--allow-downloads` 准备依赖，再不带该参数验证离线安装。
默认 pytest 跳过实际 Engine HTTP 和 Docker 两项；它们不是默认测试已通过的项目。
完整运行范围、阶段提交与失败记录见 [交付报告](docs/DELIVERY_REPORT.md)。

- [能力与明确限制](docs/CAPABILITY_STATUS.md)
- [API / CLI](docs/API.md)
- [运行、备份恢复、删除与故障处理](docs/OPERATIONS.md)
- [验收场景映射](docs/ACCEPTANCE.md)
- [上游只读核查](docs/BASELINE_AUDIT.md)
- [依赖与许可证](docs/LICENSES.md)

本版本没有对外发布端点、付费服务执行配置或自动采购/联系供应商功能。
视觉方向由 Agent 暂定，尚未获得用户设计验收；截图不是商业验证。
