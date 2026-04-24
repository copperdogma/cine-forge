---
id: "187"
title: "Long-Form Scene Analysis Runtime Regression"
status: "Pending"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
spec_refs:
  - "spec:2.7"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "155"
  - "161"
  - "183"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "driver_and_runtime"
roadmap_tags:
  - "throughput"
  - "scene-analysis"
  - "long-form"
  - "follow-up-from-183"
legacy_system: ""
---

# Story 187 — Long-Form Scene Analysis Runtime Regression

**Priority**: Medium
**Status**: Pending
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), R12 (radical transparency)
**Spec Refs**: spec:2.7, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane / film-lane boundary)
**Depends On**: Story 155 (throughput detector), Story 161 (prior scene-analysis reduction), Story 183 (fresh runtime truth)

## Goal

Investigate and reverse the fresh long-form `world_building.analyze_scenes` runtime regression exposed by Story 183 without weakening downstream world-building quality. Story 161 reduced the Big Fish scene-analysis stage to `810.038s` on 2026-04-12, but Story 183 measured the same representative long case at `1130.834s` on 2026-04-24. That is slower than both the Story 161 optimized run and the original Story 155 baseline (`888.476s`), so the next implementation work should focus on the concrete regressed stage instead of opening a vague Deep Breakdown optimization bucket.

## Acceptance Criteria

- [ ] A current diagnostic pass explains why `world_building.analyze_scenes` regressed from `810.038s` to `1130.834s` on the maintained Big Fish long-form fixture.
- [ ] The chosen fix materially reduces long-form `analyze_scenes` runtime from the Story 183 measurement without starving downstream entity discovery, bible generation, or continuity tracking.
- [ ] A targeted detector rerun records the before/after result in `docs/evals/registry.yaml`, including total runtime, `analyze_scenes` runtime, cost, token volume, output volume, `git_sha`, result path, and runtime-blocking classification.
- [ ] Focused unit coverage exists for any changed batching, prompt-shaping, retry, provider timeout, or output-compaction behavior.
- [ ] If the diagnostic proves the regression is provider-side noise rather than local code or prompt behavior, the story records that evidence and updates follow-up pressure instead of shipping a speculative code change.

## Out of Scope

- Generic Deep Breakdown optimization across every stage
- Continuity prompt/output-budget work unless diagnostics prove scene-analysis changes caused continuity degradation
- UI messaging about slow runs
- Replacing the maintained full-script throughput detector
- Changing model defaults without live model discovery and eval evidence

## Approach Evaluation

- **Simplification baseline**: The product still needs rich scene understanding under C4; a single cheap structural pass is not enough evidence to delete scene analysis. The simplification question for this story is narrower: can the current prompt/batching path do less repeated work while preserving downstream utility?
- **AI-only**: Plausible only as an experiment if a stronger model can analyze larger batches more quickly with less retry/output churn. Because this changes model choice, it requires live model discovery before adoption.
- **Hybrid**: Likely candidate. Deterministic batch planning, prompt compaction, and timeout/retry instrumentation can reduce waste while leaving narrative analysis to the model.
- **Pure code**: Useful for instrumentation, batch sizing, cached inputs, and harness reporting. It is not sufficient if the actual regression is provider/model behavior.
- **Repo constraints / ADRs**: ADR-003 keeps the story lane honest: this is `mvp_ingest` plus `world_building`, not film-lane generation. `spec:2.7` and C4 preserve richer scene analysis until the detector proves it can be simplified. `spec:8` requires cost and latency truth to be inspectable.
- **Existing patterns to reuse**: Reuse `scene_analysis_v1` batching/execution helpers, Story 161's batch-planning tests, and the `full-script-throughput` detector from Story 155/183.
- **Eval**: The discriminating eval is a targeted `big_fish_long` throughput rerun compared against Story 183's report. Local unit tests can prove changed batching behavior, but only the paid detector can prove the regression is reversed.

## Tasks

