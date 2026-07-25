---
id: "210"
title: "Opus 5 Bounded Script-Bible Eval"
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
  - "opus-5"
  - "anthropic"
legacy_system: "Cross-Cutting"
---

# Story 210 — Opus 5 Bounded Script-Bible Eval

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Story 035, Story 208, Story 209

## Goal

Evaluate first-party Anthropic `claude-opus-5` on one bounded, production-shaped
full-script surface: the `script_bible_v1` contract. Use a progressive
two-corpus/comparator ladder, stopping as soon as a valid result makes adoption
impossible under the absolute gates. Preserve exact transport, identity, usage,
latency, cost, and mismatch evidence without changing production transport or a
runtime default.

## Eval Ladder Context

- **Root / parent need**: R1 requires complete screenplay understanding; `spec:8`
  requires current evidence-backed value choices; C3 remains `hold` until one
  model clears repaired quality, latency, cost, reliability, privacy, and safety
  gates across the relevant surface.
- **Parent eval**: `script-bible`, a default-driving full-script proxy over The
  Mariner and Open Frequency.
- **Latest higher-level result**: Story 208 repaired the second corpus, goldens,
  scorer, and exact-schema rules, but the registry records no repaired
  two-corpus row through the exact runtime prompt/schema boundary.
- **Measured failure mode**: historical one-corpus rows and the current
  benchmark-only prompt are not eligible to decide the executable
  `script_bible_v1` default.
- **Child baseline**: one fresh two-model, two-corpus runtime-shaped comparison.
  This can decide only the script-bible slot; it cannot eliminate C3 or justify
  a whole-pipeline model change.

## Decision Contract

- **Candidate**: Anthropic Messages API `claude-opus-5`; requested and returned
  identities must match exactly.
- **Runtime default / comparator**: `gemini-3.5-flash-lite`, confirmed from
  `script_bible_v1/main.py` and `module.yaml`; rerun fresh on identical inputs.
- **Surface**: `script-bible`; exact module prompt, `ScriptBible` Pydantic schema,
  The Mariner and Open Frequency fixtures, maintained structural scorer and
  semantic rubric.
- **Configuration**: Opus 5 standard mode, adaptive thinking at provider default
  high effort, no sampling parameters, provider-enforced
  `output_config.format`, `max_tokens=65536`; Gemini default minimal thinking and
  `max_tokens=65536`.
- **Judging**: retain the maintained Opus 4.6 rubric for comparability, but it is
  same-provider evidence for Opus 5. Predeclare a capable OpenAI second judge on
  frozen outputs if the Anthropic judgment could affect adoption; deterministic
  hard gates remain independent.
- **Execution controls**: no cache, concurrency 1, at most one transport retry,
  default total paid-call cap US$5. Stop if pricing or the smallest valid matrix
  cannot be bounded under the cap.
- **Target / gates**: current registry target `overall >= 0.90`,
  `latency_ms <= 30000`, `cost_usd <= 0.01`, every assertion must pass, exact
  identity/usage/schema required, no safety or privacy incompatibility.
- **Freshness / provenance**: base SHA
  `aacf185829d8616aa577c903e2a73f69554ff6f4`; record hashes and a patch for every
  relevant dirty contract file and retain new result identities without
  overwriting history.
- **Stop conditions**: access/identity failure yields capability not measured;
  contract failure is repaired only at the narrow transport seam before scoring;
  a valid miss is classified model-wrong, golden-wrong, or ambiguous.

## Acceptance Criteria

- [x] Official Opus 5 contract and live catalog/access evidence identify
  `claude-opus-5` without alias substitution.
- [x] Native access and strict structured-output probes preserve served identity,
  request ID, terminal status, usage, latency, and cost.
- [x] The progressive ladder runs Opus 5 through the exact `script_bible_v1`
  prompt/schema boundary and records why the second corpus and fresh Gemini
  comparator became non-decision-relevant after the absolute value-gate miss.
- [x] Both maintained scoring layers run; same-provider judge bias is disclosed
  and no second judge is spent because it cannot reverse the hard value result.
- [x] Every material mismatch is source-inspected and classified, with
  runtime-blocking significance recorded.
- [x] Raw results, attempt, registry history, story work log, cost ledger, and
  dirty-contract provenance are complete and replayable.
- [x] A scoped adopt / conditional-adopt / do-not-adopt / defer decision is
  stated for script bible only; no default changes implicitly.

## Out of Scope

- The full ingest/world-building/render pipeline or the multi-hour full-script
  throughput detector.
- QA-pass, ordered-frame/video-understanding, character extraction, or any other
  model slot.
- Native video/audio claims, C3 elimination, production rollout, deployment,
  commit, push, or default changes.
- Golden, scorer, or semantic-prompt tuning to rescue either model.

## Approach Evaluation

- **Simplification baseline**: this is the single-call full-script baseline. If
  Opus 5 clears the repaired exact runtime contract, it may be a slot candidate;
  one slot cannot prove whole-pipeline simplification.
