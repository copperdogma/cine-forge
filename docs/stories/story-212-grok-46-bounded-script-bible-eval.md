---
id: "212"
title: "Grok 4.6 Bounded Script-Bible Eval"
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
  - "207"
  - "208"
  - "209"
  - "210"
  - "211"
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
  - "xai"
  - "grok-4.6"
legacy_system: "Cross-Cutting"
---

# Story 212 — Grok 4.6 Bounded Script-Bible Eval

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (script bible and model-upgrade boundary)
**Depends On**: Stories 207, 208, 209, 210, 211

## Goal

Qualify direct xAI `grok-4.6` and run the smallest source-backed exact-runtime
script-bible evaluation that can change CineForge's ingest-model decision.
Advance beyond the synthetic Open Frequency screenplay only if the frozen arm
clears quality, latency, cost, reliability, privacy, and safety gates. Preserve
exact identity, usage, pricing, retention evidence, and failures; do not change
the production default without a separate explicit user decision.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and compromise C3 require current evidence
  before a new model can replace a value-optimized slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest higher-level result**: Story 208 repaired the source/scorer/corpus
  truth; Stories 210 and 211 established the bounded exact-runtime ladder.
  There is still no eligible repaired two-corpus result.
- **Measured trigger**: live xAI discovery on 2026-08-12 returned exact new slug
  `grok-4.6`. First-party docs declare native Responses and Chat Completions,
  strict structured output, required reasoning, 500k context, and current
  `$2/M` input plus `$6/M` output pricing below 200k prompt tokens.
- **Child baseline**: qualify a minimal direct strict-schema response, then run
  the exact-runtime Open Frequency case at concurrency one. Advance to The
  Mariner and a fresh incumbent only after every absolute gate passes.

## Decision Contract

- **Candidate/access path**: direct xAI API, exact slug `grok-4.6`, no router or
  fallback. Require exact returned model, response ID, terminal completion,
  strict `ScriptBible` schema, and reconciled prompt/reasoning/visible/total
  usage. The initial native probe uses xAI Responses; harness parity may use
  the existing direct Chat Completions transport only after request inspection
  proves the same strict production contract.
- **Frozen configuration**: `reasoning_effort=low`; omit temperature, top-p,
  seed, stop, penalties, and other unverified/unsupported sampling controls.
  Reasoning cannot be disabled. The official docs do not publish a separate
  Grok 4.6 output limit, so the access/contract probe must establish an accepted
  bounded cap before the full-script call.
- **Selected slot/eval**: `script_bible_v1` / maintained `script-bible`.
- **Executable default**: `gemini-3.5-flash-lite`, 65,536 output tokens,
  minimal thinking.
- **Best eligible maintained evidence**: none under the repaired exact-runtime
  two-corpus contract. Grok 4.5's historical `0.975` row used the obsolete
  one-corpus/runtime-mismatched boundary and missed latency/cost gates.
- **Frozen semantic contract**: production `EXTRACTION_PROMPT`, `ScriptBible`
  Pydantic schema, maintained Python scorer, source-linked Open Frequency
  golden, pinned Opus 4.6 rubric, and base SHA
  `3832dee7f397978d441f4914edd8df5e7eb2e6ed`.
- **Matrix**: one low-reasoning Grok arm on complete repo-authored synthetic
  Open Frequency. Run a fresh Gemini incumbent on the same case and later The
  Mariner only if Grok clears the first case's absolute gates. No diagnostic
  candidate arm is predeclared.
- **Absolute gates**: every assertion passes; aggregate overall `>=0.90`;
  latency `<=30,000 ms`; subject cost `<=$0.01`; exact identity; terminal strict
  schema; sane usage; no refusal; acceptable first-attempt reliability.
- **Privacy**: only repo-authored Open Frequency is eligible until the live
  `x-zero-data-retention` header proves team ZDR. `store:false` alone is not ZDR
  proof. The Mariner remains excluded unless ZDR is proven.
- **Judge/bias**: maintained Opus 4.6 is cross-provider for xAI. Keep Python and
  rubric scores separate and inspect source before interpreting their mean.
- **Budget**: aggregate paid-call cap `$5`; begin at `$0`. Probe plus one subject
  and judge are conservatively below the cap. Stop before any unbounded stage.
- **Cache/concurrency/retries**: `--no-cache`, `-j 1`, one capacity/transport
  retry maximum, and no semantic retry after a valid completed response.
- **Progressive stop**: any mandatory access, transport, privacy, quality,
  latency, cost, reliability, or safety failure stops expansion. A clean
  one-case pass is provisional; adoption evidence needs the declared second
  corpus and fresh incumbent on the same frozen contract.

## Acceptance Criteria

- [x] Exact authenticated access, native and harness served identity, strict
  JSON Schema, reasoning, usage, finish status, price, and live ZDR header are
  retained without exposing credentials.
- [x] The exact-runtime Open Frequency cell runs no-cache at concurrency one or
  its pre-response blocker is retained without being scored as model quality.
- [x] Structural and semantic scores, subject/judge latency and cost, and every
  significant source mismatch are inspected and classified.
- [x] Expansion occurs only if all declared first-case gates clear; every
  unmeasured later surface is reported as not measured.
- [x] Result, attempt, registry, story, cost ledger, and contract provenance are
  replayable; production transport/defaults remain unchanged.

## Out of Scope

- QA-pass, video/ordered-frame, image/video generation, or a broad slot sweep.
- Private fixtures before live team ZDR is proven.
- Golden, scorer, rubric, or semantic-prompt tuning to rescue the candidate.
- Production xAI integration, default changes, deployment, commit, or push.

