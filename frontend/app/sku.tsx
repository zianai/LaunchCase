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
};

export default function SkuWorkspace({
  current,
  data,
  busy,
  api,
  act,
  reload,
}: Props) {
  const [sku, setSku] = useState("");
  const [kind, setKind] = useState("product_photo");
  const [source, setSource] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [expires, setExpires] = useState("");
  const [cleared, setCleared] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [rule, setRule] = useState("");
  const [reason, setReason] = useState("");
  const [reviewId, setReviewId] = useState("");
  const [reviewDecision, setReviewDecision] = useState("rejected");
  const items = (name: string) => data[name] || [];
  const images = items("sku-images");
  const rights = items("sources").filter((s) => s.source_type === "rights");
  const g2 = items("gates").find(
    (g) => g.gate === "G2" && g.status === "current" && g.decision === "select",
  );
  const g4 = items("gates").find(
    (g) =>
      g.gate === "G4" &&
      g.status === "current" &&
      g.decision === "verify_sample",
  );
  const sample = items("samples").find((s) => s.id === g4?.subject_id);
  const truth = items("truth").find((t) => t.id === sample?.data.truth_id);
  const upload = () =>
    act(async () => {
      if (!file || !cleared) throw Error("请选择原图并确认当前使用权");
      if (
        file.size > 1048576 ||
        !["image/png", "image/jpeg", "image/webp"].includes(file.type)
      )
        throw Error("只接受 1 MiB 以内的 PNG、JPEG 或 WebP");
      const bytes = new Uint8Array(await file.arrayBuffer());
      const hash = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
      )
        .map((n) => n.toString(16).padStart(2, "0"))
        .join("");
      let binary = "";
      for (const byte of bytes) binary += String.fromCharCode(byte);
      await api(`product-cases/${current.id}/sku-images`, {
        sku,
        filename: file.name,
        kind,
        data_base64: btoa(binary),
        original_sha256: hash,
        is_synthetic: current.is_synthetic,
        rights: {
          source_id: source,
          exact_excerpt: excerpt,
          expires_at_utc: new Date(expires).toISOString(),
          external_allowed: cleared,
        },
      });
      setCleared(false);
      await reload();
    });
  const blocked =
    !g2 ||
    !g4 ||
    !truth ||
    !rule ||
    !selected.some((id) =>
      images.some(
        (i) =>
          i.id === id &&
          i.metadata_json.kind === "cutout" &&
          i.eligibility.current,
      ),
    );
  return (
    <section className="paper sku-workspace" aria-labelledby="sku-title">
      <p className="eyebrow">原始素材 → 真实产品事实 → 严格保真</p>
      <h3 id="sku-title">SKU 原图与授权</h3>
      <p className="review-warning">
        原图、概念图与生成图分别保存。图片审核、样品确认和内部交接是独立决定；这里不授权发布。
        {current.is_synthetic
          ? " 当前为合成测试项目，不能升级为真实 SKU。"
          : ""}
      </p>
      <details open={!images.length}>
        <summary>上传产品照片或透明抠图</summary>
        <form
          className="sku-form"
          onSubmit={(e) => {
            e.preventDefault();
            upload();
          }}
        >
          <label>
            SKU / 样品编号
            <input
              required
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              pattern="[A-Za-z0-9_.:\-]+"
              maxLength={160}
            />
          </label>
          <label>
            原图用途
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="product_photo">产品原始照片</option>
              <option value="cutout">透明抠图（保持产品结构）</option>
              <option value="logo">授权 Logo</option>
            </select>
          </label>
          <label>
            图片文件
            <input
              required
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          <p className="hint">
            上限 1 MiB / 800
            万像素。浏览器计算原始文件哈希，服务端校验解码内容；预览移除图片元数据。
          </p>
          <label>
            权利证明来源
            <select
              required
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              <option value="">先在「证据来源」导入素材权利证明</option>
              {rights.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.filename} · {s.rights_status}
                </option>
              ))}
            </select>
          </label>
          <label>
            权利原文摘录
            <textarea
              required
              minLength={20}
              maxLength={3000}
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
            />
          </label>
          <label>
            权利复核截止时间
            <input
              type="datetime-local"
              required
              value={expires}
              onChange={(e) => setExpires(e.target.value)}
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={cleared}
              onChange={(e) => setCleared(e.target.checked)}
            />
            我有权导入此原图，且权利证明允许向本地图片服务传输；这不批准发布
          </label>
          <button className="secondary" disabled={busy || !cleared || !file}>
            保存原始素材，等待独立审核
          </button>
        </form>
      </details>
      <div className="sku-sources">
        {images.map((image) => (
          <article key={image.id} className="sku-source">
            <img
              src={`/api/sku-images/${image.id}/content`}
              alt={`${image.is_synthetic ? "合成测试" : "原始"} ${image.metadata_json.kind} · ${image.metadata_json.sku}`}
            />
            <div>
              <h4>{image.filename}</h4>
              <p>
                {image.is_synthetic ? "合成测试素材" : "原始素材（非生成图）"} ·
                SKU {image.metadata_json.sku}
              </p>
              <p role="status">
                {image.eligibility.current
                  ? "原图审核有效；仍需样品、事实和规则"
                  : `待核验 / 已失效：${image.eligibility.reason}`}
              </p>
              <details>
                <summary>来源、权利与版本</summary>
                <p>来源 {image.id}</p>
                <p className="hash">原图 SHA-256 {image.sha256}</p>
                <p className="hash">审核对象 {image.subject_hash}</p>
                <q>{image.metadata_json.rights.exact_excerpt}</q>
                <p>截止 {image.metadata_json.rights.expires_at_utc}</p>
                <a
                  href={`/api/sources/${image.metadata_json.rights.source_id}/content`}
                  target="_blank"
                  rel="noreferrer"
                >
                  查看权利原文 ↗
                </a>
              </details>
              <button
                className="secondary"
                disabled={busy || !image.review_allowed}
                onClick={() => {
                  setReviewId(image.id);
                  setReviewDecision("rejected");
                  setReason("");
                }}
              >
                审核原始素材
              </button>
              {reviewId === image.id && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    act(async () => {
                      await api(`sku-images/${image.id}/review`, {
                        expected_subject_hash: image.subject_hash,
                        decision: reviewDecision,
                        reason,
                      });
                      setReviewId("");
                      await reload();
                    });
                  }}
                >
                  <label>
                    原图审核决定
                    <select
                      value={reviewDecision}
                      onChange={(e) => setReviewDecision(e.target.value)}
                    >
                      <option value="rejected">拒绝 / 补充证据</option>
                      <option value="approved">确认当前原图与权利</option>
                    </select>
                  </label>
                  <label>
                    原图审核理由
                    <textarea
                      required
                      minLength={10}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </label>
                  <button disabled={busy}>记录原图决定</button>
                </form>
              )}
              <label className="check">
                <input
                  type="checkbox"
                  disabled={
                    !image.eligibility.current ||
                    image.metadata_json.kind === "logo"
                  }
                  checked={selected.includes(image.id)}
                  onChange={(e) =>
                    setSelected(
                      e.target.checked
                        ? [...selected, image.id]
                        : selected.filter((id) => id !== image.id),
                    )
                  }
                />
                用于严格保真计划
              </label>
            </div>
          </article>
        ))}
      </div>
      <h4>严格保真商品素材计划</h4>
      <p>
        当前样品：{sample?.data.sample_identifier || "未确认"} · 事实快照：
        {truth ? `第 ${truth.version} 版` : "未确认"} · 仅确定性复用或合成。
      </p>
      {truth && (
        <details>
          <summary>已确认事实与原文</summary>
          {truth.data.facts.map((fact: any, i: number) => (
            <p key={i}>
              {fact.name}: {fact.value} · {fact.status}
              <br />
              <q>{fact.exact_excerpt}</q>
              <br />
              <a href={`/api/sources/${fact.source_id}/content`}>
                查看事实来源 ↗
              </a>
            </p>
          ))}
        </details>
      )}
      <label>
        本次适用规则
        <select value={rule} onChange={(e) => setRule(e.target.value)}>
          <option value="">选择已复核规则</option>
          {items("rules").map((r) => (
            <option key={r.id} value={r.id}>
              {r.data.revision} · 第 {r.version} 版
            </option>
          ))}
        </select>
      </label>
      {blocked && (
        <p role="status">
          需要当前
          G2、G4、事实快照、适用规则及已审核透明抠图。缺项时不会改用概念生成。
        </p>
      )}
      <button
        className="secondary"
        disabled={busy || blocked}
        onClick={() =>
          act(async () => {
            await api(`product-cases/${current.id}/visual-tasks`, {
              concept_id: g2!.subject_id,
              intent: "listing",
              requirements:
                "Internal strict original SKU composition; no structural modifications; no publication authorization.",
              source_asset_ids: selected,
              truth_snapshot_id: truth!.id,
              platform_rule_id: rule,
              allowed_changes: ["background", "layout"],
              variants: 1,
              budget_usd: 0,
            });
            await reload();
          })
        }
      >
        创建严格保真计划（仍待计划审批）
      </button>
    </section>
  );
}
