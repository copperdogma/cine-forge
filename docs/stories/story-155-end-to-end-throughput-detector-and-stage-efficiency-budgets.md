---
id: "155"
title: "End-to-End Throughput Detector and Stage Efficiency Budgets"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "vision-level preference: Easy, fun, and engaging"
  - "vision-level preference: Radical transparency"
spec_refs:
  - "spec:2"
  - "spec:2.5"
  - "spec:2.6"
  - "spec:2.7"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "032"
  - "150"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "driver_and_runtime"
  - "ingest_and_world_building"
roadmap_tags:
  - "throughput"
  - "latency"
  - "runtime"
  - "output-budget"
legacy_system: ""
---

# Story 155 — End-to-End Throughput Detector and Stage Efficiency Budgets

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Easy, fun, and engaging, vision-level preference: Radical transparency
**Spec Refs**: spec:2, spec:2.5, spec:2.6, spec:2.7, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane / film-lane boundary). No dedicated throughput ADR was found after search.
**Depends On**: Story 032 (cost tracking substrate), Story 150 (custom runtime detector pattern)

## Goal

Establish an honest throughput requirement for CineForge's currently shipped screenplay-understanding path. The repo already tracks stage durations, token counts, and run cost, but it still lacks a checked-in detector for the question we actually care about: how long does a real screenplay take to become usable, which stages dominate that runtime, and where are we over-spending on output volume or model choice without quality justification? This story creates the detector, the first stage-efficiency budgets, and the measurement discipline so future requests like "optimize total pipeline time" route into a concrete benchmark-and-follow-up workflow instead of vague anecdotal tuning.

## Acceptance Criteria

- [ ] A custom runtime detector exists for the current honest screenplay-understanding boundary, using representative checked-in fixtures and including at least one long-screenplay case.
- [ ] The detector records total wall-clock runtime plus per-stage duration, input tokens, output tokens, estimated cost, and output-volume evidence so verbosity waste is visible instead of speculative.
- [ ] The measured boundary is honest about scope: it distinguishes the currently shipped story-lane path from unfinished film-lane work instead of pretending CineForge's entire ideal pipeline is already benchmarkable end to end.
- [ ] Stage-efficiency budgets or target ranges are recorded for the measured boundary, and they are labeled clearly as current budget versus climb goal rather than stop-ship requirements.
- [ ] `docs/evals/registry.yaml`, Story 155, and `docs/methodology/state.yaml` all agree on ownership so future optimization work can split into measured follow-up stories instead of one undifferentiated "performance" bucket.

## Out of Scope

- Benchmarking every HTTP endpoint or non-AI CRUD path
- Pretending unfinished film-lane generation/export work is already a stable end-to-end throughput boundary
- Speculative caching, prompt-shortening, or model swaps before the detector proves a bottleneck
- Large UI/dashboard work beyond the minimum needed to inspect the detector output

## Approach Evaluation

- **Simplification baseline**: Existing run artifacts and `cost_tracking.py` already expose stage durations, token counts, and run costs. Reuse that substrate first instead of inventing a parallel telemetry system. The missing piece is a checked-in detector and budget discipline at the full-script boundary.
- **AI-only**: Rejected. This is a measurement/orchestration problem with deterministic source data available. An LLM can summarize results later, but it should not be the source of truth for runtime evidence.
- **Hybrid**: Possible only as a thin layer: deterministic runtime capture plus optional AI-assisted bottleneck summaries. Any recommendation layer must stay downstream of the measured facts.
- **Pure code**: Best fit. A benchmark harness can drive the honest recipe boundary, read `run_state.json` and cost summaries, and emit reproducible reports without changing product behavior.
- **Repo constraints / ADRs**: No dedicated throughput ADR exists yet. ADR-003 matters because the first honest detector boundary should be the story lane that actually ships on import, not a pretend "whole pipeline" finish line that includes unfinished film-lane behavior.
- **Existing patterns to reuse**: Reuse Story 150's runtime-detector pattern, `benchmarks/scripts/runtime_media_validation_eval.py`, existing `run_state.json` timing data, and `src/cine_forge/services/cost_tracking.py` rather than inventing new measurement plumbing by default.
- **Eval**: This story should create a registry-backed custom runtime detector for screenplay throughput. The discriminator is whether the harness can produce repeatable total/runtime/cost/token/output-volume reports and isolate the stages that dominate them.

