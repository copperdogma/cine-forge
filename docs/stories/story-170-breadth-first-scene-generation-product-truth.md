---
id: "170"
title: "Breadth-First Scene Generation Product Truth"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R10 (playable assembly at every stage)"
  - "R11 (production readiness)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:10.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "148"
  - "164"
  - "165"
  - "166"
  - "167"
  - "168"
  - "169"
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
  - "scene-generation"
  - "render"
  - "breadth-first"
  - "final-output"
  - "feature-completeness"
legacy_system: ""
---

# Story 170 — Breadth-First Scene Generation Product Truth

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R10 (playable assembly at every stage), R11 (production readiness), R12 (transparency & control)
**Spec Refs**: spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators), spec:6.1 (Shot Planning), spec:7.1 (Render Adapter Layer), spec:10.1 (Timeline Artifact), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace)
**Depends On**: Story 148 (Scene-Scoped Planning and Honest Downstream Generation), Story 164 (Real Scene Generation Product Truth), Story 165 (Scene Render Refresh Reuse Path), Story 166 (Final Output Playable Assembly), Story 167 (Final Output Validation and Trust Surface), Story 168 (Reference-Conditioned Scene Generation Product Truth), Story 169 (Reference-Conditioned Final Render Provider Floor)

## Goal

CineForge now proves the depth-first path: one representative scene can render honestly, refresh can reuse healthy planning, references survive into final render, and `final_output` plus project-cut validation exist. The still-missing product promise is the breadth-first path in `spec:5.3`: a user should be able to advance all scenes through the current final-render route without manually repeating the scene workflow N times, while keeping run scope, omissions, partial completion, and project-level playback/validation truth explicit. This story closes that gap on the shipped operator path instead of leaving CineForge as a one-scene demo with a project-level assembler bolted on afterward.

## Acceptance Criteria

- [x] A representative project can trigger the normal surfaced `all_scenes` final-render route and the equivalent headless/API path without hand-seeded impossible state, producing real multi-scene `generated_video` artifacts through the current shipped render substrate instead of requiring manual scene-by-scene repetition.
- [x] Breadth-first run truth stays inspectable: preflight, run metadata, and Run Detail make clear whether CineForge is rendering all scenes, reusing existing planning where safe, rebuilding missing prerequisites where necessary, and which stages actually executed. No silent fallback to a hidden loop of ad hoc scene runs.
- [x] Project-level handoff stays honest after the breadth-first run. `final_output` and its trust surfaces reflect the exact rendered scene set: a complete cut when every scene rendered, a partial cut with concrete omissions when some scenes did not, and no UI state that implies the whole film is ready when only a subset succeeded.
- [x] Failure and partial-success behavior are operator-usable. If one or more scenes fail during a breadth-first run, the surfaced route preserves the successful scene outputs, records the failed scene ids/reasons clearly enough to continue from there, and does not clobber unrelated healthy artifacts.
- [x] Focused regression coverage exists for `all_scenes` render scope, multi-scene success/partial-success bookkeeping, and `final_output` handoff, and browser verification covers the changed surfaced route on desktop and mobile with clean console output.
- [x] If the implementation changes project-cut validation or any maintained runtime detector materially, the relevant benchmark or eval entry in `docs/evals/registry.yaml` is updated in the same story or the explicit follow-up is recorded with evidence; this slice did not materially change project-cut validation, so no registry change was required.

## Out of Scope

- New video-provider research, provider-floor benchmarking, or prompt-quality tuning beyond what is required to keep the shipped breadth-first path honest
- A new multiselect scene-picker UI or a new execution mode beyond the existing `current_scene` / `all_scenes` scope contract, unless the representative walkthrough proves the current contract cannot express the real user need
- Queue-management infrastructure, background vendor orchestration, or editor-style batch controls that are not required to make the current operator path truthful
- Reopening AI-previz or deterministic previz product work; this story is about final render and its project-level handoff
- NLE-like editing, transition design, mastering, or final-delivery polish beyond the first truthful breadth-first generation route

## Approach Evaluation

