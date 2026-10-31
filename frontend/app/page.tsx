"use client";
import { useCallback, useEffect, useRef, useState } from "react";

type Item = { id: string; [key: string]: any };
type Review = {
  title: string;
  endpoint: string;
  hash: string;
  options: { value: string; label: string }[];
  subject?: { subject_type: string; subject_id: string };
};
const tabs = [
  "总览",
  "证据来源",
  "VOC 研究",
  "机会",
  "概念与 Spec",
  "可行性",
  "视觉资产",
  "LaunchPack",
  "活动",
];
const kinds = [
  "sources",
  "evidence",
  "insights",
  "opportunities",
  "concepts",
  "spec-versions",
  "feasibility",
  "visual-tasks",
  "launch-packs",
  "activity",
  "gates",
  "research",
];
const stages: Record<string, string> = {
  collecting_sources: "收集证据",
  opportunity_review: "G1 · 机会审核",
  concepting: "开发概念",
  concept_review: "G2 · 概念审核",
  feasibility_review: "G3 · 可行性审核",
  awaiting_sample_validation: "G4 · 等待样品验证",
  ready_for_internal_handoff: "内部草稿已形成",
  launch_draft: "准备内部草稿",
};
const costNames: Record<string, string> = {
  net_sales_revenue_ex_tax: "不含税销售收入",
  ex_factory: "出厂成本",
  freight: "运费",
  tariff_duty: "关税",
  import_handling: "进口与操作费",
  referral_fee: "平台佣金",
  fulfillment: "履约费",
  variable_storage: "变动仓储费",
  advertising_allocated: "广告摊销",
  returns_allowance: "退货准备",
  other_variable_costs: "其他变动成本",
};
const emptyBrief = {
  schema_version: "1.0.0",
  title: "",
  mode: "differentiation",
  target_market: "US",
  marketplace: "amazon_us",
  category: "",
  target_segment: "",
  problem_statement: "",
  goals: ["建立可追溯的产品开发假设"],
  constraints: {
    budget_usd: null,
    target_retail_price_usd: null,
    target_landed_cost_usd: null,
    must_preserve: ["不宣称未经核实的安全与性能"],
    must_not_claim: ["certified", "production ready"],
  },
  data_policy: {
    data_origin: "user_import",
    rights_status: "authorized",
    allowed_external_use: false,
    is_synthetic: false,
  },
};
const fixtureBrief = {
  ...emptyBrief,
  title: "[SYNTHETIC] US Pet Furniture: Easier Assembly",
  category: "pet furniture and dog crate furniture",
  target_segment: "Adults comparing furniture-style indoor dog crates",
  problem_statement:
    "Investigate easier assembly and compact shipping as product hypotheses. This is synthetic functional testing, not proven market demand.",
  data_policy: {
    data_origin: "synthetic_demo_only",
    rights_status: "synthetic_fixture",
    allowed_external_use: false,
    is_synthetic: true,
  },
};
function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="empty">
      <span aria-hidden="true">↳</span>
      <p>{children}</p>
    </div>
  );
}
function Meta({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="meta">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function Workbench() {
  const [authenticated, setAuthenticated] = useState(false),
    [token, setToken] = useState(""),
    [cases, setCases] = useState<Item[]>([]),
    [current, setCurrent] = useState<Item | null>(null),
    [data, setData] = useState<Record<string, Item[]>>({}),
    [tab, setTab] = useState("总览"),
    [screen, setScreen] = useState("cases");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [newCase, setNewCase] = useState(false),
    [brief, setBrief] = useState(emptyBrief),
    [review, setReview] = useState<Review | null>(null),
    [reason, setReason] = useState(""),
    [decision, setDecision] = useState(""),
    [sourceType, setSourceType] = useState("review"),
    [synthetic, setSynthetic] = useState(true),
    [rights, setRights] = useState(false),
    [excerpt, setExcerpt] = useState<Item | null>(null),
    [specEdit, setSpecEdit] = useState<Item | null>(null),
    [costEdit, setCostEdit] = useState(false),
    [costs, setCosts] = useState<Record<string, string>>({}),
    [capabilities, setCapabilities] = useState<Item | null>(null),
    [diff, setDiff] = useState<any[] | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const api = useCallback(
    async (path: string, body?: unknown, method?: string) => {
      const response = await fetch("/api/" + path, {
        method: method || (body === undefined ? "GET" : "POST"),
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (!response.ok) {
        const d = await response.json().catch(() => ({}));
        if (response.status === 401) setAuthenticated(false);
        throw Error(d.error?.message || `请求失败 (${response.status})`);
      }
      return response.json();
    },
    [],
  );
  const loadCases = useCallback(async () => {
    const response = await api("product-cases");
    setCases(response.items);
    setAuthenticated(true);
  }, [api]);
  const load = useCallback(
    async (id: string) => {
      const [c, ...results] = await Promise.all([
        api(`product-cases/${id}`),
        ...kinds.map((k) =>
          api(`product-cases/${id}/${k}`).catch((e) => {
            if (k === "visual-tasks") return { items: [] };
            throw e;
          }),
        ),
      ]);
      setCurrent(c);
      const next: Record<string, Item[]> = {};
      kinds.forEach((k, i) => (next[k] = results[i].items));
      setData(next);
      await loadCases();
    },
    [api, loadCases],
  );
  useEffect(() => {
    fetch("/api/session")
      .then((r) => r.json())
      .then((s) => {
        if (s.authenticated)
          return loadCases().then(() =>
            api("capabilities").then(setCapabilities),
          );
      })
      .catch(() => {});
  }, [api, loadCases]);
  useEffect(() => {
    if (review || newCase || specEdit || costEdit) {
      if (!dialog.current?.open) dialog.current?.showModal();
    } else if (dialog.current?.open) dialog.current.close();
  }, [review, newCase, specEdit, costEdit]);
  const act = async (work: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    } finally {
      setBusy(false);
    }
  };
  const openCase = (id: string) =>
    act(async () => {
      setScreen("cases");
      setTab("总览");
      setExcerpt(null);
      await load(id);
    });
  const items = (kind: string) => data[kind] || [];
  const activeGate = (gate: string) =>
    items("gates")
      .filter(
        (g) =>
          g.gate === gate &&
          g.status === "current" &&
          [
            "accept",
            "select",
            "sample_validation",
            "verify_sample",
            "internal_handoff",
          ].includes(g.decision),
      )
      .at(-1);
  const selectedConcept = items("concepts").find(
    (c) => c.id === activeGate("G2")?.subject_id,
  );
  const latestSpec = (conceptId: string) =>
    items("spec-versions")
      .filter((s) => s.data.concept_id === conceptId)
      .sort((a, b) => b.version - a.version)[0];
  const run = (kind: string) =>
    act(async () => {
      if (!current) return;
      const task = await api(`product-cases/${current.id}/runs/${kind}`, {});
      let result = task;
      for (let i = 0; i < 40; i++) {
        result = await api(`tasks/${task.id}`);
        if (["succeeded", "failed"].includes(result.status)) break;
        await new Promise((r) => setTimeout(r, 250));
      }
      if (result.status === "failed")
        throw Error(`任务失败：${result.error_code}`);
      await load(current.id);
      setNotice(
        result.status === "succeeded"
          ? `已完成，等待 ${result.result.waiting_for}`
          : "任务已保存，可稍后刷新继续查看",
      );
    });
  const currentGate = !activeGate("G1")
    ? "G1"
    : !activeGate("G2")
      ? "G2"
      : !activeGate("G3")
        ? "G3"
        : !activeGate("G4")
          ? "G4"
          : "G5";
  const gateLabels: Record<string, string> = {
    G1: "机会选择与证据复核",
    G2: "概念与规格审核",
    G3: "可行性与样品调查",
    G4: "等待真实样品验证",
    G5: "上市交接条件尚待核实",
  };
  const nextAction = () => {
    if (!items("sources").length)
      return { label: "导入原始证据 →", action: () => setTab("证据来源") };
    if (!items("research").length)
      return { label: "运行证据研究 →", action: () => run("research") };
    if (!activeGate("G1"))
      return { label: "审核产品机会 →", action: () => setTab("机会") };
    if (!activeGate("G2"))
      return {
        label: items("concepts").length ? "比较并审核概念 →" : "开发概念方向 →",
        action: () =>
          items("concepts").length ? setTab("概念与 Spec") : run("concepts"),
      };
    if (!items("feasibility").length)
      return { label: "计算可行性 →", action: () => run("feasibility") };
    if (!activeGate("G3"))
      return {
        label: "审核可行性与样品调查 →",
        action: () => setTab("可行性"),
      };
    return {
      label: items("launch-packs").length
        ? "查看真实样品验证待办 →"
        : "准备内部草稿 →",
      action: () => setTab("LaunchPack"),
    };
  };
  const gateReview = (gate: string, subject: Item) =>
    act(async () => {
      if (!current) return;
      const info = await api(
        `product-cases/${current.id}/gates/${gate}/subject/${subject.id}`,
      );
      const options =
        gate === "G1"
          ? [
              { value: "accept", label: "选择这个机会" },
              { value: "research_more", label: "补充研究" },
              { value: "reject", label: "否决" },
            ]
          : gate === "G2"
            ? [
                { value: "select", label: "选择这个概念" },
                { value: "revise", label: "修改后重审" },
                { value: "reject", label: "否决" },
              ]
            : [
                { value: "sample_validation", label: "仅授权样品调查" },
                { value: "revise", label: "补充可行性数据" },
                { value: "hold", label: "暂缓" },
              ];
      setReview({
        title: `${gate} · ${subject.data.title || "可行性决策"}`,
        endpoint: `product-cases/${current.id}/gates/${gate}/decision`,
        hash: info.subject_hash,
        options,
        subject: {
          subject_type:
            gate === "G1"
              ? "opportunity"
              : gate === "G2"
                ? "concept"
                : "feasibility",
          subject_id: subject.id,
        },
      });
      setDecision(options[0].value);
      setReason("");
    });
  const visualReview = (task: Item, asset?: Item) =>
    act(async () => {
      const info = asset ? await api(`visual-assets/${asset.id}`) : task;
      setReview({
        title: asset ? "独立审核图片资产" : "审核概念计划 · 零预算 Mock",
        endpoint: asset
          ? `visual-assets/${asset.id}/review`
          : `visual-tasks/${task.id}/approve-plan`,
        hash: asset ? info.subject_hash : task.plan_hash,
        options: [
          {
            value: "approved",
            label: asset ? "批准内部使用" : "批准执行此计划",
          },
          { value: "rejected", label: "拒绝" },
        ],
      });
      setDecision("approved");
      setReason("");
    });
  const cite = (id: string) => {
    const e = items("evidence").find((e) => e.id === id);
    if (e) {
      setExcerpt(e);
      setTab("证据来源");
    }
  };
  const refs = (ids: string[]) => (
    <div className="citations">
      {ids.map((id, i) => (
        <button className="text-button" key={id} onClick={() => cite(id)}>
          ↗ 原文 {i + 1}
        </button>
      ))}
    </div>
  );
  const refresh = () =>
    current &&
    act(async () => {
      await load(current.id);
      setNotice("已读取当前数据库版本");
    });
  const closeDialog = () => {
    setReview(null);
    setNewCase(false);
    setSpecEdit(null);
    setCostEdit(false);
  };
  const create = () =>
    act(async () => {
      const c = await api("product-cases", brief);
      setNewCase(false);
      await load(c.id);
      setTab("证据来源");
    });
  const importFile = (file: File) =>
    act(async () => {
      if (!current) return;
      if (!rights) throw Error("请先确认导入权限");
      if (file.size > 1048576) throw Error("文本文件不得超过 1 MiB");
      await api(`product-cases/${current.id}/sources/import`, {
        filename: file.name,
        content: await file.text(),
        source_type: sourceType,
        rights_status: synthetic ? "synthetic_fixture" : "authorized",
        is_synthetic: synthetic,
      });
      await load(current.id);
      setNotice("已保存原文、哈希与逐行证据引用");
    });
  const login = () =>
    act(async () => {
      const submittedToken = token;
      setToken("");
      const r = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: submittedToken }),
      });
      if (!r.ok) throw Error("身份凭证无效，请使用本地 CLI 创建的凭证");
      setToken("");
      await loadCases();
      setCapabilities(await api("capabilities"));
    });

  if (!authenticated)
    return (
      <main className="login-shell">
        <div className="login-brand">
          <span className="monogram">LC</span>
          <span>LAUNCHCASE</span>
        </div>
        <div className="login-copy">
          <p className="eyebrow">PRODUCT DEVELOPMENT / AMAZON US</p>
          <h1>
            让产品决策
            <br />
            有据可循。
          </h1>
          <p>
            从客户原话，到产品假设，再到可审核的内部草稿。每个结论保留来源，每个关键决定由人确认。
          </p>
        </div>
        <form
          className="login-form"
          onSubmit={(e) => {
            e.preventDefault();
            login();
          }}
        >
          <p className="eyebrow">LOCAL WORKSPACE</p>
          <h2>进入工作台</h2>
          <label>
            本地身份凭证
            <input
              type="password"
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </label>
          <p className="hint">
            使用工作区管理员通过 CLI
            创建的身份凭证。凭证保存在仅服务器可读的会话中。
          </p>
          <button className="primary" disabled={busy}>
            进入工作区 →
          </button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <div className="login-boundary">
            默认离线 · 不调用付费服务 · 不自动发布
          </div>
        </form>
      </main>
    );

  return (
    <div className="app-shell">
      <a href="#main" className="skip">
        跳至主要内容
      </a>
      <aside className="sidebar">
        <button
          className="brand"
          onClick={() => {
            setCurrent(null);
            setScreen("cases");
          }}
        >
          <span className="monogram">LC</span>
          <span>
            LaunchCase<small>PRODUCT DEVELOPMENT</small>
          </span>
        </button>
        <div className="workspace-label">
          独立产品工作区 <span>V1</span>
        </div>
        <nav aria-label="主导航">
          {[
            ["cases", "◫", "产品 Cases"],
            ["inbox", "◷", "审核收件箱"],
            ["sources", "≡", "来源与知识"],
            ["assets", "▧", "视觉资产"],
            ["settings", "⚙", "能力与设置"],
          ].map(([id, icon, label]) => (
            <button
              key={id}
              className={screen === id ? "active" : ""}
              onClick={() => {
                setScreen(id);
                if (id === "cases" || id === "inbox") setCurrent(null);
                if (id === "sources") setTab("证据来源");
                if (id === "assets") setTab("视觉资产");
              }}
            >
              <span aria-hidden="true">{icon}</span>
              {label}
              {id === "inbox" && (
                <b>{cases.filter((c) => c.status === "needs_review").length}</b>
              )}
            </button>
          ))}
        </nav>
        <small className="scroll-hint">左右滑动，查看更多入口 →</small>
        <div className="sidebar-note">
          <span className="dot" /> OFFLINE FIRST
          <p>
            先核实，再决策。
            <br />
            概念不等于产品事实。
          </p>
        </div>
        <button
          className="logout"
          onClick={() =>
            act(async () => {
              await fetch("/api/session", { method: "DELETE" });
              setAuthenticated(false);
              setCurrent(null);
            })
          }
        >
          退出本地会话 ↗
        </button>
      </aside>
      <main id="main" className="main">
        <header className="topline">
          <span>
            工作台 <i>/</i> {current ? "产品 Case" : "案例库"}
          </span>
          <div>
            <span className="online-dot" /> 本地连接{" "}
            <span className="top-separator">|</span> Amazon US · 差异化开发
          </div>
        </header>
        {error && (
          <div role="alert" className="error banner">
            {error}
            <button onClick={() => setError("")} aria-label="关闭错误">
              ×
            </button>
          </div>
        )}
        {notice && (
          <p role="status" className="notice banner">
            {notice}
          </p>
        )}
        {screen === "settings" ? (
          <>
            <div className="page-heading">
              <div>
                <p className="eyebrow">CAPABILITIES & BOUNDARIES</p>
                <h1>清楚知道，做到哪一步。</h1>
              </div>
            </div>
            <div className="paper">
              <h2>V1 当前能力</h2>
              <dl className="definition">
                <dt>业务模式</dt>
                <dd>Amazon US · 差异化消费品开发</dd>
                <dt>研究运行</dt>
                <dd>Agents SDK + 本地 Fake Model；不代表真实模型质量</dd>
                <dt>视觉执行</dt>
                <dd>CreativeEngine Mock · 内部概念素材</dd>
                <dt>付费模型</dt>
                <dd>{capabilities?.paid_models ? "启用" : "关闭"}</dd>
                <dt>对外发布</dt>
                <dd>不可用</dd>
                <dt>G4 / G5</dt>
                <dd>真实样品、事实、规则和授权需要独立确认</dd>
                <dt>视觉设计</dt>
                <dd>Agent 暂定版本，等待用户确认</dd>
                <dt>扩展模式 A / C</dt>
                <dd>尚未实现</dd>
              </dl>
            </div>
          </>
        ) : !current ? (
          <>
            <div className="page-heading">
              <div>
                <p className="eyebrow">EVIDENCE → DECISION → INTERNAL DRAFT</p>
                <h1>
                  {screen === "inbox"
                    ? "等待你的判断。"
                    : "产品开发，从一份 Case 开始。"}
                </h1>
                <p className="subtitle">
                  把原始证据、产品假设和人工决策放在同一条可追溯的链路上。
                </p>
              </div>
              <button
                className="primary"
                onClick={() => {
                  setBrief(emptyBrief);
                  setNewCase(true);
                }}
              >
                ＋ 创建产品 Case
              </button>
            </div>
            <div className="portfolio-line">
              <span>
                {cases.length.toString().padStart(2, "0")}{" "}
                <small>产品 Cases</small>
              </span>
              <p>
                所有成果默认为内部草稿，
                <br />
                真实上市准备需要样品与事实验证。
              </p>
            </div>
            <div className="case-table">
              <div className="table-head">
                <span>项目 / 产品方向</span>
                <span>当前阶段</span>
                <span>最近更新</span>
              </div>
              {cases
                .filter(
                  (c) => screen !== "inbox" || c.status === "needs_review",
                )
                .map((c, i) => (
                  <button
                    className="case-row"
                    key={c.id}
                    onClick={() => openCase(c.id)}
                  >
                    <span className="case-title">
                      <small>{(i + 1).toString().padStart(2, "0")}</small>
                      <span>
                        <strong>{c.title}</strong>
                        <em>
                          {c.is_synthetic ? "合成测试案例" : "用户导入数据"} ·
                          Brief v{c.brief_version}
                        </em>
                      </span>
                    </span>
                    <span>
                      <Badge tone="amber">{stages[c.stage] || c.stage}</Badge>
                    </span>
                    <span className="date">
                      {new Date(c.updated_at).toLocaleDateString("zh-CN")} ↗
                    </span>
                  </button>
                ))}
              {!cases.length && (
                <Empty>
                  创建第一份
                  Case，定义目标人群与待验证的问题，然后导入有权使用的原始资料。
                </Empty>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="case-heading">
              <div>
                <p className="eyebrow">
                  PRODUCT CASE <span>/{current.id.slice(0, 8)}</span>
                </p>
                <h1>{current.title}</h1>
                <div className="heading-badges">
                  <Badge tone="amber">
                    {currentGate} · {gateLabels[currentGate]}
                  </Badge>
                  {items("launch-packs").length > 0 && (
                    <Badge>
                      内部草稿 v{items("launch-packs").at(-1)!.version}
                    </Badge>
                  )}
                  {current.is_synthetic && <Badge>合成数据 / 功能测试</Badge>}
                  <span className="revision">
                    Brief v{current.brief_version} · 修订 {current.revision}
                  </span>
                </div>
              </div>
              <button className="secondary" onClick={refresh} disabled={busy}>
                ↻ 刷新
              </button>
            </div>
            <div className="case-tabs" role="tablist" aria-label="Case 内容">
              {tabs.map((t) => (
                <button
                  key={t}
                  role="tab"
                  aria-selected={tab === t}
                  className={tab === t ? "selected" : ""}
                  onClick={() => {
                    setTab(t);
                    setScreen("cases");
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
            <small className="scroll-hint">左右滑动切换 Case 工作区 →</small>
            <section role="tabpanel" aria-label={tab} className="tab-content">
              {tab === "总览" && (
                <>
                  <div className="next-step">
                    <div>
                      <p className="eyebrow">CURRENT DECISION GATE</p>
                      <h2>
                        当前 {currentGate} · {gateLabels[currentGate]}
                      </h2>
                      <p>
                        {items("launch-packs").length
                          ? "内部草稿已形成；真实产品验证仍需完成。"
                          : "每个决定绑定当前证据与规格版本。"}
                      </p>
                    </div>{" "}
                    <div className="actions">
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={nextAction().action}
                      >
                        {nextAction().label}
                      </button>
                      <button
                        className="text-button"
                        onClick={() => setTab("证据来源")}
                      >
                        查看 {items("evidence").length} 条证据 ↗
                      </button>
                    </div>
                  </div>
                  <div className="overview-grid">
                    <div className="paper brief-paper">
                      <p className="eyebrow">THE QUESTION</p>
                      <h2>我们在验证什么？</h2>
                      <p className="lead">{current.brief.problem_statement}</p>
                      <div className="brief-details">
                        <Meta
                          label="目标用户"
                          value={current.brief.target_segment}
                        />
                        <Meta label="产品类别" value={current.brief.category} />
                        <Meta label="目标市场" value="Amazon · United States" />
                      </div>
                    </div>
                    <div className="gate-rail">
                      <p className="eyebrow">HUMAN DECISION GATES</p>
                      {[
                        ["G1", "机会选择"],
                        ["G2", "概念与规格"],
                        ["G3", "可行性 / 样品调查"],
                        ["G4", "真实样品验证"],
                        ["G5", "上市交接审核"],
                      ].map(([gate, label]) => (
                        <div className="gate-step" key={gate}>
                          <b
                            className={
                              activeGate(gate)
                                ? "complete"
                                : gate === currentGate
                                  ? "current-gate"
                                  : ""
                            }
                          >
                            {gate}
                          </b>
                          <div>
                            <strong>{label}</strong>
                            <p>
                              {activeGate(gate)
                                ? `${activeGate(gate)?.is_synthetic ? "合成测试决定 · " : ""}${activeGate(gate)?.decision}`
                                : gate === "G4"
                                  ? "等待真实样品与测试"
                                  : gate === "G5"
                                    ? "事实 / 规则 / 权利尚待核实"
                                    : "待人工决策"}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="boundary-note">
                    <span>!</span>
                    <div>
                      <strong>可形成内部草稿，不能据此宣称产品可上市。</strong>
                      <p>
                        AI 推断、概念图和合成审批均不构成真实产品事实。G4 / G5
                        的验证责任始终保留。
                      </p>
                    </div>
                  </div>
                </>
              )}
              {tab === "证据来源" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">IMMUTABLE ORIGINALS</p>
                      <h2>原文是起点。</h2>
                    </div>
                    <span className="hint">
                      {items("sources").length} 个来源 ·{" "}
                      {items("evidence").length} 条去重观察
                    </span>
                  </div>
                  <div className="import-panel">
                    <label>
                      资料类型
                      <select
                        value={sourceType}
                        onChange={(e) => setSourceType(e.target.value)}
                      >
                        <option value="review">客户评价 / VOC</option>
                        <option value="competitor">竞品资料</option>
                        <option value="quote">供应商成本</option>
                        <option value="spec">产品资料</option>
                        <option value="sample">真实样品记录</option>
                        <option value="rule">规则来源</option>
                      </select>
                    </label>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={synthetic}
                        onChange={(e) => setSynthetic(e.target.checked)}
                      />
                      这是合成测试资料
                    </label>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={rights}
                        onChange={(e) => setRights(e.target.checked)}
                      />
                      我有权导入并用于内部研究
                    </label>
                    <label className="file-picker">
                      ＋ 导入文件
                      <input
                        aria-label="导入来源文件"
                        type="file"
                        accept=".csv,.json,.txt,.md"
                        disabled={busy}
                        onChange={(e) => {
                          if (e.target.files?.[0])
                            importFile(e.target.files[0]);
                          e.target.value = "";
                        }}
                      />
                    </label>
                    <p className="hint">
                      CSV / JSON / TXT / MD · 最大 1 MiB · 不抓取外部网页
                    </p>
                  </div>
                  <div className="source-list">
                    {items("sources").map((s) => (
                      <details key={s.id}>
                        <summary>
                          <strong>{s.filename}</strong>
                          <Badge>
                            {s.is_synthetic ? "SYNTHETIC" : s.rights_status}
                          </Badge>
                          <span>{s.source_type}</span>
                        </summary>
                        <p className="hash">SHA256 {s.sha256}</p>
                        <a
                          href={`/api/sources/${s.id}/content`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          打开不可变原文 ↗
                        </a>
                      </details>
                    ))}
                  </div>
                  {excerpt && (
                    <aside className="evidence-focus">
                      <button
                        className="text-button"
                        onClick={() => setExcerpt(null)}
                      >
                        关闭引用 ×
                      </button>
                      <p className="eyebrow">{excerpt.source_locator}</p>
                      <blockquote>{excerpt.quote}</blockquote>
                      <p>
                        产品 {excerpt.data.product_identity} · 变体{" "}
                        {excerpt.data.variant} ·{" "}
                        {excerpt.data.observed_at || "日期未知"}
                      </p>
                    </aside>
                  )}
                  <div className="evidence-table">
                    {items("evidence").map((e) => (
                      <button
                        key={e.id}
                        className="evidence-row"
                        onClick={() => setExcerpt(e)}
                      >
                        <span className="locator">
                          {e.source_locator}
                          <small>
                            {e.data.product_identity} / {e.data.variant}
                          </small>
                        </span>
                        <span>{e.quote}</span>
                        <span className="hint">原始观察 ↗</span>
                      </button>
                    ))}
                  </div>
                  {!items("sources").length && (
                    <Empty>
                      导入后，逐行引用、重复数据和原文哈希会显示在这里。
                    </Empty>
                  )}
                </>
              )}
              {tab === "VOC 研究" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">VOICE OF CUSTOMER</p>
                      <h2>保留分歧，不制造共识。</h2>
                    </div>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => run("research")}
                    >
                      运行研究
                    </button>
                  </div>
                  {items("research").at(-1) && (
                    <div className="research-note">
                      <Badge tone="amber">
                        {items("research").at(-1)?.data.sufficiency.status}
                      </Badge>
                      <p>
                        {items("research")
                          .at(-1)
                          ?.data.output.sample_limitations.join(" ")}
                      </p>
                      <small>
                        SDK Fake Model · 已记录 Skill 哈希 · 不代表真实模型效果
                      </small>
                    </div>
                  )}
                  <div className="insights">
                    {items("insights").map((i) => (
                      <article className="insight" key={i.id}>
                        <div>
                          <span className="eyebrow">
                            INFERRED / {i.data.confidence_class}
                          </span>
                          <h3>{i.data.name}</h3>
                          <p>{i.data.interpretation}</p>
                        </div>
                        <div>
                          <strong>
                            支持观察 · {i.data.supporting_evidence_refs.length}
                          </strong>
                          {refs(i.data.supporting_evidence_refs)}
                          <strong>
                            反证 / 不同体验 ·{" "}
                            {i.data.contradicting_evidence_refs.length}
                          </strong>
                          {refs(i.data.contradicting_evidence_refs)}
                        </div>
                      </article>
                    ))}
                  </div>
                  {!items("insights").length && (
                    <Empty>
                      先导入足够的评价，再运行研究。缺少证据时流程会请求补充资料。
                    </Empty>
                  )}
                </>
              )}
              {tab === "机会" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">G1 / OPPORTUNITY REVIEW</p>
                      <h2>值得验证的产品假设。</h2>
                    </div>
                    <button
                      className="secondary"
                      onClick={() => run("concepts")}
                      disabled={busy || activeGate("G1")?.decision !== "accept"}
                    >
                      从选中机会开发概念 →
                    </button>
                  </div>
                  {items("opportunities").map((o, i) => (
                    <article className="opportunity" key={o.id}>
                      <div className="opportunity-no">
                        {String(i + 1).padStart(2, "0")}
                      </div>
                      <div>
                        <div className="heading-badges">
                          <Badge>HYPOTHESIS</Badge>
                          <Badge tone="amber">
                            {o.data.data_sufficiency_status}
                          </Badge>
                        </div>
                        <h3>{o.data.title}</h3>
                        <p>{o.data.problem}</p>
                        <details>
                          <summary>假设、替代解释与证伪计划</summary>
                          <p>{o.data.assumptions.join(" · ")}</p>
                          <p>{o.data.alternatives.join(" · ")}</p>
                          <p>{o.data.falsification_plan}</p>
                        </details>
                        {refs(o.data.evidence_refs)}
                        <button
                          className="primary small"
                          disabled={busy}
                          onClick={() => gateReview("G1", o)}
                        >
                          审核机会
                        </button>
                        {activeGate("G1")?.subject_id === o.id && (
                          <Badge tone="green">当前选择</Badge>
                        )}
                      </div>
                    </article>
                  ))}
                  {!items("opportunities").length && (
                    <Empty>研究完成后，带引用的机会假设会出现在这里。</Empty>
                  )}
                </>
              )}
              {tab === "概念与 Spec" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">G2 / PRODUCT DEFINITION</p>
                      <h2>比较方向，明确未知。</h2>
                    </div>
                    <button
                      className="primary"
                      onClick={() => run("concepts")}
                      disabled={busy}
                    >
                      生成概念方向
                    </button>
                  </div>
                  <div className="concept-grid">
                    {items("concepts").map((c, i) => {
                      const spec = latestSpec(c.id);
                      return (
                        <article className="concept" key={c.id}>
                          <div className="concept-number">
                            DIRECTION {String(i + 1).padStart(2, "0")}
                          </div>
                          <h3>{c.data.title}</h3>
                          <p className="concept-intent">
                            {c.data.design_intent}
                          </p>
                          <ul>
                            {c.data.differentiators.map((d: string) => (
                              <li key={d}>{d}</li>
                            ))}
                          </ul>
                          <details>
                            <summary>工程风险与验证计划</summary>
                            <p>{c.data.risks.join(" · ")}</p>
                            <p>{c.data.validation_plan}</p>
                          </details>
                          {spec && (
                            <>
                              <div className="spec-heading">
                                <strong>Proposed Spec · v{spec.version}</strong>
                                <button
                                  className="text-button"
                                  onClick={() =>
                                    setSpecEdit(structuredClone(spec))
                                  }
                                >
                                  修订
                                </button>
                              </div>
                              <dl className="spec-list">
                                {spec.data.claims.map((claim: any) => (
                                  <div key={claim.name}>
                                    <dt>{claim.name}</dt>
                                    <dd>
                                      {claim.value || (
                                        <span className="unknown">
                                          尚未核实
                                        </span>
                                      )}
                                    </dd>
                                  </div>
                                ))}
                              </dl>
                            </>
                          )}
                          <div className="actions">
                            <button
                              className="primary small"
                              disabled={busy}
                              onClick={() => gateReview("G2", c)}
                            >
                              审核概念
                            </button>
                            {selectedConcept?.id === c.id && (
                              <Badge tone="green">已选 · 当前版本</Badge>
                            )}
                          </div>
                        </article>
                      );
                    })}
                  </div>
                  {items("spec-versions").length > 1 && (
                    <details className="paper">
                      <summary>Spec 版本历史与差异</summary>
                      {items("spec-versions").map((s) => (
                        <div className="history-row" key={s.id}>
                          <span>
                            v{s.version} · {s.data.reason}
                          </span>
                          {s.data.parent_spec_id && (
                            <button
                              className="text-button"
                              onClick={() =>
                                act(async () => {
                                  const d = await api(
                                    `product-cases/${current.id}/spec-diff?left=${s.data.parent_spec_id}&right=${s.id}`,
                                  );
                                  setDiff(d.changes);
                                })
                              }
                            >
                              比较前一版
                            </button>
                          )}
                        </div>
                      ))}
                      {diff &&
                        diff.map((d) => (
                          <p key={d.name}>
                            {d.name}：{d.before?.value || "未知"} →{" "}
                            {d.after?.value || "未知"}
                          </p>
                        ))}
                    </details>
                  )}
                  {!items("concepts").length && (
                    <Empty>
                      先在 G1 选择一个机会。概念为提案，不是已经存在的 SKU。
                    </Empty>
                  )}
                </>
              )}
              {tab === "可行性" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">G3 / COMMERCIAL FEASIBILITY</p>
                      <h2>不知道的成本，不能算成零。</h2>
                    </div>
                    <div className="actions">
                      <button
                        className="secondary"
                        onClick={() => {
                          setCosts({});
                          setCostEdit(true);
                        }}
                      >
                        录入假设场景
                      </button>
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() => run("feasibility")}
                      >
                        计算可行性
                      </button>
                    </div>
                  </div>
                  {items("feasibility").at(-1) ? (
                    (() => {
                      const f = items("feasibility").at(-1)!;
                      return (
                        <>
                          <div className="economics-summary">
                            <div>
                              <p className="eyebrow">UNIT CONTRIBUTION / USD</p>
                              <strong>
                                {f.data.economics.unit_contribution ?? "—"}
                              </strong>
                              <p>
                                {f.data.economics.unit_contribution === null
                                  ? "资料不足，无法计算"
                                  : "场景计算，不是盈利结论"}
                              </p>
                            </div>
                            <div>
                              <Badge tone="amber">
                                {f.data.economics.status}
                              </Badge>
                              <p>
                                按件计算 · 固定投入单列
                                <br />
                                FX、费用与数据有效期均需明确依据。
                              </p>
                              <button
                                className="primary"
                                disabled={busy}
                                onClick={() => gateReview("G3", f)}
                              >
                                审核可行性 / 样品调查
                              </button>
                            </div>
                          </div>
                          <div className="cost-table">
                            {Object.entries(f.data.economics.components).map(
                              ([key, value]) => (
                                <div key={key}>
                                  <span>{costNames[key] || key}</span>
                                  <strong>
                                    {value === null ? "未知" : `${value} USD`}
                                  </strong>
                                </div>
                              ),
                            )}
                          </div>
                          <h3 className="subhead">尚需负责人与证据的风险</h3>
                          <div className="risk-list">
                            {f.data.risks.map((r: any) => (
                              <div key={r.domain}>
                                <Badge tone="amber">待核实</Badge>
                                <strong>{r.domain}</strong>
                                <p>{r.question}</p>
                                <small>责任方：{r.owner}</small>
                              </div>
                            ))}
                          </div>
                        </>
                      );
                    })()
                  ) : (
                    <Empty>
                      选定概念后，计算已知与缺失费用。不内置未经核实的平台费率或供应商报价。
                    </Empty>
                  )}
                </>
              )}
              {tab === "视觉资产" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">
                        CREATIVEENGINE / INTERNAL CONCEPT
                      </p>
                      <h2>把想法看清，别把图像当事实。</h2>
                    </div>
                    <button
                      className="primary"
                      disabled={busy || !selectedConcept}
                      onClick={() =>
                        act(async () => {
                          await api(
                            `product-cases/${current.id}/visual-tasks`,
                            {
                              concept_id: selectedConcept!.id,
                              intent: "concept_exploration",
                              requirements: `Internal concept exploration: ${selectedConcept!.data.design_intent}. No verified product performance claims.`,
                              variants: 1,
                              budget_usd: 0,
                            },
                          );
                          await load(current.id);
                        })
                      }
                    >
                      ＋ 创建概念计划
                    </button>
                  </div>
                  <p className="hint">
                    仅内部用途 · Mock / Concept · 预算 $0 ·
                    计划批准与图片审核分别进行
                  </p>
                  {items("visual-tasks").map((v) => (
                    <article className="visual-task paper" key={v.id}>
                      <div className="section-heading">
                        <div>
                          <Badge tone={v.current ? "neutral" : "amber"}>
                            {v.current ? v.state : "版本已过期"}
                          </Badge>
                          <h3>{v.request.requirements}</h3>
                          <p className="hash">
                            计划哈希 {v.plan_hash || "尚无计划"}
                          </p>
                        </div>
                        <div className="actions">
                          {v.state === "awaiting_plan_review" && (
                            <button
                              className="primary"
                              disabled={busy}
                              onClick={() => visualReview(v)}
                            >
                              审核计划
                            </button>
                          )}
                          {v.state === "plan_approved" && (
                            <button
                              className="primary"
                              disabled={busy}
                              onClick={() =>
                                act(async () => {
                                  await api(`visual-tasks/${v.id}/submit`, {});
                                  await api(`visual-tasks/${v.id}/sync`, {});
                                  await load(current.id);
                                })
                              }
                            >
                              执行已批准计划
                            </button>
                          )}
                          {["submitted", "running", "reconciling"].includes(
                            v.state,
                          ) && (
                            <button
                              className="secondary"
                              disabled={busy}
                              onClick={() =>
                                act(async () => {
                                  await api(`visual-tasks/${v.id}/sync`, {});
                                  await load(current.id);
                                })
                              }
                            >
                              同步已有任务
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="asset-grid">
                        {v.assets.map((asset: Item) => (
                          <div key={asset.id} className="asset">
                            <img
                              src={`/api/visual-assets/${asset.id}/content`}
                              alt="MOCK 内部概念素材，不代表真实产品"
                            />
                            <div>
                              <Badge>MOCK · CONCEPT</Badge>
                              <p>
                                机器 QA：
                                {asset.qa.status === "warn"
                                  ? "有待确认项"
                                  : asset.qa.status === "block"
                                    ? "阻止使用"
                                    : "检查通过"}
                              </p>
                              <p className="hint">
                                {asset.qa.issues
                                  ?.map((issue: any) => issue.description)
                                  .join(" · ") ||
                                  "请结合原始 QA 记录核实素材。"}
                              </p>
                              <p className="hint">
                                {asset.identity === "mock"
                                  ? "固定 Mock 测试图片；未运行视觉语义检测，不验证产品性能。"
                                  : "概念图片不能作为实物验证依据。"}
                              </p>
                              <p>
                                人工审核：
                                {asset.review.decision === "approved"
                                  ? "已批准内部使用"
                                  : asset.review.decision === "rejected"
                                    ? "已拒绝"
                                    : "待独立审核"}
                              </p>
                              <button
                                className="secondary"
                                disabled={busy || !v.current}
                                onClick={() => visualReview(v, asset)}
                              >
                                审核图片资产
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      {v.error_code && (
                        <p className="error">
                          {v.error_code} · 研究与产品定义仍可继续
                        </p>
                      )}
                    </article>
                  ))}
                  {!items("visual-tasks").length && (
                    <Empty>
                      完成 G2 后，可以创建概念图计划。无真实产品照片时，正式
                      Listing 图像受阻。
                    </Empty>
                  )}
                </>
              )}
              {tab === "LaunchPack" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">INTERNAL DRAFT / HANDOFF</p>
                      <h2>可交接的草稿，明确未完成的验证。</h2>
                    </div>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() =>
                        act(async () => {
                          await api(
                            `product-cases/${current.id}/launch-packs`,
                            {},
                          );
                          await load(current.id);
                        })
                      }
                    >
                      {items("launch-packs").length
                        ? "生成内部草稿新版本"
                        : "生成内部 LaunchPack"}
                    </button>
                  </div>
                  {items("launch-packs").map((p) => (
                    <article className="pack paper" key={p.id}>
                      <div className="pack-banner">
                        INTERNAL DRAFT <span>v{p.version}</span>
                      </div>
                      <h3>{p.data.title}</h3>
                      <div className="heading-badges">
                        <Badge>内部使用</Badge>
                        <Badge tone="amber">不可发布</Badge>
                        {p.data.is_synthetic && <Badge>合成测试</Badge>}
                      </div>
                      <ul className="blockers">
                        {p.data.blockers.map((b: string) => (
                          <li key={b}>{b}</li>
                        ))}
                      </ul>
                      <p>
                        包括机会备忘录、概念比较、PRD、成本模型、风险表、原文附录和已审核内部素材。
                      </p>
                      <div className="actions">
                        {["json", "md", "zip"].map((f) => (
                          <a
                            className="download"
                            key={f}
                            href={`/api/launch-packs/${p.id}/export?format=${f}`}
                          >
                            下载 {f.toUpperCase()} ↗
                          </a>
                        ))}
                      </div>
                      <details>
                        <summary>版本追溯清单</summary>
                        <p className="hash">Spec {p.data.manifest.spec_hash}</p>
                        <p>
                          {p.data.manifest.sources.length} 个来源 ·{" "}
                          {p.data.manifest.assets.length} 个已审核内部素材 ·{" "}
                          {p.data.manifest.decisions.length} 条决策
                        </p>
                      </details>
                    </article>
                  ))}
                  {!items("launch-packs").length && (
                    <Empty>
                      先完成机会、概念审核及可行性分析。缺少样品时仍可生成内部草稿，G4/G5
                      不会因此通过。
                    </Empty>
                  )}
                </>
              )}
              {tab === "活动" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">APPEND-ONLY ACTIVITY</p>
                      <h2>每次变更，都有来处。</h2>
                    </div>
                    <a
                      className="text-button"
                      href={`/api/product-cases/${current.id}/events`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      事件回放 ↗
                    </a>
                  </div>
                  <ol className="timeline">
                    {items("activity")
                      .slice()
                      .reverse()
                      .map((e) => (
                        <li key={e.id}>
                          <span>{e.sequence.toString().padStart(2, "0")}</span>
                          <div>
                            <strong>{e.action}</strong>
                            <p>
                              {new Date(e.created_at).toLocaleString("zh-CN")} ·
                              操作者 {e.actor_id.slice(0, 8)}
                            </p>
                          </div>
                        </li>
                      ))}
                  </ol>
                </>
              )}
            </section>
          </>
        )}
        <footer>
          LAUNCHCASE <span>证据 / 推断 / 假设 / 决策，各有边界。</span>
          <small>V1 · INTERNAL WORKSPACE</small>
        </footer>
      </main>
      <dialog ref={dialog} onCancel={closeDialog} className="modal">
        <button
          className="close-dialog"
          aria-label="关闭对话框"
          onClick={closeDialog}
        >
          ×
        </button>
        {newCase && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              create();
            }}
          >
            <p className="eyebrow">NEW PRODUCT CASE</p>
            <h2>定义一个值得验证的问题。</h2>
            <button
              type="button"
              className="text-button"
              onClick={() => setBrief(fixtureBrief)}
            >
              载入合成宠物家具示例
            </button>
            <label>
              Case 名称
              <input
                required
                minLength={3}
                value={brief.title}
                onChange={(e) => setBrief({ ...brief, title: e.target.value })}
              />
            </label>
            <label>
              产品类别
              <input
                required
                minLength={2}
                value={brief.category}
                onChange={(e) =>
                  setBrief({ ...brief, category: e.target.value })
                }
              />
            </label>
            <label>
              目标用户
              <input
                required
                minLength={3}
                value={brief.target_segment}
                onChange={(e) =>
                  setBrief({ ...brief, target_segment: e.target.value })
                }
              />
            </label>
            <label>
              待验证的问题
              <textarea
                required
                minLength={10}
                value={brief.problem_statement}
                onChange={(e) =>
                  setBrief({ ...brief, problem_statement: e.target.value })
                }
              />
            </label>
            <p className="hint">
              Amazon US · 差异化开发 ·{" "}
              {brief.data_policy.is_synthetic
                ? "合成测试数据"
                : "用户资料，未经系统核实"}{" "}
              · 默认内部用途
            </p>
            <button className="primary" disabled={busy}>
              创建 Case
            </button>
          </form>
        )}
        {review && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                await api(review.endpoint, {
                  decision,
                  expected_subject_hash: review.hash,
                  reason,
                  ...review.subject,
                });
                setReview(null);
                if (current) await load(current.id);
                setNotice("决策已记录，并绑定本次审核的精确版本");
              });
            }}
          >
            <p className="eyebrow">HUMAN REVIEW / EXACT VERSION</p>
            <h2>{review.title}</h2>
            <p>
              该决定只适用于你正在审核的版本。资料或 Spec 变化后需要重新审核。
            </p>
            {current?.is_synthetic && (
              <p className="review-warning">
                这是合成测试 Case；本次决定不构成真实商业批准。
              </p>
            )}
            <label>
              决定
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
              >
                {review.options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              理由与适用边界
              <textarea
                autoFocus
                required
                minLength={5}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="说明为什么选择，以及仍需验证什么"
              />
            </label>
            <p className="hash">版本绑定 {review.hash}</p>
            <button className="primary" disabled={busy}>
              记录人工决定
            </button>
          </form>
        )}
        {specEdit && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                await api(
                  `product-cases/${current!.id}/concepts/${specEdit.data.concept_id}/spec-versions`,
                  {
                    expected_subject_hash: specEdit.sha256,
                    claims: specEdit.data.claims,
                    reason:
                      "Operator revised proposed fields; verification still pending",
                  },
                );
                setSpecEdit(null);
                await load(current!.id);
              });
            }}
          >
            <h2>修订提出的规格</h2>
            <p>修订创建新版本，旧审批失效。这里不能把提案改为已验证事实。</p>
            {specEdit.data.claims.map((claim: any, i: number) => (
              <label key={claim.name}>
                {claim.name}
                <input
                  placeholder="未知，留空"
                  value={claim.value || ""}
                  onChange={(e) => {
                    const next = structuredClone(specEdit);
                    next.data.claims[i].value = e.target.value || null;
                    next.data.claims[i].status = e.target.value
                      ? "proposed"
                      : "unknown";
                    setSpecEdit(next);
                  }}
                />
              </label>
            ))}
            <button className="primary" disabled={busy}>
              保存新 Spec 版本
            </button>
          </form>
        )}
        {costEdit && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                const components = Object.fromEntries(
                  Object.keys(costNames).map((name) => [
                    name,
                    {
                      amount: costs[name] || null,
                      currency: "USD",
                      unit: "piece",
                      provenance: costs[name] ? "assumption" : "missing",
                    },
                  ]),
                );
                await api(`product-cases/${current!.id}/feasibility`, {
                  components,
                  fixed_costs: {},
                  fx_rates: [],
                  assumptions: [
                    "Operator-entered scenario assumptions; not supplier quotations",
                  ],
                });
                setCostEdit(false);
                await load(current!.id);
              });
            }}
          >
            <h2>每件 USD · 假设场景</h2>
            <p>手工输入均标为假设，留空就是未知；零需要明确输入。</p>
            <div className="cost-inputs">
              {Object.entries(costNames).map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    inputMode="decimal"
                    pattern="[0-9]+(\.[0-9]{1,8})?"
                    value={costs[key] || ""}
                    onChange={(e) =>
                      setCosts({ ...costs, [key]: e.target.value })
                    }
                    placeholder="未知"
                  />
                </label>
              ))}
            </div>
            <button className="primary" disabled={busy}>
              保存并计算场景
            </button>
          </form>
        )}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </dialog>
    </div>
  );
}
