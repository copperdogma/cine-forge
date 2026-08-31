---
id: "217"
title: "Hy4 Preview Bounded Script-Bible Evaluation"
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
  - "208"
  - "211"
  - "216"
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
  - "hy4-preview"
legacy_system: "Cross-Cutting"
---

# Story 217 — Hy4 Preview Bounded Script-Bible Evaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R12, R18
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Stories 208, 211, 216

## Goal

Qualify exact OpenRouter `tencent/hy4-preview` and run the smallest
source-backed exact-runtime script-bible evaluation that could change the
provisional `gemini-3.5-flash-lite` decision. Keep access, transport,
reliability, capability, economics, and adoption separate, and stop after the
repo-authored synthetic Open Frequency case on any absolute gate failure.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and C3 require current evidence before a new
  model can replace a value-optimized slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest result**: Story 216 found no exact-runtime two-corpus production-
  eligible model; the provisional Gemini default remains below the quality gate.
- **Trigger**: exact `tencent/hy4-preview` is newly API-listed on OpenRouter with
  a 1M context window, 64K output, reasoning controls, and advertised structured
  output at a price plausibly below the lane cap.
- **Child baseline**: native tiny strict-schema probe precedes harness parity and
  one uncached Open Frequency case. Stop at the first absolute miss.

## Decision Contract

- **Route**: OpenRouter Chat Completions, exact requested/served
  `tencent/hy4-preview`; no model-list fallback. Do not pin the sole same-model
  provider because route identity is not decision-bearing; record it instead.
- **Eval**: reuse `script-bible`; do not create a parallel eval ID.
- **Default**: retain provisional `gemini-3.5-flash-lite`.
- **Production contract**: `script_bible_v1.EXTRACTION_PROMPT` and
  `src/cine_forge/schemas/script_bible.py#ScriptBible`.
- **Frozen scoring**: repaired maintained Python scorer, Open Frequency golden,
  and cross-provider Claude Opus 4.6 rubric.
- **Configuration**: low reasoning excluded from visible output, sampling
  omitted, configured 65,536 output-token ceiling capped to the route's 64,000.
- **Quality gates**: overall `>=0.90`; deterministic `>=0.70` plus every hard
  assertion; Opus rubric `>=0.80`; every assertion passes.
- **Operational gates**: latency `<=30,000 ms`; subject cost `<=$0.01`; exact
  identity; terminal complete output; raw reconciled usage/cost; provider-
  enforced strict `ScriptBible` JSON.
- **Privacy**: only repo-authored synthetic Open Frequency is eligible. The
  selected route may retain or train on it; no ZDR or data-collection filter is
  required or implied, and no provider account setting may change.
- **Execution**: US$0.75 aggregate cap; no cache; concurrency one; one transient
  retry; no semantic retry after a valid completion.
- **Stop**: stop before scoring on access, identity, terminal, schema, usage, or
  parity failure; stop after Open Frequency on any absolute miss. No private
  corpus, second corpus, or comparator under this approved lane.

## Acceptance Criteria

- [x] Exact access, served identity, strict schema, terminal completion, usage,
  route, and cost are retained, or the pre-response blocker is recorded.
- [x] A zero-cost resolved-matrix preflight precedes paid multi-case execution.
- [x] If qualified, one no-cache Open Frequency case is inspected against all
  declared gates and every significant mismatch is classified.
- [x] Attempt, registry, story, ledger, commands, and sanitized provenance are
  replayable.
- [x] Production transport/defaults remain unchanged.

## Out of Scope

A new eval ID, private payloads, second corpus, incumbent, prompt/scorer/golden/
rubric tuning, production integration, defaults, deployment, commit, or push.

## Approach Evaluation

- **Simplification baseline**: the exact-runtime one-call lane is the baseline;
  one passing slot would not prove whole-pipeline simplification.
- **AI-only**: one call reads the screenplay and returns strict `ScriptBible`.
- **Hybrid**: provider JSON Schema plus Pydantic validation, deterministic
  source checks, and an independent semantic rubric.
- **Pure code**: only transport qualification and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  defines the script-bible boundary. `spec:8` is hold-state work. No new
  architecture decision is introduced.
- **Existing patterns**: Attempts 020–030, the benchmark-only OpenRouter seam,
  env wrapper, identity validator, and retained evidence manifests.
- **Eval**: reuse maintained `script-bible`.

## Tasks

- [x] Read alignment, decision, registry, prior-attempt, runtime, scorer, golden,
  and runbook contracts; run live discovery and endpoint inspection.
