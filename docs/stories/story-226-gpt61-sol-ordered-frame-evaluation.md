---
id: "226"
title: "GPT-6.1 Sol Ordered-Frame Comparison"
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
  - "225"
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
legacy_system: "Cross-Cutting"
---

# Story 226 — GPT-6.1 Sol Ordered-Frame Comparison

Cam selected Scout078 item3: run only CineForge's six synthetic five-JPEG `video-understanding` cases at a USD4 all-provider hard cap. The fresh challenger is direct Responses Standard exact `gpt-6.1-sol`, low reasoning, strict schema, initial4096 total output tokens. The matched fresh control is `gpt-6-luna`, low/1400 on its maintained configuration. Exact fetched `origin/main` is `58a001716c2f20a07e4aefcc99d280e5a0c8bb10`; the isolated worktree/branch is `codex/gpt61-sol-eval-20260929`. The primary checkout is untouched.

The decision is the preferred headless research reference, because the task has no product ordered-frame analyzer. Full autonomous QA requires >=0.80 quality, <=15s and <=USD0.02 per subject. The evaluation does not change a default, production analyzer, account or private data. Cam subsequently authorized scoped validation, closure, commit and landing. Freeze the current v4 source truth, neutral prompt, five JPEGs per case, adapter/scorer and rubric. Each case is an independent request; no subject output cache or extra model arm. Qualify exact served identity, terminal strict schema, all five images, native/adapter body parity, usage and cost before scoring. Use explicit cross-provider `claude-opus-4-6` rubric judgments on both saved arms plus independent source-first review of each material mismatch. A same-provider GPT judge is not independent corroboration.

Pricing checked 2026-09-29: [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) USD2 input/USD0.10 cached/USD2.50 cache-write/USD10 output per MTok, [Opus4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview) USD5/USD25, and maintained Luna USD0.10/USD0.01/USD0.125-write/USD0.50. Initial conservative full topology reserves eight possible Sol calls (including qualification/recovery) at106K input+4096 output =USD2.44768; eight Luna at20K+1400 =USD0.02560; twelve Opus text-rubric judgments at10K+1024 =USD0.90720. TotalUSD3.38048 leavesUSD0.61952 for source-backed judge/operational recovery. Release reservations only after receipt usage settles; retain full unknown exposure. Four operational retries/repairs maximum, one causal change at a time; judge repairs reuse subject answers. The first case gates the six-case expansion after contract and value review.

Preflight 2026-09-29: current base already contains Story225/Attempt045's v4 source/scorer/judge repairs, so no stale-primary import is needed. V4 source generator check passes13 files; source contact sheet was inspected. Live owner catalog lists exact Sol6.1, Luna and Opus4.6; owner wrapper resolves both existing credentials by presence only. Zero-cost rendered topology has six independent cases, five original JPEGs each, no chained conversation, and63 hash-frozen source/config/media files. Focused adapter/dataset/scorer tests pass38/38. No paid request yet.

Work log: Final receipts, source classification, registry history, validation and recommendation will be recorded in Attempt046. A bounded comparison can choose a headless reference but cannot establish product QA adoption.

2026-09-29 result — [Attempt046](../evals/attempts/046-gpt61-sol-vs-luna-v4-ordered-frame-comparison.md) completed six fresh matched subjects with exact native/adapter parity and all five source JPEGs. GPT-6.1 Sol leads the source-adjudicated combined score0.65712 versus Luna0.61166 (four paired wins, one tie, one loss). Sol correctly classifies the red-to-blue prop continuity break and better describes the moving red streaks and rooftop arc; Luna remains about17.8x cheaper and1.10s faster per subject. All12 subjects met15s/USD0.02, all12 passed hard constraints, yet neither model passed any of six0.80 quality cases. Prefer Sol for this headless research-reference task when source fidelity matters; retain Luna as the economical control. No autonomous QA or product runtime/default change follows.

The initial cross-provider Opus judge misread case004's zero-based frames; a symmetric clarification still invented an all-five evidence requirement and penalized an unavailable blue enum tag. Those four Opus judgments remain in evidence and are invalid for case004. A symmetric source-first Sonnet5.5 image review of the same saved outputs scored Sol0.80/Luna0.35 and alone supplies the effective case004 rubric value. No subject, target, scorer or runtime prompt was changed after freeze. All30 paid calls settled at estimatedUSD0.22886042/4, unknown exposure0, includingUSD0.042421 judge recovery. Full raw receipts and hashes are retained in the Story226 evidence manifest; no credential was copied or injected.

