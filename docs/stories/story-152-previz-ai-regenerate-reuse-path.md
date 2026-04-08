---
id: "152"
title: "Previz AI Regenerate Reuse Path"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
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
  - "151"
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

# Story 152 — Previz AI Regenerate Reuse Path

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 149, Story 150, Story 151

## Goal

Reduce AI-previz iteration latency by reusing existing healthy planning instead of silently rerunning the full scene-planning substrate every time the operator asks for another AI-previz clip. Story 151 proved that `shot_planning` can be cut down to ~20-25 seconds, but the current regenerate path still pays that cost because the UI launches `ai_previz_generation` with `force=true`, which disables stage-cache reuse. This story makes the product path honest: when CineForge already has a healthy shot plan for the target scope, AI-previz generation should jump straight to the `ai_previz` stage and rerun only the provider-backed clip plus media validation.

## Acceptance Criteria

- [x] Scene-action preflight can recommend `start_from: ai_previz` for AI-previz runs when the target scope already has healthy `shot_plan` artifacts and the required shared substrate is present; stale or missing planning keeps the current full-path behavior.
- [x] The Scene Workspace AI-previz action uses the backend-recommended `start_from` value so healthy existing planning is reused for both initial clip generation-from-shot-plan and clip regeneration, while unsafe states still run the full recipe.
- [x] Preflight/UI copy makes the reuse behavior legible enough that operators can tell when CineForge is regenerating from the current plan instead of replanning the scene.
- [x] Targeted tests cover the new preflight recommendation logic, including at least one stale-planning case.
- [x] A mechanical runtime benchmark on an honest project state records the delta between full AI-previz regeneration and the `start_from=ai_previz` reuse path, and the result is written into the story and `docs/evals/registry.yaml`.

## Out of Scope

- Redesigning first-time AI-previz latency from raw screenplay input
- Further prompt/schema changes inside `shot_plan_v1`
- Provider/model quality benchmarking across new Veo/Sora packs
- Relaxing health/staleness rules to force reuse when planning is stale or missing

## Approach Evaluation

- **Simplification baseline**: Do nothing and keep full regeneration. Real run-state evidence already falsifies this as the right operator loop: on the same honest benchmark project, full AI-previz regeneration reran `shot_planning` for `20.9637s` before the provider call even finished, while the sliced `start_from=ai_previz` run executes only `ai_previz` and `validate_media`.
- **AI-only**: Wrong fit. This is orchestration and runtime reuse, not a reasoning gap.
- **Hybrid**: Possible but unnecessary. Adding another planner/chooser stage would add pipeline and latency to save latency.
- **Pure code**: Best fit. Preflight already understands scene scope and substrate readiness, and the driver already supports `start_from`; the missing piece is connecting those two truths into the operator path.
- **Repo constraints / ADRs**: ADR-002 favors explicit warn/proceed behavior instead of hidden backend magic. ADR-003 keeps previz in Scene Workspace as an operator-readable planning surface. Reuse must respect immutable artifacts and stale-health truth; it cannot pretend a stale shot plan is safe.
- **Existing patterns to reuse**: Reuse `build_scene_action_preflight`, the existing `start_from` run contract, stage-cache / stage-slicing in `DriverEngine`, and the existing Scene Workspace action controls rather than inventing a second previz recipe.
- **Eval**: Mechanical runtime comparison on the same honest project state: full `ai_previz_generation` with `force=true` versus `start_from=ai_previz`. Browser verification on the real project route confirms the product path sends the reused start stage and still renders correctly.

## Tasks

- [x] Extend scene-action preflight so AI-previz can recommend `start_from=ai_previz` only when planning reuse is safe for the current scope.
- [x] Wire the Scene Workspace AI-previz action to honor the recommended start stage and disclose reuse clearly in the UI.
- [x] Add targeted backend tests for healthy-vs-stale planning reuse decisions.
- [x] Run the reuse benchmark on an honest project state, capture the measured delta, and update `docs/evals/registry.yaml`.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: classify all mismatches and update `docs/evals/registry.yaml`
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: The reuse decision belongs in `pipeline/scene_actions.py`, because that is already the shared preflight/scene-scope truth for UI and API actions. The UI should consume the recommendation, not re-derive it from artifact groups on its own.
- **Data contracts**: No new cross-layer schema is required if the existing `SceneActionPreflight.start_from` field becomes the effective recommended start stage. The run contract already supports `start_from`.
- **File sizes**: `make check-size` flags `src/cine_forge/pipeline/scene_actions.py` at `482` lines, `ui/src/components/PrevizPanel.tsx` at `629` lines, `ui/src/lib/types.ts` at `680` lines, and `src/cine_forge/api/models.py` at `510` lines. The plan should keep edits surgical and avoid widening ownership unnecessarily.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 149 blocker evidence, Story 150/151 runtime results, `DriverEngine` stage-slicing/reuse behavior, and the current PrevizPanel start-run payloads.

## Files to Modify

- `src/cine_forge/pipeline/scene_actions.py` — recommend safe AI-previz reuse start stages from preflight (`482` lines)
- `ui/src/components/PrevizPanel.tsx` — use preflight-recommended `start_from` and disclose reuse in the action flow (`629` lines)
- `ui/src/lib/types.ts` — keep the TS contract aligned if response typing needs adjustment (`680` lines)
- `tests/unit/test_scene_actions.py` — cover healthy and stale reuse cases (`99` lines)
- `docs/stories/story-152-previz-ai-regenerate-reuse-path.md` — track exploration, implementation, and measured runtime evidence
- `docs/evals/registry.yaml` — record the reuse benchmark result and whether the remaining gap is still runtime-blocking

## Redundancy / Removal Targets

