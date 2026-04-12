---
id: "164"
title: "Real Scene Generation Product Truth"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.5"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "028"
  - "140"
  - "148"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "scene-generation"
  - "render"
  - "product-truth"
  - "feature-completeness"
legacy_system: ""
---

# Story 164 — Real Scene Generation Product Truth

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.5, spec:6.1, spec:7.1, spec:7.2, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 028, Story 140, Story 148

## Goal

Make the normal Scene Workspace render path a representative, operator-usable way to generate an actual scene. CineForge already has scene-scoped planning, render compilation, and media validation substrate, but the app is still not feature complete if a user cannot take a fresh project, open one scene, and reliably reach a real `generated_video` artifact through the surfaced render route with honest preflight, inspectable prompt/output artifacts, and clean desktop/mobile behavior.

## Acceptance Criteria

- [x] A fresh API-created project can reach a real scene-scoped `generated_video` artifact from the normal Scene Workspace `Render` tab without hand-seeded impossible state. The run may auto-build minimal prerequisites for the selected scene, but every inferred step is surfaced honestly.
- [x] The same representative route lands and exposes the full trust surface for the selected scene: `render_prompt`, `generated_video`, and any `media_validation` artifact or honest missing-validation state, all reachable from Scene Workspace and Artifact Detail.
- [x] The render preflight behaves honestly for missing upstream guidance: optional direction and keyframes warn, minimum substrate auto-builds when appropriate, and only truly meaningless requests soft-block.
- [x] Headless behavior matches the UI path: the selected scene scope survives through the run contract and run-state metadata so backend/API consumers can reason about what actually ran.
- [x] Browser verification covers the changed render flow in both desktop and mobile views on a representative real project route with clean console output.

## Out of Scope

- Provider-floor benchmarking or runtime-optimization work whose only purpose is speed rather than feature completeness
- Multi-scene batch rendering, project-level final-output assembly, or export polish beyond what this story needs to validate one honest scene-level render path
- Reopening AI-previz lane policy, deterministic-baseline removal, or throughput-detector work already closed by Stories 149–153 and 155–163
- Broad prompt-quality tuning unless the representative render walkthrough proves the current compiled prompt path is the blocker

## Approach Evaluation

- **Simplification baseline**: The current `render_generation` lane may already be close enough. The first task is to run the representative Scene Workspace render path on a fresh project and capture the exact blocker before inventing new substrate.
- **AI-only**: Wrong fit for the main gap. The models can already compile prompts and generate scene videos; the missing value is honest orchestration, preflight, trust surfacing, and end-to-end product behavior.
- **Hybrid**: Strong candidate. Keep AI for prompt compilation and video generation, while using deterministic preflight, scoped run orchestration, and media-validation trust surfaces to make the route usable.
- **Pure code**: Appropriate for the likely fixes if the blocker is in UI/API/run orchestration, artifact surfacing, or validation wiring rather than prompt semantics.
- **Repo constraints / ADRs**: ADR-002 requires proceed / warn / soft-block behavior instead of silent pipeline traps. ADR-003 keeps render compilation as a stateless prompt-compiler stage and preserves scene-first workspace behavior. Generated-video trust should reuse the existing `media_validation_v1` path rather than inventing a second review system.
- **Existing patterns to reuse**: Story 148's scene-scoped downstream generation path, Story 140's media-validation trust loop, Story 144's artifact-health overlay reuse, `GeneratedVideoPanel`, `SceneActionControls`, `scene_actions.py` preflight logic, and the existing render prompt / generated video viewers.
- **Eval**: The first distinguishing test is a representative API-created project walkthrough, not a new benchmark. If implementation changes the generated-video trust path materially, reuse `runtime-media-validation`; if it changes prompt/output behavior materially, note whether an existing eval is insufficient and needs follow-on work.

## Tasks

