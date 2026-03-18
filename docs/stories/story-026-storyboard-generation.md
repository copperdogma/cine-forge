# Story 026: Storyboard Generation (Optional)

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:6.2 (Storyboards), spec:10.2 (Tracks — storyboard track), spec:10.3 (Always-Playable Rule)
**Depends On**: Story 025 (shot planning — storyboards derived from shot plan), Story 013 (track system — storyboard track slot)

---

## Goal

Generate **storyboard frames** from the shot plan. Each storyboard frame corresponds to one or more shots and provides a cheap visual representation of the scene — useful for blocking, eyeline verification, camera intent, and creative review.

Storyboards are optional. The pipeline can skip this stage entirely and go straight to animatics or generation.

---

## Acceptance Criteria

### Storyboard Generation
- [x] Each storyboard frame derived from a shot definition (Story 025).
- [x] Storyboard output includes:
  - [x] Visual representation of the shot (character positions, camera angle, composition).
  - [x] Shot metadata available for deterministic presentation/export (shot ID, size, angle, movement).
  - [x] Character labels and blocking indicators available for deterministic presentation/export.
  - [x] Camera position/movement indicator available for deterministic presentation/export.
- [x] Multiple frames per scene (one per key shot in the coverage plan).

### Storyboard Styles (Spec 14.2)
- [x] Support for multiple visual styles:
  - [x] Sketch (rough, fast, low-detail).
  - [x] Clean line (clear outlines, minimal shading).
  - [x] Animation-style (simplified but visually clear).
  - [x] Abstract color-coded (shapes and colors representing elements).
  - [x] Photoreal (discouraged, gated — requires explicit user opt-in due to cost).
- [x] Style selection configurable per-project or per-run.

### Image Generation Integration
- [x] Storyboard images generated via AI image generation API.
- [x] Generation prompt constructed from:
  - [x] Shot definition (framing, camera, content).
  - [x] Look & Feel concern group (lighting, color palette, composition, camera personality, visual motifs).
  - [x] Character descriptions from bibles.
  - [x] Location descriptions from bibles.
  - [x] Continuity states for character/location appearance.
  - [x] Canonical `visual_reference_image` from the relevant bible manifest when available (propagated by Story 119).
- [x] Cost tracking per frame.
- [x] Retry logic for generation failures.

### Track Integration
- [x] Generated storyboard frames placed on the storyboard track (Story 013).
- [x] Always-playable rule: storyboards serve as visual representation when no animatic or video exists.
- [x] Stored as image files within the project artifact structure and referenced from scene-level storyboard artifacts.

### UI Integration
- [x] Scene workspace exposes storyboards as a first-class scene tab, not only via generic artifact browsing.
- [x] Storyboard tab supports the same operational loop as shot planning:
  - [x] Empty state explains value and how generation runs.
  - [x] Run / refresh action launches the project-wide storyboard recipe and resolves back to the current scene.
  - [x] In-progress state explains that the run is project-wide while keeping the current scene view usable.
  - [x] Success state renders the latest storyboard inline for the current scene.
- [x] Inline storyboard view shows:
  - [x] Actual storyboard frame images loaded from project asset paths.
  - [x] Ordered frame cards with shot linkage and deterministic metadata (shot IDs, shot size, angle, movement, character labels, blocking, camera indicator, edit intent when present).
  - [x] Style, frame count, total estimated duration, and total estimated cost summary.
  - [x] Prompt transparency fields that help debugging (`prompt_sources_used`, reference-image presence) without turning the panel into raw JSON.