## Tasks

- [ ] Define the first honest throughput boundary for current CineForge product reality, likely `screenplay -> story-lane ready` / `workspace-ready`, and choose representative fixtures including one long screenplay.
- [ ] Build the runtime harness and checked-in manifest, reusing existing run-state and cost-tracking substrate wherever possible.
- [ ] Capture per-stage duration, token usage, cost, and output-volume evidence. If output-volume evidence is not currently available, land the smallest substrate change needed to expose it.
- [ ] Register the detector in `docs/evals/registry.yaml` with a clear target, command, result artifact path, and runtime-blocking classification rules.
- [ ] Run the baseline, inspect the report, and split the measured hotspots into concrete follow-up stories instead of absorbing multiple optimization bets into one diff.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: This should live as a new benchmark/runtime harness under `benchmarks/scripts/`, not as more product logic inside the API or driver. Product runtime data should continue to come from the existing run artifacts and cost summaries.
- **Data contracts**: Prefer benchmark-local Pydantic models for manifest, run summary, and decision output. Product schemas should change only if the current run summaries cannot expose the minimum output-volume evidence needed for this detector.
- **File sizes**: `src/cine_forge/services/cost_tracking.py` is already `789` lines, `docs/evals/registry.yaml` is `2149`, and `benchmarks/scripts/real_ai_previz_runtime_eval.py` is `484`. If implementation touches `cost_tracking.py`, keep the edit narrow or extract helpers instead of accreting more logic into an already large file.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, Story 040, Story 149, Story 150, and searched decision docs for a direct throughput ADR. No dedicated throughput ADR exists yet; ADR-003 is the relevant boundary constraint.

## Files to Modify

- `benchmarks/scripts/full_script_throughput_eval.py` — new detector runner for honest screenplay-throughput measurement (`new`)
- `benchmarks/scripts/full_script_throughput_support.py` — optional extracted helpers if the harness needs manifest/report models (`new`)
- `benchmarks/fixtures/full_script_throughput_cases.json` — checked-in fixture manifest for representative screenplay cases (`new`)
- `docs/evals/registry.yaml` — register detector target, result paths, and latest measurements (`2149`)
- `src/cine_forge/services/cost_tracking.py` — only if existing run summaries lack output-volume evidence (`789`)
- `docs/stories/story-155-end-to-end-throughput-detector-and-stage-efficiency-budgets.md` — keep the plan, work log, and closure truth aligned (`this file`)

## Redundancy / Removal Targets

- Ad hoc "the pipeline feels slow" tuning without a reproducible detector
- One-off shell timing scripts that are not registered or fixture-backed
- Prompt/output verbosity expansions that survive only because nobody measured their cost against quality

## Notes

- This is deliberately not the repo's top active focus. It is a standing secondary requirement that should stay visible while the broader pipeline is still being built.
- The first measured boundary should start where CineForge already ships honest value today: screenplay intake and story-lane understanding. Film-lane and final generation throughput can layer on later as those boundaries stabilize.
- The detector should treat verbosity as a first-class performance input. If a stage produces materially more output than downstream consumers need, that is a quality/cost/runtime problem, not just a prompt-style preference.

## Plan

Written during setup so future agents can route the work correctly.

1. When this becomes active, run `/build-story 155` and lock the first honest throughput boundary plus fixture pack before writing code.
2. Build the detector first, using existing runtime/cost substrate before adding new telemetry.
3. Use the first baseline to create measured follow-up stories for the dominant hotspots instead of hiding multiple optimization bets inside Story 155.

## Work Log

- 20260410-1036 — setup: Created the throughput/efficiency requirement as Story 155 and anchored it to `spec:2` + `spec:8` instead of a generic performance bucket. Evidence: `spec:2` already owns "quickly enough to start creative work," `spec:8` already owns cost/speed/model tradeoffs, Story 150 already proves the custom runtime-detector pattern, and the repo already tracks stage durations plus token counts in `cost_tracking.py`. Next step: when this line is promoted, run `/build-story 155` to lock the first honest screenplay-throughput boundary and fixture set.