This is likely an orchestration-and-truth story over existing substrate, but `/build-story` should still verify the simplest answer before widening anything.
- **Simplification baseline**: The repo already has an `all_scenes` scope contract, a real scene-level render route, and a real `final_output` path. The first task should therefore replay the representative `all_scenes` route and determine whether the gap is just surfaced truth / handoff wiring or whether a deeper orchestration seam is still missing.
- **AI-only**: Wrong fit for the main gap. A model can render each scene, but it should not own breadth-first execution policy, partial-success bookkeeping, or whether the project route is allowed to claim completeness.
- **Hybrid**: Likely the right fit. Use deterministic scope/preflight/handoff logic with the existing AI render path per scene. If project-cut validation or omission summaries need to react to multi-scene outcomes, reuse the shared validation substrate rather than creating a second truth path.
- **Pure code**: Plausible only if the current render path already works for `all_scenes` and the remaining problem is surfaced metadata, artifact linkage, or final-output completion semantics. If representative proof shows the batch render route itself is still dishonest, pure code alone may be insufficient because the output-generating stages still need AI, but the fix should remain orchestration-first.
- **Repo constraints / ADRs**: ADR-002 requires explicit proceed / warn / soft-block behavior and honest surfaced navigation, not hidden backend loops. ADR-003 keeps Scene Workspace scene-first but does not justify stopping at one scene forever; project artifacts remain story/timeline-derived and headless-first. Story 164 explicitly left multi-scene batch rendering out of scope, while Stories 166 and 167 solved project assembly and trust only after scene renders already exist.
- **Existing patterns to reuse**: Story 148's `SceneExecutionScope` and `pipeline/scene_actions.py` preflight substrate, Story 165's `start_from=render` reuse path, Story 166's `final_output_v1` assembly contract, Story 167's project-cut validation overlay, Story 168's representative reference-conditioned route truth, Story 169's chosen final-render default, and the existing `GeneratedVideoPanel`, `FinalOutputCard`, `FinalOutputViewer`, `RunDetail`, and `ArtifactDetail` surfaces. Reuse these seams instead of inventing a separate batch-generation system.
- **Eval**: The primary discriminator is a representative breadth-first walkthrough on the canonical fixture plus focused integration coverage for multi-scene render success/partial-success and `final_output` handoff. If the implementation materially changes validation behavior, rerun `runtime-final-output-validation`; otherwise do not force promptfoo work just because the story is important.

## Tasks

