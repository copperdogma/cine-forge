# Story 132 — Shot Planning UI and Shot List Exports

**Priority**: High
**Status**: Done
**Ideal Refs**: R9 (professional exports), R11 (production readiness per scene), R7 (iterative refinement)
**Spec Refs**: 4.6 (Film Lane on demand), 12.7 (Readiness Indicators), 13 (Shot Planning), 13.4 (Export Compatibility), note 1050 (scene-first with shot detail drill-down)
**ADR Refs**: `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/decisions/adr-003-film-elements/adr.md`
**Depends On**: Story 025 (Shot Planning), Story 058 (Comprehensive Export & Share), Story 099 (Scene Workspace), Story 101 (Centralized Long-Running Action System)

## Goal

Make shot planning usable by a human operator. Story 025 landed the backend artifact, run recipe, and export endpoints, but CineForge still has no UI surface that lets a user intentionally run shot planning, inspect a readable shot plan, or discover the shot-list exports without guessing URLs. This story closes that product gap by adding a scene-first shot-planning surface in Scene Workspace, wiring shot-list exports into the existing export UI, and making `shot_plan` artifacts first-class instead of raw JSON.

## Acceptance Criteria

- [x] Scene Workspace exposes an explicit downstream shot-planning surface for the current scene. If no `shot_plan` exists, the empty state explains what shot planning does and offers a primary action to run it. If a `shot_plan` exists, the UI renders a readable summary and ordered shot list instead of raw JSON.
- [x] The shot-planning action launches the existing run infrastructure, makes execution scope honest before the run starts, and returns the user to the current scene's results when the run finishes. No bespoke polling, hidden backend calls, or parallel progress UI are introduced.
- [x] `shot_plan` artifacts become first-class in the UI: `ui/src/lib/artifact-meta.ts` has a labeled entry, Artifact Detail uses a dedicated viewer, and the scene/project surfaces no longer force users through a generic JSON fallback.
- [x] The existing export UI exposes Shot List CSV and Shot List PDF by calling the backend export routes. If no shot plans exist yet, the UI handles that state directly with disabled actions or clear explanatory copy instead of sending the user to a backend `404`.
- [x] Browser verification covers the operator path end to end: open a scene, start shot planning, inspect the resulting shot plan in the UI, and download the shot-list export with no browser console errors.

## Out of Scope

- Reworking shot-planning quality, prompt strategy, or the creative schema from Story 025
- Storyboards, animatics, render generation, or a new dedicated project-wide "Shots workspace"
- Export fidelity improvements already scoped to Story 130 (call-sheet redesign, narrative-aware interchange formats)
- A second client-side export implementation or chat-only workaround for shot-list access

## Approach Evaluation

The backend capability already exists. The question is not whether a model can plan shots; it is how little code we need to add to surface that capability honestly and readably in the product.
- **Simplification baseline**: Story 025 already proved the creative baseline. A single scene-level LLM call can generate a valid structured shot plan; the missing work is UI/product plumbing. The first build question is whether the existing project-level `shot_planning` recipe can be surfaced directly with acceptable UX or whether a small typed scope filter is needed to keep Scene Workspace honest.
- **AI-only**: Wrong fit. Chat-generated ad hoc shot lists or chat-only "download this URL" guidance would bypass the artifact store, duplicate export behavior, and create an untestable shadow UI.
- **Hybrid**: Plausible only if a small amount of backend support is needed for scene-scoped execution or export filtering. The creative reasoning remains in the existing shot-planning module; UI rendering, scope handling, and export wiring stay deterministic.
- **Pure code**: Strong candidate. Most of the work is Scene Workspace orchestration, viewer rendering, and export-modal integration over existing backend endpoints and schemas.
- **Repo constraints / ADRs**: ADR-003 requires scene-first UX with shot detail as drill-down. ADR-002 requires capabilities to be discoverable from the real UI, not hidden behind page-local buttons or undocumented URLs. AGENTS.md requires headless operation to remain the source of truth, so UI must wrap the existing backend routes rather than invent a client-only path. `ui/src/pages/SceneWorkspacePage.tsx` and `ui/src/components/ArtifactViewers.tsx` are already oversized; this story must extract focused presentation components instead of adding more inline branches.
- **Existing patterns to reuse**: `useStartRun`, `useChatStore().setActiveRun`, `OperationBanner`, `ExportModal`, `ui/src/lib/api/exports.ts`, `useArtifact`, `useArtifactGroups`, `getArtifactMeta`, and the existing artifact-detail viewer switch in `ui/src/pages/ArtifactDetail.tsx`.
- **Eval**: No new model eval is expected if this remains a UI/plumbing story. The distinguishing evidence is runtime behavior: browser walkthrough, export download, targeted frontend tests, and targeted backend tests only if scope/filtering support is added. `docs/evals/registry.yaml` should change only if implementation expands into shot-planning model behavior.

