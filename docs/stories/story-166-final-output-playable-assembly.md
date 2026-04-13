---
id: "166"
title: "Final Output Playable Assembly"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R9 (export to professional formats)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:7"
  - "spec:10.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "013"
  - "027"
  - "028"
  - "130"
  - "148"
  - "164"
  - "165"
category_refs:
  - "spec:5"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "final-output"
  - "assembly"
  - "feature-completeness"
legacy_system: ""
---

# Story 166 — Final Output Playable Assembly

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R9 (export to professional formats), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:7, spec:10.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 013, Story 027, Story 028, Story 130, Story 148, Story 164, Story 165

## Goal

Ship the first real `final_output` slice: a project-level playable cut assembled from the latest scene-level `generated_video` artifacts in timeline order, with explicit partial-vs-complete coverage truth, a headless-first module/recipe path, and a surfaced review/download route that does not force the operator to hunt through raw files or pretend the scene render tab is the end of the product. Story 164 proved one real scene render can land honestly; Story 165 proved the refine loop can reuse that substrate. The next missing promise is letting the operator watch and export the rendered cut of the film, even when only part of it is ready, without collapsing into a fake NLE or silently mixing lower-fidelity placeholders into something labeled “final.”

## Acceptance Criteria

- [x] A headless module/recipe path can assemble a project-level `final_output` artifact from the latest `timeline`, `track_manifest`, and scene-level `generated_video` artifacts without rerunning scene renders. The artifact stores typed provenance including at least the assembled media path, `timeline_ref`, `track_manifest_ref`, included scene ids, omitted scene ids, and a coverage state (`partial` vs `complete`).
- [x] If included scene clips are not directly concat-compatible, the first slice applies a bounded deterministic normalization step before assembly rather than failing silently or rerunning generation.
- [x] The first slice stays honest about source media: it assembles only `generated_video` entries into `final_output`, never silently splices storyboards, animatics, or AI previz clips into something labeled as final output. When only some scenes are rendered, the output is explicitly marked as a partial cut with concrete omission reasons.
- [x] The normal surfaced project route exposes Final Output status and actionability without route hunting, and Artifact Detail can review the assembled cut plus its coverage/provenance truth. Browser verification covers that route on desktop and mobile with clean console output.
- [x] The operator can download or open the assembled cut through a backend-owned path; the UI must stay a thin client over that backend path rather than introducing a second export/download implementation.
- [x] Pipeline graph / production-stage truth aligns with the shipped slice: `final_output` no longer appears as an unimplemented placeholder once the first slice lands, and targeted regression coverage exists for assembly ordering, coverage metadata, and surfaced route wiring.

## Out of Scope

- A full timeline editor, trim UI, scene-strip reorder UI, or any NLE-like editing surface
- Re-rendering scenes, auto-generating missing scenes, or inventing transitions/music to hide missing coverage
- Mixed-fidelity “best available” project playback across storyboards, historical animatic/previz artifacts, or AI previz; that remains the job of earlier always-playable review surfaces, not `final_output`
- Advanced mastering, color/audio finishing, or provider-specific final-delivery optimization
- New model benchmarking unless implementation reveals a concrete runtime quality detector is required

## Approach Evaluation

The likely repo-fit answer is deterministic assembly over existing render outputs, but build-story should still prove that against the simplest baseline instead of assuming a new subsystem.
- **Simplification baseline**: Before adding any new workflow surface, measure whether deterministic concat of the latest timeline-ordered `generated_video` refs plus the current backend media-serving path already closes the user-visible gap. If it does, the first slice should stay narrow and avoid inventing broader orchestration.
- **AI-only**: Wrong fit for the first slice. Assembly order, coverage truth, provenance, and downloadability are deterministic substrate concerns, not reasoning gaps. An LLM could summarize omissions later, but it should not own the assembly contract.
- **Hybrid**: Plausible only for optional omission summaries or future transition guidance while keeping the assembly pipeline deterministic. That is a possible follow-up, not the default answer.
- **Pure code**: Strong candidate. The missing work appears to be timeline/track resolution, media assembly, typed artifact persistence, and surfaced route honesty.
- **Repo constraints / ADRs**: ADR-002 requires explicit preflight and truthful downstream UX instead of hidden backend magic. ADR-003 keeps film artifacts story/timeline-derived and headless-first. AGENTS requires all core capabilities to be operable via CLI/backend without the UI. `src/cine_forge/pipeline/graph.py` still marks `final_output` as unimplemented, so this story must close a real user-facing gap rather than add sidecar tooling.
- **Existing patterns to reuse**: Story 027's historical project-level `previz_reel` artifact/viewer pattern, Story 130's `project_loader.py` export helpers, the existing backend asset-file route, Story 013's `track_manifest` and always-playable resolver helpers, Story 028's generated-video artifact contract, and Story 165's surfaced-route honesty patterns.
- **Eval**: No model eval by default. The distinguishing evidence is deterministic runtime behavior on two representative states: one partial-rendered project and one complete-rendered project. If the first slice reveals the need for a maintained runtime detector or assembly-quality harness, create that follow-up explicitly instead of silently absorbing it here.