Validation: original v4 source check passed13 files, then55 focused adapter/dataset/scorer/eval-contract checks passed after registry expectation update. Ruff passes all changed Python. Registry, truth ledger, new immutable v18 contract manifest, methodology compile/check, and diff whitespace checks pass. The paid call-time runner is archived byte-for-byte after a post-run dead-branch cleanup, so the63 frozen identities remain verifiable. This bounded, uncommitted comparison can be reviewed in the result, source-review record and raw manifest; no unchanged six-case rerun is recommended.


## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via /mark-story-done
- [x] Tenet verification complete
- [x] Documentation updates complete

## Close-out — 2026-09-29

No material product or evaluation verdict defect found. The results are non-runtime-blocking: this headless research comparison has no product analyzer to replace, and the autonomous-QA detector remains red. ADR-003's visual evidence/quality direction and spec:7/8/9 climb lanes remain intact. The sole close-out defect was the original report's dependency on ignored local receipts; added a read-only verifier using the 90 tracked receipts and immutable result ledger. Original report, result, call-time source archive, grades, and execution evidence remain byte-identical. Trailing whitespace was removed only from the current runner; archived call-time runner and execution patch retain their exact bytes and are excluded from the whitespace gate. No paid requests were repeated.

85 focused adapter/dataset/scorer/contracts tests plus an offline-verification regression with absent local receipts and blocked network, changed Python lint, registry and truth-ledger checks, v19 close-out contract manifest (preserving v18 call-time inventory), source builder check, and generated-methodology checks supply candidate validation. The source-reviewed output and original recovery judgments were inspected; mismatch classifications remain in Attempt046 and the source-review record. No UI, runtime, dependencies or CI/release workflows changed; no hosted CI configuration exists. Latest fetched origin/main remains the original base 58a0017, so no integration change is needed. Changelog and generated planning views are current. The commit containing this close-out identifies the preserved hash-frozen evaluation evidence; run-time base identity remains unchanged.

Where to verify: `PYTHONPATH=src python benchmarks/scripts/verify_gpt61_video_comparison.py` checks tracked hashes, saved scores and the settled ledger without provider calls. Remote landing remains pending the coordinator's all-repository preflight.


## Scout 092 Argon continuation — 2026-10-13

Approved Conductor item3: inclusive hard cap USD5; exact native Google `gemini-4-argon` medium with32768 output including thinking, versus fresh `gpt-6.1-sol` low4096 and `gpt-6-luna` low1400 direct Responses. Reuse Story226 because this is the same subsystem and success surface. Three independent v4 cases cover dialogue, prop continuity and storm motion, using five original JPEGs, unchanged prompt/scorer/targets, and pinned cross-provider Opus4.6 strict1024 on all arms. Freeze identity, bytes, topology, judge and reservations before spending. Qualify native image/schema transport then maintained adapter parity. A valid source-grounded decisive failure stops candidate progression; ambiguous scoring alone does not. Gates remain deterministic.70, rubric/overall.80, latency15s and subject costUSD.02. No six-case promotion, other lanes, private inputs, raw MP4/audio, default/account/deployment changes, commit or push.

Freshly fetched remote base1a38bbae97382abdffe99b2abe959154b02dace6; isolated branch/path `codex/scout092-argon-cineforge-20261013` at `/Users/cam/.codex/worktrees/scout092-argon-cineforge-20261013`. Primary eight dirty entries preserved. Existing credentials available through the normal owner wrapper only. Existing Python runtime reused, without dependency copies. R12/R18 and spec7/8/9 remain owning references; this headless child does not establish the full-film Ideal, a product analyzer, or any compromise removal.

Pre-spend independent source review confirmed all15 frame hashes and found a dialogue scorer false-credit possibility: camera-push-in wording can credit bodygrowth despite excluded camera. Preserve the frozen scorer; use source-first independent review to distinguish visible growth from unknown mechanism. Original scores remain conditional research history with no current score promotion. Conservative serial reservations: Argon2.424832 using the full1048576 input window plus32768 output at launch2/10M; Sol.30596 at maximum input-write rate; Luna.0032; Opus.0756. Serial settlement releases reservations; worst-case completion of the full matrix is not guaranteed. Unknown exposure stays reserved. The hard cap includes qualification, subjects, controls, judges and finite operational recovery.

