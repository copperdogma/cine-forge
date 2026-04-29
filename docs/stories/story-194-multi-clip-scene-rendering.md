---
id: "194"
title: "Multi-Clip Scene Rendering"
status: "Draft"
priority: "High"
ideal_refs:
  - "R8 (professional-grade production artifacts)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:6.1"
  - "spec:6.3"
  - "spec:6.4"
  - "spec:7.1"
  - "spec:7.1.2"
  - "spec:7.2"
  - "spec:10.1"
  - "spec:10.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "193"
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
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "render-planning"
  - "multi-clip-render"
  - "timeline-assembly"
  - "brick-steel"
legacy_system: ""
---

# Story 194 - Multi-Clip Scene Rendering

**Priority**: High
**Status**: Draft
**Ideal Refs**: R8 (professional-grade production artifacts), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:6.1, spec:6.3, spec:6.4, spec:7.1, spec:7.1.2, spec:7.2, spec:10.1, spec:10.2, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 193

## Goal

Change final-render execution from "one scene becomes one provider video" to "one scene may become one or more provider-constrained render clips, each with its own prompt, generated video artifact, provenance, and timeline offset, then assembled into the best available scene playback." This story consumes the `render_clip_plan` from Story 193 and makes long dialogue or action scenes renderable without forcing impossible 8-second compression.

## Eval Ladder Context

- **Root Ideal need**: R8 requires generated media with intentional editing and coherent visual language. R10 requires a playable assembly. R12 requires prompt/provenance transparency for each AI decision and generated artifact.
- **Parent story**: Story 193 creates the `render_clip_plan` artifact and proves Brick & Steel-style scene duration/clip splitting without changing generation execution.
- **Measured failure mode**: current `render_adapter_v1` emits one `render_prompt` and one `generated_video` per scene. That cannot represent a 30-second scene when the selected engine pack can only generate 8-second clips.
- **Child story boundary**: this story generates and registers multiple render clips for a scene and assembles them into playback/export paths. It does not redesign shot planning or change the provider floor.
- **Parent eval rerun**: after implementation, rerun or extend the final-render provider-floor/quality harness only if the story changes the maintained final-render route or default engine pack. Otherwise use a focused Brick & Steel multi-clip fixture and media-validation evidence.

## Acceptance Criteria

- [ ] `render_adapter_v1` can consume a `render_clip_plan` and generate one prompt/video pair per render clip for scenes whose plan contains multiple clips.
- [ ] `CompiledRenderPrompt` and `GeneratedVideoArtifact` contracts can represent render-clip units without losing scene-level lineage, source shot ids, clip ids, timeline offsets, resolved inputs, provider params, or prompt-source provenance.
- [ ] Track manifest entries for generated video preserve clip ordering and start/end offsets so final output can assemble the scene from multiple clip artifacts.
- [ ] `final_output_v1` or a focused assembly helper uses ordered generated-video clip entries when present and still falls back to existing scene-level generated video, AI previz, storyboard, or script tracks when multi-clip output is absent.
- [ ] A Brick & Steel-style fixture renders at least four provider-bounded clip requests from one scene plan and produces an inspectable assembled scene path or track sequence.
- [ ] Per-clip prompts include only the relevant dialogue/action/continuity slice plus resolved character/location/reference state for that clip; they do not repeat the full scene dialogue in every prompt.
- [ ] The UI or artifact surfaces expose enough truth for an operator to tell that one scene was generated as multiple clips, inspect each prompt/video, and understand any fallback or missing clip.
- [ ] Focused tests cover multi-clip prompt generation, partial failure behavior, track ordering, final assembly fallback, and schema round-tripping.

## Out of Scope

- Creating the `render_clip_plan` artifact itself; Story 193 owns that.
- Replacing shot planning or making every shot a render clip.
- Advanced visual stitching, optical flow, transition smoothing, or NLE-grade clip trimming.
- Changing default video providers or provider-floor decisions unless multi-clip execution proves the current default unusable.
- Solving all continuity-state override compilation. This story should leave a narrow seam for resolved per-clip state, but a broader continuity-override compiler can be a later story if needed.
- Full timeline editor UI. The UI work here should be minimal product truth for generated clips and playback.

## Approach Evaluation

- **Simplification baseline**: A single LLM call cannot generate multiple provider videos or assemble track entries. It can compile per-clip prompts from a render plan, but execution, lineage, partial failure handling, and final assembly are code-owned.
- **AI-only**: Useful only for per-clip prompt compilation. Not sufficient for artifact contracts, track offsets, retries, or assembly.
- **Hybrid**: Likely strongest. Use deterministic execution for clip iteration, provider calls, artifacts, tracks, and final assembly; use the existing render prompt compiler for each clip's provider-ready prompt.
- **Pure code**: Strong for orchestration and assembly. Insufficient for high-quality provider prompt text unless it reuses the existing compiler path.
- **Repo constraints / ADRs**: ADR-003 says prompts are read-only compiled artifacts, so each clip prompt should be a projection of upstream plan/state. ADR-002 says expensive operations need honest preflight and visible fallback, so partial clip failures must be explicit rather than hidden. `spec:10` requires best-available playback, not a pile of disconnected clips.
- **Existing patterns to reuse**: `render_adapter_v1` engine pack/request shaping, Story 191 dialogue contract, `GeneratedVideoArtifact` and `CompiledRenderPrompt` lineage, `TrackEntry` start/end time fields, `final_output_v1` clip assembly/probing, media validation, `GeneratedVideoViewer`, `RenderPromptViewer`, and Story 148 scene-scoped runtime filtering.
- **Eval**: First test structurally with a fake video provider and Brick & Steel-style plan. Then run media validation on a generated multi-clip fixture. Only rerun live provider-floor evals if implementation changes provider selection or if fake-provider tests cannot prove assembly behavior.