## Tasks

- [x] Measure the simplification baseline on a representative rendered project: confirm whether deterministic timeline-ordered assembly of existing `generated_video` artifacts already works, and record any codec/container or coverage blocker before adding more substrate.
- [x] Add a schema-first `final_output` contract plus a focused module/recipe path that assembles the latest rendered scene clips into a project-level artifact without rerunning scene renders.
- [x] Surface Final Output status/actionability on the normal project route and add Artifact Detail review for the assembled cut, including explicit `partial` vs `complete` coverage truth and a backend-owned open/download path.
- [x] Absorb the small coupled runtime delta discovered during exploration: if render clips differ in codec/container details, add a bounded normalization fallback inside final-output assembly instead of punting the problem to a follow-up story.
- [x] Add focused regression coverage for assembly ordering, omission/coverage metadata, graph-stage truth, and any API/UI glue added by the surfaced route.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
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

- **Owning class/module**: This should land in a new focused module such as `src/cine_forge/modules/timeline/final_output_v1/`, not inside the already-large `track_system_v1/main.py` or `render_adapter_v1/main.py`. The project-level surfaced route should live in a dedicated card/viewer path rather than overloading the scene render tab.
- **Data contracts**: Add a schema-first `final_output` payload in a new `src/cine_forge/schemas/final_output.py` before wiring module or UI code. On the UI side, prefer local typed parser/view-model helpers inside new focused components instead of widening `ui/src/lib/types.ts` unless a new dedicated API response shape becomes necessary.
- **File sizes**: `src/cine_forge/pipeline/graph.py` is `716` lines, `src/cine_forge/modules/generation/render_adapter_v1/main.py` is `1554`, `src/cine_forge/modules/timeline/track_system_v1/main.py` is `599`, `src/cine_forge/pipeline/scene_actions.py` is `571`, `src/cine_forge/export/project_loader.py` is `184`, `ui/src/pages/ProjectHome.tsx` is `604`, `ui/src/pages/ArtifactDetail.tsx` is `637`, `ui/src/lib/types.ts` is `764`, `ui/src/components/PipelineBar.tsx` is `395`, and `ui/src/components/GeneratedVideoViewer.tsx` is `182`. The large-file pressure is in `render_adapter_v1`, `graph.py`, `track_system_v1`, `scene_actions.py`, `ProjectHome`, `ArtifactDetail`, and `types.ts`, so the first slice should prefer new focused files and surgical registration changes instead of piling more branching into those files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, ADR-002, ADR-003, Story 013, Story 027, Story 028, Story 130, Story 148, Story 164, and Story 165, plus the current pipeline graph, asset router, project home, Artifact Detail, render fixtures, and pipeline-bar code paths. No more specific ADR currently settles final-output assembly ownership or surfaced route shape.

## Files to Modify

