---
id: "225"
title: "Sonnet 5.5 Ordered-Frame Comparison"
status: "Done"
priority: "High"
ideal_refs:
  - "R12"
  - "R18"
spec_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
adr_refs:
  - "ADR-003"
depends_on:
  - "222"
category_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "anthropic"
legacy_system: "Cross-Cutting"
---

# Story 225 — Sonnet 5.5 Ordered-Frame Comparison

Cam approved Conductor's five-repo Sonnet 5.5 proposal, including this exact six-case v4 synthetic frame-understanding lane at an all-provider USD3 hard ceiling. Isolated branch `codex/sonnet55-eval-20260928` starts from current `origin/main` `a3ac35743c94e253e0406fafe6ee4964a0330bf3`. The shared primary checkout remains untouched. ADR-003's transparency/model-improvement direction applies; no architecture decision is changed.

The current maintained owner is the Promptfoo headless task, whose Python `call_api` adapter can also be invoked directly. There is no adopted product ordered-frame analyzer. The comparator is fresh exact `gpt-6-luna` direct Responses Standard, low effort, strict JSON schema, 1400 output tokens; historical v4 evidence 0.5986 is context only. Exact direct `claude-sonnet-5-5` uses adaptive thinking with medium effort, native JSON schema, five ordered JPEGs, 4096 output tokens (enough for thinking plus the maintained 13-key schema), no sampling, no subject-output cache, concurrency one. No candidate tuning or private ScriptBible/screenplay, audio or native video is authorized. Public/synthetic fixtures may use Standard provider retention/no-training defaults; ZDR is unverified, and `store:false` is not proof of ZDR.

Freeze the exact task, neutral prompt, all six frame packets, v4 targets/schema/scorer, adapter and runner before paid qualification. Native direct dispatch and maintained adapter `call_api` must produce byte-identical request bodies; complete exact identity, terminal status, usage and schema outputs are mandatory. The first parity output is the first cohort case; other subjects are fresh independent calls. Two native probes plus twelve cohort calls use seven calls per arm, with eight reserved to allow one operational recovery. No semantic scoring influences configuration selection.

Quality target remains >=0.80, latency <=15 seconds and subject cost <=USD0.02 **per call**. Report deterministic and rubric components separately. Opus 4.6 remains the pinned maintained judge. Its same-provider relationship to Sonnet and prior v4 ambiguities require independent corroboration: predeclare symmetric `gpt-6-sol` low source review on all twelve saved outputs, using actual five JPEGs plus the frozen same rubric/reference. Neither judge receives model names. Source-check any material disagreement and repair only demonstrated evaluator defects; reuse saved subjects. No tuning to rescue a clear subject miss.

Full conservative reservations: eight Sonnet calls at 20K input +4096 output =USD0.64768; eight Luna calls at 20K input using cache-write upper rate +1400 output =USD0.02560; twelve Opus judges at10K input+1024 output =USD0.90720; twelve Sol source-review judges at20K input using cache-write upper rate+4096 output =USD1.09152. Planned bound USD2.67200 leaves USD0.32800 recovery. Input bounds preserve all bytes: each 640x360 image is below native family image-token ceilings, five-image allowance exceeds observed historical4.5K total by over4x; prompt/schema are small. Returned usage reconciles settled estimates after each request. Reserve unknown or failed-call exposure in full until resolved. No transfers or cap increase.

Plan: zero-cost topology and tests; independent native+parity qualification; six matched cohorts; maintained and independent source judgments; inspect source-backed significant mismatches; durable exact outputs/receipts, spend/freeze manifests, numbered attempt, registry history and focused validation. No commits/pushes/default edits.

2026-09-28 preflight: current remote already contains v4 overlay and Attempt043, so no historical code import needed. Live owner model discovery lists exact Sonnet5.5, Luna and Sol. Official current source notes are retained by Conductor coordinator; direct documentation fetching returned403 in this worker. Overlay builder validates13 files and source-frame hashes. Initial zero-cost runner attempt caught incorrect relative basePath; corrected to the maintained task directory before any provider call.

2026-09-28 result — [Attempt045](../evals/attempts/045-sonnet55-vs-luna-v4-ordered-frame-comparison.md) completes all six matched subjects, native/parity qualification, initial Opus and independent Sol image reviews, source-backed scorer fixes and six symmetric Opus recovery reviews without a subject rerun. Revised combined Sonnet0.53735/Luna0.62179; independent Sol combined0.61402/0.69263. Sonnet4.390s/USD0.013724 versusLuna8.119s/USD0.000488341 (prompt-cache-normalized LunaUSD0.000543675). Retain Luna headless preference; no autonomous QA/default promotion. Both miss propcontinuity classification; Sonnet duplicate rooftop tags and fixed-background lateral_track also remain failures. All44 paid calls settled at estimatedUSD0.38597572/3; no unresolved exposure. Source/receipt/ledger copies and original/derived scores are durable within this uncommitted worktree.

2026-09-28 validation —83/83 focused adapter/schema/dataset/scorer/adversarial/report/archive checks passed before registry closeout. Full `make test-unit` ran2201 tests:2200 passed and the one exact historical registry expectation failed because it did not yet enumerate the newly authorized rows. Updated that expectation;58 affected registry/contract/dataset/scorer/archive tests then passed. Source-backed negation and unrelated invented-cue regressions remain passing. Ruff passes every changed Python file. Original63 call-time identities verify against exact archived bytes. Original Story222 frozen inputs remain recoverable in predecessor archives, and its old paid runner correctly rejects evolved active inputs. Paid modes and source-review runner refuse an existing immutable result, including without ignored output state. `make check-evals` passes registry, truth-ledger and new immutable v16 contract manifest; all previous manifests remain unchanged. Initial methodology compilation found unsupported inline frontmatter lists; replaced with canonical block lists before successful generation/check. No additional provider calls were made during validation.

Recommended next step: no unchanged six-case rerun. Future model promotion needs a new checkpoint or a broader source-backed scene set; current comparison and corrections are ready for review and an explicitly authorized scoped landing.

2026-09-28 authorized closeout — Cam approved scoped finish-and-push. Current
`origin/main` remains the execution base. Added the required CalVer changelog
entry and decomposed the judge request builder to keep methods below100 lines;
its ~480-line bounded campaign runner is explicitly acknowledged as isolated
methodology tooling, with no product responsibility. Preserved original final-v1
runner bytes in a separate snapshot and rolled contract custody forward to v17;
paid call-time archives and every provider response/result remain unchanged.
Push remains held pending the coordinator's global preflight release.

2026-09-28 landing validation —46 affected offline tests passed after cleanup;
Ruff, registry/truth-ledger/v17 contract, methodology compile/check, and diff
whitespace checks pass. All24 rebuilt judge request bodies exactly match the
archived prior helper with placeholder credentials; all runner methods are now
<=100 lines. All156 final-v1 evidence identities remain recoverable and the
original63 paid call-time identities verify. Prior83+58 focused passes and2200
unchanged unit passes are reused; no wider suite or paid call is required.
Existing architecture audit and UI-scout freshness warnings are unrelated.