- **AI-only**: each subject receives one full screenplay and returns one strict
  `ScriptBible`; this is the behavior under evaluation.
- **Hybrid**: provider-enforced Pydantic structure plus deterministic source
  checks and semantic judging protect schema, fidelity, and qualitative depth.
- **Pure code**: appropriate only for transport qualification, identity/usage
  preservation, pricing, and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment;
  ADR-003 makes script bible a core story artifact. Story 208 requires repaired
  source truth and exact provenance; Story 209 requires transport qualification,
  a fair bounded matrix, and no implicit default change.
- **Existing patterns to reuse**: `script_bible_v1`, the generic Anthropic
  Messages provider, Story 206's Opus transport/pricing work, Story 208's
  two-corpus scorer/goldens, the provider-env wrapper, and metric extractor.
- **Eval**: the existing `script-bible` registry entry owns scoring and lineage;
  add the minimum runtime-shaped provider lane rather than create a parallel
  capability eval.

## Tasks

- [x] Read Ideal/spec/state/graph/build-map, registry, Story 208/209, relevant
  ADR/design records, all `script-bible` attempts, task, prompt, scorer, goldens,
  runtime module, and Promptfoo runbook.
- [x] Confirm exact official identity, access path, pricing, limits, thinking,
  structured output, privacy, and rejected parameters; run live discovery.
- [x] Resolve a clean evaluation worktree and predeclare the matrix/spend ledger.
- [x] Add narrowly tested Opus 5 pricing support and an isolated exact
  runtime-shaped Promptfoo provider lane; leave production transport unchanged.
- [x] Run access, native strict-schema, and harness-parity probes before scoring.
- [x] Apply the declared progressive stop after the first exact-runtime full-script
  case failed absolute latency and cost gates; mark the remaining matrix not measured.
- [x] Inspect source, outputs, both score layers, judge bias, identity, usage,
  latency, and cost; classify every significant mismatch.
- [x] Record an immutable result, attempt, registry history, story evidence, and
  regenerated methodology surfaces.
- [x] Check whether the chosen implementation makes any existing code, helper
  paths, or docs redundant; remove it or record a concrete retirement condition.
- [x] Run required checks for touched scope:
  - [x] Backend minimum:
    `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Focused backend lint/tests for transport, provider, scorer, and registry.
  - [x] UI not touched; UI/browser checks are not applicable.
- [x] If story metadata or methodology state changes:
  `pnpm methodology:compile` and `pnpm methodology:check`.
- [x] Run `/improve-eval`-equivalent mismatch investigation and update the
  registry for every executed eval, including inconclusive transport attempts.
- [x] Search all docs and update related truth surfaces.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** only repo-owned screenplay fixtures leave the repo;
    credentials remain inside the provider-env wrapper.
  - [x] **T1 — AI-Coded:** exact commands, identities, hashes, and classifications
    make the run reproducible by another agent.
  - [x] **T2 — Architect for 100x:** the runtime-shaped single-call baseline is
    measured before adding scaffolding.
  - [x] **T3 — Fewer Files:** reuse the maintained eval and provider seams.
  - [x] **T4 — Verbose Artifacts:** raw evidence and the work log preserve the
    decision, failures, and spend.
  - [x] **T5 — Ideal vs Today:** only current evidence can shrink model tiering.

## Workflow Gates

- [x] Build complete: implementation finished and required checks run
- [x] Validation complete
- [x] Story marked done by the owning `/evaluate-model` workflow

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `script_bible_v1` owns the exact prompt/schema call;
  `benchmarks/providers/` owns the isolated Opus 5 parity transport;
  `src/cine_forge/evals/cost_metrics.py` owns retained result pricing; the
  existing registry entry owns the decision.
- **Data contracts**: existing `ScriptBible` Pydantic schema crosses the
  provider/runtime boundary; no new inter-layer model is introduced.
- **File sizes**: production `src/cine_forge/ai/llm.py` remains unchanged so
  Story 208's immutable evidence hashes remain valid. The focused benchmark
  provider is covered by unit tests. `benchmarks/providers/anthropic_messages_provider.py` is 136 lines,
  `benchmarks/tasks/script-bible.yaml` 220,
  `benchmarks/scorers/script_bible_scorer.py` 416,
  `scripts/extract-eval-metrics.py` 400, and the registry 4,244.
- **Decision context**: reviewed ADR-001, ADR-003, textual golden
  reverification, registry evidence consistency, independent closeout review,
  Stories 206/208/209, and the current Anthropic documentation. No new ADR is
  needed because this repairs and measures an existing provider/runtime
  contract without choosing a new architecture.

## Files to Modify

- `src/cine_forge/evals/cost_metrics.py` — Opus 5 retained-result pricing.
- `benchmarks/providers/script_bible_runtime_provider.py` — exact
  `script_bible_v1` runtime-shaped parity and metadata without changing
  production transport.
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` and
  `benchmarks/prompts/script-bible-runtime-marker.txt` — bounded two-arm ladder.