- `docs/stories/story-166-final-output-playable-assembly.md` — scope, plan, and work log for this slice
- `src/cine_forge/schemas/final_output.py` — NEW typed contract for assembled project output and coverage truth
- `src/cine_forge/schemas/__init__.py` — register the new final-output schema export (`412`)
- `src/cine_forge/driver/schema_registry.py` — register `final_output` for driver validation (`118`)
- `src/cine_forge/modules/timeline/final_output_v1/main.py` — NEW headless project-level assembly module
- `src/cine_forge/modules/timeline/final_output_v1/module.yaml` — NEW module manifest
- `configs/recipes/recipe-final-output.yaml` — NEW recipe / module wiring for the first slice
- `src/cine_forge/pipeline/graph.py` — mark `final_output` as implemented and align production-stage truth (`716`)
- `src/cine_forge/export/project_loader.py` — shared loading helpers for timeline, track manifest, and generated-video inputs if the new module/export path needs them (`184`)
- `src/cine_forge/api/routers/assets.py` — extend the existing backend media path only if download/open semantics need filename or attachment support (`201`)
- `ui/src/lib/artifact-meta.ts` — register `final_output` display metadata
- `ui/src/lib/constants.ts` — human-facing recipe labels/messages for the new final-output run (`212`)
- `ui/src/lib/api/assets.ts` — final-output open/download helper over the existing backend asset route (`123`)
- `ui/src/pages/ProjectHome.tsx` — surfaced project-level Final Output action/status without route hunting (`604`)
- `ui/src/components/FinalOutputCard.tsx` — NEW project-level status/action card that keeps `ProjectHome` thin
- `ui/src/pages/ArtifactDetail.tsx` — register the dedicated viewer (`637`)
- `ui/src/components/FinalOutputViewer.tsx` — NEW project-level playback + coverage/provenance viewer
- `tests/render_fixtures.py` — extend render fixtures for multi-scene final-output coverage cases (`291`)
- `tests/unit/test_pipeline_graph.py` — update production-phase expectations for implemented `final_output` (`639`)
- `tests/unit/test_final_output_schema.py` and `tests/unit/test_final_output_module.py` — NEW schema/module regression coverage
- `tests/integration/test_final_output_integration.py` — NEW project-level assembly regression coverage

## Redundancy / Removal Targets

- The `final_output` placeholder truth in `src/cine_forge/pipeline/graph.py`
- Any product copy or planning text that still treats the Scene Workspace render tab as the furthest downstream shipped boundary once a real project-level cut exists
- Any route-specific media download hack that duplicates the existing backend asset-file path once final-output open/download wiring lands

## Notes

- The first slice should stay honest about scope: this is project-level cut assembly, not an editing system.
- Project-level mixed-fidelity playback belongs to the always-playable track stack and earlier review surfaces. This story should not blur `final_output` by silently splicing storyboard or AI-previz media into something labeled as final.
- There is no dedicated `final_output` eval entry in `docs/evals/registry.yaml` today. That is acceptable if this remains a deterministic assembly story. If build-story reveals a new runtime detector is warranted, create a follow-up rather than bloating this slice.

## Plan

### Exploration Summary

- Triaged from the live `scene-generation-completion` campaign after Stories 164 and 165 closed the representative scene-render and refresh-reuse slices.
- Current repo truth:
  - `src/cine_forge/pipeline/graph.py` still marks `final_output` as `implemented=False`.
  - Story 148 explicitly left film-level assembly/export orchestration out of scope.
  - Stories 164 and 165 explicitly left multi-scene final-output assembly/final-render workflow out of scope.
  - Story 027's `previz_reel` is historical evidence for a project-level artifact/viewer pattern, but `animatics_generation` is no longer part of the shipped workflow; this story should reuse the project-artifact pattern, not resurrect previz as the current production surface.
  - `FreshImportView` already has `artifactGroups` plus `scenes`, which makes the project home the thinnest existing surfaced route for a Final Output status/action card without inventing a new page.
  - The existing asset router already serves project-relative media through backend `FileResponse`; that is a better open/download seam for final output than creating a second media-export path under the export router.
  - `tests/render_fixtures.py` seeds real `generated_video` MP4 fixtures, and local `ffmpeg` is available. The simplest concat path is plausible, but mixed provider outputs still create a real compatibility risk.
- This means the next gap is not speculative. The repo has scene-level render truth, backend media serving, and project-level artifact patterns, but no project-level assembled output.

### Ideal Alignment And Eval-First Gate

- This story directly closes an Ideal gap: R7 and R10 require iterative end-to-end output, while R8/R9 require the result to be usable as a real production artifact/export surface.
- Baseline today is effectively `0/1` for project-level final output:
  - `final_output` exists only as an unimplemented graph node.
  - No module or recipe assembles rendered scenes into a project-level artifact.
  - No surfaced route lets the operator watch or download the rendered cut of the project.
  - No human-facing recipe label exists yet for a final-output run, so any first slice needs the normal run-label/message wiring as part of the surfaced path.
