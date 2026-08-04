---
id: "211"
title: "OpenRouter Bounded Script-Bible Challenger Evals"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
  - "208"
  - "209"
  - "210"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "openrouter"
  - "qwen3.8"
  - "deepseek-v4-flash"
legacy_system: "Cross-Cutting"
---

# Story 211 — OpenRouter Bounded Script-Bible Challenger Evals

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (script bible and model-upgrade boundary)
**Depends On**: Stories 035, 208, 209, 210

## Goal

Qualify one OpenRouter challenger at a time and run the smallest source-backed
script-bible comparison that can change CineForge's ingest-model decision. Keep
access, transport, reliability, conditional semantic quality, and adoption
separate; preserve exact identity, usage, pricing, privacy, and failure
evidence; and do not change the production default without a later explicit
user decision. Qwen3.8 completed the first bounded arm; DeepSeek V4 Flash
completed a second bounded attempt on the same decision surface.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and compromise C3 require current evidence
  before a new model can replace a value-optimized slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest higher-level result**: Story 208 repaired the scorer, two-corpus
  fixture, exact schema, and provenance contracts; Story 210 proved the bounded
  exact-runtime ladder but left no eligible repaired comparator row.
- **Measured trigger**: on 2026-08-03 OpenRouter's live catalog added exact slug
  `qwen/qwen3.8-max` with canonical snapshot
  `qwen/qwen3.8-max-20260803`, one Alibaba endpoint, mandatory reasoning, strict
  structured output, 1M context, and 131,072 maximum completion tokens.
- **Child baseline**: qualify a minimal strict-schema call, then run the exact
  runtime-shaped Open Frequency case at concurrency one. Advance to broader
  corpus/comparator evidence only if absolute quality, latency, cost,
  reliability, and privacy gates remain viable.
- **Current trigger**: OpenRouter now exposes the immutable
  `deepseek/deepseek-v4-flash-0731` snapshot (canonical
  `deepseek/deepseek-v4-flash-20260731`) with strict structured-output and ZDR
  routes. The user requested one repaired, full-screenplay `script_bible_v1`
  comparison, explicitly excluding a five-slot sweep.

## Decision Contract

### Completed Qwen3.8 arm

- **Candidate/access path**: `qwen/qwen3.8-max` through OpenRouter Chat
  Completions, pinned to provider `Alibaba`, `allow_fallbacks=false`, and
  `require_parameters=true`. Returned model, OpenRouter response ID, provider,
  finish reason, and real token counters are mandatory.
- **Candidate arms**: freeze `reasoning.effort=low` with reasoning excluded from
  the visible strict-JSON response as the value-slot arm. At most one `xhigh`
  diagnostic may run only if low-effort quality fails while latency/cost leave
  plausible headroom; it cannot become promotion evidence without a fresh
  frozen confirmation.
- **Selected slot/eval**: `script_bible_v1` / `script-bible`.
- **Executable default**: `gemini-3.5-flash-lite`, 65,536 output tokens,
  minimal thinking.
- **Best eligible maintained evidence**: none under the repaired exact-runtime
  two-corpus contract. Historical Grok/Gemini rows and the provisional default
  row are non-decision-grade; Opus 5 is a bounded value-gate rejection.
- **Frozen contract**: production `EXTRACTION_PROMPT`, `ScriptBible` Pydantic
  schema, maintained Python scorer, Opus 4.6 rubric, source-linked Open
  Frequency golden, and current base SHA `f01e86567a7466b234e45fdcbda45efbaf9edf19`.
- **Absolute gates**: overall `>=0.90`, latency `<=30,000 ms`, cost
  `<=$0.01` per subject call, terminal strict-schema success, exact identity,
  sane usage, no fallback, and no policy/safety refusal.
- **Privacy**: the Alibaba endpoint is not on OpenRouter's ZDR list. Only the
  repo-authored synthetic Open Frequency fixture may be sent until a stronger
  endpoint policy is proven or the user explicitly approves another payload.