- Focused unit tests under `tests/unit/` — transport, provider, identity, usage,
  and cost regression coverage.
- `benchmarks/results/` — fresh raw subject/judge evidence and provenance manifest.
- `docs/evals/attempts/020-script-bible-opus-5-runtime-comparison.md` — plan,
  classification, metrics, and conclusion.
- `docs/evals/truth-audit-ledger.yaml` — explicit prompt/transport inventory and
  bounded live-evidence limitations.
- `docs/evals/registry.yaml` — exact run history and scoped recommendation.
- `docs/stories/story-210-opus-5-bounded-script-bible-eval.md` — live decision
  contract, spend ledger, work log, and validation.
- `docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json` —
  regenerated views.

## Redundancy / Removal Targets

- Retire any Opus-specific Promptfoo workaround once the built-in provider
  supports Opus 5's rejected sampling parameters, adaptive thinking, strict
  `output_config.format`, and replayable identity/usage contract.

## Notes

- Official evidence checked 2026-07-24: Opus 5 uses
  `claude-opus-5` at `$5/MTok` input and `$25/MTok` output, with a 1M context,
  128k synchronous output, adaptive thinking, and GA structured output.
- Repo fixtures are owned test assets. No user/private project payload is used.
- Historical script-bible scores remain context only because they predate the
  repaired two-corpus exact-runtime contract.

## Plan

1. Implement only the benchmark transport gaps proven by current docs/local
   payload inspection: Opus 5 pricing/limits/no-sampling and Anthropic
   `output_config.format` for Pydantic responses, with focused unit tests.
2. Add a runtime-shaped Promptfoo lane that invokes the exact module prompt and
   schema for both Opus 5 and the executable Gemini default.
3. Qualify live native identity/schema first, then one-case parity, then run the
   frozen two-corpus matrix under the US$5 cap.
4. Inspect and classify output against source before recording the attempt and
   registry history. Run an independent OpenAI judge only if same-provider bias
   could change the decision.
5. Compile/check methodology, run focused and full validation, and return a
   script-bible-only adoption decision. Do not change the runtime default.

## Work Log

20260724-1138 — discovery-and-decision-contract: interpreted the request as one
bounded full-script or ordered-frame/QA surface, created a clean worktree at
`aacf185`, and initially considered repaired QA. A read-only leverage audit
showed `script-bible` is the stronger clean decision gap: Story 208 repaired its
two-corpus truth but no exact-runtime-shaped row exists. Official Anthropic docs
and live discovery confirmed `claude-opus-5`, Messages API access, strict
structured output, adaptive thinking, `$5/$25` per MTok pricing, and account
catalog availability. Predeclared Opus 5 versus fresh Gemini 3.5 Flash-Lite on
the two frozen full scripts, no cache, concurrency 1, one retry, US$5 aggregate
cap, and no default change. Spend ledger remains `$0.00`. Next step: implement
and locally test the minimum exact-runtime transport/parity seam before the
first paid call.

20260724-1147 — native-and-parity-result: the native Opus 5 probe returned exact
requested/served identity, strict parsed schema, sane usage, `3.154s`, and
`$0.001835`. The first full-script parity attempt correctly remained a transport
diagnostic after Anthropic rejected unsupported Pydantic `minimum` constraints.
Applied Anthropic's documented SDK-style schema normalization, retained original
Pydantic post-validation, and reran. Before retaining final evidence, moved that
transport into the isolated benchmark provider and restored the shared
production transport byte-for-byte so Story 208's immutable hashes remained
valid. The final The Mariner call returned exact schema/identity at `64,961ms`
and `$0.148500`; deterministic `0.6999` failed, same-provider Opus rubric `0.88`
passed, combined `0.78995`. Source inspection found material scorer under-reading
plus two real errors: moving a back wound to the leg and declaring two dropped
thugs killed. Because the valid call exceeded the `30s` gate by `2.17x` and
`$0.01` gate by `14.85x`, the declared ladder stopped before Open Frequency and
the fresh Gemini comparator. Final-evidence spend including the judge is about
`$0.374195`; actual task spend including the superseded v2 diagnostic is about
`$0.740985`. Recorded Attempt 020, all diagnostics/final raw result, a
hash-complete dirty-contract manifest, and a non-decision-grade bounded registry
row. Next step: validate all recorded contracts and close with a
script-bible-only do-not-adopt decision.

20260724-1215 — validation-and-closeout: retained the final v3 isolated-provider
result and registered its prompt and transport explicitly in the repository
truth-audit ledger. Focused provider/transport tests passed `83/83`; the ledger
suite passed `20/20`; registry consistency, Ruff, JSON/YAML parsing,
`git diff --check`, and methodology compile/check passed. The full unit suite
passed `2,046/2,046`. Existing methodology warnings about two unrelated
architecture domains and UI-scout freshness remain unchanged. No production
transport, runtime default, commit, or push changed. Final decision: do not adopt
Opus 5 for script bible at current latency and price; the second corpus and
fresh comparator remain intentionally unmeasured under the declared stop.
