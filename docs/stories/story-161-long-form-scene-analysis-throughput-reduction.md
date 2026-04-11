---
id: "161"
title: "Long-Form Scene Analysis Throughput Reduction"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:2.7"
  - "spec:2.7.2"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "040"
  - "155"
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
roadmap_tags:
  - "throughput"
  - "scene-analysis"
  - "long-form"
  - "follow-up-from-155"
legacy_system: ""
---

# Story 161 — Long-Form Scene Analysis Throughput Reduction

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:2.7, spec:2.7.2, spec:8.1, spec:8.3
**ADR Refs**: ADR-003. No dedicated scene-analysis throughput ADR was found after search.
**Depends On**: Story 040, Story 155

## Goal

Reduce the absolute long-form wait before world-building can proceed. Story 155's full-script detector shows `big_fish_long.world_building.analyze_scenes` alone takes `888.476s` and `$0.9336` before downstream bible or continuity work can even start. That runtime is already a product problem regardless of the later bible truncation failure: full-length screenplay understanding does not feel interactive or even patient-operator-friendly when the first world-building stage consumes nearly fifteen minutes by itself.

## Acceptance Criteria

- [ ] A rerun of the Story 155 long case reduces `world_building.analyze_scenes` materially from the current `888.476s` baseline without a semantic quality collapse.
- [ ] The chosen optimization explains whether the main driver was batch size, prompt volume, model routing, retry behavior, or unnecessary output verbosity.
- [ ] Scene-analysis outputs remain sufficient for downstream world-building modules; speedups that merely starve later stages do not count as success.
- [ ] Focused regression coverage exists for any new batching, chunking, or prompt-compaction behavior before another paid rerun.
- [ ] Story 155 and `docs/evals/registry.yaml` record the before/after detector evidence and classify any remaining long-form delay as runtime-blocking or non-runtime-blocking.

## Out of Scope

- Replacing scene analysis with a different product concept
- Generic world-building optimization that is not meaningfully driven by the long-form `analyze_scenes` baseline
- UI work outside of optional follow-on surfacing of the detector result
- Treating short-script success as evidence that long-form runtime is solved

## Approach Evaluation

- **Simplification baseline**: First test whether prompt/output compaction or batch-size tuning alone can shrink the long-form stage without any module decomposition.
- **AI-only**: Possible if the current macro-analysis prompt is simply too verbose or too conservative on batch size.
- **Hybrid**: Plausible if deterministic pre-processing can cut repeated context while leaving narrative judgment to the model.
- **Pure code**: Appropriate for orchestration changes such as better batching, caching, or state reuse; not for replacing scene reasoning with brittle heuristics.
- **Repo constraints / ADRs**: `spec:2.7` and C4 explicitly preserve a richer scene-analysis tier because the structural-only path is not enough. The fix must preserve that richer output.
- **Existing patterns to reuse**: Story 155 detector, Story 040 performance lessons, existing macro-analysis batching in `scene_analysis_v1`, and current scene-index/discovery-tier contracts.
- **Eval**: The discriminating eval is the long-form Story 155 detector rerun, compared against the same `Big Fish` baseline plus any focused local fixture tests.

## Tasks

- [ ] Reproduce the `big_fish_long` `analyze_scenes` runtime with direct instrumentation and identify the dominant cost driver before changing code.
- [ ] Test the smallest viable optimizations first: batch-size tuning, prompt/output compaction, or selective context reduction.
- [ ] Add focused regression coverage for any changed batching or prompt-shaping logic.
- [ ] Rerun the long Story 155 case, then the full detector pack if the long case improves meaningfully.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals are rerun: classify all significant mismatches and update `docs/evals/registry.yaml`
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

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` is the primary owner. Keep the detector and reporting logic inside Story 155's benchmark harness instead of embedding throughput reporting into product code.
- **Data contracts**: Preserve current enriched scene artifacts and scene-index semantics. If batching changes require extra metadata, keep it schema-first and compatible with downstream world-building consumers.
- **Decision context**: Story 155 baseline shows the long case spends `888.476s` in `analyze_scenes` before later long-form failures even begin. That makes scene analysis an independent long-form wait problem, not just a side effect of later bible truncation.

## Files to Modify

- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`
- focused scene-analysis tests under `tests/unit/` or `tests/integration/`
- `docs/evals/registry.yaml`
- `docs/stories/story-161-long-form-scene-analysis-throughput-reduction.md`

## Redundancy / Removal Targets

- Overly large macro-analysis context windows that do not change downstream usefulness
- Output verbosity that later stages do not need
- Detector notes that blame the whole world-building lane when the actual delay is concentrated in `analyze_scenes`

## Notes

- Story 155 baseline evidence:
  - `open_frequency_short.world_building.analyze_scenes` = `26.336s`
  - `last_birthday_card_medium.world_building.analyze_scenes` = `127.554s`
  - `big_fish_long.world_building.analyze_scenes` = `888.476s`
- The long-case runtime is already a blocker even before character/location bible truncation is considered.

## Work Log

- 20260410-2234 — story-created: split Story 155's absolute long-form scene-analysis wait into its own follow-up line so it does not disappear under the broader world-building runtime story. Evidence: `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}` shows `big_fish_long.world_building.analyze_scenes` at `888.476s` / `$0.9336` before downstream long-form failures even start. Next step: run `/build-story 161` when the repo is ready to focus on long-form scene-analysis scale.