- [x] Add the smallest isolated Hy4 provider/config seam with focused tests.
- [x] Run zero-cost resolved-harness preflight and tiny native strict probe.
- [x] If qualified, run one no-cache Open Frequency case at `-j 1`.
- [x] Record Attempt 031, registry history, ledger, hashes, and story work log.
- [x] Run proportional validation and `git diff --check`.

## Workflow Gates

- [x] Build complete
- [x] Validation complete
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owner**: benchmark-only runtime provider; no production class changes.
- **Contract**: existing `ScriptBible` Pydantic schema.
- **Sizes**: provider is already over 400 lines; this adds only declarative model
  metadata and reuses the existing generic OpenRouter function.
- **Decisions**: ADR-001 and ADR-003 apply; no new ADR is needed.

## Files to Modify

- `benchmarks/providers/script_bible_runtime_provider.py` — model metadata.
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — bounded provider arm.
- `tests/unit/test_openrouter_script_bible_provider.py` — request contract.
- `docs/evals/attempts/031-script-bible-hy4-preview.md` through Attempt 034 —
  strict retries and bounded diagnostic records.
- `docs/evals/story-217-hy4-preview-*.json` — sanitized transport, ledger, and
  diagnostic provenance.
- `docs/evals/registry.yaml` — lineage and attempt history.
- this story and generated methodology dashboards.

## Redundancy / Removal Targets

The benchmark-only entry is removable if the router stops serving the model.

## Plan

1. Freeze this contract and Attempt 031 before provider calls.
2. Prove exact access and provider-enforced strict schema on a tiny source.
3. Verify the resolved one-cell Open Frequency topology without spending.
4. Run the one decision case only if all earlier gates qualify.
5. Record the layered verdict and validate proportionately.

## Work Log

20260829-2020 — preflight: accepted isolated clean worktree at
`2530ca6c0910672a20594bd2c3908b4b7df43535`; read the complete owner evaluation
skill and companion workflow contracts, alignment stack, relevant ADR-backed
script-bible boundary, registry, all exact-runtime attempts, provider/task,
scorer/golden, and Promptfoo runbook. Live owner discovery and public OpenRouter
metadata resolve exact `tencent/hy4-preview`, canonical snapshot
`tencent/hy4-preview-20260827`, one Tencent route, 1,048,576 context, 64,000
maximum completion tokens, and advertised strict-output parameters. Froze the
synthetic-only privacy boundary, US$0.75 cap, and no-default/no-commit limits;
provider spend remains `$0`.

20260829-2027 — progressive capacity stop: focused Hy4 request/config tests and
the one-cell resolved-matrix preflight passed. The exact tiny strict-schema probe
then returned OpenRouter/Tencent upstream shared-pool 429 before invocation; the
provider-directed identical retry after 60 seconds returned the same result.
Stopped before screenplay, scorer, judge, incumbent, or second corpus. Access is
constrained; transport/capability/latency/subject economics are unmeasured;
provider spend is `$0` of US$0.75. Evidence is retained in
`docs/evals/story-217-hy4-preview-access-transport-evidence.json`; defaults are
unchanged.

20260829-2033 — validation: methodology compilation, evidence JSON and registry
YAML parsing, 55 focused provider/scorer/registry tests, Ruff, and whitespace
checks passed. The complete unit run reached `2174 passed, 1 failed`; the sole
failure was Story 213's intentionally rolling hash manifest detecting the new
registry/provider/config/test bytes. Refreshed only those four hashes, then the
manifest/provider/registry verification passed `32/32`. No product prompt,
schema, scorer, golden, default, provider account setting, or runtime transport
changed.

20260830-1108 — scheduled transport retry: refreshed the live OpenRouter endpoint
catalog and resumed at Attempt 031's exact tiny strict-`ScriptBible` gate. The
single Tencent route still advertised the exact 20260827 snapshot and required
strict-output controls. One production-shaped synthetic micro-source request
returned no headers, identity, terminal response, usage, or cost after more than
115 seconds, so the client was terminated after the `<=30s` operational gate had
already failed. Stopped before Open Frequency, scorer, judge, incumbent, or any
private/second corpus. Confirmed spend remains `$0`; provider-reported cost is
unavailable, with conservative maximum exposure bounded below `$0.162` and thus
within the original US$0.75 ceiling. Attempt 032 retains the layered verdict;
capability and strict-schema compatibility remain unmeasured, defaults unchanged.

