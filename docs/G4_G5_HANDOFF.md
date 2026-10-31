# G4/G5 内部业务交接

本次能力升级允许有依据的人工 G4 与 G5 内部交接。没有增加发布接口，`publishable` 始终为 false。当前演示仍是合成案例，不具备真实业务批准。

## 操作顺序

1. 使用负责人身份另建真实 Case，完成有来源的 G1/G2/G3。合成 Case/身份不能转成真实批准。
2. 在证据来源中导入授权的样品原始文本/CSV/JSON/MD。在「样品与交接」录入当前 Spec 哈希、样品编号/SKU/批次、测试方法、实测值、准确原文、时间、负责人和未测/失败项目。公开网页 URL 不得充作本样品测试记录。
3. 保存事实不等于通过 G4。负责人单独审核特定记录；默认选择暂缓。多项测试通过 JSON 一次提交完整 facts。新记录是新测试范围，不自动合并旧记录，也不代表全部性能已验证。
4. 导入官方规则短摘录，填写原始 URL。支持政府 `.gov` 与 Amazon 官方主站/卖家中心域名；系统只做来源、哈希、时间及品类绑定检查，不自动认证法规适用性。负责人填写版本、生效时间、复核截止时间和适用理由。其他官方标准来源需要后续明确扩展域名策略。
5. G4 完成后生成新 LaunchPack，再选择具体包与适用规则，记录成本缺口、风险处置及责任人、排除的声明，确认素材仅供内部使用。
6. 准备材料不等于通过 G5。负责人审核精确版本；默认选择补充材料。批准后可查看回执、下载完整内部交接 ZIP、同步已批准流程到 LangGraph 完成状态。
7. 新样品、Spec/来源/成本/使用权变更、新交接材料或规则过期均可能使旧批准失效。系统拒绝失效回执和交接导出，需重审。

## 交接包

原始 LaunchPack 保持不可变，保留生成时的待审核提示。单独的 `approval.json` 绑定包哈希、G5 人工决定和交接准备材料。ZIP 另含规则快照、授权原文、样品原始记录和文件哈希清单。回执批准范围为内部业务交接，不是上市、合规认证或外部图片授权。

缺失成本允许作为有责任人和后续行动的内部交接风险保留，不能据此作盈利或商业可行性结论。Mock 图只能内部使用；真实图片外部授权、真实 Listing 生成/发布仍不在本次范围。

## API

- `GET product-cases/{id}/samples`、`truth`、`rules`、`handoff-preparations`
- `POST product-cases/{id}/sample-attestations`：增加 sample_identifier、test_method；真实路径必须填写。facts.value 必须存在于 exact_excerpt 中。
- `POST product-cases/{id}/rule-attestations`：原始来源 URL 一致，品类与 Case category 一致，授权且未过期。
- `POST product-cases/{id}/handoff-preparations`：pack_id、expected_pack_hash、rule_ids、responsible_person、risk_acceptance、excluded_claims、internal_assets_only=true。
- 原有 `gates/G4|G5/subject/{id}` 与 `decision`：绑定精确版本，角色授权、租户隔离与幂等仍适用。
- `GET launch-packs/{id}/handoff-receipt`、`handoff-export`：只有当前有效 G5 批准可用。
- `POST product-cases/{id}/runs/handoff`：持久化任务重新验证批准后推进图到 `complete_internal_handoff`，无外部动作。

没有数据库字段变更；新材料使用现有不可变 Artifact 存储，不需要新迁移。

## 公共来源测试资料

`fixtures/public-references/manifest.json` 记录检索日、URL、用途和限制。短摘录来自 [FTC 广告声明依据政策](https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation) 和 [CPSC 一般用途产品测试与认证指引](https://www.cpsc.gov/Business--Manufacturing/Testing-Certification/General-Use-Products-Certification-and-Testing)。仅测试导入、原文和规则追溯；没有作出对本宠物家具的适用性或合规结论。没有收集真实客户需求、供应商报价或本 SKU 样品测试，不能用网页补齐这些缺口。

## 可重复测试

- `LAUNCHCASE_TEST_ENGINE_HTTP=1 uv run pytest -q`
- `uv run python ops/seed_handoff_test.py`：创建 `.launchcase/handoff-e2e/` 下新的隔离测试库，不使用演示库；其中真实模式字段仅用于软件契约测试，标题与文本明确 TEST ONLY。
- `npm run build --prefix frontend`
- `cd frontend && npx playwright test --config playwright.handoff.config.ts`：8812/3312 临时测试服务，结束后关闭；涵盖表单、默认暂缓、独立审批、导出、桌面/手机与 axe。
- 原三项浏览器回归仍使用 8810/3310；截图输出可通过 LAUNCHCASE_SCREENSHOT_DIR 指定。

所有成功审批测试都是软件测试，不是人类实际验样、真实法规审核或业务验收。