- **Budget**: aggregate paid-call cap `$5`. Initial native and schema probes
  must remain below `$0.02`; the bounded Open Frequency subject plus judge is
  expected below `$0.25`. Stop before any stage that cannot be conservatively
  bounded.
- **Cache/concurrency/retries**: `--no-cache`, `-j 1`, one capacity/transport
  retry at most, and no semantic retry after a valid completed response.
- **Progressive stop**: any mandatory transport, privacy, quality, latency, or
  cost failure stops expansion. A one-case pass remains provisional and cannot
  support adoption without the second corpus and a fresh default comparator.

### DeepSeek V4 Flash extension

- **Candidate/access path**: immutable OpenRouter model
  `deepseek/deepseek-v4-flash-0731`, canonical snapshot
  `deepseek/deepseek-v4-flash-20260731`, through Chat Completions. Pin one
  provider that supports strict structured output and ZDR, set
  `allow_fallbacks=false`, `require_parameters=true`, `data_collection=deny`,
  and `zdr=true`. Returned model, response ID, upstream provider, finish reason,
  and reconciled token/cost counters are mandatory.
- **Candidate arm**: low reasoning, excluded from the visible strict-JSON
  response. No second DeepSeek configuration arm is planned.
- **Comparison**: fresh DeepSeek V4 Flash versus fresh executable incumbent
  `gemini-3.5-flash-lite` with minimal thinking on the same complete synthetic
  Open Frequency screenplay. This is one slot, one fixture, and two subject
  arms—not a historical-row comparison and not a five-slot sweep.
- **Selected slot/eval**: `script_bible_v1` / maintained `script-bible`.
- **Frozen semantic contract**: production `EXTRACTION_PROMPT`, `ScriptBible`
  Pydantic schema, maintained Opus 4.6 rubric, source-linked Open Frequency
  golden, and exact base SHA `9d878a8e68d17175a40f155239c29baed6783235`.
- **Scorer repair boundary**: repair only the three source-proven defects from
  Attempt 021 before paid comparison calls: schema-permitted descriptive act
  boundaries, source-faithful annotated theme evidence, and the `Kell ... cell
  towers are dead` false-positive death regex. Add regression fixtures first.
  Do not change the golden, semantic prompt, rubric, thresholds, or genuine
  hallucination penalties.
- **Absolute gates**: overall `>=0.90`, latency `<=30,000 ms`, cost
  `<=$0.01` per subject call, terminal strict-schema success, exact identity,
  sane usage, no fallback, and no policy/safety refusal.
- **Budget**: aggregate paid-call cap `$5`. Native access/schema probe plus the
  two one-case subjects and their maintained judges must remain conservatively
  below the cap. Stop before any unbounded stage.
- **Privacy**: only the repo-authored synthetic Open Frequency screenplay may
  leave the repo, and only through a pinned ZDR endpoint. The Mariner remains
  excluded.
- **Cache/concurrency/retries**: `--no-cache`, `-j 1`, one capacity/transport
  retry at most, and no semantic retry after a valid completed response.
- **Progressive stop**: a pre-response access or transport block ends the run
  with capability not measured. Otherwise complete the requested two-arm
  comparison, then stop; do not advance into any other slot or corpus.

## Acceptance Criteria

- [x] Exact catalog, authenticated access, native served identity, provider
  pinning, strict JSON Schema, usage, finish reason, and pricing are qualified.
- [x] An isolated OpenRouter exact-runtime provider lane is covered by focused
  tests and does not change production transport or defaults.
- [x] The frozen Open Frequency `script-bible` case runs no-cache at concurrency
  one with structural and semantic scoring, or its pre-response blocker is
  retained without being misclassified as model quality.
- [x] Every significant mismatch is source-inspected and classified as
  model-wrong, golden-wrong, or ambiguous, with runtime significance.
- [x] Result, attempt, registry, story, cost ledger, and dirty-contract
  provenance are complete and replayable.
- [x] A scoped adopt / conditional-adopt / do-not-adopt / defer decision is
  stated for script bible only; production defaults remain unchanged.