## Tasks

- [ ] Re-read the landed Story 193 schema and update this story's plan if the final `render_clip_plan` contract differs from the draft assumptions here.
- [ ] Extend render prompt/video schemas so render units can be scene-level or render-clip-level while preserving scene ids, clip ids, source shot ids, timeline offsets, resolved inputs, and provenance.
- [ ] Refactor `render_adapter_v1` so scene rendering loops over render clips when a multi-clip plan is present, while preserving the existing one-scene path for single-clip plans.
- [ ] Ensure each clip prompt receives only its clip-specific dialogue/action/continuity slice plus shared resolved references, avoiding full-scene prompt duplication.
- [ ] Decide and implement artifact entity-id strategy for clip artifacts, for example `scene_001__clip_001`, without preserving old unused IDs for backwards compatibility.
- [ ] Update generated-video track registration so multiple clip entries for one scene have stable start/end offsets and deterministic ordering.
- [ ] Update `final_output_v1` or a focused assembly helper to assemble multi-clip scene entries in timeline order and fall back cleanly when a scene has only one generated video.
- [ ] Add partial-failure behavior: preserve successful clip artifacts, mark missing/failed clips visibly, and fail the run only when the resulting scene cannot be represented honestly.
- [ ] Add minimal UI/artifact truth if current surfaces hide clip multiplicity: per-clip prompt links, per-clip video links, and an assembled scene/playback indication.
- [ ] Add focused tests for schema compatibility, multi-clip render execution with fake provider bytes, track ordering, final-output assembly, partial failure, and the one-scene fallback path.
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

- **Owning class/module**: `render_adapter_v1` remains the generation orchestrator, but new logic should be extracted into focused helpers rather than deepening the oversized `main.py`. `final_output_v1` owns playable assembly and may need a helper for ordered generated-video clip sequences.
- **Data contracts**: Story 193's `render_clip_plan` contract is the required input. This story likely changes `CompiledRenderPrompt`, `GeneratedVideoArtifact`, and possibly `TrackEntry` to include render clip identity and offsets schema-first.
- **File sizes**: likely large touch points are `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1985, LARGE), `src/cine_forge/modules/timeline/final_output_v1/main.py` (600, LARGE), `tests/unit/test_render_adapter_module.py` (1070, test file), and `tests/unit/test_shot_planning_module.py` (829, test file). Smaller likely owners include `src/cine_forge/schemas/render.py` (251), `src/cine_forge/schemas/track.py` (51), focused new render-adapter helper files, and new unit tests.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/design/decisions.md`, `docs/spec.md` sections 6/7/10, Story 148 scene-scoped downstream generation, Story 166 final-output playable assembly, Story 169 final-render provider floor, Story 191 prompt repair, and draft Story 193. No new ADR is needed unless this changes prompt editability, timeline ownership, or provider strategy.

## Files to Modify

- `src/cine_forge/schemas/render.py` - allow render-clip unit identity in prompt/video artifacts (251)
- `src/cine_forge/schemas/track.py` - add clip identity only if `shot_id` cannot honestly carry render-clip ids (51)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` - orchestration integration only; extract helpers first where possible (1985, LARGE)
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` - per-clip compiler context if needed (327)
- `src/cine_forge/modules/timeline/final_output_v1/main.py` - assemble ordered generated-video clip entries (600, LARGE)
- `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/components/GeneratedVideoViewer.tsx`, or `ui/src/components/RenderPromptViewer.tsx` - minimal product-truth UI if current surfaces hide multi-clip output
- `tests/unit/test_render_adapter_module.py` - multi-clip render execution and partial failure coverage (1070, test file)
- `tests/unit/test_final_output_module.py` or focused new tests - multi-clip assembly/fallback coverage
- `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` - update only if the normal user-facing render flow changes

## Redundancy / Removal Targets

- Any assumption that `render_prompt` and `generated_video` are one-per-scene.
- Any final-output path that selects only one generated-video entry per scene when clip offsets exist.
- Any UI copy that says a scene render is a single video when the track contains multiple clips.
- Prompt code that repeats full-scene dialogue in every clip prompt.

## Notes

- Keep the shot/render-clip boundary explicit. The plan may map one shot to many clips, many shots to one clip, or a fallback beat to one clip.
- This story is intentionally Draft until Story 193 lands, because the exact schema and provenance fields should drive the implementation.
- If the first build pass discovers that continuity/state override compilation is the larger blocker, create a follow-up rather than folding a full node-state compiler into this story.

## Plan

Do not start until Story 193's `render_clip_plan` contract exists. Build-story should first re-read the final contract, then implement the smallest headless multi-clip path with a fake provider: compile clip prompts, generate fake clip videos, register ordered track entries, and assemble playback. Only after that is structurally green should UI truth and optional live-provider smoke be added.

## Work Log

20260428-2338 - story-created: created as the larger consumer story after the user and agent agreed the current one-scene/one-video render model is the wrong abstraction for scenes that exceed provider duration limits. This story depends on Story 193's render-clip planning artifact and remains Draft until that contract lands.