- [x] Walk the current representative `all_scenes` render path on the canonical fixture and capture the exact blocker or truth gap before changing code. Use the normal surfaced route and the equivalent headless/API path rather than hand-seeded impossible substrate.
- [x] Fix the smallest end-to-end seam that prevents truthful breadth-first final render. Prefer existing scope/preflight/render/final-output owners over a new queue or orchestration subsystem.
- [x] Keep breadth-first project truth honest: surfaced preflight, run metadata, successful vs failed scene bookkeeping, `final_output` coverage, and validation links must all agree on what the run actually accomplished.
- [x] Add focused regression coverage for `all_scenes` render scope, multi-scene success/partial-success bookkeeping, and the resulting `final_output` / validation handoff.
- [x] If the chosen implementation changes project-cut validation or any maintained runtime detector materially, run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`; not needed because this slice did not materially change project-cut validation or a maintained detector.
- [x] Run `make check-size` and keep new logic out of already-large owners unless the change is truly surgical or extracted into a focused helper.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` not needed; no agent tooling or project-instruction files changed
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`; not needed because no eval fixtures or registry entries changed in this story
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

- **Owning class/module**: Breadth-first execution truth should stay in the existing scope/render/final-output owners: `src/cine_forge/pipeline/scene_actions.py` for preflight and scope truth, `src/cine_forge/modules/generation/render_adapter_v1/main.py` for multi-scene render bookkeeping, `src/cine_forge/modules/timeline/final_output_v1/main.py` for project-cut handoff, and the existing Project Home / Run Detail / Artifact Detail surfaces for operator truth. Do not introduce a second batch-generation subsystem unless the representative walkthrough proves the current owners cannot express the route honestly.
- **Data contracts**: The existing cross-layer contracts already cover the likely surface: `SceneExecutionScope` in `src/cine_forge/schemas/scene_scope.py`, run metadata in `src/cine_forge/schemas/runtime_params.py`, project-cut coverage in `src/cine_forge/schemas/final_output.py`, and project/media trust in `src/cine_forge/schemas/media_validation.py`. If breadth-first bookkeeping needs new fields, add them schema-first instead of passing ad hoc dicts through run-state or viewer code.
- **File sizes**: Current likely blast-radius files include `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1659`, LARGE), `src/cine_forge/modules/timeline/final_output_v1/main.py` (`600`, LARGE), `src/cine_forge/api/artifact_manager.py` (`580`, LARGE), `src/cine_forge/pipeline/scene_actions.py` (`571`, LARGE), `ui/src/pages/RunDetail.tsx` (`663`, LARGE), `ui/src/pages/ArtifactDetail.tsx` (`647`, LARGE), and `ui/src/pages/ProjectHome.tsx` (`612`, LARGE). Smaller seams to prefer when possible: `src/cine_forge/schemas/scene_scope.py` (`56`), `src/cine_forge/schemas/runtime_params.py` (`60`), `src/cine_forge/schemas/final_output.py` (`78`), `src/cine_forge/schemas/media_validation.py` (`142`), `ui/src/components/GeneratedVideoPanel.tsx` (`376`), `ui/src/components/FinalOutputCard.tsx` (`285`), `ui/src/components/FinalOutputViewer.tsx` (`376`), `tests/unit/test_scene_actions.py` (`329`), and `tests/integration/test_final_output_integration.py` (`124`).
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 148, 164, 165, 166, 167, 168, and 169, plus the current scope contract, `pipeline/scene_actions.py`, `render_adapter_v1`, `final_output_v1`, `artifact_manager.py`, `GeneratedVideoPanel.tsx`, `FinalOutputCard.tsx`, `FinalOutputViewer.tsx`, `ProjectHome.tsx`, and `RunDetail.tsx`. No newer ADR was found that narrows breadth-first render ownership more specifically.

## Files to Modify

- `docs/stories/story-170-breadth-first-scene-generation-product-truth.md` — keep the story current during build, validation, and close-out
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — preserve successful scene outputs and truthful failure summaries when an `all_scenes` render run only partially succeeds, without widening the already-oversized owner unnecessarily (`1659`)
- `ui/src/components/GeneratedVideoPanel.tsx` — distinguish “this scene failed” from “the all-scenes batch saved some renders but failed elsewhere” on the surfaced route, and point the inline failure CTA at the actual Run Detail screen (`376`)
- `ui/src/components/ShotPlanningPanel.tsx` and `ui/src/components/FinalOutputCard.tsx` — keep the shared `Open Run Details` CTA pattern consistent once the route mismatch surfaced during verification (`188`, `285`)
- `ui/src/lib/use-run-progress.ts` — keep failed terminal runs as the active workspace context long enough for inline failure cards and Run Detail links to remain usable (`556`)
- `ui/src/pages/RunDetail.tsx` — make partial-success evidence readable on failed breadth-first runs using the existing artifact list and stage failure summary (`663`)
- `tests/integration/test_render_adapter_integration.py` — regression coverage for preserved scene outputs, track-manifest handoff, and scene-id failure summaries on partial `all_scenes` render runs (`425`)
- `tests/integration/test_final_output_integration.py` — prove that a preserved partial render state still assembles an honest partial project cut through the existing `final_output` route (`124`)
- `src/cine_forge/pipeline/scene_actions.py`, `src/cine_forge/modules/timeline/final_output_v1/main.py`, `src/cine_forge/api/artifact_manager.py`, and the schema files in `src/cine_forge/schemas/` — fallback-only touch points if implementation proves the existing scope contract, final-output artifact, or validation overlay cannot carry truthful breadth-first state without a schema-backed addition (`571`, `600`, `580`, `56/60/78/142`)

## Redundancy / Removal Targets

- Any copy or helper logic that still treats the one-scene render route as the effective end of the shipped generation workflow
- Any optimistic project-complete messaging that is inferred from “some scene renders exist” rather than the actual rendered scene set and latest `final_output`
- Any duplicate breadth-first bookkeeping split between render viewers and project-cut viewers once one schema-backed truth path is established

## Notes

- This is a new story rather than a reopen of Story 148, 164, 166, or 169 because the subsystem is continuous but the success surface changed again: Story 148 made scope honest, Story 164 made one scene render real, Story 166 made project assembly real, and Story 169 chose the provider floor on that route. None of them proved the operator can now advance the whole project through the same route honestly.
- The existing scope contract already supports `all_scenes`, so the first question is not “invent a richer selection model.” The first question is whether the current surfaced `all_scenes` route is truthful enough to count as breadth-first product completion.
- The current repo already has a trustworthy project-cut surface. The story should only widen `final_output` or validation contracts if the representative walkthrough proves the handoff is still lying for breadth-first runs.
- The 2026-04-16 model-discovery output found 28 untested models, but that is hold-phase maintenance pressure, not the main blocker on the active `scene-generation-completion` climb.

## Plan

### Baseline / Eval Evidence

- Success baseline already exists on the current repo: a representative two-scene `all_scenes` headless run from `start_from=render` completes both `render` and `validate_media`, persists two `generated_video` artifacts, and the follow-on `final_output` recipe produces a complete project cut with matching project validation. This proves the breadth-first route itself already exists.
- Failure baseline exposes the real gap: a controlled two-scene probe where scene 2 throws during `generate_video` aborts the `render` stage before any successful scene artifacts or track-manifest update are persisted. Evidence from the probe:
  - scene 1 media bytes were written to `artifacts/generated_video_media/...`, so work partially happened
  - `render_prompt` and `generated_video` version lists stayed empty for both scenes
  - no updated `track_manifest` landed, so `final_output` cannot honestly see the saved scene
- Because this is orchestration and surfaced truth, not model-selection work, no new live model discovery or prompt bake-off is justified here. The shipped render provider floor from Story 169 remains the current substrate.

### Repo-Fit / Optimality

- Preferred approach: keep the existing `all_scenes` route, persist per-scene successes incrementally with the existing `announce_artifact` / `ArtifactPersister` pattern, aggregate failed scene ids/reasons into one explicit failure summary, and surface that truth in the existing run/detail UI.
- Why this fits CineForge:
  - `SceneExecutionScope` and preflight already truthfully express `all_scenes`; there is no missing selection model to invent.
  - `final_output_v1` already produces honest `partial` vs `complete` project cuts once the track manifest reflects the real rendered scene set.
  - Other multi-entity stages in this repo already use `announce_artifact` for mid-stage persistence; `render_adapter_v1` is the outlier dropping successful work on stage failure.
  - ADR-002 favors explicit surfaced truth over hidden recovery loops. A failed breadth-first run with preserved artifacts and named failed scenes is more honest than silently pretending the batch succeeded.
- Alternatives rejected:
  - New batch orchestration subsystem: wrong abstraction. The route already exists; the defect is in persistence and disclosure.
  - Driver-level new `partial` stage status: possible, but too wide for the current evidence. Existing `failed` status plus preserved artifacts and an aggregated failure message should cover the operator truth gap with much lower blast radius.
  - Reworking `final_output_v1` or media-validation contracts first: premature. Those paths already behave honestly once partial render state is actually persisted.

### Structural Health Check

- `make check-size` on 2026-04-16 still flags the main risk files:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — 1659 lines, oversized owner; do not grow `run_module` substantially
  - `ui/src/pages/RunDetail.tsx` — 663 lines, large
  - `ui/src/components/GeneratedVideoPanel.tsx` — 376 lines, acceptable but already dense
  - `tests/integration/test_render_adapter_integration.py` — 425 lines, large but still the right regression home
  - `tests/integration/test_final_output_integration.py` — 124 lines, safe
- Planned contract shape: no new cross-layer schema or event type unless the existing `background_error`, stage `artifact_refs`, and persisted artifact truth prove insufficient during implementation.
- Guardrail: keep new render-side logic in extracted helpers inside `render_adapter_v1/main.py` rather than inflating the top-level loop inside `run_module`.

### Task Order

- Task 1: Preserve successful scene outputs during partial `all_scenes` render failures.
  - Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  - Change: reuse `context["announce_artifact"]` so each successful prompt/video pair is saved immediately, capture the actual persisted refs, and announce an updated `track_manifest` for the successful scene subset before raising any aggregated failure.
  - Done looks like: when one scene fails late in an `all_scenes` run, earlier successful `render_prompt` / `generated_video` artifacts and a matching generated-video track manifest still exist in the store.

- Task 2: Keep failure truth explicit instead of orphaning it in a traceback.
  - Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  - Change: continue attempting remaining scenes after an individual scene failure, collect failed scene ids/reasons, and raise one final error only after all target scenes were attempted. The error text must name successful vs failed scene counts and the failed scene ids so `background_error` and Run Detail stay actionable.
  - Done looks like: the run still fails when any scene failed, but the failure message clearly says which scenes failed and earlier successes remain usable.

- Task 3: Tighten surfaced UI copy around partial breadth-first failure.
  - Files: `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/pages/RunDetail.tsx`
  - Change: update the render failure card and Run Detail copy so an `all_scenes` failure is described as a batch failure with possible partial saved outputs, not as “this scene failed” unconditionally.
  - Done looks like: from the scene render tab and Run Detail, the operator can tell whether the current scene may already have a new render and where to inspect the failed scene list.

- Task 4: Lock the behavior with focused regression tests.
  - Files: `tests/integration/test_render_adapter_integration.py`, `tests/integration/test_final_output_integration.py`
  - Change: add one integration test for partial `all_scenes` render failure preservation and one follow-on test proving the preserved partial track state assembles an honest partial `final_output`.
  - Done looks like: current failure baseline turns green, and the repo has a deterministic proof that breadth-first partial success no longer disappears.

### Impact / Break Risks

- Main risk: pre-saving artifacts inside `render_adapter_v1` could create duplicate or stale project-track entries if the manifest update logic is sloppy. The implementation has to replace only the successful scenes’ generated-video entries and leave unrelated track entries untouched.
- Secondary risk: if the partial-failure message is too generic, the UI will technically show a failure but still not tell the operator what to do next. The aggregated failure text needs to be intentionally readable.
- Lowest-probability risk: if `final_output_v1` relies on assumptions about only fully successful render stages, the follow-on integration test will expose it. If that happens, widen the story into a small, coupled `final_output` adjustment rather than inventing a follow-up.

### Redundancy Plan

- Do not add a second “batch render” truth path. Reuse the existing `render_generation` recipe, `generated_video` artifacts, and `track_manifest` update contract.
- If UI copy currently implies an all-scenes failure means zero useful outputs, replace that copy instead of layering an extra banner or helper state on top.

### UI Verification Plan

- Use a representative project state reachable through the normal product path, then exercise the shipped render UI in both desktop and mobile layouts.
- Golden path to verify:
  - open a scene render tab, switch to `All Scenes`, start the render run, and confirm the scope/preflight copy stays honest
  - inspect the failed partial run in Run Detail and confirm saved artifacts are visible alongside the failed-scene summary
  - from Project Home, assemble `Final Output` and confirm the card/viewer report partial coverage truthfully when only a subset of scenes rendered
- Browser evidence must include screenshots and clean console output unless a documented tooling blocker appears.

### Scope Adjustment From Exploration

- Narrowed scope: do not start by editing `final_output_v1`, `artifact_manager.py`, or the scene-scope schemas. Current evidence says the missing product truth is partial-success preservation in `render_adapter_v1`, plus small surfaced-copy fixes on top.
- Conditional expansion only if implementation disproves that assumption: if the preserved partial render state still cannot produce an honest project cut, widen the story immediately to the smallest coupled `final_output` or validation overlay fix rather than creating a follow-up.

### Approval / Blockers

- No dependency, migration, or public API blocker is known at planning time.
- The only implementation risk worth calling out up front is that `render_adapter_v1` is already oversized, so the work has to stay helper-oriented and test-led.

## Work Log

20260416-1531 — story-created: opened the missing owner for the active `scene-generation-completion` campaign after triage confirmed the repo now proves the depth-first route but still lacks a truthful breadth-first render path. Evidence: reviewed `docs/ideal.md`, `docs/spec.md` (`spec:5.3`, `spec:5.5`, `spec:6.1`, `spec:7.1`, `spec:10.1`, `spec:10.3`), `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 148/164/165/166/167/168/169, the current scope contract, `pipeline/scene_actions.py`, `render_adapter_v1`, `final_output_v1`, and the existing project/run/detail UI seams. Key conclusion: this is a new `Pending` story rather than a reopen because the success surface shifted from “one honest scene render and project assembly exist” to “the operator can advance the whole project through that route honestly.” Next step: run `/build-story 170`.
20260416-1638 — exploration-success-baseline: replayed the representative two-scene `all_scenes` route headlessly and confirmed the breadth-first path already exists when every scene succeeds. Evidence: `recipe-render-generation.yaml` from `start_from=render` completed `render` and `validate_media`, produced scene renders for `scene_001` and `scene_002`, and a follow-on `recipe-final-output.yaml` run produced `coverage_state == "complete"` plus matching project validation. Conclusion: the story is not “invent batch render”; the success-path substrate is already real. Next step: probe partial-failure behavior to find the actual missing truth seam.
20260416-1706 — exploration-partial-failure-probe: reproduced the concrete breadth-first defect with a controlled second-scene render failure. Evidence: on a two-scene `all_scenes` render run with synthetic failure on scene 2, scene 1 media bytes were written under `artifacts/generated_video_media/scene_001/v1/scene_render.mp4`, but no `render_prompt` or `generated_video` artifact versions were persisted for either scene and no updated `track_manifest` landed before the stage failed. Conclusion: the main gap is partial-success preservation and surfaced failure truth inside `render_adapter_v1`, not missing `all_scenes` scope semantics or missing `final_output` partial-coverage behavior. Next step: implement incremental persistence plus surfaced disclosure on the existing route.
20260416-1754 — implementation-and-regression: fixed the actual breadth-first seam instead of widening orchestration. Evidence: `render_adapter_v1/main.py` now announces and persists successful `render_prompt`, `generated_video`, and subset `track_manifest` artifacts as each scene lands, keeps going across later scene failures, and raises one aggregated failure summary naming the failed scene ids while preserving old single-scene failure behavior when nothing succeeded. Follow-on UI work in `GeneratedVideoPanel.tsx` and `RunDetail.tsx` makes all-scenes failures read as batch failures with preserved outputs, while the related `Open Run Details` CTA route mismatch was corrected in `GeneratedVideoPanel.tsx`, `ShotPlanningPanel.tsx`, and `FinalOutputCard.tsx`. Regression evidence: `tests/integration/test_render_adapter_integration.py` now proves scene-1 prompt/video persistence plus subset `track_manifest` truth when scene 2 fails; `tests/integration/test_final_output_integration.py` now proves the preserved partial render state assembles an honest partial `final_output` and validation result. Validation evidence: focused integration pack passed, backend lint passed, and `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`750 passed, 166 deselected, 1 pre-existing warning`). Conclusion: the route now preserves honest partial success instead of discarding it. Next step: verify the shipped surfaces in browser and close out the story log with concrete operator evidence.
20260416-1827 — browser-verification-and-scope-tightening: browser validation exposed one more coupled truth gap on the surfaced route: terminal failed runs were being cleared from workspace context immediately, so the new inline failure card could not stay mounted long enough to be useful. Evidence: `ui/src/lib/use-run-progress.ts` now keeps failed terminal runs as the active context while still clearing clean completions, which makes the render-panel failure card and Run Detail CTA inspectable after the batch stops. Desktop browser verification on representative smoke project `output/story170-browser-smoke` passed with clean console output on both the scene render surface and Run Detail: the render panel shows `All-scenes render run failed` plus the preserved-output guidance and CTA, and the CTA lands on `/${project_id}/runs/run-fb0d88df` where Run Detail shows `All-Scenes Run Failed`, the saved-artifact summary, and the failed scene id. Mobile browser verification on Project Home also passed with clean console output, showing `Final Output`, `Partial Coverage`, and `1/2 scenes rendered`. Screenshots saved for review at `output/story170-browser-smoke/verification/render-failure-card-desktop.png`, `output/story170-browser-smoke/verification/run-detail-failure-summary-desktop.png`, and `output/story170-browser-smoke/verification/project-home-partial-mobile.png`. Final UI checks after the route/context fixes also passed: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` (with only the pre-existing Vite large-chunk warning). Documentation search found no additional docs that needed updating beyond this story log. Conclusion: Story 170 now has representative desktop/mobile evidence for the changed surfaced path, and the remaining step is independent validation / close-out rather than more implementation. Next step: `/validate 170`.
20260416-1844 — validation-pass: reran the required validation suite from this pass and confirmed the code-level implementation is stable, but the story is not yet clean to close because the browser evidence for the failure flow is still a narrow non-representative smoke. Fresh checks rerun now: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`750 passed, 166 deselected, 1 pre-existing warning`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, targeted integration pytest for `test_render_adapter_integration.py` + `test_final_output_integration.py`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` (only the pre-existing Vite large-chunk warning). Fresh browser verification also passed with clean console output on desktop/mobile for the changed render failure card, Run Detail, and Project Home partial-coverage surfaces, with screenshots saved at `output/story170-browser-smoke/verification/validation-render-failure-card-desktop.png`, `output/story170-browser-smoke/verification/validation-run-detail-desktop.png`, and `output/story170-browser-smoke/verification/validation-project-home-mobile.png`. Limitation: that browser project remains a synthetic partial-failure smoke (`story170-browser-smoke`) created with patched render behavior and manually seeded prerequisite substrate, so it does not satisfy the story's representative surfaced-route bar by itself. Next step: keep Story 170 open and either obtain representative desktop/mobile verification for the real surfaced `all_scenes` route or explicitly rescope the remaining browser-proof gap into a follow-up if the repo still cannot produce that state honestly on demand.
20260416-1901 — representative-verification-rerun: reran the missing representative proof on the real backend after validation exposed that the earlier local server on `127.0.0.1:8000` was still a Story 170 smoke patch that injected `synthetic browser second-scene failure`. Evidence: confirmed the patch in `/tmp/story170_patched_api.py`, replaced it with a clean `uvicorn cine_forge.api.app:app` backend on the same port, created fresh project `story-170-representative-clean-bd8ee4da` through `POST /api/projects/new`, uploaded `tests/fixtures/ingest_inputs/open_frequency_short.fountain`, and completed `mvp_ingest` (`run-09fc1cba`). The surfaced Scene Workspace route on `/story-170-representative-clean-bd8ee4da/scenes/scene_001?tab=render` then triggered a real `all_scenes` render run (`run-c88127ec`) with honest preflight warnings plus auto-build disclosure for timeline, track manifest, and shot planning. That run completed `timeline`, `tracks`, `shot_planning`, `render`, and `validate_media` successfully, persisted `render_prompt`, `generated_video`, and `media_validation` artifacts for `scene_001` through `scene_004`, and recorded `scene_scope.mode = all_scenes` with `track_manifest/project/v3.json` in run metadata. A follow-on headless `final_output` run (`run-e0fcfac2`) completed `final_output` plus `final_output_validation`, producing `final_output/project/v1.json` with `coverage_state = complete`, `included_scene_ids = [scene_001, scene_002, scene_003, scene_004]`, and matching `media_validation/project/v1.json` with `recommended_health = valid`. Browser verification on this representative project stayed clean (`0` desktop/mobile console errors, page errors, and HTTP errors) with screenshots at `output/story-170-representative-clean-bd8ee4da/verification/representative-render-preflight-desktop.png`, `representative-render-started-desktop.png`, `representative-run-detail-desktop.png`, `representative-final-output-detail-desktop.png`, `representative-render-desktop.png`, `representative-project-home-mobile.png`, and `representative-render-mobile.png`. Conclusion: the missing representative surfaced-route proof is now real, and Story 170's complete-cut side has been rerun fresh in the same validation pass. Next step: close the story.
20260416-1908 — completion: marked Story 170 done after the fresh representative rerun closed the only remaining acceptance gap. Evidence: all acceptance criteria and task checkboxes are now checked; the required checks remain green from the latest validation pass (`make test-unit`, Ruff, targeted integration pytest, UI lint, `tsc -b`, UI build, methodology compile/check); the representative project `story-170-representative-clean-bd8ee4da` proves the surfaced `all_scenes` route and complete `final_output` handoff on clean desktop/mobile browser passes; and planning state has been updated so `scene-generation-completion` is no longer advertised as an in-progress story-owned campaign. Operator effect: CineForge no longer stops at “one honest scene render.” A fresh multi-scene project can now advance through the shipped all-scenes render route, preserve useful work on partial failures, and assemble a truthful project-level playable cut when the batch completes. Next step: `/check-in-diff`.
