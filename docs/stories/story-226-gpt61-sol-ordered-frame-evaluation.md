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

## Scout 096 Nemotron continuation — 2026-10-16

Approved item4, hard inclusive USD3. Three frozen v4 cases (dialogue, prop, storm), five original JPEGs each, versus fresh Sol6.1 low4096/Luna6 low1400. Candidate exact router `nvidia/nemotron-3.5-super-vl` checkpoint20261015, Together pinned/no fallback/max price .15/.50M, `reasoning.enabled:true`/32768. The control is accepted/observed at router level; native regular-versus-medium equivalence remains unverified. No effort sweep. Headless research only; no product analyzer/default or C2/C3/C5 promotion. R12/R18 and spec7/8/9 own this continuation; ADR003 visual-evidence direction applies, no architectural change.

Hypothesis: candidate improves source fidelity toward deterministic.70, rubric/overall.80 while meeting15s andUSD.02 per subject; parity needs meaningful >=30% cost/latency benefit to prioritize qualification. Freeze existing prompts/targets/scorer; known lexical/camera-credit defects remain quarantined. Use independent fixed native Opus4.6 strict1024 and all five original frames for every review from the outset, applying the prior source-verified interpretation boundaries symmetrically. First clear source-backed candidate contradiction stops its arm; judge/adapter faults require repair on saved outputs. No subject semantic retuning or six-case expansion. Inputs are authored synthetic; downstream retention unknown, no private media or audio/rawMP4. These exposed research cases are not independent promotion material.

Fresh remote base3a02901, isolated codex/scout096-cine-20261016 at `/Users/cam/.codex/worktrees/scout096-cine-20261016`; primary dirty work remains untouched. Existing owner credentials resolved only through normal wrapper; no injection. Zero-cost preflight resolves independent case grouping, full13-key strict schema, exact prompt/frames, native/harness same-body parity, explicit independent judge, no subject cache and serial concurrency. Every POST reserves maximum input/output exposure; unknowns remain reserved. Router requests hold campaign flock through response/settlement. Native/contract/parity first case, then source inspection before progression. Operational recovery within inclusive cap; new immutable result identity.

2026-10-16 — Candidate native/parity strict image contract passed; both first dialogue answers claim the scene/figures remain identical across all frames. Root and owner directly compared frames0/4: bodies and heads visibly enlarge while background/prop stay fixed. Fixed full-source Opus corroborates growth miss. Stop candidate after1/3; remaining two not measured. All six fresh controls completed. One symmetric saved-answer prop-review repair is necessary because original Luna judge invents an all-five/frame1 evidence obligation and gradual-transition assertion, and penalizes visible stillness; retain both originals. The actual intact-versus-broken continuity errors remain model-wrong. No subject/scorer/golden tuning; native Opus1024, full originals, same rubric plus explicit correction of demonstrated review faults. Cap/reservations unchanged;17 settled calls before repair USD.177321495; reserve .15each within3.

2026-10-16 — Closed bounded Scout096 measurement: candidate1/3 stopped on physically verified growth miss; fixed source-image Opus.38, deterministic.1719/combined.27595 versus matched fresh Sol.7282/Luna.625. Candidate5.642s/USD.00125455; no quality pass. Controls3/3 remain below gates; after one symmetric saved-answer prop repair, combined Sol.596067/Luna.566933 (original.612733/.5636 retained). Both control prop labelsintact are genuine continuity-contract failures; subjective/lexical scoring limits remain quarantined. Reject tested router-enabled candidate for this task, retain maintained research references. No further paid work.

Nineteen settled calls USD.219046495/3, unknown0: qualification.011732225, subjects.02517927, originaljudges.140410, repairjudges.041725. Candidate total.00241710 including nativequalification. Reported router charges and estimated native costs stay distinct. Existing owner credentials only, no injection/cleanup. Attempt051, finalv2result, originalpre-repairresult, freeze, call-time runner snapshot, complete safe receipts/ledger and final hash manifest provide durable custody. Original freeze's copied metadata date2026-10-13/shortSHA is explicitly corrected by Attempt051 and manifest; frozen input hashes unchanged. Final runner guards the stopped arm; no default/runtime/UI changes or commit/push.

