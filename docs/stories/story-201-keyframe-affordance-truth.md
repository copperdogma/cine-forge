---
id: "201"
title: "Keyframe Affordance Truth"
status: "Pending"
priority: "Medium"
ideal_refs:
  - "vision-level preference: easy, fun, and engaging"
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:6.4"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "027"
  - "149"
  - "194"
  - "196"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs:
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "keyframes"
  - "scene-generation"
  - "operator-truth"
  - "brick-steel"
legacy_system: ""
---

# Story 201 - Keyframe Affordance Truth

**Priority**: Medium
**Status**: Pending
**Ideal Refs**: easy/fun/engaging, R7, R8, R11, R12
**Spec Refs**: spec:6.4, spec:7.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 027, Story 149, Story 194, Story 196

## Goal

Make keyframe truth honest on the surfaced scene-generation path. The current Brick & Steel Render preflight warns `Keyframes missing` but does not give the operator a real way to generate, review, or intentionally skip keyframes from the current Scene Workspace. That is worse than a missing feature because the UI implies an actionable gap while the shipped AI-previz/render workflow can proceed prompt-first. This story either restores a coherent keyframe route or removes/demotes the warning so users are not sent in circles.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R11 require scene generation to expose useful production controls without making optional substrate feel like hidden required work.
- **Parent evidence**: Story 027 originally shipped animatic/keyframe review surfaces; Story 149 later removed deterministic previz/animatic substrate and re-homed keyframes away from shipped previz semantics; Story 194 fixed missing-warning action links for several scene preflight items; Story 196 found the current Render tab still warns `Keyframes missing` while only offering an `Open Render` action on the Render tab itself.
- **Measured failure mode**: Story 196 browser evidence on `brick-steel-full-retired/scenes/scene_001?tab=render` shows the current render path has 8 generated clips and clean browser output, but the preflight still presents keyframes as missing actionable context. `artifact-snapshot.json` confirms there is no current `keyframe` artifact for `scene_001`.
- **Child validation**: browser and API preflight evidence must prove the keyframe state is either genuinely actionable or honestly optional/non-actionable.

## Acceptance Criteria

- [ ] Render and AI-previz preflight no longer surface `Keyframes missing` as an actionable warning unless there is a real current-scene route to create/review keyframes.
- [ ] If keyframes remain user-facing, the Scene Workspace exposes a coherent generation/review route with artifact detail links and immutable version truth.
- [ ] If keyframes are only optional render-support substrate for now, the UI copy says that plainly and does not offer self-referential `Open Render` actions.
- [ ] Focused backend tests cover scene-action preflight classification for missing optional keyframes.
- [ ] Browser verification covers desktop and mobile Scene Workspace Render on a representative project with and without keyframe artifacts or with a documented no-keyframe fixture.
- [ ] The story does not resurrect deterministic previz/animatics as shipped product flow unless a separate measured decision proves that is the right direction.

## Out of Scope

- Rebuilding the removed deterministic previz/animatic lane from Story 149.
- Making keyframes required for render generation.
- Improving video quality, reference fidelity, or exact-dialogue prompt compilation.
- Building a broad keyframe editor beyond the minimum route needed for truthful operator affordance.

## Approach Evaluation

- **Simplification baseline**: If render can proceed prompt-first and current providers do not require keyframes, the simplest correct move may be to demote missing keyframes to optional context copy instead of creating a new UI route.
- **AI-only**: Not sufficient. An LLM can propose keyframe descriptions, but the defect is an operator-affordance and preflight truth problem.
- **Hybrid**: Useful if keyframes remain first-class: code owns route/preflight/artifact contracts, while AI may later generate candidate keyframe descriptions or images.
- **Pure code**: Likely enough for the first repair because current evidence is routing/copy/preflight state, not model capability.
- **Repo constraints / ADRs**: ADR-002 requires downstream actions to expose honest preflight and obvious next actions. ADR-003 says scene-level film elements belong in Scene Workspace when user-facing. Story 149 explicitly removed deterministic previz and warned against keeping orphaned keyframe substrate alive without a concrete non-previz owner.
- **Existing patterns to reuse**: `src/cine_forge/pipeline/scene_actions.py` preflight items, `SceneActionControls`, existing `keyframe_v1` support if still active, `KeyframeViewer`/Artifact Detail if still registered, and Story 194 missing-warning action coverage.
- **Eval**: No promptfoo eval is warranted. The discriminator is API preflight plus desktop/mobile browser evidence: does the user see either a real route or an honest optional-state explanation?