- [x] Walk the normal Scene Workspace render path on a fresh representative project and capture the exact blocker or trust gap before changing code. Record the run ids / artifacts / console state in the work log.
- [x] Fix the smallest end-to-end blocker that prevents representative scene generation, keeping backend/API and UI in the same story so the surfaced feature is actually usable.
- [x] Keep the render trust surface honest for the selected scene: `render_prompt`, `generated_video`, and `media_validation` (or an explicit reason it is absent) must line up between Scene Workspace, Artifact Detail, and run-state metadata.
- [x] Add focused regression coverage for the chosen seam without widening existing oversized files unnecessarily. Prefer narrow helper tests over dumping more branching into `render_adapter_v1/main.py` or `SceneWorkspacePage.tsx`.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] Confirm whether agent tooling or project instructions were touched; result: no, so `make skills-check` was not required
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] Confirm whether generated-video trust behavior changed materially enough to require an eval rerun; result: no change to `media_validation_v1` semantics, so no `/improve-eval` rerun or `docs/evals/registry.yaml` update was required for this story
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

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: The actual blocker lives inside `src/cine_forge/modules/generation/render_adapter_v1/main.py`, not in scene-scope orchestration. Scene scope, preflight, run-state propagation, and media-validation wiring already exist and work far enough to launch the representative render route.
- **Data contracts**: Reuse the existing typed scene-scope contract. If we need to distinguish warning-level prompt gaps from truly blocking gaps, do it schema-first in `src/cine_forge/schemas/render.py` rather than smuggling meaning through ad hoc strings or UI-only logic.
- **File sizes**: `src/cine_forge/modules/generation/render_adapter_v1/main.py` is `1554` lines, `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` is `306`, `src/cine_forge/schemas/render.py` is `247`, `src/cine_forge/driver/engine.py` is `1373`, `ui/src/components/GeneratedVideoPanel.tsx` is `361`, `tests/unit/test_render_adapter_module.py` is `501`, `tests/integration/test_render_adapter_integration.py` is `351`, and `tests/unit/test_run_state_writes.py` is `52`. The oversized production files in the final blast radius are `render_adapter_v1/main.py` and `driver/engine.py`, so the fix keeps policy changes in focused helper seams and limits the runtime expansion to an atomic write at the existing persistence boundary instead of widening orchestration logic further.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/spec.md` (`spec:5.5`, `spec:6.1`, `spec:7.1`, `spec:7.2`, `spec:10.3`), Story 028, Story 140, Story 148, Story 149, and the current methodology state/build map. No other ADR was found that narrows the render-route ownership more specifically.

## Files to Modify

- `docs/stories/story-164-real-scene-generation-product-truth.md` — keep the work log, blocker truth, and validation evidence current
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — align render-stage completeness blocking with the warning-level preflight contract without widening the already-oversized `_render_scene` path (`1554`)
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` — expose the known prompt-category list so completeness classification can distinguish advisory vs blocking gaps without duplicating category knowledge (`306`)
- `src/cine_forge/schemas/render.py` — schema-first split of prompt completeness into blocking vs advisory fields (`247`)
- `src/cine_forge/driver/engine.py` — make `run_state.json` writes atomic after representative render polling exposed a surfaced `/api/runs/{id}/state` partial-read race (`1373`)
- `ui/src/components/GeneratedVideoPanel.tsx` — keep the render surface honest after a failed run by reusing the existing failed-run banner pattern instead of silently falling back to the empty state (`361`)
- `tests/unit/test_render_adapter_module.py` — cover advisory-gap render success vs blocking-gap failure (`501`)
- `tests/integration/test_render_adapter_integration.py` — keep the representative minimal-context render regression green end to end (`351`)
- `tests/unit/test_run_state_writes.py` — lock in the atomic run-state write contract that the surfaced polling path now relies on (`52`)
- `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, `docs/ui-scout.md`, `docs/ui-scout/2026-04-12-open-frequency-render-story-164-local.md`, and `docs/methodology/state.yaml` `ui_scout` — move the honest FP1 boundary from “render tab reachable” to “one real scene render lands surfaced prompt/video/validation detail through the normal route”

## Redundancy / Removal Targets

- The contradiction where `scene_actions.py` says render can proceed with warnings but `render_adapter_v1` treats those same gaps as fatal
- The current empty-state-only `GeneratedVideoPanel` failure behavior if a failed-run card can reuse the existing shot-planning pattern
- Any stale UI-scout/runbook language that still treats “render tab reached” as the honest downstream boundary once a real scene render becomes the shipped path

## Notes

- This story exists because the user explicitly reprioritized away from long-form throughput and toward feature completeness: the next product question is not “how fast is Big Fish,” but “can a user actually generate a real scene through the normal app path?”
- Existing render substrate is real: Story 028 landed render compilation, Story 140 landed media-validation trust, and Story 148 made downstream generation scene-scoped and honest. The current gap is making that path representative and operator-usable end to end.
- Existing eval coverage is partial but relevant: `runtime-media-validation` already covers generated-video trust semantics; no separate render product-truth eval currently exists, so the representative walkthrough is the first gate and should stay explicit in the work log.
- Fresh exploration tightened the gap further: the current Scene Workspace `Render` route already launches scene-scoped runs, auto-builds minimum prerequisites, and lands failure details in chat/inbox. The live blocker is that `render_adapter_v1` still aborts on warning-level missing context, while `GeneratedVideoPanel` does not surface that failure inline.

## Plan

### Eval / Baseline Gate

- This is primarily product/orchestration honesty work over existing substrate, not a new promptfoo or model-selection story.
- Baseline evidence from a fresh surfaced run on 2026-04-12:
  - Created `open-frequency-render-test` through `/new` with `tests/fixtures/ingest_inputs/open_frequency_short.fountain`.
  - `run-a83e9ae3` (`mvp_ingest`) completed successfully and made the normal Scene Workspace route reachable.
  - On `/open-frequency-render-test/scenes/scene_001?tab=render`, the preflight summary said `Render can run for scene_001 with warnings.` Items were:
    - auto-build `Timeline`
    - auto-build `Track manifest`
    - auto-build `Shot planning`
    - warning `Continuity tracking missing`
    - warning `Rhythm & Flow missing`
    - warning `Look & Feel missing`
    - warning `Sound & Music missing`
    - warning `Keyframes missing`
  - Starting render from the surfaced button created `run-a9ecd372`. `timeline`, `tracks`, and `shot_planning` finished, then `render` failed with:
    - `render_adapter_v1 prompt for scene_001 is incomplete: character_bible_state, creative_brief, injected_assets, keyframes, location_bible_state, look_and_feel, rhythm_and_flow, sound_and_music`
  - After failure, the `Render` tab fell back to the same empty state and start button. The failure was visible only in chat/inbox/run detail, not inline on the render surface itself.
- Success measures for implementation:
  - A minimal post-ingest render regression passes headlessly and produces `render_prompt`, `generated_video`, and downstream `media_validation` for a selected scene without requiring optional direction/keyframe/reference substrate.
  - The surfaced Scene Workspace `Render` tab on a fresh representative project reaches those artifacts through the normal button path and links to detail views.
  - If a future render run genuinely fails, the `Render` tab shows the failure inline with a path to run details instead of silently resetting to the empty state.

### Approach Choice

- **Broad orchestration rewrite:** rejected. Story 148 already landed scene scope, preflight, and run-state propagation, and the live run proved those seams work far enough to auto-build timeline/tracks/shot planning from the render button.
- **Preflight hard-block on missing direction:** rejected. ADR-002 and Story 148 explicitly chose warn/proceed behavior for outputs that remain meaningful with placeholders. Blocking on `Look & Feel`, `Sound & Music`, `Rhythm & Flow`, or keyframes would move away from the depth-first scene path the user is asking for.
- **Auto-generate all missing upstream direction before render:** rejected for the first fix. It adds unnecessary blast radius, hides the real bug, and weakens transparency by changing what “Run Render for Current Scene” actually does.
- **Chosen approach:** keep the current warn/proceed preflight contract, change render completeness handling so warning-level upstream gaps are persisted as prompt completeness metadata instead of causing a fatal `ValueError`, and add inline failed-run truth to `GeneratedVideoPanel` using the existing shot-planning failure pattern.

### Repo-Fit / Optimality Evidence

- ADR-002 says expensive downstream actions should show a preflight summary with proceed / warn / soft-block semantics. The current preflight already does that; the render-stage hard failure is the inconsistency.
- ADR-003 keeps Scene Workspace scene-first and explicitly allows users to let AI fill missing elements. The surfaced `Render` path should therefore tolerate missing creative-direction slices and report the tradeoff honestly, not crash after promising it can proceed.
- `RenderPromptViewer` already understands `RenderCompletenessCheck.missing_categories`, so the repo already has a transparency surface for advisory gaps. Using that surface is more coherent than treating every reported gap as fatal.
- `ShotPlanningPanel` already has the right inline-failure UX pattern (`runHasFailed` + error card + run details link). Reusing that in `GeneratedVideoPanel` is better than inventing a new failure mechanism or relying on chat/inbox alone.
- Rejected alternatives:
  - Reopening `scene_actions.py`, `run_orchestrator.py`, or `ArtifactDetail.tsx` as first moves is wrong because the live blocker occurs after those seams succeed.
  - Requiring `Deep Breakdown` or full direction before render would directly contradict the product goal this story was created to serve.

### Structural Health Check

- `make check-size` confirms the only oversized production file in the likely blast radius is `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1528`).
- Planning guardrails:
  - Do not add more branching directly into `_render_scene`; put new completeness classification into a focused helper, ideally alongside the existing prompting/finalization seam.
  - `ui/src/components/GeneratedVideoPanel.tsx` (`316`) is small enough for the failure-state addition without extraction pressure.
  - If advisory vs blocking completeness becomes a cross-layer distinction, add it schema-first in `src/cine_forge/schemas/render.py` before backend/UI code consumes it.
  - No new event type is planned; existing run-state and failed-stage plumbing should remain sufficient.

### Implementation Order

1. Add a regression fixture/test that reproduces the current product-truth failure with minimal upstream context.
   Files: `tests/render_fixtures.py`, `tests/unit/test_render_adapter_module.py`, `tests/integration/test_render_adapter_integration.py`
   Done looks like: a post-ingest, current-scene render path without optional direction/keyframes/assets is represented in tests and currently captures the same seam we saw in `run-a9ecd372`.

2. Extract render completeness blocking into a focused helper instead of widening `_render_scene`.
   Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`, possibly `src/cine_forge/modules/generation/render_adapter_v1/prompting.py`
   Done looks like: the render stage can distinguish “advisory gap to persist in prompt completeness” from “real blocker that should still fail the run.”