### DeepSeek V4 Flash extension

- [x] The three source-proven scorer defects have regression coverage and are
  repaired without weakening real hallucination detection.
- [x] Exact authenticated model/provider identity, ZDR/no-fallback routing,
  strict schema, usage, finish reason, and current pricing are qualified.
- [x] The fresh DeepSeek/Gemini Open Frequency comparison was attempted at
  `--no-cache -j 1`; Gemini's valid cell was structurally and semantically
  scored, while DeepSeek's timeout and one rate-limited retry are retained as
  pre-response transport evidence rather than fabricated quality scores.
- [x] Every significant mismatch is source-inspected and classified as
  model-wrong, golden-wrong, or ambiguous, with runtime significance.
- [x] Result, attempt, registry, truth ledger, story, and spend evidence are
  complete and replayable; no default, commit, push, or deployment occurs.

## Out of Scope

- QA-pass, ordered-frame/video-understanding, image/video generation, or the
  multi-hour full-script throughput detector.
- Private or unapproved fixtures while the sole endpoint lacks ZDR.
- Golden, scorer, rubric, or semantic-prompt tuning to rescue the candidate.
- Production OpenRouter integration, deployment, commit, push, or default
  changes.

## Approach Evaluation

- **Simplification baseline**: this is the single-call full-script baseline;
  one passing slot would not prove whole-pipeline simplification.
- **AI-only**: one model call reads the complete synthetic screenplay and
  returns one strict `ScriptBible`.
- **Hybrid**: provider-enforced JSON Schema plus Pydantic validation,
  deterministic source checks, and an independently pinned semantic rubric.
- **Pure code**: appropriate only for provider pinning, transport validation,
  identity/usage preservation, pricing, and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  makes script bible a core artifact and keeps model upgrades behind prompt
  compilation. `spec:8` is hold-state maintenance while `spec:6/spec:7` remain
  the active product focus, so this evaluation stays narrow.
- **Existing patterns to reuse**: Story 210's exact-runtime provider and bounded
  ladder, Story 208's repaired task/scorer/golden, provider-env wrapper, model
  identity validator, and metric extractor.
- **Eval**: reuse `script-bible`; do not create a parallel capability eval.

## Tasks

### Completed Qwen3.8 arm

- [x] Qualify catalog, endpoint, authentication, privacy, native strict schema,
  exact identity, usage, price, and reasoning contract.
- [x] Add a narrowly tested OpenRouter branch to the existing exact-runtime
  script-bible provider and one isolated focused test file.
- [x] Run the declared no-cache Open Frequency lane and apply progressive stop.
- [x] Inspect source/output/scorer/rubric evidence and classify every mismatch.
- [x] Record result, attempt, registry history, story work log, contract hashes,
  and cost ledger; regenerate methodology surfaces.
- [x] Check whether the chosen implementation makes any existing code, helper
  paths, or docs redundant; remove them or record a concrete retirement condition.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Focused backend lint/tests for provider, env, identity, scorer, and registry.
  - [x] UI not touched; browser verification is not applicable.
- [x] If story metadata changes: `pnpm methodology:compile` and `pnpm methodology:check`.
- [x] Run `/improve-eval`-equivalent mismatch investigation and update the
  registry for every executed eval.
- [x] Search all docs and update any related truth surfaces.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** only the synthetic Open Frequency screenplay leaves the repo.
  - [x] **T1 — AI-Coded:** exact contracts and evidence make the result reproducible.
  - [x] **T2 — Architect for 100x:** test the single-call baseline first.
  - [x] **T3 — Fewer Files:** reuse maintained eval/provider seams.
  - [x] **T4 — Verbose Artifacts:** preserve raw evidence and a live cost ledger.
  - [x] **T5 — Ideal vs Today:** do not add scaffolding beyond the measured transport need.

### DeepSeek V4 Flash extension

- [x] Add failing regression tests for the three source-proven scorer defects,
  then make the smallest scorer repair.