- [x] Artifact Detail renders storyboard artifacts with a dedicated storyboard viewer rather than raw JSON.
- [x] Storyboard artifacts have proper artifact metadata (label/icon/color) anywhere artifact types are surfaced in the UI.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/visualization/storyboard_v1/`
- [x] Reads shot plan, Look & Feel concern group artifacts, character/location bibles, continuity states, and bible-manifest visual references when present.
- [x] Outputs one scene-level `storyboard` artifact per scene containing frame metadata/index plus storyboard image files.

### Testing
- [x] Unit tests for prompt construction from shot definitions (mocked AI).
- [x] Unit tests for style selection.
- [x] Unit tests for track integration.
- [x] Integration test: shot plan → storyboard module → scene-level storyboard artifacts + image files.
- [x] Schema validation on scene-level storyboard artifacts.

---

## Design Notes

### Storyboards as Quick Feedback
Storyboards are the cheapest visual feedback in the pipeline. They let the user see "is this roughly what I imagined?" before committing to expensive animatics or video generation. The quality bar is low — correctness of composition and blocking matters more than visual fidelity.

### Photoreal Gating
Photoreal storyboards are expensive and often unnecessary. They should be gated behind explicit user opt-in and should carry a cost warning. The default should be sketch or clean line style.

### Character Consistency
Maintaining visual consistency for characters across storyboard frames is a known challenge with AI image generation. Consider using character reference images (from user asset injection, Story 029) or style-consistent generation techniques.

### Sequencing with Design Studies
Story 119 is the preferred upstream for storyboard quality because it writes selected design-study finals back to bible manifests as `visual_reference_image`. Storyboard generation should consume that canonical field when present rather than inventing a second reference-selection path, while still degrading gracefully when no design-study reference exists yet.

---

## Tasks

- [x] Design storyboard prompt construction from shot definitions.
- [x] Implement style selection and configuration.
- [x] Create `storyboard_v1` module.
- [x] Implement AI image generation integration.
- [x] Implement scene-level storyboard artifact schema and persistence.
- [x] Implement track integration (storyboard track).
- [x] Implement cost tracking and photoreal gating.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Design storyboard UI integration for Scene Workspace and Artifact Detail.
- [x] Implement `StoryboardViewer` with inline image rendering and deterministic metadata presentation.
- [x] Implement `StoryboardPanel` scene workspace surface with project-wide run controls and scene-scoped resolution.
- [x] Integrate storyboard viewing into `SceneWorkspacePage`, `ArtifactDetail`, and artifact metadata.
- [x] Run UI checks (`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`) and browser verification.
- [x] Run `make test-unit` and the relevant lint scope (`ruff check src/ tests/`); repo-wide `ruff check .` still has pre-existing failures outside this story.
- [x] Search all docs and update any related to what we touched.
- [x] Update AGENTS.md with any lessons learned.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Storyboard generation writes new immutable artifacts and frame files only; no existing user data is mutated in place.
  - [x] **T1 — AI-Coded:** The implementation stays schema-first, splits generation/prompting helpers into focused files, and keeps UI rendering in dedicated components that another agent can trace quickly.
  - [x] **T2 — Architect for 100x:** The feature wraps the existing headless driver/module model instead of inventing a UI-only storyboard path or a second indexing abstraction.
  - [x] **T3 — Fewer Files:** New files were added only where they reduce pressure on already-oversized modules and pages; no parallel frontend-only schema system was introduced.
  - [x] **T4 — Verbose Artifacts:** The work log records the planning correction, backend implementation, UI expansion, validation evidence, and closure updates needed for handoff.
  - [x] **T5 — Ideal vs Today:** This lands the fast visual `generate -> react -> refine` loop closer to the Ideal by making storyboard review directly usable from Scene Workspace.

---

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

---

## Plan

### Scope Adjustment

- Replace the separate "storyboard index" artifact with one scene-level `storyboard` artifact per scene that records ordered frame metadata and file references. This matches the existing `shot_plan` artifact plus `shots` track pattern and avoids a second indexing layer with no clear consumer in the current repo.
- Keep shot IDs, labels, blocking indicators, and camera markers deterministic. The image model should generate composition imagery; overlays and labels should come from structured metadata or a deterministic compositor, not from unreliable model-rendered text.

### Eval-First Baseline

- Minimal eval for this story is code-level rather than promptfoo: schema validation, mocked unit tests for prompt construction and style selection, track integration assertions, and an integration fixture that proves `shot_plan -> storyboard artifact + image files + track_manifest`.
- Baseline on current code: there is no storyboard schema, module, recipe, or tests yet, while `src/cine_forge/pipeline/graph.py` already carries an unimplemented `storyboard_gen` node and `src/cine_forge/modules/timeline/track_system_v1/main.py` already reserves `storyboards`.
- Candidate approaches considered:
  - AI-only orchestration: one model plans frames, writes metadata, and handles file layout. Rejected because track persistence, cost accounting, and overlay correctness are deterministic responsibilities already standardized elsewhere in this repo.
  - Hybrid orchestration: deterministic prompt/context assembly, persistence, and track registration plus AI image generation per planned frame. Chosen because it matches existing module boundaries and keeps the model focused on visual synthesis.
  - Pure code rendering: diagrams only, no image model. Rejected because it misses the story goal of fast visual composition feedback grounded in look-and-feel and bible references.

### Repo-Fit Evidence

- The Ideal calls for a fast visual `generate -> react -> refine` loop and always-playable film outputs. Storyboards directly advance that path before animatics or video exist.
- Story 025 already established scene-scoped shot plans. Storyboard generation should mirror that contract instead of inventing a second indexing abstraction.
- Story 119 established `visual_reference_image` on bible manifests as the canonical visual-reference path. Reusing it is better than adding storyboard-specific reference selection.
- Story 013 and `src/cine_forge/modules/timeline/track_system_v1/main.py` already define `storyboards` as the fallback visual lane before animatics/video, so the missing work is the producer, not new playback architecture.
- Rejected alternative: a standalone `storyboard_index` artifact would create a new lookup layer not used anywhere else in the pipeline.

### Structural Health

- Planned existing touch points and current line counts:
  - `src/cine_forge/pipeline/graph.py` (697) — large; keep changes limited to registering `storyboard_v1`.
  - `src/cine_forge/ai/image.py` (452) — near the threshold; prefer thin helper reuse over new branching logic.
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` (1103) — oversized; do not add storyboard generation logic here.
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` (599) — oversized; avoid behavior changes unless a missing contract forces them.
  - `src/cine_forge/artifacts/store.py` (290) — acceptable only for a small file-path helper if needed.
- New cross-layer contract must be schema-first: add `src/cine_forge/schemas/storyboard.py` before module, API, or UI code consumes storyboard data.
- UI files that would be involved in direct inspection are already large:
  - `ui/src/pages/ArtifactDetail.tsx` (601)
  - `ui/src/components/ArtifactViewers.tsx` (1187)
  - `ui/src/pages/SceneWorkspacePage.tsx` (687)
  - `ui/src/components/ShotPlanViewer.tsx` (404)
- UI scope is now explicitly approved. To stay inside the size rules, add new dedicated components (`StoryboardViewer`, `StoryboardPanel`) instead of inflating `ArtifactViewers.tsx`, `SceneWorkspacePage.tsx`, or `ArtifactDetail.tsx` with large embedded layouts.
- Cross-layer contract is already schema-first on the backend. UI should read the existing `storyboard` payload shape directly instead of inventing a parallel frontend-only type system.

### Task Plan

1. Schema and contract
   - Files: new `src/cine_forge/schemas/storyboard.py`, `src/cine_forge/schemas/__init__.py`, and any schema-registry hook required by the driver.
   - Change: define the scene-level `storyboard` artifact model, frame entries, style enum, prompt lineage, file refs, cost fields, and deterministic overlay metadata.
   - Risk: artifact deserialization and registry wiring.
   - Done when: storyboard artifacts validate cleanly in unit tests.

2. Module implementation
   - Files: new `src/cine_forge/modules/visualization/storyboard_v1/main.py`, new `src/cine_forge/modules/visualization/storyboard_v1/module.yaml`, and only minimal helper touches in `src/cine_forge/ai/image.py` or `src/cine_forge/artifacts/store.py` if reuse requires them.
   - Change: read shot plans, concern groups, bible manifests, and continuity state; build generation prompts; call image generation per selected frame; persist image files; emit one scene-level artifact per scene.
   - Risk: image-generation retry handling, cost accounting, and project-relative asset paths.
   - Done when: mocked unit tests prove prompt construction, style selection, retry/cost behavior, and persisted artifact contents.

3. Pipeline and track integration
   - Files: `src/cine_forge/pipeline/graph.py`, recipe file(s) under `configs/recipes/`, and only the minimum timeline glue required if current contracts prove insufficient.
   - Change: wire `storyboard_v1` into the visualization phase, register `storyboard` output artifacts, and add `storyboards` track entries that point at the scene-level artifact.
   - Risk: graph dependency ordering and always-playable selection.
   - Done when: an integration fixture proves the storyboard track is selected when animatics/video are absent.

4. Verification and docs
   - Files: new or updated tests under `tests/unit/` and `tests/integration/`, this story file, and `AGENTS.md` only if implementation reveals a reusable lesson.
   - Change: add unit and integration coverage, run `make test-unit` and lint, and record evidence in the work log.
   - Risk: thin coverage that validates schema shape but misses semantic regressions.
   - Done when: required checks pass and the story contains validation-ready evidence.

5. Storyboard viewer component
   - Files: new `ui/src/components/StoryboardViewer.tsx` and any tiny shared helper additions needed for asset URL building.
   - Change: parse the `storyboard` payload into a typed view model, render ordered frame cards, load frame images via `/api/projects/{project_id}/assets/file/...`, and present structured overlay metadata, prompt provenance, and cost/time summaries in a way that matches existing card/badge patterns.
   - Risk: broken image URLs, overexposing raw prompt text, or shipping a viewer that only works on ideal data.
   - Done when: a storyboard artifact can be inspected without raw JSON and the viewer degrades cleanly when optional fields are absent.

6. Scene workspace integration
   - Files: new `ui/src/components/StoryboardPanel.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, and any small hook/type imports already used by `ShotPlanningPanel`.
   - Change: add a `Storyboard` tab beside `Shots`, mirror the existing run-control pattern from shot planning, resolve the latest scene-level storyboard artifact for the current scene, and render the viewer inline under empty/running/error/success states.
   - Risk: confusing duplication with the Shot Planning tab or incorrect messaging about the recipe running project-wide.
   - Done when: the scene workspace makes storyboard generation discoverable, operable, and reviewable without forcing the user into artifact browsing.

