// Business wording for stored machine values. Records keep their original
// values; unknown values show a neutral label instead of a raw program field.
function lookup(table: Record<string, string>, value: unknown, other: string) {
  const key = String(value ?? "");
  return table[key] || (key ? other : "—");
}

export const tabGroups: { label: string; tabs: string[] }[] = [
  { label: "", tabs: ["总览"] },
  { label: "研究需求", tabs: ["证据来源", "用户反馈研究", "产品机会"] },
  { label: "选择方案", tabs: ["产品方案与规格", "概念图片"] },
  { label: "核算", tabs: ["成本与风险"] },
  { label: "验证与交接", tabs: ["样品与交接", "内部交接资料"] },
  { label: "记录", tabs: ["变更记录"] },
];

/** The five steps a user follows; G1–G5 remain only as a secondary reference. */
export const gateSteps = [
  {
    gate: "G1",
    name: "选择产品机会",
    done: "机会已选定",
    waiting: "待人工决定",
  },
  {
    gate: "G2",
    name: "选择产品方案",
    done: "方案已选定",
    waiting: "待人工决定",
  },
  {
    gate: "G3",
    name: "核算成本与风险",
    done: "已同意进行样品验证",
    waiting: "待人工决定",
  },
  {
    gate: "G4",
    name: "验证样品",
    done: "本次样品记录已确认",
    waiting: "等待真实样品与测试",
  },
  {
    gate: "G5",
    name: "整理内部交接",
    done: "内部交接已批准（未发布）",
    waiting: "事实、规则和权利尚待核实",
  },
];
export const gateName = (gate: string) =>
  gateSteps.find((s) => s.gate === gate)?.name || "人工审核";

export const stageLabels: Record<string, string> = {
  collecting_sources: "收集资料",
  opportunity_review: "待选择产品机会",
  concepting: "开发产品方案",
  concept_review: "待选择产品方案",
  feasibility_review: "待核算成本与风险",
  awaiting_sample_validation: "待验证样品",
  ready_for_internal_handoff: "内部资料已形成",
  launch_draft: "准备内部资料",
};
export const stageLabel = (value: unknown) =>
  lookup(stageLabels, value, "进行中");

const waiting: Record<string, string> = {
  G2: "下一步：选择产品方案（G2）",
  G3: "下一步：核算成本与风险（G3）",
  G4: "下一步：验证样品（G4）",
  G5: "下一步：整理内部交接（G5）",
  needs_input: "资料还不够，请先补充",
  complete_internal_handoff: "内部交接流程已同步",
};
export const waitingLabel = (value: unknown) =>
  lookup(waiting, value, "已完成，请查看结果");

const specFields: Record<string, string> = {
  design_direction: "设计方向",
  dimensions: "尺寸",
  material: "材质",
  load_rating: "承重",
  pet_safety: "宠物安全",
  manufacturing_tolerance: "制造公差",
  proposal: "方案说明",
};
export const specFieldLabel = (value: unknown) => {
  const key = String(value ?? "");
  return specFields[key] || (/^[a-z0-9_]+$/.test(key) ? "其他规格项" : key);
};

const sourceTypes: Record<string, string> = {
  review: "客户评价",
  competitor: "竞品资料",
  spec: "产品资料",
  quote: "供应商成本",
  sample: "真实样品记录",
  rule: "规则来源",
};
export const sourceTypeLabel = (value: unknown) =>
  lookup(sourceTypes, value, "其他资料");
const rights: Record<string, string> = {
  synthetic_fixture: "合成测试",
  authorized: "已授权",
  unknown: "权利未确认",
  revoked: "授权已撤销",
};
export const rightsLabel = (value: unknown) =>
  lookup(rights, value, "权利未确认");

const sufficiency: Record<string, string> = {
  conflicted: "用户反馈存在分歧",
  sufficient_for_draft: "足够形成内部草稿",
  needs_more_data: "资料不足，需要补充",
};
export const sufficiencyLabel = (value: unknown) =>
  lookup(sufficiency, value, "资料状态待确认");
const confidence: Record<string, string> = {
  limited: "依据有限",
  conflicted: "依据存在分歧",
};
export const confidenceLabel = (value: unknown) =>
  lookup(confidence, value, "依据待确认");

const economics: Record<string, string> = {
  needs_input: "缺少必要成本",
  conditional: "有前提条件的估算",
  calculated: "已完成场景计算",
};
export const economicsLabel = (value: unknown) =>
  lookup(economics, value, "待核对");

const visualStates: Record<string, string> = {
  awaiting_plan_review: "计划待审核",
  plan_approved: "计划已批准，待执行",
  rejected: "已拒绝",
  submitting: "正在提交",
  submitted: "已提交，等待结果",
  running: "制作中",
  reconciling: "正在核对结果",
  awaiting_asset_review: "图片待审核",
  approved: "图片已批准",
  blocked: "已受阻",
  cancelled: "已取消",
};
export const visualStateLabel = (value: unknown) =>
  lookup(visualStates, value, "处理中");