- [x] Generalize the existing isolated OpenRouter strict-schema seam for the
  immutable DeepSeek snapshot without changing production transport.
- [x] Qualify one pinned ZDR route and run the fresh two-arm Open Frequency
  comparison at `--no-cache -j 1`.
- [x] Inspect source/output/scorer/rubric evidence and classify every mismatch.
- [x] Record Attempt 022, registry row/history, truth ledger, work log, contract
  hashes, and spend; regenerate methodology surfaces.
- [x] Run focused tests/lint, `make test-unit`, registry/truth checks,
  `pnpm methodology:compile`, and `pnpm methodology:check`.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done through the same acceptance and methodology checks

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `benchmarks/providers/script_bible_runtime_provider.py`
  owns exact-runtime benchmark transport. The OpenRouter branch belongs there
  because it must preserve the same prompt/schema/output contract without
  changing production `llm.py`.
- **Data contracts**: existing `ScriptBible` Pydantic schema; no new inter-layer
  protocol is introduced.
- **File sizes**: runtime provider 281 lines, runtime task 101, env helper 127,
  registry 4,282, truth ledger 3,690. Existing
  `tests/unit/test_eval_text_providers.py` is 504 lines, so OpenRouter coverage
  goes in a new focused test file rather than enlarging it. `make check-size`
  flags existing large production files but none are touched.
- **Decision context**: reviewed Ideal R1/R12/R18, methodology state/graph,
  `spec:8` hold phase, ADR-001, ADR-003, Stories 208-210, the maintained eval,
  task, scorer, goldens, and Promptfoo runbook. No new ADR is needed because
  this is an isolated provider qualification and model measurement.
- **DeepSeek extension**: reuse Story 211 because this is the same subsystem,
  validation boundary, and success surface. The 422-line benchmark provider is
  above the 400-line planning watchpoint; generalize its existing OpenRouter
  branch instead of adding a parallel transport, and do not add production
  responsibilities to it.

## Files to Modify

- `benchmarks/providers/script_bible_runtime_provider.py` — exact OpenRouter
  strict-schema transport and replayable metadata (281 lines).
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — Qwen3.8 frozen provider
  arm (101 lines).
- `tests/unit/test_openrouter_script_bible_provider.py` — focused new contract
  tests rather than adding to the 504-line existing provider test file.
- `docs/evals/attempts/021-script-bible-qwen38-openrouter.md` — plan, evidence,
  classifications, metrics, and conclusion.
- `docs/evals/truth-audit-ledger.yaml` — provider/task evidence inventory.
- `docs/evals/registry.yaml` — exact result history and scoped recommendation.
- `docs/stories/story-211-qwen38-openrouter-bounded-script-bible-eval.md` — live
  decision contract, spend ledger, work log, and validation.
- `docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json` —
  regenerated views.
- `benchmarks/scorers/script_bible_scorer.py` and focused scorer tests — repair
  the three source-proven Attempt 021 defects without changing the golden.
- `benchmarks/providers/script_bible_runtime_provider.py` and
  `tests/unit/test_openrouter_script_bible_provider.py` — generalize the
  isolated OpenRouter strict-schema path for the DeepSeek snapshot.
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — one DeepSeek arm plus
  the maintained Gemini comparator.
- `docs/evals/attempts/022-script-bible-deepseek-v4-flash.md` — predeclared
  matrix, spend ledger, metrics, classifications, and conclusion.

## Redundancy / Removal Targets

- Retire the benchmark-only OpenRouter branch if production later gains a
  provider-agnostic OpenRouter transport with the same identity, strict-schema,
  usage, privacy, and fallback guarantees.

## Notes

- OpenRouter catalog/endpoint evidence checked 2026-08-03. Catalog presence is
  not treated as authenticated callability or semantic evidence.
- The OpenRouter credential remains only in ignored local `.env`; its value is
  never printed, copied into tracked files, or recorded in evidence.

## Completed Qwen3.8 Plan