- [ ] Inspect Story 183 artifacts and current `scene_analysis_v1` logs/code to identify whether the regression came from batch count, prompt size, retry behavior, model routing, provider latency, or output verbosity.
- [ ] Run live model discovery before selecting any alternate model for scene analysis.
- [ ] Implement the smallest targeted fix: batching/prompt compaction, retry/timeout tuning, instrumentation, or model-routing adjustment backed by evidence.
- [ ] Add focused tests for any changed scene-analysis batching, execution, prompt-shaping, or output handling behavior.
- [ ] Rerun the targeted `big_fish_long` throughput detector and compare against Story 183's `1130.834s` scene-analysis measurement.
- [ ] Update `docs/evals/registry.yaml` with the new result row and classify any remaining mismatch as model-wrong, golden-wrong, or ambiguous; classify runtime impact as runtime-blocking or non-runtime-blocking.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI not expected; if touched unexpectedly: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check` (not expected)
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched unexpectedly: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

- **Owning class/module**: `src/cine_forge/modules/ingest/scene_analysis_v1/` owns scene-analysis batching and execution. Do not move this into driver orchestration unless diagnostics prove a driver-level timing/reporting issue.
- **Data contracts**: Reuse existing scene and scene-index artifact schemas. No new cross-layer API contract is expected unless diagnostics require surfacing richer detector metadata.
- **File sizes**: `scene_analysis_v1/main.py` is `160`, `execution.py` is `270`, `batching.py` is `95`, `outputs.py` is `260`, `tests/unit/test_scene_analysis_batch_planning.py` is `131`, `tests/unit/test_scene_analysis_execution.py` is `142`, `tests/unit/test_scene_analysis_module.py` is `238`, `docs/evals/registry.yaml` is `2872`, and `benchmarks/scripts/full_script_throughput_eval.py` is `244`.
- **Decision context**: Reviewed ADR-003, Story 155, Story 161, Story 183, and the current full-script throughput detector outputs.

## Files to Modify

- `src/cine_forge/modules/ingest/scene_analysis_v1/batching.py` — likely batch-planning or word-budget fix if diagnostics point there (`95`)
- `src/cine_forge/modules/ingest/scene_analysis_v1/execution.py` — likely prompt/execution/timeout instrumentation fix if diagnostics point there (`270`)
- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — only if module wiring or runtime params need a narrow update (`160`)
- `src/cine_forge/modules/ingest/scene_analysis_v1/outputs.py` — only if output compaction changes the persisted scene analysis shape (`260`)
- `tests/unit/test_scene_analysis_batch_planning.py` — focused batch-planning regression coverage (`131`)
- `tests/unit/test_scene_analysis_execution.py` — focused execution/prompt behavior coverage (`142`)
- `tests/unit/test_scene_analysis_module.py` — module-boundary regression coverage if wiring changes (`238`)
- `docs/evals/registry.yaml` — before/after detector evidence and classification (`2872`)
- `docs/stories/story-187-long-form-scene-analysis-runtime-regression.md` — work log and final evidence (`this file`)

## Redundancy / Removal Targets

- Any stale note that Story 161's `810.038s` result is still current long-form scene-analysis truth
- Any scene-analysis batching or prompt guard that diagnostics prove no longer reduces work
- Any duplicated runtime instrumentation that can be folded into the maintained throughput detector

## Notes

- Story 183 also showed continuity remained the top hotspot at `1968.725s` and `55.6%` of runtime, but continuity fallback quality slightly improved versus Story 161 (`48` latest `needs_review` states vs `52`). This story is deliberately scoped to the sharper regression: scene analysis got materially slower, from `810.038s` to `1130.834s`.
- The target is not "make Deep Breakdown fast" in one vague pass. The target is to explain and reverse the stage regression that Story 183 measured.

## Plan

To be written by `/build-story` before implementation.

## Work Log

20260424-0004 — story-created: split from Story 183 because the fresh `big_fish_long` detector rerun exposed a concrete `world_building.analyze_scenes` regression: Story 161 measured `810.038s`, while Story 183 measured `1130.834s` on the same maintained long-form fixture. Evidence: `benchmarks/results/full-script-throughput-story-183-big-fish-2026-04-24.{json,md}`, `output/eval-full-script-throughput-big_fish_long-1d6a59`, and Story 161's checked-in result. Next step: `/build-story 187` when throughput work resumes.