20260830-1112 — retry validation: parsed the new evidence JSON and registry YAML;
eval-registry consistency passed; methodology compile/check is current; 37
focused OpenRouter provider, script-bible scorer, and eval-manifest tests passed;
focused Ruff and `git diff --check` passed. Refreshed only Story 213's rolling
registry hash after adding Attempt 032. Existing architecture-audit and UI-scout
freshness warnings are unrelated. No product code, prompt, schema, scorer,
golden, runtime default, or provider account setting changed.

20260830-2310 — scheduled heartbeat-2 transport retry: the live catalog still
resolved exact `tencent/hy4-preview` to the sole Tencent 20260827 endpoint. One
unchanged production-shaped tiny strict-`ScriptBible` request pinned Tencent and
disabled fallback. The client accepted non-error response headers and entered
chunked body reading, but no complete body existed at the absolute 30-second
latency boundary, so the request was interrupted. Stopped before Open Frequency,
scorer, judge, incumbent, or any private/second corpus. No request ID, served
identity, terminal output, schema artifact, usage, provider-reported cost, or raw
file existed. Confirmed spend remains `$0`; conservative unreconciled exposure
is now `<=US$0.324` cumulative, leaving `US$0.426` under the original ceiling.
Attempt 033 records transport/reliability failure and capability unmeasured;
defaults remain unchanged.

20260830-2313 — heartbeat-2 validation: new evidence JSON and registry YAML
parsed; eval-registry consistency passed; methodology compile/check is current;
37 focused OpenRouter provider, script-bible scorer, and eval-manifest tests
passed; focused Ruff and `git diff --check` passed. Refreshed only Story 213's
rolling registry hash after adding Attempt 033. Existing architecture-audit and
UI-scout freshness warnings are unrelated. No product code, prompt, schema,
scorer, golden, runtime default, or provider account setting changed.

20260831-0928 — capability-diagnostic preflight: the strict production path has
never produced a terminal valid answer, so predeclared Attempt 034 to isolate
raw capability by relaxing exactly provider-enforced `response_format` / JSON
Schema on the same synthetic micro-source. All other request, model, route,
reasoning, token, privacy, cache, concurrency, prompt, and input constraints are
frozen. The diagnostic runner retains raw bytes in ignored/protected `output/`
before parsing and enforces a 180-second total deadline while preserving the
failed `<=30s` production latency verdict. Confirmed spend remains `$0`; prior
conservative exposure `<=US$0.324` leaves `US$0.426`. Production adoption remains
deferred regardless of diagnostic quality.

20260831-0937 — capability-diagnostic stop: submitted one tiny synthetic request
with the exact model, Tencent pin, fallback disabled, frozen prompt/input,
reasoning low, 64,000-token ceiling, parameter enforcement, no cache, and
concurrency one; only provider `response_format` was omitted. OpenRouter accepted
the request with HTTP 200 and a generation ID, but its chunked response delivered
zero body bytes by the 180.006-second diagnostic deadline. The ignored raw
envelope, headers, request manifest, and summary were retained and hashed before
any parse. No returned identity, finish, usage, reported cost, schema, semantic
content, or score exists. Since the relaxation did not yield a terminal answer,
strict-mode failure was not isolated; stopped before Open Frequency, scorer, or
judge. Confirmed spend remains `$0`; cumulative conservative unreconciled
exposure is `<=US$0.486`, leaving `US$0.264`. Production adoption remains defer,
and unchanged retries are exhausted pending a material transport change or new
authorization.

20260831-0947 — capability-diagnostic validation: evidence JSON and registry
YAML parsed; eval-registry consistency passed; methodology compile/check is
current; 37 focused provider, scorer, and eval-contract tests passed; focused
Ruff and `git diff --check` passed. Refreshed only Story 213's rolling registry
hash for Attempt 034. Existing architecture-audit and UI-scout freshness
warnings remain unrelated. No product prompt, schema, scorer, golden, default,
provider account setting, or production transport changed.

20260831-1011 — closeout: full backend validation passed (`2175` unit tests),
full `src/` and `tests/` Ruff passed, methodology outputs and eval-registry
consistency were current, all tracked/untracked files were audited as Story 217
campaign evidence, and ignored credential/raw-output paths were excluded from
the landing set. The failed/deferred result satisfies the story's progressive-
stop contract: Hy4 never produced a terminal production response, no semantic
score was invented, the provisional Gemini default remains unchanged, and
unchanged retries are exhausted. Marked Story 217 Done. Recommended next step:
`/check-in-diff`.