1. Qualify the exact route with authenticated metadata and a tiny synthetic
   strict-schema call under the initial `$0.02` ledger.
2. Implement only the transport proven necessary by native evidence, with
   focused tests and exact identity/usage/fallback validation.
3. Run one exact-runtime Open Frequency case through Promptfoo at `-j 1` and
   inspect structural/rubric results before any expansion.
4. Apply absolute gates and the privacy boundary. Stop or advance exactly as
   predeclared; do not change prompts, scorers, goldens, or defaults.
5. Record immutable evidence, validate the touched scope, and close with a
   per-slot adoption verdict.

## DeepSeek V4 Flash Extension Plan

1. Lock the immutable candidate, fresh incumbent, one complete synthetic
   screenplay, low/minimal reasoning settings, budget, privacy, and stop gates.
2. Add regression tests for the three known scorer defects, repair only those
   defects, and verify existing negative controls still fail.
3. Generalize the isolated OpenRouter strict-schema seam, qualify exact
   authenticated ZDR/no-fallback transport, and preserve raw identity/usage.
4. Run DeepSeek and Gemini together through the exact runtime task at
   `--no-cache -j 1`; inspect both structural details and rubric evidence.
5. Classify all mismatches, record immutable evidence and the scoped adoption
   verdict, regenerate methodology surfaces, and run the full required checks.

## Work Log

20260803-1255 — decision-contract: live OpenRouter catalog now lists exact
`qwen/qwen3.8-max` / canonical `qwen/qwen3.8-max-20260803` with one Alibaba
endpoint. Repository survey selected `script-bible` as the smallest clean
default-driving lane; current default is Gemini 3.5 Flash-Lite, no eligible
repaired comparator exists, and QA/video remain quarantined. A matching
evaluation-only credential was copied into ignored CineForge `.env` under
explicit user authorization. Next: authenticated native and strict-schema
qualification before implementation or scoring.

20260803-1410 — qualification-and-run: exact native OpenRouter/Alibaba strict
schema and no-fallback routing passed. The no-cache low-reasoning Open Frequency
call returned valid `ScriptBible` JSON with exact model/provider identity and
replayable usage. It scored `0.82495` overall (`0.6999` deterministic fail,
`0.95` rubric pass), took `64,608 ms`, and cost `$0.021418`. Operator impact:
Qwen3.8 is available and semantically strong, but it is currently more than
twice the slot's latency and cost limits, so the production default stays put.
Next falsifiable step: regrade this frozen output after the documented scorer
defects are independently repaired; make no new paid subject call until price
and latency can plausibly clear their gates.

20260803-1430 — mismatch-and-validation: source inspection classified exact
act-description rejection, annotated theme-evidence rejection, and the
`Kell ... cell towers are dead` death-regex match as scorer/contract defects;
minor unsupported severity, power-grid, and American-town claims are
model-wrong. Total task spend was approximately `$0.149572`, including the
native probe and maintained judge. Registry, truth ledger, JSON/YAML parsing,
focused provider/metric tests, Ruff, diff hygiene, and all `2,049` unit tests
passed. Methodology generated views were refreshed and checked. No private
fixture, production transport, model default, commit, or push was involved.

20260803-2127 — deepseek-decision-contract: reopened Story 211 instead of
fragmenting the same exact-runtime decision surface into another model-specific
story. Live DeepSeek and OpenRouter docs resolve the candidate to immutable
`deepseek/deepseek-v4-flash-0731`; the repo has OpenRouter but no native
DeepSeek credential. Predeclared one complete synthetic Open Frequency
comparison against fresh Gemini 3.5 Flash-Lite, low/minimal reasoning,
`--no-cache -j 1`, ZDR/no-fallback routing, `$5` aggregate cap, and the existing
quality/latency/cost gates. The three Attempt 021 scorer defects will be repaired
with regression coverage before any paid comparison call; prompt, schema,
golden, rubric, thresholds, production transport, and defaults remain frozen.
Next: implement and validate the scorer/provider repairs, then run the bounded
two-arm comparison.

