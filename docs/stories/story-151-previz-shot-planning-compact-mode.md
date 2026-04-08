---
id: "151"
title: "Previz Shot Planning Compact Mode"
status: "In Progress"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "R17 (real-world and partial-workflow inputs)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "149"
  - "150"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "previz"
  - "runtime"
  - "substrate"
legacy_system: ""
---

# Story 151 — Previz Shot Planning Compact Mode

**Priority**: High
**Status**: In Progress
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 149, Story 150

## Goal

Reduce scene-scoped AI-previz latency by shrinking the shot-planning critical path instead of arguing about Veo pack variants. Story 150's first runtime pilot proved the main cost was not just video generation: the shipped scene-ready case spent `109.3s` in `shot_planning`, and the Fast scene-ready branch was even worse at `189.3s`, with huge prompt/output payloads driven by long-form creative-direction context and long-form shot-plan prose. This story introduces a previz-specific compact planning mode so AI-previz can ask for the same core coverage decision with materially less prompt and response volume, while leaving the general shot-planning contract and the animatics path intact.

## Acceptance Criteria

- [x] `shot_plan_v1` supports a previz-specific compact prompt profile that shortens upstream direction context and asks for a shorter operator-readable shot plan without changing the schema contract.
- [x] The AI-previz recipe uses that compact shot-planning profile and a lower output cap, while the animatics recipe keeps the broader default planning profile.
- [x] Targeted tests cover both prompt compaction behavior and real param plumbing into `run_module`.
- [x] A real rerun of the Story 150 pilot subset shows a material reduction in `shot_planning` runtime and token volume on the same cases.
- [x] `docs/evals/registry.yaml` and the story artifacts record the new measured result and whether the remaining failure is still runtime-blocking.

## Out of Scope

- Rewriting shot planning into a new schema or module
- Removing creative direction from shot planning entirely
- Global prompt compression for animatics, storyboards, or other downstream planning paths
- Pretending the current AI-previz path is “fast enough” if the rerun still misses the `<= 6000 ms` detector

## Approach Evaluation

- **Simplification baseline**: Do nothing except pick a different Veo pack. Story 150's pilot already falsified that as the main lever; `fast_4_scene_ready` was worse than shipped because `shot_planning` dominated.
- **AI-only**: Ask a model to summarize or rewrite creative direction outside the module. Wrong boundary. The runtime problem is in the real pipeline and should be solved in the module/recipe that owns it.
- **Hybrid**: Possible, but overkill for the first pass. Adding a separate summarizer stage before shot planning would create more pipeline and more artifacts before proving the simpler fix insufficient.
- **Pure code**: Best first move. Keep the same module and schema, but add a previz-specific prompt profile that compacts long context, narrows expected shot count, and reduces output verbosity. Wire it only into the AI-previz recipe, then rerun the real runtime eval.
- **Repo constraints / ADRs**: ADR-002 and ADR-003 both push toward honest operator surfaces and scene-scoped planning rather than hidden backend magic. The change should stay inside the substrate, not masquerade as a product claim.
- **Existing patterns to reuse**: Reuse `shot_plan_v1`, the existing recipe params, Story 150's runtime harness, and the current shot-plan schema. No new artifact family is justified yet.
- **Eval**: Reuse the `real-ai-previz-runtime` custom eval and rerun the same pilot subset for apples-to-apples comparison against Story 150's baseline.

## Tasks

- [x] Add previz-fast prompt compaction and shorter shot-count guidance to `shot_plan_v1`.
- [x] Wire the compact profile into `recipe-ai-previz-generation.yaml` only.
- [x] Add targeted unit coverage for prompt compaction and param plumbing.
- [x] Rerun the real AI-previz runtime pilot subset and inspect the measured before/after.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [x] Focused unit tests: `.venv/bin/python -m pytest tests/unit/test_shot_planning_module.py -q`
  - [x] Focused lint: `.venv/bin/python -m ruff check src/cine_forge/modules/shot_planning/shot_plan_v1/main.py tests/unit/test_shot_planning_module.py`
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: classify all mismatches and update `docs/evals/registry.yaml`
- [x] Search all docs and update any related to what we touched
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

- **Owning class/module**: `shot_plan_v1` already owns scene-level coverage planning, so the compact previz profile belongs there rather than in the render adapter or API layer.
- **Data contracts**: No new schema was added. The contract remains the existing `ShotPlan` / `ShotDefinition` schema; only prompt shaping and recipe params changed.
- **File sizes**: `make check-size` already flags `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` at `1206` lines, so this change deliberately stayed small and local. If further perf work is needed, the next step should include extraction rather than continuing to widen this file.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 149 blocker evidence, Story 150 pilot results, and the real shot-planning run states that showed large prompt/output volume on scene-scoped previz runs.