- First measurement must be simplification-first:
  - Start with deterministic concat over timeline-ordered `generated_video` artifacts and the existing backend asset path.
  - If stream properties already line up, keep the slice narrow.
  - If they do not line up, absorb the small coupled fix: a bounded normalization fallback before concat, still without rerunning generation or inventing a mastering pipeline.

### Repo-Fit / Optimality Evidence

- Story 013's `track_manifest` already records canonical scene-level representation state and should remain the source of truth for coverage discovery instead of inventing a second project-level scene-selection system.
- Story 028's `generated_video` artifact plus Story 165's honest render reuse now provide the minimum substrate to assemble a real cut without re-running generation.
- Story 027 is useful only as a historical project-artifact/viewer pattern. Reusing its current product assumptions would be wrong because the deterministic previz lane was intentionally removed from the shipped workflow.
- The asset router is a stronger repo fit than the export router for final-output media because it already serves project-relative files and keeps the UI thin over one backend path.
- `FreshImportView` is a better first surfaced route than a PipelineBar redesign: it already has the scene/artifact counts needed for actionability, while the Production phase truth in `PipelineBar` will improve automatically once `final_output` is marked implemented.
- Rejected first-slice alternatives:
  - **Mixed-fidelity final output**: wrong naming and wrong trust boundary; earlier review artifacts already cover that lane.
  - **UI-only stitched player or download flow**: violates headless-first rules and duplicates backend responsibility.
  - **Extending `render_adapter_v1` or `track_system_v1`**: wrong ownership and too much blast radius in already-oversized files.
  - **PipelineBar navigation redesign**: plausible later, but too much UX blast radius for the first project-level playback slice when the root project route can host the CTA now.
  - **AI-generated transitions / cleanup**: adds cost and ambiguity before the baseline deterministic cut exists.

### Structural Health Check

- Keep new logic out of:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1554`)
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` (`599`)
  - `src/cine_forge/pipeline/scene_actions.py` (`571`)
  - `src/cine_forge/pipeline/graph.py` (`716`)
  - `ui/src/pages/ProjectHome.tsx` (`604`)
  - `ui/src/pages/ArtifactDetail.tsx` (`637`)
  - `ui/src/lib/types.ts` (`764`)
- Prefer:
  - one new schema file
  - one new focused module package
  - one new focused project-home card
  - one new focused viewer component
  - surgical registration changes in existing large files
  - local parser/view-model helpers in the new components instead of widening cross-app type files unless a new dedicated API contract is introduced

### Scope Adjustment

- Small coupled scope expansion absorbed during planning: if render clips are not concat-compatible, add a bounded deterministic normalization fallback inside the final-output module instead of punting a likely runtime failure to a follow-up.
- The surfaced route should stay thin and project-level: add a focused card on `ProjectHome` plus Artifact Detail support, not a new production workspace or PipelineBar/nav rewrite.
- Prefer the existing asset-file backend path for open/download semantics. Only extend that router if filename/attachment behavior is insufficient after the first implementation pass.

### Implementation Order

1. **Schema and loader contract**
   - Files: new `src/cine_forge/schemas/final_output.py`, plus `src/cine_forge/schemas/__init__.py`, `src/cine_forge/driver/schema_registry.py`, and `src/cine_forge/export/project_loader.py`.
   - Change: define the persisted project-level output contract and the helper(s) that resolve timeline-ordered generated-video refs plus omission state from the latest `timeline` and `track_manifest`.
   - Done looks like: one typed backend contract exists before module/UI code, and the project-level assembly logic depends on `track_manifest` truth instead of ad hoc store scans.

2. **Headless assembly module and recipe**
   - Files: new `src/cine_forge/modules/timeline/final_output_v1/`, new `configs/recipes/recipe-final-output.yaml`, and `src/cine_forge/pipeline/graph.py`.
   - Change: add a focused project-level assembly stage that reads only the current timeline/track/generated-video substrate, assembles timeline-ordered scene clips, applies a bounded normalization fallback only when direct concat is not safe, persists the `final_output` artifact/media, and marks the pipeline node as implemented with a real fix recipe.
   - Done looks like: CLI/backend can produce a partial or complete rendered cut without rerunning scene generation.

