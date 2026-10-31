"use client";
import { useState } from "react";
import { dateTime } from "./labels";
type Item = { id: string; [key: string]: any };
type FactRow = { name: string; value: string; excerpt: string };
const emptyFact: FactRow = { name: "", value: "", excerpt: "" };
function factProblem(fact: FactRow) {
  if (fact.name.trim().length < 2) return "事实名称至少 2 个字";
  if (!fact.value.trim()) return "请填写实测值和单位";
  if (fact.excerpt.trim().length < 5) return "原文摘录至少 5 个字";
  if (!fact.excerpt.includes(fact.value.trim()))
    return "原文摘录必须包含这个实测值";
  return "";
}
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
  const [facts, setFacts] = useState<FactRow[]>([{ ...emptyFact }]);
  const [checked, setChecked] = useState(false);
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
  const [handoffPerson, setHandoffPerson] = useState("");
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
  const updateFact = (index: number, patch: Partial<FactRow>) =>
    setFacts((rows) =>
      rows.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  const latestFirst = (kind: string) =>
    [...items(kind)].sort((a, b) => b.version - a.version);
  const samples = latestFirst("samples");
  const preparations = latestFirst("handoff-preparations");
  const isCurrent = (record: Item, all: Item[], subject?: string) =>
    record.id === all[0]?.id || record.id === subject;
  const statusLabel = (g: string) =>
    !gate(g)
      ? "尚未审核"
      : gate(g)?.status !== "current"
        ? "资料或版本已变化，请重新审核"
        : approved(g)
          ? g === "G4"
            ? "本次样品记录已确认（仅限记录范围）"
            : "内部交接已批准（未发布）"
          : "暂缓或待补充材料";
  const save = (endpoint: string, body: unknown) =>
    act(async () => {
      await api(`${root}/${endpoint}`, body);
      await reload();
    });
  const sampleCard = (s: Item) => (
    <article key={s.id}>
      <h4>样品记录第 {s.version} 版</h4>
      {items("truth")
        .filter((t) => t.id === s.data.truth_id)
        .map((t) => (
          <div key={t.id}>
            <p>
              负责人：{t.data.responsible_person} · 测试时间：
              {dateTime(t.data.confirmed_at)}
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
          ? "重新审核样品记录（将替代当前决定）"
          : "审核样品记录"}
      </button>
    </article>
  );
  const preparationCard = (h: Item) => (
    <article key={h.id}>
      <h4>
        交接材料第 {h.version} 版 · {h.data.responsible_person}
      </h4>
      <p>{h.data.risk_acceptance}</p>
      <p>{h.data.excluded_claims}</p>
      <button
        className="secondary"
        disabled={busy}
        onClick={() => {
          const p = items("launch-packs").find((p) => p.id === h.data.pack_id);
          if (p) review("G5", p);
        }}
      >
        {approved("G5") && gate("G5")?.subject_id === h.data.pack_id
          ? "重新审核内部交接（将替代当前决定）"
          : "审核内部交接"}
      </button>
    </article>
  );
  return (
    <>
      <p className="eyebrow">样品验证 → 内部交接</p>
      <h2>把实测事实与交接责任放在一起。</h2>
      <p role="status">
        {approved("G5")
          ? "本轮内部交接已完成。可以下载交接包或查看批准回执。"
          : approved("G4")
            ? "本次样品记录已确认。下一步：复核规则并准备内部交接材料。"
            : "下一步：录入样品记录，并由负责人审核。"}
      </p>
      {approved("G5") && (
        <div className="handoff-summary">
          <a
            className="download primary-link"
            href={`/api/launch-packs/${gate("G5")?.subject_id}/handoff-export`}
          >
            下载完整内部交接包 ZIP ↗
          </a>
          <a
            className="download"
            href={`/api/launch-packs/${gate("G5")?.subject_id}/handoff-receipt`}
          >
            查看内部交接批准回执 ↗
          </a>
          <button
            className="text-button"
            disabled={busy}
            onClick={() => save("runs/handoff", {})}
          >
            同步已批准的交接流程
          </button>
        </div>
      )}
      <nav className="actions" aria-label="交接步骤">
        <a href="#g4-sample">1 样品记录</a>
        <a href="#handoff-rules">2 规则复核</a>
        <a href="#g5-handoff">3 内部交接</a>
      </nav>
      <p className="review-warning">
        {current.is_synthetic
          ? "合成测试项目不能确认真实样品，也不能通过业务交接。请另建真实项目。"
          : "公开网页可用于研究和规则核对，不能证明本 SKU 的实测性能。"}{" "}
        交接批准不授权发布。
      </p>
      <div className="paper handoff-section" id="g4-sample">
        <h3>1 · 样品记录</h3>
        <p>
          先在「证据来源」导入有权使用的真实样品记录。一次可以录入多条实测事实，每条都要能在原文中找到。
        </p>
        <details open={!items("samples").length}>
          <summary>录入新的样品记录</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setChecked(true);
              if (facts.some(factProblem)) return;
              save("sample-attestations", {
                expected_spec_hash: spec?.sha256,
                sample_identifier: sampleId,
                test_method: method,
                facts: facts.map((fact) => ({
                  name: fact.name.trim(),
                  value: fact.value.trim(),
                  source_id: sampleSource,
                  exact_excerpt: fact.excerpt,
                  external_allowed: false,
                })),
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
              <table className="fact-table">
                <caption className="sr-only">实测事实</caption>
                <thead>
                  <tr>
                    <th scope="col">事实名称</th>
                    <th scope="col">实测值（含单位）</th>
                    <th scope="col">原文摘录（须包含实测值）</th>
                    <th scope="col">
                      <span className="sr-only">操作</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {facts.map((fact, i) => {
                    const problem = checked ? factProblem(fact) : "";
                    return (
                      <tr key={i}>
                        <td>
                          <input
                            aria-label={`第 ${i + 1} 条事实名称`}
                            value={fact.name}
                            placeholder="例如：外包装宽度"
                            onChange={(e) =>
                              updateFact(i, { name: e.target.value })
                            }
                          />
                        </td>
                        <td>
                          <input
                            aria-label={`第 ${i + 1} 条实测值`}
                            value={fact.value}
                            placeholder="例如：40 cm"
                            onChange={(e) =>
                              updateFact(i, { value: e.target.value })
                            }
                          />
                        </td>
                        <td>
                          <textarea
                            aria-label={`第 ${i + 1} 条原文摘录`}
                            rows={2}
                            value={fact.excerpt}
                            onChange={(e) =>
                              updateFact(i, { excerpt: e.target.value })
                            }
                          />
                          {problem && (
                            <span className="row-error" role="alert">
                              {problem}
                            </span>
                          )}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="text-button"
                            disabled={facts.length === 1}
                            aria-label={`删除第 ${i + 1} 条事实`}
                            onClick={() =>
                              setFacts((rows) =>
                                rows.filter((_, index) => index !== i),
                              )
                            }
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <button
                type="button"
                className="secondary"
                onClick={() => setFacts((rows) => [...rows, { ...emptyFact }])}
              >
                ＋ 增加一条事实
              </button>
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
              {!spec && <p className="hint">请先选定产品方案。</p>}
              <details className="tech-details">
                <summary>技术信息</summary>
                <p className="hash">当前规格校验值 {spec?.sha256 || "—"}</p>
              </details>
              <button className="primary">保存样品记录，等待审核</button>
            </fieldset>
          </form>
        </details>
        <details>
          <summary>高级：从 JSON 文件导入</summary>
          <p className="hint">
            供系统批量导入使用，日常录入请用上面的表格。文件须包含
            expected_spec_hash、sample_identifier、test_method、facts、tested_at、responsible_person、limitations；导入后仍需单独审核。
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
        {samples
          .filter((s) => isCurrent(s, samples, gate("G4")?.subject_id))
          .map((s) => sampleCard(s))}
        {samples.some(
          (s) => !isCurrent(s, samples, gate("G4")?.subject_id),
        ) && (
          <details className="older-records">
            <summary>较早的样品记录</summary>
            {samples
              .filter((s) => !isCurrent(s, samples, gate("G4")?.subject_id))
              .map((s) => sampleCard(s))}
          </details>
        )}
        <p>样品验证：{statusLabel("G4")}</p>
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
        <h3 id="g5-handoff">3 · 内部交接</h3>
        <p>
          样品记录确认后，先生成新的内部交接资料，再逐项记录成本缺口、风险责任和排除的声明。素材继续限内部使用，准备材料不会自动批准。
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
                responsible_person: handoffPerson,
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
                  <option value="">选择样品确认后生成的版本</option>
                  {items("launch-packs").map((p) => (
                    <option key={p.id} value={p.id}>
                      第 {p.version} 版 · {dateTime(p.created_at)}
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
                  {dateTime(r.data.review_due_at)}
                </label>
              ))}
              <label>
                交接负责人
                <input
                  required
                  minLength={2}
                  value={handoffPerson}
                  onChange={(e) => setHandoffPerson(e.target.value)}
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
                本次仅内部交接；模拟素材不具有外部使用权，不批准发布
              </label>
              <button className="primary" disabled={!selectedRules.length}>
                保存交接材料，等待审核
              </button>
            </fieldset>
          </form>
        </details>
        {preparations
          .filter((h) => isCurrent(h, preparations))
          .map(preparationCard)}
        {preparations.length > 1 && (
          <details className="older-records">
            <summary>较早的交接材料</summary>
            {preparations
              .filter((h) => !isCurrent(h, preparations))
              .map(preparationCard)}
          </details>
        )}
        <p>内部交接：{statusLabel("G5")}</p>
      </div>
    </>
  );
}