3. Align render completeness policy with the preflight contract.
   Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/prompting.py`, optionally `src/cine_forge/schemas/render.py`
   Done looks like: warning-level missing context such as absent direction/keyframes/injected assets is recorded in the prompt artifact and allowed to proceed, while genuinely required coverage failures still stop the run.

4. Surface render failure inline on the Scene Workspace render route.
   Files: `ui/src/components/GeneratedVideoPanel.tsx`
   Done looks like: when a render run fails, the panel shows a destructive summary card with the current error and an `Open Run Details` link instead of only showing the old empty state.

5. Verify the representative path and trust surfaces.
   Files: runtime outputs plus any touched tests/docs
   Done looks like: the same fresh project route produces `render_prompt`, `generated_video`, and `media_validation`; Scene Workspace and Artifact Detail expose them; desktop and mobile browser checks confirm the path; and no secondary blocker appears in the selected-scene run metadata.

6. If the honest downstream boundary moves, update the UI-scout lane in the same change.
   Files: `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, `docs/ui-scout.md`, `docs/methodology/state.yaml`, and the dated `docs/ui-scout/` report
   Done looks like: the manual walkthrough and freshness lane no longer stop at “render tab reachable” once one real scene render is the honest shipped boundary.

### Impact / Risk Notes

- The main risk is accidentally letting truly incomplete prompts through. The mitigation is to keep blocking logic tied to missing coverage for actually provided required categories, not to delete completeness checks wholesale.
- Successful render runs will now advance farther into `validate_media`, so integration tests need to assert the downstream artifact set rather than only the absence of failure.
- The render panel currently reuses active-run state but not failed-run state. If the inline failure card is added, make sure it clears when a later render run succeeds so the panel does not pin stale errors.