## Tasks

- [x] Decide the minimum honest execution scope for the Scene Workspace action: reuse the existing project-level `shot_planning` recipe as-is, or add the smallest typed scope filter needed so the UI does not misrepresent what will run.
- [x] Extract a focused shot-planning surface out of `ui/src/pages/SceneWorkspacePage.tsx` and add a downstream `Shots` tab or equivalent scene-first surface that can show empty, running, and populated states.
- [x] Create a dedicated `shot_plan` viewer component and reuse it from both Scene Workspace and Artifact Detail. Do not leave `shot_plan` as a raw-JSON-only artifact type.
- [x] Extend the existing export UI plumbing (`ui/src/components/ExportModal.tsx` and `ui/src/lib/api/exports.ts`) to expose Shot List CSV and Shot List PDF with clear empty-state handling.
- [x] Add the minimum discoverability wiring needed so users can find shot planning from existing scene/project surfaces without guessing: artifact metadata, readable labels, and any small navigation affordance required by the chosen UI.
- [x] If execution or export scope needs backend support, add the smallest typed contract in the existing shot-planning/export path rather than inventing a UI-only side channel.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `.venv` is absent in this worktree, so fallback validation used `make test-unit PYTHON=python` and now passes (`519 passed, 118 deselected`)
  - [x] Backend lint: `python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Architectural Fit

- **Owning class/module**: Scene Workspace should own the user-facing shot-planning entry point, but shot-plan rendering belongs in a new focused viewer/panel component rather than more code inside `ui/src/pages/SceneWorkspacePage.tsx` or `ui/src/components/ArtifactViewers.tsx`. Export selection remains owned by `ui/src/components/ExportModal.tsx`. If scope support is needed, keep it inside the existing shot-planning module and export router.
- **Data contracts**: Reuse the existing backend `ShotPlan` schema from Story 025 as the source of truth. If the UI needs stronger typing, add a TypeScript shape that mirrors `shot_plan` rather than passing stringly-typed dicts around. If a new execution/export scope parameter is needed, extend the existing typed run/export interfaces rather than inventing ad hoc query strings.
- **File sizes**: `ui/src/pages/SceneWorkspacePage.tsx` (658, over 500 - extraction required if touched), `ui/src/components/ArtifactViewers.tsx` (1187, over 500 - avoid adding inline viewer logic), `ui/src/pages/ArtifactDetail.tsx` (568, over 500 - keep changes surgical), `ui/src/components/ExportModal.tsx` (235), `ui/src/lib/api/exports.ts` (63), `ui/src/lib/artifact-meta.ts` (51). If backend scope support is added: `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` (1099, over 500 - isolate any change), `src/cine_forge/api/routers/export.py` (361), `src/cine_forge/pipeline/graph.py` (686, over 500 - touch only if discoverability absolutely requires it). `make check-size` already confirms these large-file risks.
- **Decision context**: Reviewed ADR-002 (goal-oriented navigation), ADR-003 (scene-first creative concerns), Story 025 (backend shot planning), Story 058 (backend-first export), Story 099 (Scene Workspace), Story 085 (pipeline graph), Story 101 (long-running action system), and `docs/design/ui-stack.md`. No separate ADR currently defines a dedicated shot-plan UI surface.

## Files to Modify

- `ui/src/pages/SceneWorkspacePage.tsx` — add or host the shot-planning entry point and extracted shot surface (658)
- `ui/src/components/ExportModal.tsx` — expose shot-list actions in the existing modal (235)
- `ui/src/lib/api/exports.ts` — add shot-list format wiring and any typed scope params (63)
- `ui/src/lib/artifact-meta.ts` — add `shot_plan` metadata entry (51)
- `ui/src/pages/ArtifactDetail.tsx` — route `shot_plan` to the dedicated viewer (568)
- `ui/src/components/ShotPlanViewer.tsx` or similar new focused component — readable shot-plan UI shared across surfaces (new)
- `ui/src/components/ShotPlanningPanel.tsx` or similar new focused component — extracted Scene Workspace shot-planning surface (new)
- `ui/src/lib/constants.ts` and/or `ui/src/lib/chat-messages.ts` — honest shot-planning run labels/copy in existing progress UI
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — dynamic-import-safe shot-planning response schema rebuild after runtime smoke exposed a driver-only failure (1099)
- `tests/unit/test_shot_planning_module.py` — regression coverage for dynamic-import-safe `shot_plan_v1` response schema loading
- `src/cine_forge/api/routers/export.py` — only if export scope or error-handling support must change for the UI (361)

## Redundancy / Removal Targets

- Raw JSON-only fallback behavior for `shot_plan` in the user-facing artifact flow
- Any hard-coded export format list in the UI that still omits shot-list formats after this lands
- Any one-off Scene Workspace shot-plan rendering logic that should become the shared viewer component instead

## Notes

This story exists because the product currently violates its own architecture:

- `docs/spec.md` says Film Lane runs on demand when the user enters Scene Workspace or explicitly requests generation.
- Story 099 explicitly scoped out "Generate scene", leaving no downstream shot-planning action in the scene-first workspace.
- Story 025 added the backend recipe and export routes, but `ui/src/lib/api/exports.ts` still only knows `markdown`, `pdf`, `call-sheet`, `fountain`, and `docx`.
- `ui/src/lib/artifact-meta.ts` has no `shot_plan` entry, and Artifact Detail falls back to `DefaultViewer`, so even discovered shot plans are not really readable.

The correct product move is to surface the existing headless capability through the real UI, not to build a second backend path or tell operators to hand-edit URLs.

## Plan

### Ideal Alignment and Eval-First Gate

- This story closes a direct product gap, not speculative infrastructure. Ideal `R8`, `R9`, and `R11`, plus spec `4.6`, `12.7`, and `13`, already require shot planning and shot-list exports to be usable from the real UI. Story 025 landed the backend artifact and export routes, but the operator path is still hidden behind raw artifact URLs and backend endpoints.
- Baseline from exploration:
  - `ui/src/pages/SceneWorkspacePage.tsx` has no downstream shot-planning surface.
  - `shot_plan` has no entry in `ui/src/lib/artifact-meta.ts` and falls through to `DefaultViewer` in `ui/src/pages/ArtifactDetail.tsx`.
  - `ui/src/components/ExportModal.tsx` and `ui/src/lib/api/exports.ts` do not expose shot-list formats.
  - The backend already exposes `/api/projects/{project_id}/export/shot-list.csv` and `/api/projects/{project_id}/export/shot-list.pdf`.
- Candidate approaches:
  - **AI-only / chat-only workaround:** reject. It bypasses the artifact store and export routes, violates ADR-002 discoverability, and creates an untestable shadow path.
  - **Hybrid with new scene-scope backend contract:** possible, but not the starting point. `RunStartPayload` has no scene-scope field, `configs/recipes/recipe-shot-planning.yaml` is project-wide, and adding scene filtering would force new contract work through `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` (1099 lines) for a UX problem that honest scope copy can solve.
  - **Pure code UI/plumbing over existing backend capability:** chosen. Reuse the project-wide `shot_planning` recipe and existing export routes, make the scope explicit in the UI, and let the existing run infrastructure refresh the current scene in place.
- No new model eval is expected. This is a UI/plumbing story. Success evidence is targeted UI checks, browser verification, and backend checks only if implementation expands into Python.

### Repo-Fit / Scope Choice

- Repo-specific evidence:
  - ADR-003 and spec note 1050 explicitly prefer **scene-first UX with shot detail as drill-down**, not a separate project-wide shots workspace.
  - ADR-002 requires capabilities to be discoverable from the real UI, not hidden behind undocumented routes or backend-only actions.
  - Story 099 made Scene Workspace the film-lane entry point. Story 101 standardized long-running run feedback around `useStartRun`, `useChatStore().setActiveRun`, `OperationBanner`, and `useRunProgressChat`.
  - `ui/src/components/AppShell.tsx` already refetches artifact groups while `activeRunId` is set, and `ui/src/lib/use-run-progress.ts` invalidates `['projects', projectId, 'artifacts']` during active runs. That means the current scene can stay mounted and reveal its `shot_plan` when the run finishes without new polling logic.
- Scope decision:
  - Start with the existing **project-wide** `shot_planning` recipe.
  - Make execution scope honest in the UI copy and CTA label, for example: "Run shot planning for all scenes" / "Refresh shot plans for all scenes."
  - Keep the user on the current scene page so the page resolves back to that scene's results when artifacts land.
  - Only add backend scope filtering if implementation proves the honest project-wide action still fails the acceptance criteria.
- Alternatives rejected:
  - A second client-side export path: duplicates Story 058's backend-first architecture.
  - A hidden direct fetch to shot-list routes without UI affordances: still leaves the operator guessing and does not handle the empty-state 404 honestly.

### Structural Health Check

- `make check-size` plus `wc -l` on likely touch points:
  - `ui/src/pages/SceneWorkspacePage.tsx` — **658 lines**. Over 500; extraction is required before adding new logic.
  - `ui/src/components/ArtifactViewers.tsx` — **1187 lines**. Over 500; do not add `shot_plan` viewer logic inline here.
  - `ui/src/pages/ArtifactDetail.tsx` — **568 lines**. Over 500; keep changes surgical: import the new viewer and add one switch case.
  - `ui/src/components/ExportModal.tsx` — **235 lines**. Safe to extend modestly.
  - `ui/src/lib/api/exports.ts` — **63 lines**. Safe to extend with typed shot-list routes.
  - `ui/src/lib/constants.ts` — **96 lines** and `ui/src/lib/chat-messages.ts` — **203 lines**. Safe places for honest shot-planning run labels/copy.
  - `src/cine_forge/api/routers/export.py` — **361 lines**. No change planned unless the UI cannot avoid the backend 404 cleanly.
- No new backend schema or event type is expected. Reuse the existing `ShotPlan` Pydantic schema from Story 025. If the UI needs stronger typing, add a small TypeScript mirror/helper rather than passing raw dictionaries between new components.
- Method-size risk:
  - `ConcernGroupTabContent` and `SceneWorkspacePage` in `ui/src/pages/SceneWorkspacePage.tsx` already carry too much responsibility. The first implementation step should be extraction, not another branch added inline.

### Implementation Order

1. **Shared shot-plan presentation**
   - Create a dedicated `ShotPlanViewer` component outside `ui/src/components/ArtifactViewers.tsx`.
   - Render a readable summary: coverage approach, adequacy verdict/rationale, shot count, estimated duration, and an ordered shot list with framing/movement, in-frame characters, blocking, action, dialogue, and edit intent.
   - Include the minimal navigation affordance needed to jump from the scene surface to artifact history/detail.

2. **Scene Workspace shot-planning surface**
   - Extract a focused shot-planning panel from `ui/src/pages/SceneWorkspacePage.tsx` and add a `Shots` tab or equivalent scene-first downstream surface.
   - Empty state: explain what shot planning does, state that the current recipe runs project-wide, and offer a primary CTA that uses `useStartRun` plus `useChatStore().setActiveRun`.
   - Running state: rely on the shared run infrastructure (`OperationBanner`, chat timeline, active-run query invalidation). No bespoke progress widgets or parallel polling.
   - Populated state: fetch the latest `shot_plan` artifact for the current scene and render it with the shared viewer. Because the page stays mounted, the current scene should reveal its results as soon as the active run finishes and artifact queries invalidate.

3. **First-class artifact wiring**
   - Add `shot_plan` to `ui/src/lib/artifact-meta.ts`.
   - Route `shot_plan` to the new viewer in `ui/src/pages/ArtifactDetail.tsx`.
   - Add any small discoverability cleanup needed on project surfaces only if implementation proves it is still hard to find (for example ordering/naming where `shot_plan` still renders as a raw type string).

4. **Export UI plumbing**
   - Extend `ui/src/lib/api/exports.ts` with typed shot-list formats that map to the existing backend CSV/PDF routes.
   - Extend `ui/src/components/ExportModal.tsx` to surface Shot List CSV / Shot List PDF with honest copy that these are project-wide exports built from current shot plans.
   - Use artifact-group data to disable those actions and explain the empty state in the modal instead of letting the user hit the backend 404.

5. **Run copy / label correctness**
   - Update the small UI metadata/copy points that would otherwise misdescribe the run (`RECIPE_NAMES`, stage descriptions, artifact naming/summary text as needed).
   - Done looks like: starting shot planning from Scene Workspace produces banner/chat/run-detail copy that talks about shot planning rather than generic screenplay breakdown.

6. **Verification**
   - Static UI checks: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`.
   - Backend checks only if Python changes become necessary: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`.
   - Browser verification plan:
     - Open a project scene route in Scene Workspace.
     - Trigger shot planning from the new `Shots` tab.
     - Wait for the active run to finish and confirm the current scene resolves to readable shot-plan content with no console errors.
     - Open Artifact Detail for the same `shot_plan` and confirm the dedicated viewer renders there too.
     - Open the export modal and download Shot List CSV/PDF.
   - If browser tooling fails, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.

### Files Expected to Change

- `ui/src/pages/SceneWorkspacePage.tsx` — host the extracted shot-planning entry point without adding more inline branching
- `ui/src/components/ShotPlanningPanel.tsx` or similar — new focused Scene Workspace surface
- `ui/src/components/ShotPlanViewer.tsx` — new reusable viewer
- `ui/src/pages/ArtifactDetail.tsx` — route `shot_plan` to the shared viewer
- `ui/src/components/ExportModal.tsx` — expose shot-list exports and empty-state handling
- `ui/src/lib/api/exports.ts` — typed shot-list route wiring
- `ui/src/lib/artifact-meta.ts` — first-class `shot_plan` metadata
- `ui/src/lib/constants.ts` and/or `ui/src/lib/chat-messages.ts` — honest shot-planning naming/copy in run progress UI
- `src/cine_forge/api/routers/export.py` — only if UI-side empty-state handling proves insufficient

### Risks / Redundancy Targets

- Main risk: adding shot-plan logic inline to `ui/src/pages/SceneWorkspacePage.tsx` or `ui/src/components/ArtifactViewers.tsx` would worsen the exact file-size problem the story already called out. Extraction is mandatory, not optional.
- Main repo-fit decision: do **not** add scene-scope backend filtering unless the honest project-wide CTA fails the acceptance criteria. The current codebase has no typed scene-scope run contract, and forcing one in now is extra complexity with weak evidence.
- Redundancy targets after implementation:
  - Raw JSON fallback behavior for `shot_plan` in user-facing artifact flows
  - Any export format lists that still omit shot-list formats
  - Any duplicate inline shot-plan rendering between Scene Workspace and Artifact Detail

## Work Log

20260313-1441 — story creation: traced the missing human-operability gap across Story 025, Story 058, Story 099, ADR-002, ADR-003, and the current UI files. Confirmed there is still no UI trigger, no readable `shot_plan` viewer, and no export-modal support for shot lists. Next step: `/build-story` on this story.
20260313-1449 — validation: reviewed story structure against create-story requirements, `ideal.md`, `spec.md`, ADR-002, and ADR-003. Story is implementation-ready and aligned to the missing product gap. Environment-level checks were attempted but blocked in this worktree because `.venv/bin/python` is absent and `ui/node_modules` is not installed, so repo-wide test/lint evidence is unavailable from this validation pass. Next step: `/build-story` for Story 132; re-run repo checks in a provisioned environment during implementation/validation of the actual code change.
20260313-1549 — exploration: read `docs/ideal.md`, ADR-002, ADR-003, spec `4.6`, `12.7`, `13`, `13.4`, and dependency stories 025, 058, 099, and 101. Traced the current UI/run/export path through `SceneWorkspacePage.tsx`, `ArtifactDetail.tsx`, `ExportModal.tsx`, `ui/src/lib/api/exports.ts`, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/chat-messages.ts`, and `recipe-shot-planning.yaml`. Confirmed the backend already has project-wide shot-planning runs plus shot-list CSV/PDF routes, but the UI lacks a shot surface, metadata, viewer, format wiring, and correct run copy. Next step: write the implementation plan and present the scope choice for approval.
20260313-1553 — structural-health-check: ran `make check-size` and captured exact file sizes for the likely touch points. Key risk confirmed: `ui/src/pages/SceneWorkspacePage.tsx` (658), `ui/src/components/ArtifactViewers.tsx` (1187), and `ui/src/pages/ArtifactDetail.tsx` (568) are already over the large-file threshold, so implementation must extract a focused shot-planning component and keep Artifact Detail changes surgical. Chosen starting scope: reuse the existing project-wide `shot_planning` recipe with explicit UI copy instead of inventing a new scene-scope backend contract. Next step: human approval before implementation.
20260313-1604 — implementation: extracted `ui/src/components/ShotPlanningPanel.tsx` and `ui/src/components/ShotPlanViewer.tsx`, wired the new `Shots` tab into `ui/src/pages/SceneWorkspacePage.tsx`, routed `shot_plan` through `ui/src/pages/ArtifactDetail.tsx`, added `shot_plan` metadata, extended export typing/modal copy for Shot List CSV/PDF, and fixed run-copy/summary text in `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and `ui/src/lib/use-run-progress.ts`. Scope stayed project-wide and honest: CTA labels now say "Run/Refresh Shot Plans for All Scenes" rather than implying scene-scoped execution. Next step: static verification plus runtime smoke on a disposable project.
20260313-1611 — runtime-debugging: the first browser smoke against `127.0.0.1:8000` was invalid because that backend was serving `/Users/cam/Documents/Projects/cine-forge`, not this worktree. Started branch-local backend/UI on `http://127.0.0.1:8001` and `http://127.0.0.1:5175`, seeded disposable verification projects, and traced the remaining driver-only failure to `shot_plan_v1` dynamic imports: `_ScenePlanResponse` needed an explicit `model_rebuild()` under the real `DriverEngine` module loader. Added the rebuild plus regression coverage in `tests/unit/test_shot_planning_module.py`; targeted unit tests then passed and a direct `DriverEngine` shot-planning run completed successfully in 107s on the seeded project. Next step: rerun the operator path through the branch-local UI.
20260313-1616 — verification: static UI checks passed (`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`) with only pre-existing `react-refresh/only-export-components` warnings. Backend lint passed via `python -m ruff check src/ tests/`. `make test-unit PYTHON=python` ran because `.venv` is absent here and surfaced 1 unrelated existing ingest fixture failure in `tests/unit/test_story_ingest_module.py::test_read_source_text_fixture_matrix_has_sane_extraction[patent_registering_votes_us272011_scan_5p.pdf-pdf-APPARATUS FOR REGISTERING]`; Story 132 targeted tests still passed. Browser smoke on the clean disposable project `story-132-shot-plan-ui-clean` confirmed the full operator path on the branch-local stack: opened `http://127.0.0.1:5175/story-132-shot-plan-ui-clean/scenes/scene_001`, used the `Shots` tab empty state to start `shot_planning`, observed the shared long-running banner/chat state, waited for UI-triggered run `run-25a6a571` to complete successfully (`shot_plan`, `timeline`, `track_manifest` artifacts saved), verified the populated shot-plan viewer in Scene Workspace, opened Artifact Detail and confirmed the dedicated viewer rendered there too, then downloaded both `story-132-shot-plan-ui-clean-shot-list.csv` (6435 bytes) and `story-132-shot-plan-ui-clean-shot-list.pdf` (7446 bytes) from the export modal with no browser console errors. Next step: `/validate`.
20260313-1628 — validation: reran the required local checks on the current diff: `PYTHONPATH=src:. python -m pytest tests/unit/test_shot_planning_module.py -q`, `python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed, with the same pre-existing fast-refresh warnings in shared UI files and the same unrelated repo-wide ingest fixture failure still present when using `make test-unit PYTHON=python` because `.venv` is absent in this worktree. Fresh browser validation on the branch-local stack reloaded `http://127.0.0.1:5175/story-132-shot-plan-ui-clean/scenes/scene_001`, confirmed the populated `Shots` tab, reopened the export modal, and downloaded `story-132-shot-plan-ui-clean-shot-list.csv` again with zero browser console errors. Validation outcome: Story 132 is clean relative to its scoped changes and ready for `/mark-story-done`, with the unrelated ingest-suite failure remaining outside this story.
20260313-1635 — follow-up fix: resolved the previously unrelated ingest-suite blocker by normalizing whitespace-heavy `pdfplumber(layout=True)` output in `story_ingest_v1` before returning it. Added regression coverage in `tests/unit/test_story_ingest_module.py` for whitespace-inflated scanned PDF layout output. Verification: `PYTHONPATH=src:. python -m pytest tests/unit/test_story_ingest_module.py -q`, `python -m ruff check src/ tests/`, and `make test-unit PYTHON=python` now all pass; repo-wide unit status is green again (`519 passed, 118 deselected`).
20260313-1639 — validation rerun: repeated the full validate pass on the current diff. `.venv/bin/python` is still unavailable in this worktree, so the mandated `.venv` commands were explicitly rechecked and reported unavailable before rerunning fallbacks: `python -m ruff check src/ tests/`, `make test-unit PYTHON=python`, `PYTHONPATH=src:. python -m pytest tests/unit/test_shot_planning_module.py -q`, `PYTHONPATH=src:. python -m pytest tests/unit/test_story_ingest_module.py -q`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed. Fresh browser verification on `http://127.0.0.1:5175/story-132-shot-plan-ui-clean/scenes/scene_001` reconfirmed the populated `Shots` tab, the export modal shot-list actions, a successful `story-132-shot-plan-ui-clean-shot-list.csv` download, and zero browser console errors. Validation outcome: no scoped findings remain; Story 132 is ready for `/mark-story-done`.
20260313-1642 — story closure: marked Story 132 `Done`, checked the completion gate, updated the story index, and added the changelog entry. Closure evidence remains: backend/unit checks green via fallback commands (`519 passed, 118 deselected`), targeted shot-planning and ingest regressions green, UI lint/type/build green, and browser verification green on the branch-local stack with successful shot-list export download and zero console errors. Next step: `/check-in-diff`.