## Files to Modify

- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — add compact previz prompt profile and compaction helpers (`1206` lines)
- `configs/recipes/recipe-ai-previz-generation.yaml` — enable the compact shot-planning profile and lower max tokens for previz (`79` lines)
- `tests/unit/test_shot_planning_module.py` — cover prompt compaction and param plumbing (`791` lines)
- `docs/stories/story-151-previz-shot-planning-compact-mode.md` — track the substrate work and measurements (`119` lines before this update)
- `docs/evals/registry.yaml` — record the rerun result and runtime-blocking status (`1787` lines before update)
- `docs/stories/story-149-previz-fast-lane-and-latency-budget.md` — keep the blocked product story aligned with the improved but still-blocked runtime evidence

## Redundancy / Removal Targets

- Any assumption that creative-direction artifacts must be fed into previz shot planning at full prose length
- Any claim that Veo pack choice is the dominant runtime lever before the planning substrate is trimmed

## Notes

- Cheap prompt inspection on the real project confirmed the compact profile cuts the shot-planning prompt from `12573` chars to `4614` chars (`-63.3%`) before any paid rerun.
- The new scene-ready pilot still misses the fast detector badly, but it produces a real substrate improvement:
  - shipped Lite scene-ready total dropped from `270922 ms` to `153528 ms`
  - Fast 4-second scene-ready total dropped from `353687 ms` to `182138 ms`
  - shipped Lite `shot_planning` alone dropped from `109.3s` to `25.4s`
- The ingest-only control is noisier because `project_config` showed a large outlier on the rerun, but the internal previz recipe path still improved: `shot_planning` fell from `44.3s` to `20.4s`, and the AI-previz recipe segment fell from `102791 ms` to `68159 ms`.

## Plan

1. Finish writing the rerun measurements into the eval registry and the blocked Story 149 surface.
2. Run broader backend validation (`make test-unit`, full Ruff) to make sure the compact profile did not introduce unrelated regressions.
3. Recompile methodology surfaces so Story 151 and the updated blocker evidence appear in the dashboards.
4. Decide whether to continue with further substrate reduction or stop here with an improved-but-still-blocked state.

## Work Log

20260408-1904 — story-created: opened Story 151 because the work moved beyond Story 150's eval-only scope into real substrate reduction. Evidence: `docs/stories/story-151-previz-shot-planning-compact-mode.md`. Next step: patch the shared shot-planning module with a previz-specific compact profile.

20260408-1917 — implementation: added a `previz_fast` prompt profile to `shot_plan_v1`, compacted long upstream direction/context fields, tightened shot-count guidance, and wired the AI-previz recipe to use that profile with a lower output cap. Evidence: `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `configs/recipes/recipe-ai-previz-generation.yaml`. Next step: add focused tests and sanity-check prompt length reduction before a paid rerun.

20260408-1929 — focused-validation: added unit coverage for compact prompt behavior and param plumbing, then ran focused validation cleanly. Evidence: `.venv/bin/python -m pytest tests/unit/test_shot_planning_module.py -q` (pass), `.venv/bin/python -m ruff check src/cine_forge/modules/shot_planning/shot_plan_v1/main.py tests/unit/test_shot_planning_module.py` (pass). Next step: rerun the Story 150 pilot subset on the real pipeline.

20260408-1954 — runtime-rerun: reran the three-case real AI-previz pilot with the compact profile. Evidence: `benchmarks/results/real-ai-previz-runtime-story-151-compact-pilot-2026-04-08.json`, `benchmarks/results/real-ai-previz-runtime-story-151-compact-pilot-2026-04-08.md`. Result: shipped Lite scene-ready improved from `270922 ms` to `153528 ms`, Fast 4 scene-ready improved from `353687 ms` to `182138 ms`, and shipped Lite `shot_planning` fell from `109.3s` to `25.4s`. The detector is still red, so the remaining failure stays runtime-blocking. Next step: write the result into `docs/evals/registry.yaml`, update Story 149's blocker evidence, and run broader validation.

20260408-2011 — broader-validation: reran the minimum backend safety pass after updating the registry and story artifacts. Evidence: `make test-unit PYTHON=.venv/bin/python` (668 passed, 152 deselected) and `.venv/bin/python -m ruff check src/ tests/` (pass). Next step: recompile methodology surfaces and decide whether to continue with more substrate reduction or stop at this improved-but-still-blocked state.

20260408-2015 — methodology-sync: recompiled and rechecked the generated planning surfaces after Story 151 and registry updates. Evidence: `pnpm methodology:compile && pnpm methodology:check` (pass). Next step: summarize the measured improvement and decide whether the next story should attack prerequisite latency or provider video latency.
