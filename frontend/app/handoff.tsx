"use client";
import { useState } from "react";
type Item = { id: string; [key: string]: any };
type Props = {
  current: Item;
  data: Record<string, Item[]>;
  busy: boolean;
  api: (path: string, body?: unknown) => Promise<any>;
  act: (work: () => Promise<void>) => Promise<void>;
  reload: () => Promise<void>;
  review: (gate: string, item: Item) => void;
};
export default function HandoffWorkspace({
  current,
  data,
  busy,
  api,
  act,
  reload,
  review,
}: Props) {
  const [sampleSource, setSampleSource] = useState("");
  const [sampleId, setSampleId] = useState("");
  const [method, setMethod] = useState("");
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [tested, setTested] = useState("");
  const [person, setPerson] = useState("");
  const [limitations, setLimitations] = useState("");
  const [ruleSource, setRuleSource] = useState("");
  const [ruleExcerpt, setRuleExcerpt] = useState("");
  const [revision, setRevision] = useState("");
  const [effective, setEffective] = useState("");
  const [due, setDue] = useState("");
  const [applicability, setApplicability] = useState("");
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [packId, setPackId] = useState("");
  const [risks, setRisks] = useState("");
  const [excluded, setExcluded] = useState("");
  const [internal, setInternal] = useState(false);
  const items = (k: string) => data[k] || [];
  const g2 = items("gates").find(
    (g) => g.gate === "G2" && g.status === "current" && g.decision === "select",
  );
  const spec = items("spec-versions")
    .filter((s) => s.data.concept_id === g2?.subject_id)
    .sort((a, b) => b.version - a.version)[0];
  const realSources = (type: string) =>
    items("sources").filter(
      (s) =>
        s.source_type === type &&
        !s.is_synthetic &&
        s.rights_status === "authorized",
    );
  const root = `product-cases/${current.id}`;
  const gate = (g: string) =>
    items("gates")
      .filter((x) => x.gate === g)
      .at(-1);
  const approved = (g: string) =>
    gate(g)?.status === "current" &&
    gate(g)?.decision === (g === "G4" ? "verify_sample" : "internal_handoff");
  const statusLabel = (g: string) =>
    !gate(g)
      ? "尚未审核"
      : gate(g)?.status !== "current"
        ? "资料或版本已变化，请重新审核"
        : approved(g)
          ? g === "G4"
            ? "样品事实已确认（仅限记录范围）"
            : "内部交接已批准（未发布）"
          : "暂缓或待补充材料";
  const save = (endpoint: string, body: unknown) =>
    act(async () => {
      await api(`${root}/${endpoint}`, body);
      await reload();
    });
  return (
    <>
      <p className="eyebrow">G4 / SAMPLE → G5 / INTERNAL HANDOFF</p>
      <h2>把实测事实与交接责任放在一起。</h2>
      <p role="status">
        {approved("G5")
          ? "本轮内部交接已完成。下一步：查看批准回执或下载交接包。"
          : approved("G4")
            ? "样品事实已确认。下一步：复核规则并准备 G5 交接材料。"
            : "下一步：录入样品事实，并由负责人审核 G4。"}
      </p>
      <nav className="actions" aria-label="交接步骤">
        <a href="#g4-sample">1 样品事实</a>
        <a href="#handoff-rules">2 规则复核</a>
        <a href="#g5-handoff">3 内部交接与回执</a>
      </nav>
      <p className="review-warning">
        {current.is_synthetic
          ? "合成案例不可确认真实样品或通过业务交接。请另建真实 Case。"
          : "公开网页可用于研究和规则核对，不能证明本 SKU 的实测性能。"}{" "}
        交接批准不授权发布。
      </p>
      <div className="paper handoff-section" id="g4-sample">
        <h3>1 · 样品事实录入</h3>
        <p>
          先在「证据来源」导入有权使用的真实样品记录。每条事实绑定当前
          Spec、样品编号、方法和原文。多条事实请在 JSON
          导入中一次提交完整测试范围。
        </p>
        <details open={!items("samples").length}>
          <summary>录入新的样品记录</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save("sample-attestations", {
                expected_spec_hash: spec?.sha256,
                sample_identifier: sampleId,
                test_method: method,
                facts: [
                  {
                    name,
                    value,
                    source_id: sampleSource,
                    exact_excerpt: excerpt,
                    external_allowed: false,
                  },
                ],
                tested_at: new Date(tested).toISOString(),
                responsible_person: person,
                limitations,
              });
            }}
          >
            <fieldset disabled={busy || current.is_synthetic || !spec}>
              <label>
                样品原始记录
                <select
                  required
                  value={sampleSource}
                  onChange={(e) => setSampleSource(e.target.value)}
                >
                  <option value="">选择真实来源</option>
                  {realSources("sample").map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.filename}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                样品编号 / SKU / 批次
                <input
                  required
                  value={sampleId}
                  onChange={(e) => setSampleId(e.target.value)}
                />
              </label>
              <label>
                测试方法与判定范围
                <textarea
                  required
                  minLength={10}
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                />
              </label>
              <div className="cost-inputs">
                <label>
                  事实名称
                  <input
                    required
                    minLength={2}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </label>
                <label>
                  实测值（含单位）
                  <input
                    required
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                  />
                </label>
              </div>
              <label>
                原文摘录（须包含实测值）
                <textarea
                  required
                  minLength={5}
                  value={excerpt}
                  onChange={(e) => setExcerpt(e.target.value)}
                />
              </label>
              <label>
                测试时间
                <input
                  required
                  type="datetime-local"
                  value={tested}
                  onChange={(e) => setTested(e.target.value)}
                />
              </label>
              <label>
                测试负责人
                <input
                  required
                  minLength={2}
                  value={person}
                  onChange={(e) => setPerson(e.target.value)}
                />
              </label>
              <label>
                限制、未测项目与不通过项
                <textarea
                  required
                  minLength={5}
                  value={limitations}
                  onChange={(e) => setLimitations(e.target.value)}
                />
              </label>
              <p className="hash">当前 Spec {spec?.sha256 || "先完成 G2"}</p>
              <button className="primary">保存样品事实，待 G4 审核</button>
            </fieldset>
          </form>
        </details>
        <details>
          <summary>导入完整样品确认 JSON（多条事实）</summary>
          <p>
            JSON 必须包含当前
            expected_spec_hash、sample_identifier、test_method、facts、tested_at、responsible_person、limitations；这是事实录入，仍需单独审核。
          </p>
          <input
            aria-label="导入样品确认 JSON"
            type="file"
            accept=".json"
            disabled={busy || current.is_synthetic}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file)
                act(async () => {
                  if (file.size > 1048576) throw Error("文件超过 1 MiB");
                  await api(
                    `${root}/sample-attestations`,
                    JSON.parse(await file.text()),
                  );
                  await reload();
                });
            }}
          />
        </details>
        {items("samples").map((s) => (
          <article key={s.id}>
            <h4>样品记录 v{s.version}</h4>
            {items("truth")
              .filter((t) => t.id === s.data.truth_id)
              .map((t) => (
                <div key={t.id}>
                  <p>
                    负责人：{t.data.responsible_person} · 测试时间：
                    {t.data.confirmed_at}
                  </p>
                  <p>限制与未测项：{t.data.limitations}</p>
                </div>
              ))}
            <p>
              样品 {s.data.sample_identifier} · {s.data.test_method}
            </p>
            {s.data.facts.map((f: any, i: number) => (
              <p key={i}>
                {f.name}: {f.value}
                <br />
                <q>{f.exact_excerpt}</q>
                <br />
                <a
                  href={`/api/sources/${f.source_id}/content`}
                  target="_blank"
                  rel="noreferrer"
                >
                  查看原始记录 ↗
                </a>
              </p>
            ))}
            <button
              className="secondary"
              disabled={busy}
              onClick={() => review("G4", s)}
            >
              {approved("G4") && gate("G4")?.subject_id === s.id
                ? "重新审核 G4（将替代当前决定）"
                : "审核 G4 样品事实"}
            </button>
          </article>
        ))}
        <p>
          G4：
          {statusLabel("G4")} · 记录{" "}
          {gate("G4")?.subject_id?.slice(0, 8) || "—"}
        </p>
      </div>
      <div className="paper handoff-section">
        <h3 id="handoff-rules">2 · 规则适用性复核</h3>
        <p>
          先导入官方规则摘录并保留原始
          URL。公开来源不等于已适用于本产品；由负责人逐项说明。
        </p>
        <details open={!items("rules").length}>
          <summary>新增规则适用性复核</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const src = items("sources").find((s) => s.id === ruleSource);
              save("rule-attestations", {
                source_id: ruleSource,
                authority_url: src?.metadata_json?.source_url,
                product_scope: current.brief.category,
                revision,
                effective_at: new Date(effective).toISOString(),
                review_due_at: new Date(due).toISOString(),
                exact_excerpt: ruleExcerpt,
                applicability_reason: applicability,
              });
            }}
          >
            <fieldset disabled={busy || current.is_synthetic}>
              <label>
                官方规则来源
                <select
                  required
                  value={ruleSource}
                  onChange={(e) => setRuleSource(e.target.value)}
                >
                  <option value="">选择含官方 URL 的来源</option>
                  {realSources("rule").map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.filename}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                规则版本
                <input
                  required
                  value={revision}
                  onChange={(e) => setRevision(e.target.value)}
                />
              </label>
              <label>
                规则原文摘录
                <textarea
                  required
                  minLength={5}
                  value={ruleExcerpt}
                  onChange={(e) => setRuleExcerpt(e.target.value)}
                />
              </label>
              <label>
                生效时间
                <input
                  required
                  type="datetime-local"
                  value={effective}
                  onChange={(e) => setEffective(e.target.value)}
                />
              </label>
              <label>
                复核截止时间
                <input
                  required
                  type="datetime-local"
                  value={due}
                  onChange={(e) => setDue(e.target.value)}
                />
              </label>
              <label>
                对本品类的适用理由与未覆盖范围
                <textarea
                  required
                  minLength={10}
                  value={applicability}
                  onChange={(e) => setApplicability(e.target.value)}
                />
              </label>
              <button className="primary">记录规则适用性复核</button>
            </fieldset>
          </form>
        </details>
      </div>
      <div className="paper handoff-section">
        <h3 id="g5-handoff">3 · G5 内部业务交接</h3>
        <p>
          先完成 G4，再生成新
          LaunchPack。逐项记录成本缺口、风险责任和排除的声明；素材继续限内部使用。准备材料不会自动批准。
        </p>
        <details open={!items("handoff-preparations").length}>
          <summary>准备新的交接材料</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save("handoff-preparations", {
                pack_id: packId,
                expected_pack_hash: items("launch-packs").find(
                  (p) => p.id === packId,
                )?.sha256,
                rule_ids: selectedRules,
                responsible_person: person,
                risk_acceptance: risks,
                excluded_claims: excluded,
                internal_assets_only: internal,
              });
            }}
          >
            <fieldset disabled={busy || current.is_synthetic}>
              <label>
                交接包版本
                <select
                  required
                  value={packId}
                  onChange={(e) => setPackId(e.target.value)}
                >
                  <option value="">选择 G4 后生成的包</option>
                  {items("launch-packs").map((p) => (
                    <option key={p.id} value={p.id}>
                      v{p.version} · {p.id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </label>
              <p>选择本次适用的规则（过期或撤权后需重审）：</p>
              {items("rules").map((r) => (
                <label className="check" key={r.id}>
                  <input
                    type="checkbox"
                    checked={selectedRules.includes(r.id)}
                    onChange={(e) =>
                      setSelectedRules(
                        e.target.checked
                          ? [...selectedRules, r.id]
                          : selectedRules.filter((id) => id !== r.id),
                      )
                    }
                  />
                  {r.data.revision} · {r.data.authority_url} · 复核截止{" "}
                  {r.data.review_due_at}
                </label>
              ))}
              <label>
                交接负责人
                <input
                  required
                  minLength={2}
                  value={person}
                  onChange={(e) => setPerson(e.target.value)}
                />
              </label>
              <label>
                成本缺口、风险处置、责任人与后续行动
                <textarea
                  required
                  minLength={20}
                  value={risks}
                  onChange={(e) => setRisks(e.target.value)}
                />
              </label>
              <label>
                未验证及禁止对外使用的声明
                <textarea
                  required
                  minLength={10}
                  value={excluded}
                  onChange={(e) => setExcluded(e.target.value)}
                />
              </label>
              <label className="check">
                <input
                  required
                  type="checkbox"
                  checked={internal}
                  onChange={(e) => setInternal(e.target.checked)}
                />
                本次仅内部交接；Mock 素材不具有外部使用权，不批准发布
              </label>
              <button className="primary" disabled={!selectedRules.length}>
                保存交接材料，待 G5 审核
              </button>
            </fieldset>
          </form>
        </details>
        {items("handoff-preparations").map((h) => (
          <article key={h.id}>
            <h4>
              交接材料 v{h.version} · {h.data.responsible_person}
            </h4>
            <p>{h.data.risk_acceptance}</p>
            <p>{h.data.excluded_claims}</p>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => {
                const p = items("launch-packs").find(
                  (p) => p.id === h.data.pack_id,
                );
                if (p) review("G5", p);
              }}
            >
              {approved("G5") && gate("G5")?.subject_id === h.data.pack_id
                ? "重新审核 G5（将替代当前决定）"
                : "审核 G5 内部交接"}
            </button>
          </article>
        ))}
        <p>
          G5：
          {statusLabel("G5")} · 交接包{" "}
          {gate("G5")?.subject_id?.slice(0, 8) || "—"}
        </p>
        {gate("G5")?.status === "current" &&
          gate("G5")?.decision === "internal_handoff" && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => save("runs/handoff", {})}
            >
              同步已批准的交接流程
            </button>
          )}
        {gate("G5")?.status === "current" &&
          gate("G5")?.decision === "internal_handoff" && (
            <p>
              <a
                className="download"
                href={`/api/launch-packs/${gate("G5")?.subject_id}/handoff-export`}
              >
                下载完整内部交接包 ZIP ↗
              </a>
            </p>
          )}
        {gate("G5")?.status === "current" &&
          gate("G5")?.decision === "internal_handoff" && (
            <a
              className="download"
              href={`/api/launch-packs/${gate("G5")?.subject_id}/handoff-receipt`}
            >
              查看内部交接批准回执 ↗
            </a>
          )}
      </div>
    </>
  );
}