- The implicit “regen means rerun the whole recipe” behavior in the Scene Workspace AI-previz button
- Any UI wording that implies AI-previz regeneration always replans the scene even when CineForge already has a healthy shot plan

## Notes

- Mechanical benchmark setup on copied honest project state:
  - source project: `output/eval-real-ai-previz-fast_4_mvp_ingest_only-fe36ed`
  - full regen copy: `output/tmp/previz-regen-baseline-full`
  - sliced regen copy: `output/tmp/previz-regen-baseline-start`
- Early run-state evidence already proves the structural waste:
  - full regen run `story152-regen-full-baseline` reached `shot_planning=20.9637s` before entering the provider-backed `ai_previz` stage
  - sliced run `story152-regen-start-baseline` executes stage order `['ai_previz', 'validate_media']`, skipping `shot_planning` entirely
- Completed wall-clock result on the same sampled honest project state:
  - full regen: `81545 ms`
  - reuse regen: `75337 ms`
  - net improvement: `6208 ms`
  - caveat: `validate_media` was noisier on the sliced run (`21693 ms` vs `6704 ms`), so the measured gain was much smaller than the removed `shot_planning` stage itself
- This story does not claim to solve first-time AI-previz latency from a fresh project. It is specifically about not wasting substrate time once planning already exists.

## Plan

1. Add a focused preflight helper in `pipeline/scene_actions.py` that marks AI-previz as reusable from `ai_previz` when:
   - project `track_manifest` exists and is healthy
   - all target scenes already have healthy latest `shot_plan` artifacts
   - otherwise leave `start_from` empty and preserve the current full recipe path
   Impact: this stays inside the shared preflight boundary and avoids UI-only business logic.

2. Update `PrevizPanel.tsx` to use `aiPreflight?.start_from` when starting AI previz.
   Change: when preflight recommends `ai_previz`, send that `start_from` in the run payload and show a short note that CineForge is reusing the current shot plan. When no recommendation is present, keep the existing full-run behavior.
   Impact: product behavior changes only when the backend already proved reuse is safe.

3. Add targeted tests in `tests/unit/test_scene_actions.py`.
   Cases:
   - healthy shot plan + track manifest => AI-previz preflight recommends `start_from='ai_previz'`
   - stale shot plan => recommendation is withheld
   - missing shot plan => current auto-build path remains unchanged

4. Finish the reuse benchmark and write the result into `docs/evals/registry.yaml` plus this story work log.
   Done when: the measured delta between full regen and sliced regen is recorded with concrete run ids / durations and the remaining runtime state is classified honestly.

5. Run the required backend + UI + browser checks, then recompile methodology surfaces.
   Done when: static checks pass, browser verification passes on desktop/mobile against a reachable real project route, and Story 152 appears correctly in generated planning surfaces.

## Work Log

20260408-2018 — story-created: opened Story 152 as a distinct unblocker because the work moved from “shrink shot planning” to “avoid unnecessary replanning in the AI-previz loop.” Evidence: Story 149 is blocked on runtime, Story 150 measured the runtime envelope, and Story 151 already landed the compact planner. Next step: prove whether the current regenerate path is really rerunning `shot_planning`.

20260408-2024 — exploration: traced the current product/runtime path and found that `PrevizPanel` starts `ai_previz_generation` with `force=true` whenever an AI-previz artifact already exists, while `DriverEngine` only reuses stage cache when `force` is false. Mechanical benchmark setup on copied honest project state showed the full regen path paying `shot_planning=20.9637s` before entering provider video generation, while the sliced `start_from=ai_previz` path executes only `ai_previz` and `validate_media`. Evidence: `ui/src/components/PrevizPanel.tsx`, `src/cine_forge/driver/engine.py`, `output/runs/story152-regen-full-baseline/run_state.json`, and `output/runs/story152-regen-start-baseline/run_state.json`. Next step: implement a safe backend preflight recommendation for `start_from=ai_previz` and wire the UI to honor it.

20260408-2114 — runtime-benchmark: completed the paired regenerate benchmark on copied honest project state and recorded the result under `benchmarks/results/real-ai-previz-runtime-story-152-reuse-baseline-2026-04-08.{json,md}`. Result: `start_from=ai_previz` skipped `shot_planning` entirely and reduced wall time from `81545 ms` to `75337 ms`, but the net win was only `6208 ms` because `validate_media` was noisier on the sliced run (`21693 ms` vs `6704 ms`). Next step: finish the broader validation pass and browser-check that the real UI now sends the reuse start stage when planning is healthy.

20260408-2210 — validation: finished the honest UI verification against the live API-backed route `http://127.0.0.1:5174/story-149-real-ui-rerun/scenes/scene_001?tab=previz` using a disposable local Playwright install with system Chrome because the shared MCP browser profile was locked. Evidence: desktop and mobile screenshots at `/tmp/story152-previz-reuse-desktop.png` and `/tmp/story152-previz-reuse-mobile.png`, clean console output, visible reuse note, enabled `Regenerate AI Previz for Current Scene` button, and intercepted `/api/runs/start` payload containing `start_from: "ai_previz"` for `scene_001`. Next step: hand off Story 152 as implemented and validated, while keeping Story 149 blocked because first-time AI-previz latency is still dominated by provider generation and prerequisites.

20260408-2242 — close-out: marked Story 152 Done because the shipped slice is complete and verified. Evidence: backend and UI checks passed, honest browser validation confirmed the real Scene Workspace route sends `start_from: "ai_previz"`, and the runtime benchmark plus registry update show the iteration-loop improvement without overstating it. Remaining detector failure stays runtime-blocking for Story 149, not for this story, because Story 152's success surface was the regenerate reuse path rather than first-time raw-input latency. Next step: /check-in-diff
