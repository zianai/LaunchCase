# LaunchCase capability status

Tested code: `5eb44ff384fe86027863847d0ddf30f41f62987d`. Report/evidence commits do not change runtime code.

| Capability | Status | Boundary |
|---|---|---|
| Original PNG/JPEG/WebP and transparent cutout upload, exact rights, independent review | tested_local_http | Browser/API/DB and isolated CE; TEST ONLY geometry |
| Strict original SKU compose/reuse and independent asset approval | tested_local_http | No generative fallback, no publication; synthetic reviewer cannot approve real SKU |
| Source row/hash/model/Skill/input/prompt provenance | tested_offline + browser | Actual SDK adapter with deterministic test Model; real paid model not invoked |
| VOC exact-row dedup and variant/conflict retention | tested_offline | Distinct review IDs/dates remain independent observations; no market share claim |
| Sample/rule/quote G4/G5 and internal pack invalidation | tested_local_http | Human software roles in disposable fictional fixtures; no real attestation |
| Fixed LC → CE 1.0.0 independent consumer contract | tested_offline + tested_local_http | Unknown cost/QA/scopes fail closed; additions compatible |
| Pinned-grant pilot export, mixed-data/limit checks | tested_offline | Private data absent; no synthesized reviewer/approval |
| Single-host worker/checkpoint recovery and backup restore | tested_offline | Two real subprocesses; exact objects/decisions/pack; multi-host not tested |
| Genuine P8/E3 pilot and product-owner acceptance | BLOCKED_EXTERNAL | Data authorization, samples, independent humans and paired baseline missing |
| Production, public deployment, paid calls, GitHub remote mutation | BLOCKED_EXTERNAL | Separately authorized operations only |

Human design approval and target-user validation remain pending. Historical P7 evidence is unchanged.
