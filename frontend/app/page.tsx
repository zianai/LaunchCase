"use client";
import HandoffWorkspace from "./handoff";
import SkuWorkspace from "./sku";
import Provenance from "./provenance";
import {
  activityLabel,
  blockerLabel,
  confidenceLabel,
  dateTime,
  economicsLabel,
  errorLabel,
  gateName,
  gateSteps,
  ownerLabel,
  qaResult,
  riskDomainLabel,
  riskQuestionLabel,
  rightsLabel,
  sourceTypeLabel,
  specFieldLabel,
  stageLabel,
  sufficiencyLabel,
  tabGroups,
  visualStateLabel,
  waitingLabel,
} from "./labels";
import { useCallback, useEffect, useRef, useState } from "react";

type Item = { id: string; [key: string]: any };
type Review = {
  title: string;
  endpoint: string;
  hash: string;
  options: { value: string; label: string }[];
  subject?: { subject_type: string; subject_id: string };
};
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
  "samples",
  "truth",
  "rules",
  "handoff-preparations",
  "sku-images",
];
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
function TechDetails({
  label = "技术信息",
  children,
}: {
  label?: string;
  children: React.ReactNode;
}) {
  return (
    <details className="tech-details">
      <summary>{label}</summary>
      {children}
    </details>
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
    [sourceUrl, setSourceUrl] = useState(""),
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
        throw Error(`任务失败：${errorLabel(result.error_code)}`);
      await load(current.id);
      setNotice(
        result.status === "succeeded"
          ? `已完成。${waitingLabel(result.result.waiting_for)}`
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
          : activeGate("G5")
            ? "DONE"
            : "G5";
  const handoffDone = currentGate === "DONE";
  const approvedPack = handoffDone
    ? items("launch-packs").find((p) => p.id === activeGate("G5")?.subject_id)
    : undefined;
  const sampleLimits = items("truth")
    .filter((t) => t.data.limitations)
    .at(-1)?.data.limitations;
  const unverifiedSpecs: string[] =
    approvedPack?.data.listing_draft?.unsupported_claims_withheld || [];
  // The stage bar, primary action and remaining items all come from here.
  const stage = (): {
    step: string;
    detail: string;
    label?: string;
    action?: () => void;
  } => {
    const hasPack = items("launch-packs").length > 0;
    if (!items("sources").length)
      return {
        step: "研究需求",
        detail: "先导入有权使用的客户评价、竞品或产品资料。",
        label: "导入原始资料 →",
        action: () => setTab("证据来源"),
      };
    if (!items("research").length)
      return {
        step: "研究需求",
        detail: "资料已导入，下一步分析用户反馈。",
        label: "开始研究用户反馈 →",
        action: () => run("research"),
      };
    if (!activeGate("G1"))
      return {
        step: gateName("G1"),
        detail: "比较研究得出的产品机会，选定一个继续。",
        label: "审核产品机会 →",
        action: () => setTab("产品机会"),
      };
    if (!activeGate("G2"))
      return items("concepts").length
        ? {
            step: gateName("G2"),
            detail: "比较产品方案和规格，选定一个继续。",
            label: "比较并选择方案 →",
            action: () => setTab("产品方案与规格"),
          }
        : {
            step: gateName("G2"),
            detail: "机会已选定，下一步形成产品方案。",
            label: "生成产品方案 →",
            action: () => run("concepts"),
          };
    if (!activeGate("G3"))
      return items("feasibility").length
        ? {
            step: gateName("G3"),
            detail: "核对已知和缺失的成本，决定是否进行样品验证。",
            label: "审核成本与样品验证 →",
            action: () => setTab("成本与风险"),
          }
        : {
            step: gateName("G3"),
            detail: "方案已选定，下一步核算成本与风险。",
            label: "核算成本 →",
            action: () => run("feasibility"),
          };
    if (!activeGate("G4"))
      return hasPack
        ? {
            step: gateName("G4"),
            detail: "内部草稿已形成，但真实样品尚未验证。",
            label: "录入样品记录 →",
            action: () => setTab("样品与交接"),
          }
        : {
            step: gateName("G4"),
            detail: "可以先整理内部交接资料，真实样品验证仍需完成。",
            label: "准备内部交接资料 →",
            action: () => setTab("内部交接资料"),
          };
    if (!activeGate("G5"))
      return {
        step: gateName("G5"),
        detail: "本次样品记录已确认。接下来复核规则并提交内部交接审核。",
        label: "准备内部交接 →",
        action: () => setTab("样品与交接"),
      };
    return {
      step: "本轮内部交接已完成（未发布）",
      detail: current?.is_synthetic
        ? "这是测试数据，不能用于真实业务；交接批准也不代表可以发布。"
        : "交接批准不代表可以发布；对外使用前仍需单独确认。",
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
                { value: "select", label: "选择这个方案" },
                { value: "revise", label: "修改后重审" },
                { value: "reject", label: "否决" },
              ]
            : gate === "G4"
              ? [
                  { value: "hold", label: "暂缓，待补齐证据" },
                  {
                    value: "verify_sample",
                    label: "确认本次样品事实（不代表全部性能）",
                  },
                  { value: "rework", label: "返工重测" },
                ]
              : gate === "G5"
                ? [
                    { value: "needs_changes", label: "补充材料后重审" },
                    {
                      value: "internal_handoff",
                      label: "批准内部业务交接（不授权发布）",
                    },
                  ]
                : [
                    { value: "sample_validation", label: "同意进行样品验证" },
                    { value: "revise", label: "补充成本数据" },
                    { value: "hold", label: "暂缓" },
                  ];
      setReview({
        title: `${gateName(gate)} · ${subject.data.title || (gate === "G4" ? "样品事实与限制" : gate === "G3" ? "成本与样品验证" : "内部交接资料")}`,
        endpoint: `product-cases/${current.id}/gates/${gate}/decision`,
        hash: info.subject_hash,
        options,
        subject: {
          subject_type:
            gate === "G1"
              ? "opportunity"
              : gate === "G2"
                ? "concept"
                : gate === "G4"
                  ? "sample"
                  : gate === "G5"
                    ? "launch_pack"
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
        title: asset
          ? task.request?.intent === "listing"
            ? "审核严格保真商品素材（仅内部）"
            : "审核概念图片"
          : task.request?.intent === "listing"
            ? "审核严格保真计划（本地确定性合成）"
            : "审核概念图片计划（模拟制作，不产生费用）",
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
      setNotice("已刷新为最新数据");
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
        source_url: sourceUrl || null,
        rights_status: synthetic ? "synthetic_fixture" : "authorized",
        is_synthetic: synthetic,
      });
      await load(current.id);
      setNotice("原文已保存，并建立了逐行引用");
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
      if (!r.ok) throw Error("身份凭证无效，请向工作区管理员确认");
      setToken("");
      await loadCases();
      setCapabilities(await api("capabilities"));
    });

  if (!authenticated)
    return (
      <main className="login-shell">
        <div className="login-brand">
          <span className="monogram">LC</span>
          <span>LaunchCase</span>
        </div>
        <div className="login-copy">
          <p className="eyebrow">产品开发 · 亚马逊美国站</p>
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
          <p className="eyebrow">本地工作区</p>
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
            使用工作区管理员发放的身份凭证。凭证不会保存在浏览器页面中。
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
            LaunchCase<small>产品开发工作台</small>
          </span>
        </button>
        <div className="workspace-label">产品工作区</div>
        <nav aria-label="主导航">
          {[
            ["cases", "◫", "产品项目"],
            ["inbox", "◷", "审核收件箱"],
            ["sources", "≡", "来源与知识"],
            ["assets", "▧", "图片与素材"],
            ["settings", "⚙", "能力与设置"],
          ].map(([id, icon, label]) => (
            <button
              key={id}
              className={screen === id ? "active" : ""}
              onClick={() => {
                setScreen(id);
                if (id === "cases" || id === "inbox") setCurrent(null);
                if (id === "sources") setTab("证据来源");
                if (id === "assets") setTab("图片与素材");
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
          <span className="dot" /> 默认离线
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
            工作台 <i>/</i> {current ? current.title : "产品项目"}
          </span>
          <div>
            <span className="online-dot" /> 本地连接{" "}
            <span className="top-separator">|</span> 亚马逊美国站 · 差异化开发
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
                <p className="eyebrow">能力与设置</p>
                <h1>清楚知道，做到哪一步。</h1>
              </div>
            </div>
            <div className="paper">
              <h2>当前能力</h2>
              <dl className="definition">
                <dt>业务模式</dt>
                <dd>亚马逊美国站 · 差异化消费品开发</dd>
                <dt>研究运行</dt>
                <dd>本地模拟模型；结果不代表真实模型质量</dd>
                <dt>图片制作</dt>
                <dd>模拟制作 · 仅内部概念素材</dd>
                <dt>付费模型</dt>
                <dd>{capabilities?.paid_models ? "启用" : "关闭"}</dd>
                <dt>对外发布</dt>
                <dd>不可用</dd>
                <dt>运行拓扑</dt>
                <dd>单主机 · 未验证多主机共享</dd>
                <dt>样品验证与内部交接</dt>
                <dd>真实样品、事实、规则和授权需要独立确认</dd>
                <dt>界面设计</dt>
                <dd>暂定版本，等待业务确认</dd>
                <dt>其他开发模式</dt>
                <dd>尚未实现</dd>
              </dl>
            </div>
          </>
        ) : !current ? (
          <>
            <div className="page-heading">
              <div>
                <p className="eyebrow">
                  研究需求 → 选择方案 → 核算 → 验证样品 → 内部交接
                </p>
                <h1>
                  {screen === "inbox"
                    ? "等待你的判断。"
                    : "产品开发，从一个项目开始。"}
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
                ＋ 创建产品项目
              </button>
            </div>
            <div className="portfolio-line">
              <span>
                {cases.length.toString().padStart(2, "0")}{" "}
                <small>个产品项目</small>
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
                          {c.is_synthetic ? "合成测试项目" : "用户导入数据"} ·
                          需求第 {c.brief_version} 版
                        </em>
                      </span>
                    </span>
                    <span>
                      <Badge tone="amber">{stageLabel(c.stage)}</Badge>
                    </span>
                    <span className="date">
                      {new Date(c.updated_at).toLocaleDateString("zh-CN")} ↗
                    </span>
                  </button>
                ))}
              {!cases.length && (
                <Empty>
                  创建第一个项目，写清目标人群与待验证的问题，然后导入有权使用的原始资料。
                </Empty>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="case-heading">
              <div>
                <p className="eyebrow">产品项目</p>
                <h1>{current.title}</h1>
                <div className="heading-badges">
                  {items("launch-packs").length > 0 && (
                    <Badge>
                      内部交接资料第 {items("launch-packs").at(-1)!.version} 版
                    </Badge>
                  )}
                  {current.is_synthetic && <Badge>合成数据 / 功能测试</Badge>}
                  <span className="revision">
                    需求第 {current.brief_version} 版 · 第 {current.revision}{" "}
                    次修订
                  </span>
                </div>
              </div>
              <button className="secondary" onClick={refresh} disabled={busy}>
                ↻ 刷新
              </button>
            </div>
            <div className={handoffDone ? "next-step done" : "next-step"}>
              <div>
                <p className="eyebrow">
                  {handoffDone ? "当前结果" : "当前阶段"}
                  {!handoffDone && <span> · {currentGate}</span>}
                </p>
                <h2>{stage().step}</h2>
                <p>{stage().detail}</p>
                {handoffDone && (
                  <ul className="remaining">
                    {sampleLimits && <li>本次样品未覆盖：{sampleLimits}</li>}
                    {unverifiedSpecs.length > 0 && (
                      <li>
                        对外仍不能声明：
                        {[...new Set(unverifiedSpecs.map(specFieldLabel))].join(
                          "、",
                        )}
                      </li>
                    )}
                  </ul>
                )}
              </div>
              <div className="actions">
                {handoffDone ? (
                  <>
                    <a
                      className="download primary-link"
                      href={`/api/launch-packs/${activeGate("G5")?.subject_id}/handoff-export`}
                    >
                      下载内部交接包 ↗
                    </a>
                    <a
                      className="text-button"
                      href={`/api/launch-packs/${activeGate("G5")?.subject_id}/handoff-receipt`}
                    >
                      查看批准回执 ↗
                    </a>
                  </>
                ) : (
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={stage().action}
                  >
                    {stage().label}
                  </button>
                )}
              </div>
            </div>
            <div className="case-tabs" role="tablist" aria-label="项目内容">
              {tabGroups.map((group) => (
                <div
                  className="tab-group"
                  role="presentation"
                  key={group.tabs[0]}
                >
                  {group.label && (
                    <span className="tab-group-label" aria-hidden="true">
                      {group.label}
                    </span>
                  )}
                  <div role="presentation">
                    {group.tabs.map((t) => (
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
                </div>
              ))}
            </div>
            <small className="scroll-hint">左右滑动查看更多内容 →</small>
            <section role="tabpanel" aria-label={tab} className="tab-content">
              {tab === "总览" && (
                <>
                  <div className="overview-grid">
                    <div className="paper brief-paper">
                      <p className="eyebrow">项目需求</p>
                      <h2>我们在验证什么？</h2>
                      <p className="lead">{current.brief.problem_statement}</p>
                      <div className="brief-details">
                        <Meta
                          label="目标用户"
                          value={current.brief.target_segment}
                        />
                        <Meta label="产品类别" value={current.brief.category} />
                        <Meta label="目标市场" value="亚马逊美国站" />
                      </div>
                    </div>
                    <div className="gate-rail">
                      <p className="eyebrow">人工决定进度</p>
                      {gateSteps.map(({ gate, name, done, waiting }, index) => (
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
                            {index + 1}
                          </b>
                          <div>
                            <strong>{name}</strong>
                            <p>
                              {activeGate(gate)
                                ? `${activeGate(gate)?.is_synthetic ? "合成测试决定 · " : ""}${done}`
                                : waiting}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setTab("证据来源")}
                  >
                    查看 {items("evidence").length} 条原始依据 ↗
                  </button>
                  <div className="boundary-note">
                    <span>!</span>
                    <div>
                      <strong>可形成内部草稿，不能据此宣称产品可上市。</strong>
                      <p>
                        AI
                        推断、概念图和测试审批都不是真实产品事实，样品验证和内部交接的责任始终保留。
                      </p>
                    </div>
                  </div>
                </>
              )}
              {tab === "证据来源" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">原始资料</p>
                      <h2>原文是起点。</h2>
                    </div>
                    <span className="hint">
                      {items("sources").length} 个来源 ·{" "}
                      {items("evidence").length} 条去重后的观察
                    </span>
                  </div>
                  <div className="import-panel">
                    <label>
                      资料类型
                      <select
                        value={sourceType}
                        onChange={(e) => setSourceType(e.target.value)}
                      >
                        <option value="review">客户评价</option>
                        <option value="competitor">竞品资料</option>
                        <option value="quote">供应商成本</option>
                        <option value="spec">产品资料</option>
                        <option value="sample">真实样品记录</option>
                        <option value="rule">规则来源</option>
                        <option value="rights">素材权利证明</option>
                      </select>
                    </label>
                    <label>
                      来源 URL（规则必填；样品原始记录留空）
                      <input
                        type="url"
                        value={sourceUrl}
                        onChange={(e) => setSourceUrl(e.target.value)}
                        placeholder="https://官方来源"
                      />
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
                            {s.is_synthetic
                              ? "合成测试"
                              : rightsLabel(s.rights_status)}
                          </Badge>
                          <span>{sourceTypeLabel(s.source_type)}</span>
                        </summary>
                        <a
                          href={`/api/sources/${s.id}/content`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          打开原文 ↗
                        </a>
                        <TechDetails>
                          <p className="hash">原文校验值 {s.sha256}</p>
                        </TechDetails>
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
                    <Empty>导入后，逐行引用和重复数据提示会显示在这里。</Empty>
                  )}
                </>
              )}
              {tab === "用户反馈研究" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">用户反馈研究</p>
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
                        {sufficiencyLabel(
                          items("research").at(-1)?.data.sufficiency.status,
                        )}
                      </Badge>
                      <p>
                        {items("research")
                          .at(-1)
                          ?.data.output.sample_limitations.join(" ")}
                      </p>
                      <small>
                        {items("research").at(-1)?.data.status ===
                        "tested_live_scoped"
                          ? "授权范围内的模型输出；事实与业务仍待人工评审"
                          : "由本地模拟模型生成，不代表真实模型效果"}
                      </small>
                    </div>
                  )}
                  <div className="insights">
                    {items("insights").map((i) => (
                      <article className="insight" key={i.id}>
                        <div>
                          <span className="eyebrow">
                            推断 · {confidenceLabel(i.data.confidence_class)}
                          </span>
                          <h3>{i.data.name}</h3>
                          <p>{i.data.interpretation}</p>
                          <Provenance id={i.id} api={api} />
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
              {tab === "产品机会" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">产品机会</p>
                      <h2>值得验证的产品假设。</h2>
                    </div>
                    <button
                      className="secondary"
                      onClick={() => run("concepts")}
                      disabled={busy || activeGate("G1")?.decision !== "accept"}
                    >
                      从选中机会生成产品方案 →
                    </button>
                  </div>
                  {items("opportunities").map((o, i) => (
                    <article className="opportunity" key={o.id}>
                      <div className="opportunity-no">
                        {String(i + 1).padStart(2, "0")}
                      </div>
                      <div>
                        <div className="heading-badges">
                          <Badge>待验证假设</Badge>
                          <Badge tone="amber">
                            {sufficiencyLabel(o.data.data_sufficiency_status)}
                          </Badge>
                          {activeGate("G1")?.subject_id === o.id && (
                            <Badge tone="green">当前选择</Badge>
                          )}
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
                      </div>
                    </article>
                  ))}
                  {!items("opportunities").length && (
                    <Empty>研究完成后，带引用的机会假设会出现在这里。</Empty>
                  )}
                </>
              )}
              {tab === "产品方案与规格" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">产品方案与规格</p>
                      <h2>比较方向，明确未知。</h2>
                    </div>
                    <button
                      className="primary"
                      onClick={() => run("concepts")}
                      disabled={busy}
                    >
                      生成产品方案
                    </button>
                  </div>
                  <div className="concept-grid">
                    {items("concepts").map((c, i) => {
                      const spec = latestSpec(c.id);
                      // One shared row order keeps specs comparable side by side.
                      const specRows: string[] = [
                        ...new Set<string>(
                          items("concepts").flatMap((other) =>
                            (latestSpec(other.id)?.data.claims || []).map(
                              (claim: any) => claim.name,
                            ),
                          ),
                        ),
                      ];
                      return (
                        <article className="concept" key={c.id}>
                          <div className="concept-number">
                            <span>方案 {i + 1}</span>
                            {selectedConcept?.id === c.id && (
                              <Badge tone="green">已选 · 当前版本</Badge>
                            )}
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
                                <strong>
                                  产品规格草案 · 第 {spec.version} 版
                                </strong>
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
                                {specRows.map((name) => {
                                  const claim = spec.data.claims.find(
                                    (x: any) => x.name === name,
                                  );
                                  return (
                                    <div key={name}>
                                      <dt>{specFieldLabel(name)}</dt>
                                      <dd>
                                        {claim?.value || (
                                          <span className="unknown">
                                            尚未核实
                                          </span>
                                        )}
                                      </dd>
                                    </div>
                                  );
                                })}
                              </dl>
                              <TechDetails>
                                <p className="hash">
                                  字段 {specRows.join(" / ")}
                                  <br />
                                  规格校验值 {spec.sha256}
                                </p>
                              </TechDetails>
                            </>
                          )}
                          <div className="actions">
                            <button
                              className="primary small"
                              disabled={busy}
                              onClick={() => gateReview("G2", c)}
                            >
                              审核方案
                            </button>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                  {items("spec-versions").length > 1 && (
                    <details className="paper">
                      <summary>规格版本历史与差异</summary>
                      {items("spec-versions").map((s) => (
                        <div className="history-row" key={s.id}>
                          <span>
                            第 {s.version} 版 ·{" "}
                            {s.data.parent_spec_id ? "人工修订" : "初始草案"}
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
                            {specFieldLabel(d.name)}：
                            {d.before?.value || "未知"} →{" "}
                            {d.after?.value || "未知"}
                          </p>
                        ))}
                    </details>
                  )}
                  {!items("concepts").length && (
                    <Empty>
                      先选定一个产品机会。方案只是提案，不是已经存在的 SKU。
                    </Empty>
                  )}
                </>
              )}
              {tab === "成本与风险" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">成本与风险</p>
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
                        核算成本
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
                              <p className="eyebrow">单件贡献（美元）</p>
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
                                {economicsLabel(f.data.economics.status)}
                              </Badge>
                              <p>
                                按件计算 · 固定投入单列
                                <br />
                                汇率、费用与数据有效期都需要明确依据。
                              </p>
                              <button
                                className="primary"
                                disabled={busy}
                                onClick={() => gateReview("G3", f)}
                              >
                                审核成本与样品验证
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
                                <strong>{riskDomainLabel(r.domain)}</strong>
                                <p>{riskQuestionLabel(r.domain, r.question)}</p>
                                <small>责任方：{ownerLabel(r.owner)}</small>
                              </div>
                            ))}
                          </div>
                        </>
                      );
                    })()
                  ) : (
                    <Empty>
                      选定方案后，核算已知与缺失的费用。系统不内置未经核实的平台费率或供应商报价。
                    </Empty>
                  )}
                </>
              )}
              {tab === "图片与素材" && (
                <>
                  <SkuWorkspace
                    key={current.id}
                    current={current}
                    data={data}
                    busy={busy}
                    api={api}
                    act={act}
                    reload={() => load(current.id)}
                  />
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">概念图片 · 仅内部使用</p>
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
                      ＋ 创建概念图片计划
                    </button>
                  </div>
                  <p className="hint">
                    仅内部使用 · 模拟制作 · 不产生费用 ·
                    计划批准与图片审核分别进行
                  </p>
                  {items("visual-tasks").map((v) => (
                    <article className="visual-task paper" key={v.id}>
                      <div className="section-heading">
                        <div>
                          <Badge tone={v.current ? "neutral" : "amber"}>
                            {v.current
                              ? visualStateLabel(v.state)
                              : "方案已更新，此任务已过期"}
                          </Badge>
                          <h3>{v.request.requirements}</h3>
                          <TechDetails>
                            <p className="hash">
                              计划校验值 {v.plan_hash || "尚无计划"}
                            </p>
                          </TechDetails>
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
                              刷新制作进度
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="asset-grid">
                        {v.assets.map((asset: Item) => (
                          <div key={asset.id} className="asset">
                            <img
                              src={`/api/visual-assets/${asset.id}/content`}
                              alt={
                                asset.identity === "real_product"
                                  ? "基于授权原图的严格保真商品素材，仅内部使用"
                                  : "模拟或概念图片，不代表真实产品"
                              }
                            />
                            <div>
                              <Badge>
                                {asset.identity === "real_product"
                                  ? "原图确定性合成 · 仅内部"
                                  : asset.identity === "mock"
                                    ? "模拟图 · 概念"
                                    : "生成概念图 · 非产品事实"}
                              </Badge>
                              <p>
                                自动检查：
                                {qaResult(asset.qa).label}
                              </p>
                              <p className="hint">
                                {qaResult(asset.qa).detail}
                              </p>
                              <p className="hint">
                                {asset.identity === "mock"
                                  ? "固定的模拟测试图片；没有检查画面内容，也不验证产品性能。"
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
                                审核这张图片
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      {v.error_code && (
                        <p className="error">
                          {errorLabel(v.error_code)} · 研究与产品定义仍可继续
                        </p>
                      )}
                    </article>
                  ))}
                  {!items("visual-tasks").length && (
                    <Empty>
                      选定产品方案后，可以创建概念图片计划。没有真实产品照片时，不能制作正式商品图。
                    </Empty>
                  )}
                </>
              )}
              {tab === "样品与交接" && (
                <HandoffWorkspace
                  current={current}
                  data={data}
                  busy={busy}
                  api={api}
                  act={act}
                  reload={() => load(current.id)}
                  review={gateReview}
                />
              )}
              {tab === "内部交接资料" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">内部交接资料</p>
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
                        ? "生成新版本"
                        : "生成内部交接资料"}
                    </button>
                  </div>
                  {items("launch-packs").map((p) => (
                    <article className="pack paper" key={p.id}>
                      <div className="pack-banner">
                        内部草稿 <span>第 {p.version} 版</span>
                      </div>
                      <h3>{p.data.title}</h3>
                      <div className="heading-badges">
                        <Badge>内部使用</Badge>
                        <Badge tone="amber">不可发布</Badge>
                        {p.data.is_synthetic && <Badge>合成测试</Badge>}
                      </div>
                      <ul className="blockers">
                        {p.data.blockers.map((b: string) => (
                          <li key={b}>{blockerLabel(b)}</li>
                        ))}
                      </ul>
                      <p>
                        包括机会备忘录、方案比较、产品需求文档、成本模型、风险表、原文附录和已审核的内部素材。
                      </p>
                      <div className="actions">
                        {[
                          ["zip", "完整资料包 ZIP"],
                          ["md", "文档 Markdown"],
                          ["json", "JSON"],
                        ].map(([f, name]) => (
                          <a
                            className="download"
                            key={f}
                            href={`/api/launch-packs/${p.id}/export?format=${f}`}
                          >
                            下载 {name} ↗
                          </a>
                        ))}
                      </div>
                      <details>
                        <summary>版本追溯清单</summary>
                        <p className="hash">
                          规格校验值 {p.data.manifest.spec_hash}
                        </p>
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
                      先完成机会、方案审核和成本核算。缺少样品时仍可生成内部草稿，但样品验证和内部交接不会因此通过。
                    </Empty>
                  )}
                </>
              )}
              {tab === "变更记录" && (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">变更记录</p>
                      <h2>每次变更，都有来处。</h2>
                    </div>
                    <a
                      className="text-button"
                      href={`/api/product-cases/${current.id}/events`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      查看原始事件 ↗
                    </a>
                  </div>
                  <ol className="timeline">
                    {items("activity")
                      .slice()
                      .reverse()
                      .map((e) => (
                        <li key={e.id}>
                          <span>{e.sequence}</span>
                          <div>
                            <strong>{activityLabel(e.action)}</strong>
                            <p>{dateTime(e.created_at)}</p>
                            <TechDetails>
                              <p className="hash">
                                {e.action} · 操作者 {e.actor_id}
                              </p>
                            </TechDetails>
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
          LaunchCase <span>证据、推断、假设和决定，各有边界。</span>
          <small>内部工作区</small>
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
            <p className="eyebrow">新建产品项目</p>
            <h2>定义一个值得验证的问题。</h2>
            <button
              type="button"
              className="text-button"
              onClick={() => setBrief(fixtureBrief)}
            >
              载入合成宠物家具示例
            </button>
            <label>
              项目名称
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
              亚马逊美国站 · 差异化开发 ·{" "}
              {brief.data_policy.is_synthetic
                ? "合成测试数据"
                : "用户资料，未经系统核实"}{" "}
              · 默认内部用途
            </p>
            <button className="primary" disabled={busy}>
              创建项目
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
                setNotice("决定已记录，只对本次审核的这一版有效");
              });
            }}
          >
            <p className="eyebrow">人工决定</p>
            <h2>{review.title}</h2>
            <p>
              该决定只适用于你正在审核的这一版。资料或规格变化后需要重新审核。
            </p>
            {current?.is_synthetic && (
              <p className="review-warning">
                这是合成测试项目；本次决定不构成真实商业批准。
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
            <TechDetails>
              <p className="hash">本次决定对应的版本校验值 {review.hash}</p>
            </TechDetails>
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
                {specFieldLabel(claim.name)}
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
              保存为新版本
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
            <h2>每件成本（美元）· 假设场景</h2>
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
