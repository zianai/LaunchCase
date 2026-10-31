"use client";
import { useState } from "react";

export default function Provenance({
  id,
  api,
}: {
  id: string;
  api: (path: string) => Promise<any>;
}) {
  const [proof, setProof] = useState<any>(null);
  const [error, setError] = useState("");
  return (
    <details
      onToggle={(e) => {
        if (e.currentTarget.open)
          api(`insights/${id}/provenance`)
            .then(setProof)
            .catch(() => setError("来源暂不可用，请稍后重新核验"));
      }}
    >
      <summary>核验洞察来源与运行版本</summary>
      {error && <p role="alert">{error}</p>}
      {proof && (
        <>
          <p role="status">
            {proof.current
              ? "来源定位有效 · 人工判断仍待评审"
              : "来源已撤销、变更或不可定位 · 需要重新审核"}
          </p>
          <p>
            模型：{proof.model_id || "未记录"} ·{" "}
            {proof.run_status || "历史记录"}
          </p>
          <p className="hash">
            输入 {proof.input_hash || "未记录"}
            <br />
            提示版本 {proof.prompt_hash || "未记录"}
          </p>
          {Object.entries(proof.skill_versions || {}).map(([name, hash]) => (
            <p key={name} className="hash">
              方法 {name} · {String(hash)}
            </p>
          ))}
          {(proof.citations || []).map((c: any) => (
            <blockquote key={c.evidence_id}>
              <p>{c.excerpt}</p>
              <p>
                {c.source_locator} · {c.product_identity} / {c.variant}
              </p>
              <p className="hash">
                来源 {c.source_sha256} · 行 {c.row_sha256}
              </p>
              <a
                href={`/api/sources/${c.source_id}/content`}
                target="_blank"
                rel="noreferrer"
              >
                查看原始证据 ↗
              </a>
            </blockquote>
          ))}
        </>
      )}
    </details>
  );
}
