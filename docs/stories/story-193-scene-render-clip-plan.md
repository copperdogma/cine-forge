---
id: "193"
title: "Scene Render Clip Plan"
status: "Pending"
priority: "High"
ideal_refs:
  - "R8 (professional-grade production artifacts)"
  - "R10 (playable assembly at every stage)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:6.1"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:7.1.2"
  - "spec:7.1.3"
  - "spec:10.1"
  - "spec:10.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "191"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs:
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "driver_and_runtime"
roadmap_tags:
  - "scene-generation"
  - "render-planning"
  - "multi-clip-render"
  - "pacing"
  - "brick-steel"
legacy_system: ""
---

# Story 193 - Scene Render Clip Plan

**Priority**: High
**Status**: Pending
**Ideal Refs**: R8 (professional-grade production artifacts), R10 (playable assembly at every stage), R11 (production readiness per scene), R12 (transparency & control)
**Spec Refs**: spec:6.1, spec:6.3, spec:7.1, spec:7.1.2, spec:7.1.3, spec:10.1, spec:10.2, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 191

## Goal

Introduce a first-class `render_clip_plan` artifact that estimates the dramatic duration of each scene, compares that duration to the selected render engine's clip limits, and plans renderable clip boundaries before prompt compilation. The plan must run automatically on the final-render path, including fallback/on-demand generation when richer upstream planning is missing, and it must preserve provenance so operators can see which clip plan was AI-authored, code-defaulted, or derived from a full shot plan.

## Eval Ladder Context

- **Root Ideal need**: R8/R10/R11 require generated video to preserve pacing and intentional editing instead of compressing a whole scene into one arbitrary provider clip. R12 requires that generated/default planning be visible and overridable.
- **Parent evidence**: Story 191's Brick & Steel prompt repair exposed that exact dialogue and cadence guidance are not enough when the scene's dramatic length exceeds an engine's 8-second limit.
- **Measured failure mode**: `brick-steel-full-retired/scene_001` has seven dialogue turns, beer handoff, toast, long uncomfortable silence, and a release line. A single 8-second prompt forces rushing even when the text says not to.
- **Child story boundary**: this story creates and validates the planning artifact only. It does not generate multiple videos per scene; Story 194 consumes this artifact for multi-clip rendering.
- **Parent eval rerun**: no maintained promptfoo eval is required unless implementation changes the final-render provider-floor benchmark. Add a structural fixture/harness around Brick & Steel-style dialogue density and engine duration limits.

## Acceptance Criteria

- [ ] A typed `render_clip_plan` schema exists with scene id, target dramatic duration, duration rationale, confidence, source/provenance, selected engine pack, engine max clip duration, and an ordered list of render clips.
- [ ] Each render clip records clip id, source shot ids or fallback beat ids, timeline offsets, target duration, dialogue lines, action beats, continuity start/end notes, reference/keyframe intent, and whether it was derived from a full shot plan or generated from defaults.
- [ ] The normal final-render recipe runs render-clip planning before render prompt compilation and stores immutable `render_clip_plan` artifacts.
- [ ] If full shot planning is unavailable on a direct/headless final-render attempt, the render-clip planner can synthesize a low-confidence AI or code-default plan from scene script/timeline evidence, mark the plan as fallback/on-demand, and record missing upstream categories.
- [ ] A Brick & Steel-style fixture produces a target scene duration materially above 8 seconds and at least four clips for an 8-second-max engine, with rationale tied to dialogue turns, action beats, and the long silence.
- [ ] Existing one-scene/one-video render behavior is not replaced in this story; downstream consumers may read the plan, but multi-clip generation remains Story 194.
- [ ] Focused tests cover full-shot-plan input, missing-shot-plan fallback, engine duration limit splitting, and provenance/notes for AI-generated defaults.

## Out of Scope

- Generating more than one video artifact per scene.
- Stitching clips or changing `final_output_v1` assembly.
- UI redesign for multi-clip render review beyond existing artifact/run visibility, unless a tiny disclosure is needed to keep product truth honest.
- Changing provider defaults or rerunning the final-render provider-floor benchmark.
- Changing shot planning's editorial coverage semantics. This story distinguishes render clips from shots instead of redefining shots.
- Fixing GPT-image design-study completion/error behavior; Story 192 owns that residual.

## Approach Evaluation

- **Simplification baseline**: A single LLM call can estimate scene duration and propose clip boundaries from a scene script plus engine limits. That should be measured first on Brick & Steel and one short non-dialogue scene. The durable value is not the call itself; it is typed artifact persistence, fallback provenance, and route integration.
- **AI-only**: Strong for dramatic-duration judgment, silence/reaction-beat interpretation, and converting a script into renderable beats when a full shot plan is missing. Weak for engine-limit enforcement and provenance; those need deterministic validation.
- **Hybrid**: Likely best. Deterministic code computes dialogue lower bounds, engine max duration, minimum clip counts, and schema validation; an LLM estimates rhythm and beat grouping when shot planning is missing or ambiguous.
- **Pure code**: Acceptable as a fallback for missing upstream: dialogue word count, speaker turns, action element count, and default reaction/silence budgets can produce a conservative plan. It is not enough for nuanced rhythm, comedic timing, or intentionally slow scenes.
- **Repo constraints / ADRs**: ADR-002 says downstream generation can proceed with placeholders, but silent fallback is the worst pattern; every default must be labeled. ADR-003 says prompts are compiled artifacts, not source-of-truth edits, so scene duration and clip grouping belong upstream of prompt text. `spec:6.1` already gives shots duration estimates and dialogue lines; `spec:7.1` says render adapter translates artifacts, not creative intent; `spec:10` needs playable timing.
- **Existing patterns to reuse**: `shot_plan_v1` scene contexts and dialogue extraction, `timeline_build_v1` timeline entry durations, `render_adapter_v1` engine pack limits and request shaping, `SceneActionPreflight` provenance, `TrackManifest` start/end time fields, Story 191's dialogue-density prompt evidence, and Story 148's scene-scoped downstream action path.
- **Eval**: Add focused structural tests and a small report fixture. The first discriminating check is: given Brick & Steel dialogue plus an 8-second engine limit, does the planner refuse a single 8-second scene and propose a plausible multi-clip plan with source/provenance?