20260803-2143 — deepseek-qualification: the three source-proven scorer defects
were repaired with direct positive/negative controls. Frozen Qwen output now
passes the current scorer at `0.9533`, while its prior latency/cost rejection
remains intact. A tiny exact DeepSeek/Phala probe qualified strict `ScriptBible`,
low reasoning, terminal identity/usage/cost evidence, ZDR, denied collection,
and no fallbacks, but took `133,706 ms`—already beyond the slot's `30,000 ms`
latency limit. Operator impact: the route is real and privacy-eligible for the
synthetic fixture, but even the tiny request is too slow for this default slot.
Next: run the one frozen full-script comparison and retain any pre-response
failure without assigning a quality score.

20260803-2156 — deepseek-bounded-result: the full-script two-arm run returned a
valid fresh Gemini result but Promptfoo's independent five-minute Python-worker
watchdog killed DeepSeek before it returned. After raising only that watchdog,
the single allowed DeepSeek-only retry exhausted the pinned route's rate limits
after `182,003 ms`; no alternative endpoint, fallback, semantic retry, second
fixture, or other slot ran. Gemini scored `0.78995` overall (`0.6999`
deterministic fail, `0.88` rubric pass), with `4,128 ms` latency and estimated
`$0.0028251` subject cost. Its acts overlap the final morning scene and its
north-shelter relay account is incomplete, so the repaired hard gate correctly
rejects it despite the rubric pass. Known spend is about `$0.1254471`; even a
conservative maximum charge for the unreconciled timed-out DeepSeek request
keeps the run below the `$5` cap. Operator impact: do not adopt DeepSeek from
this evidence; its full-script quality is unmeasured and its observed access is
far too slow/unreliable. The configured Gemini default remains unchanged but
is still provisional, now with a fresh one-case maintenance signal. Next:
validate and close the evidence-only branch without committing or pushing.

20260803-2201 — validation-closeout: `88` focused scorer/provider/contract
tests, focused Ruff, JSON/YAML parsing, eval-registry consistency, truth-ledger
consistency, and methodology compile/check all passed. The first full unit run
found one registry-ordering regression because a test deliberately selects the
historical adopted Gemini row by first match; the new current-contract rejection
was moved after that immutable adoption-history row without changing either
result. The targeted regression then passed and the complete rerun finished
with `2,058 passed`; a final rerun after strengthening explicit-death negative
controls finished with `2,062 passed`. `make check-size` reported only existing large files; no
production or UI file was touched, so browser verification is not applicable.
No default, production transport, secret, commit, push, or deployment changed.

## Prior Result — Qwen3.8

**Do not adopt Qwen3.8 Max for `script_bible_v1` at current OpenRouter
price/latency.** Access and conditional semantic quality qualify, but the
measured call independently fails both absolute value gates. Reliability is a
single successful observation, and broader evidence was correctly stopped.

**Where to verify:** inspect
`benchmarks/results/script-bible-qwen38-openrouter-open-frequency-2026-08-03.json`
for the frozen response/grades and
`docs/evals/attempts/021-script-bible-qwen38-openrouter.md` for the decision
ledger and mismatch evidence.

## Current Result — DeepSeek V4 Flash

**Do not adopt DeepSeek V4 Flash for `script_bible_v1` from this run.** The
exact pinned strict-schema route qualified on a tiny probe, but no full-script
completion survived the bounded comparison: the first exceeded five minutes
and the one repaired retry exhausted rate limits. Quality is unmeasured, and
the latency/reliability gates already fail. Fresh Gemini is not a clean
current-contract pass either (`0.78995` overall), so this attempt makes no
production default change.

**Where to verify:** inspect
`benchmarks/results/script-bible-deepseek-v4-flash-vs-gemini35flashlite-open-frequency-2026-08-03.json`,
`benchmarks/results/script-bible-deepseek-v4-flash-open-frequency-retry-2026-08-03.json`,
and `docs/evals/attempts/022-script-bible-deepseek-v4-flash.md`.