2026-10-13 — All nine fresh subjects and three native qualification calls completed with exact served identities, five-image/schema qualification and native/parity body equality. Argon recognizes the core source changes; no unambiguous source contradiction required a progressive stop. Original aggregate scores: Argon.58867, Sol.61003, Luna.61498. Source-adjudicated Argon.59533; controls unchanged. All0/3 dual passes. Argon passed2/3 latency and1/3 cost gates; mean15.592s/$.01687417 with natural input caching. Cold-normalized mean$.020348, doubled from December1. Do not adopt; retain references. Quality ranking is not source-validated superiority.

2026-10-13 — One symmetric saved-answer prop review repair corrected demonstrated judge faults using the original images: stillness called invented, extra frame1 evidence requested, color-enum confusion. Argon.78→.82; Sol.72 and Luna.55 unchanged. Original judgments and charges preserved. Three repair calls form one causal repair round, superseding the agent-selected two-call soft allowance within the unchangedUSD5 cap. First repair raw response survived a Decimal/float parser fault and was reused without another paid call; provider latency unknown, receipt1ms is parsing time. No tuning or further rejudging.

2026-10-13 — Source taxonomy: Luna's prop continuity-intact judgment is model-wrong against the declared visual continuity contract. Argon camera mechanism and tone/emotion/tempo interpretations are ambiguous. Frozen scorer/golden limitations include enlargement vocabulary/camera aliases, plaque/rectangle and stillness/red penalties, storm icon/arch/line synonyms, and a false hard failure on Sol's visible third motion cue. These are documented, non-runtime-blocking research limitations. No current score promotion or semantic-inferiority claim follows. The bounded measurement is complete; a separate source-backed scoring-validity repair remains the recommended prerequisite for broader capability qualification. Historical Story226 closure stays unchanged.

Twenty-four calls settled estimatedUSD.278644895/5, unknown0 and subject retries0: qualification.030758675; subjects.07523122; original judges.109355; review repairs.063300. Candidate total.0707505; controls.035239395. Billed dollars unavailable. Naturally cached input and December launch-rate expiration remain explicit. No credential injection or cleanup.

Evidence: Attempt050 and registry history, original/repaired receipts, result, source review,46-file call-time freeze, producing runner/adapter snapshots and hash manifest. Validation uses focused Argon fail-closed/raw-custody plus existing packet/OpenAI/scorer/report checks; offline replay/hash verification; registry/truth ledger; new immutable contract manifestv22; methodology compile/check and whitespace. No product/UI suite or paid rerun is required for this isolated evaluation-tooling change.

Validation — 2026-10-13:64 focused tests passed, including five new fail-closed Argon tests and59 existing packet/OpenAI/scorer/report checks. Ruff passed touched tooling/tests. Offline verifier reconstructed9 scores and checked88 retained hashes,24 settled calls and identical native/parity bodies. Registry, truth ledger, new immutablev22 manifest, methodology build/check and whitespace passed. Primary eight dirty entries unchanged. Existing architecture-audit and UI-freshness warnings remain unrelated. Exact commands/code hashes: `docs/evals/story-226-argon20261013-validation.json`. No further paid calls.

Landing preparation — 2026-10-13: Cam explicitly authorized check in and push for Scout092. The bounded screen and layered verdict remain unchanged. Fresh remote main equals the measured base1a38bba; primary eight dirty entries and inbox preserved, with no in-scope inbox delta. Preflight found an offline-custody defect: report replay read the ignored runtime ledger despite its tracked copy being retained. The report now reads `docs/evals/evidence/story-226-argon20261013/ledger.json` explicitly; original report and evidence manifest remain sealed. New v2 closeout manifest pins the report fix and its original snapshot. Replay will be checked with runtime output unavailable. Reuse64 focused tests because provider/scorer/source inputs remain hash-identical; validate the changed offline replay and records directly. No paid calls or model/default changes. Coordinated clearance is required before pushing.