## Tasks

- [ ] Define `render_clip_plan` Pydantic schema(s) and export them through `src/cine_forge/schemas/__init__.py`.
- [ ] Create a focused `render_clip_plan_v1` module under generation/planning ownership rather than growing `render_adapter_v1/main.py`.
- [ ] Implement deterministic duration lower bounds from dialogue word count, speaker turns, action elements, explicit silence/beat language, shot-plan duration estimates, and engine-pack duration limits.
- [ ] Add the first AI planning path that can estimate dramatic duration and clip grouping from scene script plus optional shot plan; record model, confidence, rationale, missing upstream, and whether defaults were used.
- [ ] Add a code fallback for missing/failed AI planning that still produces a conservative low-confidence plan rather than blocking final render.
- [ ] Update `configs/recipes/recipe-render-generation.yaml` so render-clip planning runs after shot planning and before render.
- [ ] Update render prompt compilation only enough to include the selected `render_clip_plan` as source context and disclose when the current scene-level render path is knowingly compressing a multi-clip plan.
- [ ] Add tests for full shot-plan input, missing-shot-plan fallback, engine-limit splitting, Brick & Steel-style dialogue density, artifact lineage, and generated-default provenance.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: New focused module `src/cine_forge/modules/generation/render_clip_plan_v1/` should own scene duration estimation and provider-constrained clip grouping. `render_adapter_v1` should remain a consumer/integration point, not the owner of dramatic planning.
- **Data contracts**: Add a schema-first contract, likely `src/cine_forge/schemas/render_clip_plan.py`, with `RenderClipPlan`, `RenderClip`, and provenance/supporting-rationale models. Avoid stringly typed dicts between planner, render adapter, API, and UI.
- **File sizes**: likely touched large files are `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1985, LARGE) and `tests/unit/test_render_adapter_module.py` (1070, test file). Keep those edits narrow. Better-sized owners include new module files, `src/cine_forge/schemas/render.py` (251), `src/cine_forge/schemas/shot_plan.py` (85), `src/cine_forge/schemas/timeline.py` (36), `src/cine_forge/modules/timeline/timeline_build_v1/main.py` (368), and recipe YAML.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/design/decisions.md`, `docs/spec.md` sections 6/7/10, Story 148 scene-scoped downstream generation, Story 169 final-render provider floor, and Story 191's Brick & Steel prompt-compiler evidence. No new ADR is required unless the story changes prompt editability, timeline ownership, or provider strategy.

## Files to Modify

- `src/cine_forge/schemas/render_clip_plan.py` - new schema for scene render duration and clip plans (new)
- `src/cine_forge/schemas/__init__.py` - export new schema types
- `src/cine_forge/modules/generation/render_clip_plan_v1/module.yaml` - new module metadata
- `src/cine_forge/modules/generation/render_clip_plan_v1/main.py` - new planner implementation
- `src/cine_forge/modules/generation/render_clip_plan_v1/prompting.py` - focused AI planning prompt/schema if needed
- `configs/recipes/recipe-render-generation.yaml` - insert render-clip planning before render
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` - narrow consumer/disclosure integration only (1985, LARGE)
- `tests/unit/test_render_clip_plan_module.py` - new unit coverage
- `tests/unit/test_render_adapter_module.py` - focused integration regression only if render context changes (1070, test file)
- `docs/reports/story-193-scene-render-clip-plan/` - optional fixture/report output for Brick & Steel-style evidence

## Redundancy / Removal Targets

- Any render prompt heuristic that tries to infer scene length from final prompt text instead of consuming a typed upstream plan.
- Any one-off dialogue-density notes in `render_adapter_v1` that become redundant once `render_clip_plan` owns the duration estimate.
- Recipe or UI copy that implies final render is always one scene equals one provider clip.

## Notes

- A render clip is not the same thing as a shot. A shot is editorial coverage. A render clip is a provider-constrained generation unit. The artifact should preserve source shot ids when available, but should not force a one-to-one mapping.
- The fallback plan is allowed to be AI-generated or code-defaulted, but it must never be silent. Provenance and missing upstream categories are acceptance-critical.
- Story 194 is the consumer story that turns these plans into multiple generated videos and assembled scene playback.

## Plan

Build-story should start by measuring the one-call AI baseline on two fixtures: Brick & Steel's dialogue/silence scene and a simple short establishing scene. Then implement the schema and module with deterministic guardrails around that baseline. Keep the first slice artifact-focused: plan scenes, persist the plan, and disclose compression risk to the current scene-level render path. Do not widen into multi-video generation here.

## Work Log

20260428-2337 - story-created: created after Story 191 prompt repair exposed a larger render-planning gap. The user and agent agreed the system needs an upstream scene-duration and provider-constrained render-clip planner, but the implementation is too large to fold into the prompt-compiler story. This story owns the enabling `render_clip_plan` artifact and automatic fallback/provenance behavior; Story 194 owns multi-clip rendering/assembly.