3. **Thin surfaced route and media actions**
   - Files: `ui/src/pages/ProjectHome.tsx`, new `ui/src/components/FinalOutputCard.tsx`, `ui/src/pages/ArtifactDetail.tsx`, new `ui/src/components/FinalOutputViewer.tsx`, `ui/src/lib/artifact-meta.ts`, `ui/src/lib/constants.ts`, and optionally `src/cine_forge/api/routers/assets.py` plus `ui/src/lib/api/assets.ts`.
   - Change: surface the latest Final Output status/CTA on the normal project route, register a dedicated Artifact Detail viewer, and keep open/download behavior on the backend media path rather than adding a UI-only export flow. Avoid widening `PipelineBar`, `SceneWorkspace`, or `ui/src/lib/types.ts` for the first slice.
   - Done looks like: the operator can find, start, inspect, open, and download the current rendered cut without raw-file spelunking or route hunting.

4. **Regression coverage and graph truth**
   - Files: `tests/render_fixtures.py`, new `tests/unit/test_final_output_schema.py`, new `tests/unit/test_final_output_module.py`, new `tests/integration/test_final_output_integration.py`, and `tests/unit/test_pipeline_graph.py`.
   - Change: add multi-scene fixture support, prove timeline ordering and omission metadata for both partial and complete projects, exercise the recipe end-to-end, and update pipeline graph expectations now that `final_output` is implemented.
   - Done looks like: deterministic assembly behavior is covered in code, the graph truth is updated, and partial-vs-complete honesty is enforced by tests.

### Impact / Risk Notes

- The main product risk is fake certainty: labeling an incomplete rendered subset as a final film. Coverage metadata and surfaced copy must prevent that.
- The main technical risk is media compatibility when concatenating clips from different runs/providers. If normalization is needed, keep it bounded and deterministic instead of ballooning the story into mastering infrastructure.
- The main structural risk is duplicating assembly logic between runtime, asset serving, and UI. Keep one backend-owned assembly path and let other surfaces consume it.
- Human-approval blocker: none expected as long as implementation stays on the existing `ffmpeg` subprocess path. If implementation appears to require a new media library dependency, stop and surface that explicitly instead of silently adding it.

### Human Gate / Scope Reminder

- This story is intentionally the first `final_output` slice, not the full final-delivery system.
- If build-story discovers that genuine product value requires trim/reorder/editor behavior in the same slice, stop and surface that expansion explicitly instead of silently absorbing it.

## Work Log