const riskDomains: Record<string, string> = {
  engineering: "工程",
  supply_chain: "供应链",
  compliance: "合规",
  returns: "退货",
  marketing: "市场",
};
export const riskDomainLabel = (value: unknown) => {
  const key = String(value ?? "");
  return riskDomains[key] || (/^[a-z0-9_]+$/.test(key) ? "其他风险" : key);
};
const riskQuestions: Record<string, string> = {
  engineering: "需要实测样机强度、公差和组装情况",
  supply_chain: "需要确认供应商报价、起订量、生产工艺和交期",
  compliance: "需要取得现行官方规则，并评估对本产品的适用性",
  returns: "需要用实际产品数据调查退货原因",
  marketing: "需要验证目标客户的问题和宣传内容的真实性",
};
export const riskQuestionLabel = (domain: unknown, question: string) =>
  riskQuestions[String(domain ?? "")] || question;
export const ownerLabel = (value: unknown) =>
  lookup({ product_owner: "产品负责人" }, value, "待指定");

const activities: Record<string, string> = {
  "case.created": "创建了产品项目",
  "brief.revised": "修订了项目需求",
  "source.imported": "导入了原始资料",
  "source.rights_changed": "更新了资料授权",
  "research.completed": "完成了用户反馈研究",
  "concepts.created": "生成了产品方案",
  "spec.revised": "修订了产品规格",
  "feasibility.calculated": "计算了成本场景",
  "gate.decided": "记录了人工决定",
  "sample.attested": "录入了样品记录",
  "rule.attested": "记录了规则复核",
  "handoff.prepared": "准备了交接材料",
  "launchpack.internal_draft_created": "生成了内部交接资料",
  "visual.created": "创建了概念图片任务",
  "visual.planned": "形成了概念图片计划",
  "visual.plan_reviewed": "审核了概念图片计划",
  "visual.submitting": "提交了概念图片任务",
  "visual.asset_reviewed": "审核了概念图片",
  "task.queued": "安排了处理任务",
  "task.finished": "处理任务已结束",
};
export const activityLabel = (value: unknown) =>
  lookup(activities, value, "其他系统记录");

const blockers: [RegExp, string][] = [
  [/^G4:/, "需要真实样品与测试确认"],
  [/^G5:/, "需要已核实的产品事实、当前适用规则和图片对外使用权"],
  [/^Unit economics incomplete/, "单件成本不完整；缺失的成本不能按 0 计算"],
  [/^Mock\/concept visuals/, "模拟图和概念图只能用于内部沟通"],
];
export const blockerLabel = (value: string) =>
  blockers.find(([pattern]) => pattern.test(value))?.[1] || value;

export const errorLabel = (value: unknown) => {
  const key = String(value ?? "");
  if (/rate|429/i.test(key)) return "服务繁忙，请稍后再试";
  if (/gate|blocked/i.test(key)) return "前置步骤尚未完成";
  if (/auth|unauthor|forbidden/i.test(key)) return "没有执行权限";
  return "未能完成，详情见技术信息";
};

export const dateTime = (value: unknown) => {
  const parsed = new Date(String(value ?? ""));
  return Number.isNaN(parsed.valueOf())
    ? String(value ?? "—")
    : parsed.toLocaleString("zh-CN");
};

const issueLabels: [RegExp, string][] = [
  [/^Fixed offline fixture/, "固定的离线测试图片，没有检查画面内容"],
  [
    /vision reviewer|semantic product fidelity/,
    "产品外观尚未自动核验，请人工确认",
  ],
  [/For Review label/, "概念图：请确认画面上有“概念 / 待审核”标识"],
];
/** Only an explicit pass reads as passed; missing or unknown results stay visible. */
export function qaResult(qa: any) {
  const status = String(qa?.status ?? "").toLowerCase();
  const issues: any[] = Array.isArray(qa?.issues) ? qa.issues : [];
  const checks: any[] = Array.isArray(qa?.checks) ? qa.checks : [];
  const blocking = (value: unknown) =>
    ["block", "blocked", "fail", "failed"].includes(
      String(value ?? "").toLowerCase(),
    );
  const notes = issues
    .map((issue) => String(issue?.description ?? issue?.message ?? ""))
    .filter(Boolean)
    .map(
      (note) =>
        issueLabels.find(([pattern]) => pattern.test(note))?.[1] || note,
    );
  if (
    blocking(status) ||
    issues.some((issue) => blocking(issue?.severity)) ||
    checks.some((check) => blocking(check?.status))
  )
    return { label: "阻止使用", detail: notes.join(" · ") };
  if (["pass", "passed"].includes(status) && !notes.length)
    return { label: "检查通过", detail: "没有自动发现问题，仍需人工核对。" };
  if (notes.length) return { label: "有待确认项", detail: notes.join(" · ") };
  return {
    label: "检查信息不完整",
    detail: "没有返回具体检查项，请人工核对。",
  };
}