7. Artifact detail integration and metadata surfacing
   - Files: `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/artifact-meta.ts`, and only minimal list/detail call-site touches if the new label/icon needs propagation.
   - Change: register storyboard artifact display metadata and route `artifact_type === "storyboard"` to the dedicated viewer so the artifact page and any artifact lists speak the same language as the scene workspace.
   - Risk: widening already-large files without keeping the change thin and localized.
   - Done when: storyboard artifacts have a clear label/icon and render the same dedicated viewer in Artifact Detail.

### Redundancy Plan

- Do not add a second storyboard reference-selection path; use manifest `visual_reference_image`.
- Do not introduce a standalone `storyboard_index` artifact unless implementation proves the scene-level artifact cannot support playback/export consumers.
- Do not bake storyboard generation into shot planning; storyboard generation remains its own module boundary.
- Do not hide storyboard review behind generic JSON or artifact-list navigation once the scene workspace panel exists; the new panel becomes the primary scene-level entry point.

### UI Verification

- Primary browser path:
  - Open the Scene Workspace for a seeded scene with storyboard artifacts.
  - Verify the new `Storyboard` tab appears beside `Shots`.
  - Verify empty / running / success states read correctly and the run action text makes the project-wide scope explicit.
  - Verify frame images load, metadata is readable, and the artifact-detail link works.