## Tasks

- [ ] Trace current keyframe support after Story 149: recipe availability, graph node status, schema registration, artifact-detail viewer, and scene-action preflight.
- [ ] Decide whether missing keyframes should be a no-action optional note, a route to an existing generation flow, or a route to a new focused keyframe action.
- [ ] Implement the smallest honest fix in `scene_actions.py` and the Scene Workspace UI, avoiding new branches in oversized files where possible.
- [ ] Add focused tests for missing-keyframe preflight and any UI helper text or action path changed.
- [ ] Verify Brick & Steel `scene_001?tab=render` and `scene_001?tab=previz` on desktop and mobile with clean console/page/HTTP output.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If story metadata or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] Search all docs and update any related to what we touched.
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Are existing keyframe artifacts preserved?
  - [ ] **T1 - AI-Coded:** Is the keyframe state/action obvious to future agents?
  - [ ] **T2 - Architect for 100x:** Did we avoid rebuilding dead deterministic previz substrate?
  - [ ] **T3 - Fewer Files:** Is the fix localized to the preflight/UI owner?
  - [ ] **T4 - Verbose Artifacts:** Does browser/API evidence prove the affordance truth?
  - [ ] **T5 - Ideal vs Today:** Does the scene-generation path feel less like hidden homework?

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

- **Owning class/module**: `src/cine_forge/pipeline/scene_actions.py` owns scene-action preflight truth; `SceneActionControls` renders missing-action items; `GeneratedVideoPanel` and `PrevizPanel` consume the preflight. If a keyframe generation route survives, use the existing keyframe module/viewer contracts rather than inventing a parallel artifact type.
- **Data contracts**: Existing scene-action preflight models and keyframe artifact schemas should be enough unless the build creates a new keyframe action.
- **File sizes**: watchpoints are `src/cine_forge/pipeline/scene_actions.py` (`929`), `ui/src/components/GeneratedVideoPanel.tsx` (`660`), `ui/src/components/PrevizPanel.tsx` (`952`), and `ui/src/pages/SceneWorkspacePage.tsx` (`1030`). Prefer helper/test changes over growing these files.
- **Decision context**: ADR-002, ADR-003, Story 027, Story 149, Story 194, and Story 196 browser evidence.

## Files to Modify

- `src/cine_forge/pipeline/scene_actions.py` - missing-keyframe preflight truth/action path
- `tests/unit/test_scene_actions.py` - focused preflight regression coverage
- `ui/src/components/SceneActionControls.tsx` or panel copy only if backend classification alone cannot make the UI honest
- `docs/stories/story-201-keyframe-affordance-truth.md` - work log

## Redundancy / Removal Targets

- Any lingering copy that treats removed animatic/keyframe substrate as a normal previz prerequisite.
- Self-referential warning actions such as `Open Render` from the Render tab when no separate keyframe action exists.

## Notes

- Story 196 classified this as a live but non-runtime-blocking product-truth defect. Render and AI previz still run; the issue is misleading operator guidance.

## Plan

1. Inspect current keyframe code/recipe/UI substrate after Story 149.
2. Choose the honest affordance: actionable route if real, optional note if not.
3. Patch preflight/UI copy narrowly and add focused regression tests.
4. Verify desktop/mobile Scene Workspace Render and Previz against Brick & Steel.

## Work Log

20260504-2120 - story-created: routed from Story 196 product-truth scrub. Evidence: browser pass on `brick-steel-full-retired/scenes/scene_001?tab=render` showed a clean rendered scene with 8 clips, but preflight still warned `Keyframes missing` and offered no real generation/review path; artifact snapshot confirmed no `keyframe` artifact for `scene_001`. Next step: `/build-story 201` when this affordance lane becomes active.