Validation — 64 focused packet/dataset/OpenAI/scorer tests passed; changed Python Ruff passes. Final offline verifier reconstructs7scores,19settledcalls, native/parity bodies and all hashes without inference. Registry consistency passes; methodology build/check and whitespace supply record validation. Unchanged product/UI suites not applicable. Recommended next step remains source-backed scoring-validity repair before broader model qualification; no rerun of unchanged subject arm.


## Scout097 DeepSeek1017 continuation — 2026-10-17

Approved item4 hard inclusive USD4. Current remote base9467abc51a6ea2bebf0867fe633691c5a13c7406 isolated codex/scout097-deepseek1017-cineforge-20261017. Exact deepseek/deepseek-v4.1-flash-1017 canonical20261017, pinned Cloudflare unknownprecision, fallback false, require_parameters true, caps .30/1.20M, high32768. Fresh direct GPT6.1Sol low4096/GPT6Luna low1400; fixed blind native Opus4.6 full-source rubric8192. Source-first independent review. No semantic retuning. First dialogue discriminator precedes prop/motion expansion; valid decisive source miss stops candidate. Controls may finish independently. No six-case expansion, runtime/default changes, account changes, private inputs, MP4/audio/transcript, commit/push. Three exposed synthetic cases prioritize further qualification only. ADR003/R12/R18 and spec7/8/9 unchanged; no new architectural decision.

Zero-cost admission renders9 independent packets, five original640x360JPEGs each, current strict13keys/prompt/schema/targets. DeepSeek image documented max1024tokens each; complete text+schema UTF8 conservative bound plus image tokens below106K. Native control3072tokens/image conservative bound plus full text/schema below26K. Full source Opus count_tokens API counts complete review schema/system/rubric plus saved reference output and all original JPEGs at2509/2437/2417. These are anticipated actual packet templates, not a guarantee arbitrary output fits20K; every actual full review is counted again before dispatch and never truncated. Candidate3*.0711216=.2133648; sixcontrols allowance.60; nineOpus20K/8192=.3048each=2.7432; total3.5565648 leaves.4434352 qualification/recovery. Next-call full reservations before eachPOST, unknown charges retained. Serial independent sessions, output caches bypassed; provider input caching disclosed. Existing credentials resolved through owner wrapper, no injection. Public/synthetic ordinary retention/training uncertainty approved, ZDR unverified.

2026-10-17 — Scout097 bounded screen finished; Attempt052. Exact Cloudflare1017 native/parity strict output observed, but native reasoning accounting leaves14/55visible tokens versus full13-key JSON; generation GET confirms mismatch. Candidate formal contract unqualified, adoption defer, scores diagnostic only. Root independently confirms visible figure enlargement contradicting saved unchanged/stillness answer; no extra candidate call. Candidate1/3, fresh controls3/3, seven fixed full-source Opus reviews and one symmetric two-control prop judge repair. Sol/Luna combined.58553/.58860, both0/3 passes; no score promotion or autonomous-QA conclusion. Total19settledcallsUSD.210174063/4, unknown charges0; candidate cost generation-matched reported, native costs estimated. No injection/cleanup, defaults/account/settings/commit/push. Source-golden freeze, complete receipts, archived runner, offline verifier and manifest retained; recommended nextstep source-backed scoring-validity repair plus documented accounting correction before candidate qualification.