- Secondary browser path:
  - Open a storyboard artifact directly in Artifact Detail and confirm it renders the same dedicated viewer rather than raw JSON.
- Browser tools to use:
  - Screenshot for visual verification.
  - Console inspection for image/network errors.
  - Network request inspection if image paths fail.
- Fallback if browser automation is unavailable:
  - Run the UI build/type/lint checks and inspect rendered HTML via the local dev server manually, then record the blocker in the work log.

### Human Approval Blockers

- Scope folded into this story:
  - Scene-level `storyboard` artifacts replace the separate storyboard index.
  - Metadata overlays and labels stay deterministic rather than model-rendered.
- User decision recorded: absorb storyboard UI into this story because a user-facing visualization feature is incomplete without an in-app review surface.
- Scope increase: `S` to `M`, but tightly coupled enough that splitting it now would make validation misleading.
- No new dependency is currently required.

---

## Work Log

*(append-only)*

20260314 — Backlog cleanup: clarified that storyboard generation should consume Story 119's propagated `visual_reference_image` when available. This keeps the story Pending, but makes the preferred sequencing explicit.
20260315-2353 — exploration + planning: confirmed Story 026 advances the Ideal's fast visual feedback loop and always-playable film lane; consulted `docs/ideal.md`, `docs/spec.md` sections 7 and 14, `docs/decisions/adr-003-film-elements/adr.md`, `docs/design/principles.md`, and dependency stories 013/025/119. Traced `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `src/cine_forge/pipeline/graph.py`, `src/cine_forge/ai/image.py`, `src/cine_forge/artifacts/store.py`, and the existing artifact-detail / shot-planning UI paths; found no local storyboard schema/module/tests, but `track_system_v1` already reserves `storyboards` and the pipeline graph already defines an unimplemented `storyboard_gen` node. Key repo-fit correction: emit one scene-level `storyboard` artifact per scene with frame metadata and file refs instead of inventing a separate `storyboard_index` artifact, and keep overlays deterministic instead of relying on image-model text rendering. Main risk files are already large (`shot_plan_v1/main.py` 1103, `track_system_v1/main.py` 599, `pipeline/graph.py` 697), so implementation should stay schema-first and add a new module rather than growing those files. Next step: get approval on the plan and scope corrections, then start implementation.
20260316-0008 — implementation start: plan approved. Promoted the story to `In Progress` and started with the schema-first slice so the new `storyboard` artifact, project-level style preference, and module wiring can be validated before touching generation or track integration. Evidence: approved plan in this story, existing registry gap in `src/cine_forge/driver/schema_registry.py`, and no current storyboard implementation under `src/cine_forge/modules/visualization/`. Next step: add the storyboard schema and registry hooks, then build the module against those contracts.
20260316-0704 — implementation: added `src/cine_forge/schemas/storyboard.py`, registered the new `storyboard` artifact type, added optional `storyboard_style` to `ProjectConfig`, and implemented `storyboard_v1` plus `configs/recipes/recipe-storyboard-generation.yaml`. Result: the repo now emits one scene-level storyboard artifact per scene, writes immutable frame files under `artifacts/storyboard_frames/<scene_id>/v<version>/`, updates the `storyboards` track with per-shot entries, consumes bible-manifest `visual_reference_image` hints when present, and records deterministic overlay metadata plus per-frame estimated image cost. Evidence: `src/cine_forge/modules/visualization/storyboard_v1/main.py`, `src/cine_forge/modules/visualization/storyboard_v1/prompting.py`, `src/cine_forge/modules/visualization/storyboard_v1/generation.py`, `src/cine_forge/modules/visualization/storyboard_v1/support.py`, `src/cine_forge/ai/image.py`, `src/cine_forge/pipeline/graph.py`, and `configs/recipes/recipe-storyboard-generation.yaml`. Next step: verify through unit, integration, and runtime smoke before handing off to `/validate`.
20260316-0718 — structural cleanup + lessons learned: the first pass left `storyboard_v1/main.py` at 871 lines, which violated the repo size rule for touched files. Decomposed the module into orchestration (`main.py` 234 lines), prompting/context (`prompting.py` 272), generation/persistence (`generation.py` 191), and shared helpers (`support.py` 236), then recorded the reusable dynamic-loader import rule in `AGENTS.md`. Evidence: `wc -l` on the four storyboard module files and the new AGENTS.md note about using absolute imports for driver-loaded helper modules. Next step: rerun the full check suite against the decomposed layout.
20260316-0726 — validation: targeted storyboard tests passed (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_storyboard_module.py -q` → `4 passed`, `PYTHONPATH=src ... -m pytest tests/integration/test_storyboard_integration.py -q` → `1 passed`) and the broader unit suite passed after updating the schema-registry count for the new `storyboard` schema (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `558 passed, 131 deselected, 1 warning`). `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` also passed. Repo-wide `ruff check .` still fails in pre-existing unrelated files under `.agents/skills/webapp-testing/scripts/with_server.py`, `benchmarks/scorers/`, and `scripts/discover-models.py`; those were not touched by this story. No dedicated promptfoo/eval harness exists yet for storyboard image generation, so there were no eval mismatches to classify this turn; validation relied on deterministic unit/integration coverage with the `mock` image model. Next step: complete runtime smoke and hand off for `/validate`.
20260316-0733 — runtime smoke: started the API with `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m uvicorn cine_forge.api.app:app --host 127.0.0.1 --port 8010`, confirmed `curl http://127.0.0.1:8010/api/health` returned `{"status":"ok","version":"2026.03.15-05"}`, then cleanly shut the server down. Re-ran `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/integration/test_storyboard_integration.py -q` after the final refactor and it still passed, confirming the recipe persists storyboard artifacts, image files, and storyboard-track entries end to end through `DriverEngine`. No browser verification was required because this story remained backend-only and did not change the frontend. Next step: hand off with `Build complete` checked and recommend `/validate`.
20260316-0815 — scope correction + UI replanning: user rejected the backend-only handoff because storyboard generation is effectively user-facing and incomplete without an in-app review surface. Reopened the build gate by unchecking `Build complete`, expanded Acceptance Criteria and Tasks to cover Scene Workspace + Artifact Detail integration, and documented the repo-fit UI plan after tracing `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/components/ShotPlanningPanel.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/artifact-meta.ts`, `ui/src/lib/api/assets.ts`, and the asset-file API router. Key decision: add a dedicated `Storyboard` scene tab and separate `StoryboardViewer` / `StoryboardPanel` components rather than bloating `ArtifactViewers.tsx` or hiding storyboard review in raw JSON. Next step: implement the new viewer/panel, wire storyboard metadata into artifact detail, then run UI lint/type/build plus browser verification.
20260316-0841 — UI implementation: added `ui/src/components/StoryboardViewer.tsx` and `ui/src/components/StoryboardPanel.tsx`, then wired them into `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ArtifactDetail.tsx`, and `ui/src/lib/artifact-meta.ts`. Result: storyboard review is now first-class in the scene workspace via its own tab beside `Shots`, with the same project-wide run-control pattern, direct artifact-detail linking, inline frame rendering from project asset paths, deterministic metadata summaries, and a collapsible prompt-context section for debugging. Artifact Detail now reuses the same dedicated viewer instead of falling back to raw JSON. Evidence: browser snapshot of `/project/scenes/scene_001` showed the new `Storyboard` tab, loaded SVG frame images, overlay metadata, and prompt-source/reference-image disclosure; `/project/artifacts/storyboard/scene_001/1` rendered the same viewer. Next step: finish UI/static validation recording and hand off for `/validate`.
20260316-0853 — UI validation + browser smoke: installed locked frontend dependencies (`pnpm --dir ui install --frozen-lockfile`) because this worktree had no `ui/node_modules`, then ran `pnpm --dir ui run lint` (0 errors, 5 pre-existing fast-refresh warnings in unrelated shared UI files), `cd ui && npx tsc -b` (passed), and `pnpm --dir ui run build` (passed; only existing Vite chunk-size warning). Browser verification used a seeded disposable project generated with `tests.storyboard_fixtures.seed_storyboard_project(...)` plus `configs/recipes/recipe-storyboard-generation.yaml` using `image_model=mock`; opened the project via `/api/projects/open`, verified `/project/scenes/scene_001` shows the `Storyboard` tab with inline frames and prompt context, then verified `/project/artifacts/storyboard/scene_001/1` renders the same dedicated viewer. Playwright console check reported 0 errors, and network logs confirmed successful asset-file fetches for `artifacts/storyboard_frames/scene_001/v1/frame_01_scene_001_a.svg` and `frame_02_scene_001_b.svg`. Next step: hand off with `Build complete` rechecked and recommend `/validate`.
20260317-2135 — validation pass: collected the full local delta (`git status`, `git diff --stat`, `git diff`, untracked files), re-read `docs/ideal.md`, `docs/spec.md` sections 4.6, 7, 12, and 14, plus ADR-002 and ADR-003, then reran the full required suite on the current tree. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `558 passed, 131 deselected, 1 warning`; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` → pass; `PYTHONPATH=src ... -m pytest tests/unit/test_storyboard_module.py tests/integration/test_storyboard_integration.py -q` → `5 passed`; `pnpm --dir ui run lint` → 0 errors with 5 pre-existing fast-refresh warnings; `cd ui && npx tsc -b` → pass; `pnpm --dir ui run build` → pass with existing Vite chunk-size warning only. Browser verification against the live dev server confirmed `/project/scenes/scene_001` exposes the `Storyboard` tab, renders inline storyboard frames and deterministic metadata, expands prompt context, and can launch the project-wide storyboard refresh action; the run completed and the scene advanced from storyboard `v1` to `v2`. `/project/artifacts/storyboard/scene_001/2` reused the same dedicated viewer, Playwright console checks stayed at 0 errors, and asset fetches for storyboard frame files returned 200. No dedicated promptfoo-style semantic eval exists yet for storyboard image quality, so there were no scored mismatches to classify and no registry update was required; validation relied on the existing acceptance tests and end-to-end browser/runtime checks. Recommended next step: `/mark-story-done`.
20260317-2215 — story closure: marked Story 026 `Done` after the clean validation pass and updated the tracking docs to match the shipped slice. Evidence: all acceptance criteria and workflow gates are now checked in this story, `docs/stories.md` now records Story 026 as `Done` and advances Story 027 to `Pending`, and `CHANGELOG.md` now has the dedicated `2026-03-17-01` entry for storyboard generation plus the Scene Workspace / Artifact Detail review surface. Close-out tenet check: no mutable data path was introduced, the implementation remains headless-first and schema-first, large UI files were protected by extracting focused storyboard components, and the work log captures the full backend-to-UI path. Recommended next step: `/check-in-diff`.