20260412-1534 — story-created: packaged the missing follow-up for the active `scene-generation-completion` campaign after triage confirmed `final_output` remains unimplemented and no existing story owns the project-level assembly gap. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, ADR-002, ADR-003, Story 013, Story 027, Story 028, Story 130, Story 148, Story 164, Story 165, `src/cine_forge/pipeline/graph.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, and current UI artifact/viewer seams. Next step: run `/build-story 166`.
20260412-1556 — exploration: traced the live final-output substrate and tightened the build plan around the repo that exists today. Evidence: confirmed `final_output` remains a project-level unimplemented pipeline node in `src/cine_forge/pipeline/graph.py`; reviewed `src/cine_forge/modules/timeline/track_system_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/export/project_loader.py`, `src/cine_forge/api/routers/assets.py`, `ui/src/components/PipelineBar.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/components/GeneratedVideoViewer.tsx`, `ui/src/lib/constants.ts`, `tests/render_fixtures.py`, and `tests/integration/test_render_adapter_integration.py`; verified `ffmpeg` is installed locally and the seeded generated-video benchmark clip is H.264 MP4. Decisions: keep `final_output` as a standalone project artifact instead of a new track type, treat Story 027 as historical artifact/viewer evidence rather than current product truth, prefer the existing asset-file backend path over `export.py` for open/download, keep the first surfaced route on project home plus Artifact Detail, and absorb a bounded normalization fallback if clip streams are not directly concat-compatible. Next step: human gate on the revised implementation plan before changing code.
20260412-1601 — implementation-start: promoted Story 166 to `In Progress` after plan approval so methodology state matches active execution. Next step: land the schema-first final-output contract and focused assembly module before touching surfaced UI wiring.
20260412-1648 — implementation: shipped the first end-to-end `final_output` slice as a standalone project artifact path instead of widening track/render ownership. Evidence: added `src/cine_forge/schemas/final_output.py`; registered the schema in `src/cine_forge/schemas/__init__.py` and `src/cine_forge/driver/schema_registry.py`; added the headless assembly module in `src/cine_forge/modules/timeline/final_output_v1/` plus `configs/recipes/recipe-final-output.yaml`; marked `final_output` implemented in `src/cine_forge/pipeline/graph.py`; added multi-scene fixture support in `tests/render_fixtures.py`; added schema/module/integration regression coverage for partial and complete assembly; and surfaced the new truth through `ui/src/components/FinalOutputCard.tsx`, `ui/src/components/FinalOutputViewer.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and `ui/src/lib/artifact-meta.ts`. Result: CineForge can now assemble a project-level playable cut from rendered scenes without rerunning scene generation, and the operator can find that cut from the normal project route. Next step: run full verification, including browser checks on the surfaced route.
20260412-1712 — verification: validated the new slice across backend, UI build, and browser smoke. Evidence: `PYTHONPATH=src python -m pytest tests/unit/test_final_output_schema.py tests/unit/test_final_output_module.py tests/integration/test_final_output_integration.py tests/unit/test_pipeline_graph.py` passed; `make test-unit PYTHON=python` passed (`735 passed, 162 deselected`); targeted Ruff on the touched Python files passed; `pnpm --dir ui install --frozen-lockfile`, `pnpm --dir ui run lint`, and `pnpm --dir ui run build` passed; and a seeded partial project smoke at `output/story166-final-output-smoke` was opened through the real API/UI path with Playwright, producing screenshots at `/tmp/story166-final-output-ui/project-home-desktop.png`, `/tmp/story166-final-output-ui/artifact-detail-desktop.png`, and `/tmp/story166-final-output-ui/artifact-detail-mobile-omissions.png`, with no browser console errors or page errors. Scope note: that browser fixture is a narrow non-representative UI smoke using seeded `generated_video` artifacts, not a provider-produced multi-scene project. Remaining caveat: repo-wide `make lint PYTHON=python` still fails on pre-existing unrelated files under `.agents/skills/` and `scripts/`, so story-local lint is clean but repo-global lint is not yet green. Next step: hand off for `/validate 166` rather than marking done from implementation mode.
20260412-1651 — validation: reran the required gates and confirmed the slice is implementation-complete. Fresh evidence from this pass: `make test-unit PYTHON=python` passed (`735 passed, 162 deselected, 1 pre-existing warning`); `python -m ruff check src/ tests/` passed; `PYTHONPATH=src python -m pytest tests/unit/test_final_output_schema.py tests/unit/test_final_output_module.py tests/integration/test_final_output_integration.py tests/unit/test_pipeline_graph.py` passed (`43 passed`); `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed, with the pre-existing methodology warning for `ingest_and_world_building`. Browser verification: Playwright MCP transport remained closed, so validation followed `docs/runbooks/browser-automation-and-mcp.md` and used local Python Playwright instead. Verified the surfaced route on desktop and mobile with clean console/page/response logs in two states: a representative real-render project copied from `/Users/cam/Documents/Projects/cine-forge/output/story-137-render-ui-check` after assembling the current `final_output` recipe, plus the Story 166 seeded smoke project for the partial-coverage omission UI. Screenshots: `/tmp/story166-validate-ui/project-home-desktop.png`, `/tmp/story166-validate-ui/artifact-detail-desktop.png`, `/tmp/story166-validate-ui/artifact-detail-mobile.png`, `/tmp/story166-validate-ui/artifact-detail-mobile-omissions.png`, `/tmp/story166-validate-ui-representative/artifact-detail-desktop.png`, and `/tmp/story166-validate-ui-representative/artifact-detail-mobile.png`. Environment caveat: the repo-local `.venv/bin/python` path is absent in this worktree and `/usr/local/bin/python3.12` does not have `pytest`/`ruff` installed, so validation used the active `python` environment for backend checks. Recommended next step: `/mark-story-done 166`.
20260412-2115 — completion: marked Story 166 done after confirming the shipped slice closes the project-level final-output gap and only close-out/bookkeeping remained. Evidence: workflow gates are all checked; status is now `Done`; methodology views were refreshed after the story-state change; and the landing set includes the new headless assembly recipe/module, surfaced Final Output card/viewer path, updated graph truth, and the fresh validation record from `/validate 166`. Operator effect: CineForge now exposes a truthful project-level playable cut instead of stopping at scene-level render artifacts. Next step: `/check-in-diff`.