## Approach Evaluation

- **Simplification baseline**: this exact-runtime lane is the single-call
  baseline. One passing slot would not prove whole-pipeline simplification.
- **AI-only**: one Grok call reads the complete screenplay and returns one
  strict `ScriptBible`.
- **Hybrid**: provider-enforced JSON Schema plus Pydantic validation,
  deterministic source checks, and an independently pinned semantic rubric.
- **Pure code**: appropriate only for request qualification, identity/usage
  preservation, pricing, and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  makes script bible a cheap story-lane artifact and preserves intent across
  model upgrades. `spec:8` is hold-state maintenance while `spec:6/spec:7`
  remain active product focus, so scope stays narrow.
- **Existing patterns to reuse**: Story 211's exact-runtime provider and bounded
  ladder, Story 208's repaired scorer/goldens, provider-env wrapper, identity
  validator, and metric extractor.
- **Eval**: reuse `script-bible`; no parallel eval or architecture is needed.

## Tasks

- [x] Qualify official and live native xAI access/contract/privacy evidence.
- [x] Add only the benchmark provider/config/test support required for exact
  Grok 4.6 runtime parity; do not change production defaults.
- [x] Run the declared progressive matrix at `--no-cache -j 1`.
- [x] Run `/improve-eval`-equivalent mismatch investigation, classify every
  significant mismatch, and update the registry for every executed eval.
- [x] Record Attempt 023, result evidence, contract hashes, spend ledger, and
  story work log; regenerate methodology surfaces.
- [x] Check whether the chosen implementation makes any helper/docs redundant;
  remove them or record a concrete retirement condition.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Focused backend tests and Ruff for touched provider/eval files.
  - [x] UI not touched; browser verification is not applicable.
- [x] If story/eval metadata changes: `pnpm methodology:compile` and
  `pnpm methodology:check`.
- [x] Search all docs and update related truth surfaces.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** only eligible synthetic/public data leaves the repo.
  - [x] **T1 — AI-Coded:** evidence and contracts are replayable.
  - [x] **T2 — Architect for 100x:** test one-call capability first.
  - [x] **T3 — Fewer Files:** reuse maintained eval/provider seams.
  - [x] **T4 — Verbose Artifacts:** preserve exact result and spend evidence.
  - [x] **T5 — Ideal vs Today:** avoid scaffolding beyond measured need.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: benchmark-only `script_bible_runtime_provider.py`;
  no production class gains responsibility.
- **Data contracts**: existing `ScriptBible` Pydantic schema.
- **File sizes**: runtime provider 455 lines, runtime config 126 lines, focused
  provider tests 232 lines, registry 4,225+ lines. The provider is over the
  400-line warning but under the 500-line class threshold; additions must be
  small or extracted. No production large file should grow.
- **Decision context**: ADR-001 shared entity extraction requires eval-first
  assignment; ADR-003 defines the script-bible/model-upgrade boundary. No new
  ADR applies because this is isolated measurement, not architecture.

## Files to Modify

- `benchmarks/providers/script_bible_runtime_provider.py` — narrow direct xAI
  exact-contract lane or extraction if required (455 lines).
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — Grok 4.6 arm (126 lines).
- `tests/unit/test_openrouter_script_bible_provider.py` or a focused new test —
  request/identity/usage contract (232 lines existing).
- `docs/evals/attempts/023-script-bible-grok-46.md` — plan and results.
- `docs/evals/registry.yaml` — story lineage, score, and attempt history.
- `docs/stories/story-212-grok-46-bounded-script-bible-eval.md` — live contract/log.
- generated methodology dashboards — refreshed from canonical sources.

## Redundancy / Removal Targets

- No production path is superseded. Benchmark-only Grok support may be removed
  when the maintained provider supports generic direct Responses parity with
  equivalent identity, ZDR, strict-schema, and usage evidence.

## Notes

- Official xAI sources checked 2026-08-12: model page, launch announcement,
  structured-output, reasoning, pricing, rate-limit, generation, and security
  documentation. Exact output-token ceiling remains unverified until live probe.

## Plan

1. Freeze the contract above and create Attempt 023 before paid calls.
2. Run catalog/access and tiny direct Responses strict-schema probes.
3. Add the smallest tested harness parity seam justified by native evidence.
4. Run Open Frequency once, inspect all evidence, and apply the progressive stop.
5. Record durable results and run proportionate validation.

## Work Log

20260812-2230 — discovery and decision contract: isolated a clean current-base
worktree, confirmed exact live xAI catalog access to new `grok-4.6`, reviewed
Ideal/spec/state/graph/dashboards, ADR-001/ADR-003, all script-bible attempts,
runtime default, task/prompt/scorer/goldens/provider/runbook, and official xAI
docs. Frozen the direct-xAI low-reasoning Open Frequency-first ladder, current
gates, privacy rule, one-retry limit, `$5` ledger, and no-default boundary.
Next step: create Attempt 023 and run the tiny native strict-schema probe.

20260812-2255 — completion: exact direct Grok 4.6 access, strict production
schema parity, one no-cache Open Frequency result, source-backed mismatch
classification, progressive cost stop, registry/attempt/truth-ledger evidence,
and dirty-contract hashes are complete. Validation passed with 2,066 unit tests,
full Ruff, focused provider/accounting tests, eval-registry/truth/contract checks,
methodology compile/check, JSON/YAML loads, and `git diff --check`. UI was not
touched, so browser validation is not applicable. Story 212 closes as a bounded
do-not-adopt result; the optional next step is `/check-in-diff` if Cam wants the
evidence landed.