Scout097 landing preparation — 2026-10-17: Cam explicitly authorized finish and push of the bounded campaign records. Historical Story226 status and autonomous-QA detector remain unchanged; this continuation is complete only for its selected three-case screen and stopped candidate. Current fetched origin/main remains9467abc, matching the measured base. Primary inbox has no capture delta to reconcile and unrelated primary dirt is preserved. No CI workflow or required-review configuration is checked into this repository. Reuse69 focused tests and13-file source check because tested adapter/scorer/source bytes are unchanged. Revalidate retained72-file evidence hashes and offline reconstruction with network blocked, lint the three scoped scripts, and check registry/truth/immutable contract/generated methodology/whitespace. Changelog2026-10-17-01 records this bounded result. No paid rerun or runtime change. Coordinator clearance is required before pushing.


## Scout 099 MiniMax GA continuation — 2026-10-20

Approved item4, hard inclusive USD4. Reuse this same headless ordered-frame surface; historical story closure remains unchanged. Exact GA candidate MiniMax-M3.1-Flash via approved practical OpenRouter minimax/minimax-m3.1-flash:free pinned Minimax/tag minimax, canonical20261019, unknown quantization, no fallback. Direct owner MiniMax variables absent; existing owner OPENROUTER_API_KEY via sanctioned wrapper only, no injection/cleanup. Current fetched origin/main01527226f8047f2af4db231091f690e314e11950 isolated codex/scout099-minimax-cine-20261020. Primary dirt preserved.

Plan: high32768 vs fresh Sol6.1 low4096 and Luna6 low1400 on authored synthetic dialogue/prop/storm v4 cases, five original ordered JPEGs each, no audio/MP4/private data. Maintain13-key strict schema, deterministic.70, rubric/overall.80,15s,USD.02 per subject. Fixed blind source-first Opus4.6 reviews, input admission20K/output8192, nine reviews plus bounded saved-answer recovery. No effort sweep or semantic retry. First source-backed decisive candidate failure stops expansion; qualify required native strict contract before formal scoring, with one-variable capability-only diagnostic if unsupported. Native/harness same-body parity required. Budget includes all controls/judges/recovery; candidate route zero input/output price capped at0. Sol .10596/call, Luna .00395/call, Opus .3048/call reservations; three candidate subjects +six controls+nine judges fitUSD3.07293 withUSD.92707 qualification/recovery headroom. Unknown exposure stays reserved. Fresh serial independent requests, no subject cache; provider input cache disclosed. Source/scorer defects remain research limitations, no current score promotion.

R12/R18, spec7climb/spec8hold/spec9climb and ADR003 visual-evidence direction apply. This tests a single-call capability child; full-film Ideal and autonomous QA remain deferred, no compromise removal or shipped caller/default change. Retention/training uncertain; selection covers authored synthetic media only. Practical goal is reducing missed visible changes without purchasing a misleading quality claim.

2026-10-20 — ExactGA free route callable after strict404 parameter-filter stop. One-variable require_parameters=false diagnostic preserves full raw output; local13-key validity is not provider enforcement. Candidate first-case combined.6368/15.507s/$0 vs fresh Sol.74665/7.661s/$.0033047 and Luna.62285/5.009s/$.00020817, all0/1 dual passes. Candidate correctly observes visible body growth, unsupported push-in mechanism and subjective/lexical grades remain caveated. Required strict transport unavailable; no further candidate/controls on prop/motion, no semantic retry or quality-superiority claim. Attempt053/registry history preserve all layers and receipts. All calls settledUS$.073644545/4, unknown0; no injection or cleanup. Retain maintained references, defer candidate adoption.

Validation — 2026-10-20: v4 source overlay13files match;42 focused schema/dataset/scorer/OpenAI contract tests pass. Offline retained-receipt replay/manifest verification, registry links and methodology compile/check complete in final evidence log. No runtime/UI changes or unrelated suite required; no paid repeat.