### Scope Adjustment And Human Gate

- **Scope adjustment already folded into this story (`XS`)**: add inline render-failure truth to `GeneratedVideoPanel`. The current failure is otherwise hidden unless chat/inbox is open, which makes the surfaced render route dishonest even before the actual generated-video fix lands.
- **Scope reduction from the original draft**: do not start with `scene_actions.py`, `run_orchestrator.py`, `ArtifactDetail.tsx`, `ui/src/lib/types.ts`, or `media_validation_v1/main.py`. Exploration showed those are not the first blocker.
- **No new dependency or external API contract change is planned.** A schema tweak inside `RenderCompletenessCheck` is acceptable if it improves advisory vs blocking clarity, but it should stay internal and repo-wide.

## Work Log

20260412-1050 — story-created: shifted priority from throughput to scene-generation completeness after triage confirmed there is no open story owning the operator-facing render gap. Evidence: reviewed `docs/methodology/state.yaml`, `docs/spec.md` (`spec:6`, `spec:7`), `docs/build-map.md`, ADR-002, ADR-003, Stories 028/140/148/149/153, and the current Scene Workspace render surface. Next step: run `/build-story 164` against the normal Scene Workspace render path instead of inventing more benchmark-only follow-ups.
20260412-1122 — exploration: walked the surfaced scene-render route on fresh projects and found the live blocker is a policy contradiction, not missing scene-scope substrate. Evidence: current-worktree backend on `http://127.0.0.1:8000` (`/api/health` => `{"status":"ok","version":"2026.04.12-01"}`), shared local UI dev server on `http://127.0.0.1:4173`, fresh projects `open-frequency` and `open-frequency-render-test` created through `/new`, `run-4161e5a1` and `run-a83e9ae3` completed `mvp_ingest`, and the representative route `/open-frequency-render-test/scenes/scene_001?tab=render` showed `Render can run for scene_001 with warnings.` with auto-build `Timeline` / `Track manifest` / `Shot planning` plus warning-only continuity, direction, and keyframe gaps. Starting the surfaced render button created `run-a9ecd372`, which completed `timeline`, `tracks`, and `shot_planning` before `render` failed with `render_adapter_v1 prompt for scene_001 is incomplete: character_bible_state, creative_brief, injected_assets, keyframes, location_bible_state, look_and_feel, rhythm_and_flow, sound_and_music`; `validate_media` then failed as fallout. The Render tab itself fell back to the same empty state and start button, while chat and Inbox surfaced the failure. Files likely to change: `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/prompting.py`, `src/cine_forge/schemas/render.py` if completeness needs a blocking/advisory split, `ui/src/components/GeneratedVideoPanel.tsx`, and focused render fixtures/tests. ADRs / patterns consulted: ADR-002 warn/proceed/soft-block semantics, ADR-003 scene-first workspace and explicit AI-fill affordances, `RenderPromptViewer` completeness surfacing, and `ShotPlanningPanel`'s inline failed-run banner pattern. Next step: narrow the implementation plan to render completeness policy + inline render failure truth instead of rewriting scene-action orchestration.
20260412-1154 — implementation: split render completeness into blocking vs advisory gaps, kept warning-level prompt omissions honest instead of fatal, and surfaced failed render runs inline on the Scene Workspace render tab. Evidence: `src/cine_forge/schemas/render.py` now records `blocking_missing_categories` plus `advisory_missing_categories`; `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` exposes `known_prompt_categories()` so `src/cine_forge/modules/generation/render_adapter_v1/main.py` can fail only on truly blocking gaps while preserving warning-level omissions in prompt metadata; `ui/src/components/GeneratedVideoPanel.tsx` now reuses the existing failed-run pattern to show the render error plus `Open Run Details` instead of silently resetting to the empty state. Regression coverage landed in `tests/unit/test_render_adapter_module.py` and `tests/integration/test_render_adapter_integration.py` for advisory-gap success, blocking-gap failure, and the minimal post-ingest render route. Next step: rerun the representative fresh-project render path and verify the surfaced trust links in desktop and mobile views.
20260412-1206 — validation: the normal surfaced Scene Workspace route now produces a real scene render, and the runtime polling race uncovered during that proof is fixed in the same story. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`722 passed, 160 deselected, 1 warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_run_state_writes.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py -q` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/cine_forge/driver/engine.py src/cine_forge/modules/generation/render_adapter_v1/main.py src/cine_forge/modules/generation/render_adapter_v1/prompting.py src/cine_forge/schemas/render.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py tests/unit/test_run_state_writes.py` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed. Fresh project `open-frequency-render-story-164` created through `/new` with `tests/fixtures/ingest_inputs/open_frequency_short.fountain` reached a real scene render from `/open-frequency-render-story-164/scenes/scene_001?tab=render`: `run-43fbbd79` produced `artifacts/render_prompt/scene_001/v1.json`, `artifacts/generated_video/scene_001/v1.json`, and `artifacts/media_validation/scene_001/v1.json`; the prompt artifact recorded `missing_categories=[]`, `blocking_missing_categories=[]`, and `advisory_missing_categories=[]`; `Prompt Detail`, `Video Detail`, and `Validation Detail` all navigated to Artifact Detail pages; and media validation stayed honest with `recommended_health = needs_review` because the sampled frames did not prove the requested wide master. Active polling on that first successful run exposed a transient `/api/runs/run-43fbbd79/state` 500 caused by readers seeing `run_state.json` mid-write, so this story expanded coherently to make `DriverEngine._write_run_state()` atomic and add `tests/unit/test_run_state_writes.py`. After the fix, refresh render `run-7cacec1f` completed successfully with zero new browser console errors during active polling, the required surfaced routes (`/open-frequency-render-story-164`, `/intent`, `/scenes`, `/characters`, `/locations`, `/inbox`, and `scene_001?tab=render`) remained reachable, and browser evidence was captured on desktop and mobile (`story-164-home-desktop.png`, `story-164-scenes-desktop.png`, `render-desktop-story-164-clean.png`, `story-164-home-mobile.png`, `render-mobile-story-164-clean.png`). Next step: `/validate 164`.
20260412-1235 — validation-pass: reran the full validation suite and replayed the surfaced route on a fresh validation project, so closure no longer depends on the earlier build log. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed again (`722 passed, 160 deselected, 1 warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_run_state_writes.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py -q` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed in this validation pass (the UI build still emitted the existing Vite chunk-size warning, but it remained non-blocking). Fresh project `open-frequency-validate` was created through `/new` from `tests/fixtures/ingest_inputs/open_frequency_short.fountain`; `run-ac8e13d4` completed `mvp_ingest`; then surfaced render run `run-1cf7378f` completed `timeline`, `tracks`, `shot_planning`, `render`, and `validate_media` with no browser console errors during active polling. That rerun produced `output/open-frequency-validate/artifacts/render_prompt/scene_001/v1.json`, `.../generated_video/scene_001/v1.json`, and `.../media_validation/scene_001/v1.json`; the prompt artifact recorded `missing_categories=[]`, `blocking_missing_categories=[]`, and `advisory_missing_categories=[]`; the validation artifact recorded `recommended_health = valid`; and the surfaced `Prompt Detail`, `Video Detail`, and `Validation Detail` controls resolved to the corresponding Artifact Detail routes for `scene_001`. Fresh validation screenshots were captured at `validate-164-home-desktop.png`, `validate-164-render-desktop.png`, `validate-164-home-mobile.png`, and `validate-164-render-mobile.png`. Methodology still reports the pre-existing `ingest_and_world_building` architecture-audit warning, but validation found no new drift in the Story 164 slice. Recommended next step: `/mark-story-done 164`.
20260412-1246 — story-done: closed Story 164 after the fresh validation pass confirmed the surfaced route, artifacts, and trust surfaces all hold on representative state. Evidence: story metadata now reflects `Done`, acceptance criteria and workflow gates are fully checked, and close-out will recompile methodology surfaces so generated dashboards match the closure state before commit. Operator-visible outcome: the app now does the product-complete thing this story was meant to prove, and the planning surfaces stop treating the scene-render route as unfinished. Recommended next step: `/check-in-diff`.