Scout099 landing preparation — 2026-10-20: Cam authorized campaign commit/push. Fetched origin/main remains01527226f8047f2af4db231091f690e314e11950, matching measured base; no branch-only commits or integration conflict. Primary inbox has no delta; unrelated primary dirt preserved. Reuse42 focused tests and13-file source check because source/adapter/scorer bytes are unchanged. Retained81-file offline receipt/score/ledger/hash replay, credential-field scan, registry/truth/contract/methodology checks and whitespace pass. Changelog2026-10-20-01 records the bounded outcome. Historical Story226 closure unchanged; no checked-in CI/review workflow. No paid calls. Coordinator clearance required before commit/push.


## Scout 103 Terra continuation — 2026-10-26

Cam selected item4, inclusive hard US$5. New direct Responses Standard
`gpt-6.1-terra` high32768 versus fresh `gpt-6.1-sol` low4096 and
`gpt-6-luna` low1400, three synthetic five-JPEG v4 cases dialogue/prop/tunnel.
First discriminator before expansion, fixed strict13-key schema/prompt/scorer/
source targets, source-first Attempt047 clarifications prospectively symmetric,
nine blind native Opus4.6 reviews maximum. Native and maintained adapter parity
before scoring. Require deterministic>=.70, rubric/overall>=.80, maintained
mean<=15s and<=US$.02/subject. No semantic retries/effort sweep, private inputs,
MP4/audio, product runtime/default/deployment or commit/push. No autonomous-QA
claim from this headless screen. R12/R18, spec7/8/9 and ADR003 own this surface;
no new architecture decision. Existing current v4 truth supersedes old
quarantined v3 notes, while subjective/lexical scoring limits remain explicit.

Isolated codex/scout103-terra-cineforge-20261026 at
`/Users/cam/.codex/worktrees/scout103-terra-20261026/cine-forge`, current fetched
origin/main6e6783e47eec4d053452c83606e18dc6e96df312. Primary unrelated dirt stays
untouched. Existing owner OpenAI/Anthropic credentials through normal wrapper,
no injection or credential copy. Current authenticated zero-cost discovery lists
exact Terra, Sol, Luna and Opus4.6. Public docs checked2026-10-26: Terra model
page, pricing, images guide; text/image input, strict schema, high effort,
Responses tool family, Standard input1/output5/cachewrite1.25 USD/M. storefalse
does not establish ZDR; only authored synthetic JPEGs eligible.

Reuse proven prior Kimi runner pattern as new Terra runner, removing router
handling and adding only exact Terra/high allowlist and rates to existing
eval adapter. Preserve selected original five JPEGs and all source bytes.
Conservative serial full922K-input long-rate reservation2.79688 per candidate
call exceeds the expected106K input estimate; no unsupported dimension-token
bound is assumed. Settled actuals release reservation; entire all-worst-case
matrix is not promised. Sol.10596/Luna.00395/Opus.3048 percall, finite bounded
operational recovery within hardcap. All failed/unknown calls retain exposure.
Adequate-output repair can proceed if documented truncation occurs; no valid
semantic failure tuning. Judges reuse saved subjects for repair. No inference
before zero-cost resolved9-packet topology and full output/source judge count
admission. Full raw envelopes retained before parse, immutable receipts deny
duplicate charges.

2026-10-26 result — Attempt055 completes native direct Terra high32768 strict
image/schema parity and two decision-bearing same-input cases. All arms0/2
quality passes; correct color-change observation but Terra ambiguous and both
controls intact fail declared broken prop label. Retain references, no winner.
Terra mean9.885s/.00572835USD vsSol7.1555s/.0064841 and Luna8.184s/.0003776725.
Automatic runner improperly expanded tunnel before prop adjudication: all saved
tunnel subjects/judges retained as supplementary post-stop, excluded from main
aggregate, extra.069789425USD included. Hardened per-case admission now fails
closed; exact producing runner separately archived. All21calls settled
conservative usage-estimated.229264595/5,unknown0. No paid rerun, rejudge or effort
sweep; no runtime/default/commit/push. Exact frame sources, all raw responses,
calltime/hardened code lineage and costs retained under story226-terra6120261026.
