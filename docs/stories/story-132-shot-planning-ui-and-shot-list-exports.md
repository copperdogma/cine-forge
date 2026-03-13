# Story 132 — Shot Planning UI and Shot List Exports

**Priority**: High
**Status**: Pending
**Ideal Refs**: R9 (professional exports), R11 (production readiness per scene), R7 (iterative refinement)
**Spec Refs**: 4.6 (Film Lane on demand), 12.7 (Readiness Indicators), 13 (Shot Planning), 13.4 (Export Compatibility), note 1050 (scene-first with shot detail drill-down)
**ADR Refs**: `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/decisions/adr-003-film-elements/adr.md`
**Depends On**: Story 025 (Shot Planning), Story 058 (Comprehensive Export & Share), Story 099 (Scene Workspace), Story 101 (Centralized Long-Running Action System)

## Goal

Make shot planning usable by a human operator. Story 025 landed the backend artifact, run recipe, and export endpoints, but CineForge still has no UI surface that lets a user intentionally run shot planning, inspect a readable shot plan, or discover the shot-list exports without guessing URLs. This story closes that product gap by adding a scene-first shot-planning surface in Scene Workspace, wiring shot-list exports into the existing export UI, and making `shot_plan` artifacts first-class instead of raw JSON.

## Acceptance Criteria

- [ ] Scene Workspace exposes an explicit downstream shot-planning surface for the current scene. If no `shot_plan` exists, the empty state explains what shot planning does and offers a primary action to run it. If a `shot_plan` exists, the UI renders a readable summary and ordered shot list instead of raw JSON.
- [ ] The shot-planning action launches the existing run infrastructure, makes execution scope honest before the run starts, and returns the user to the current scene's results when the run finishes. No bespoke polling, hidden backend calls, or parallel progress UI are introduced.
- [ ] `shot_plan` artifacts become first-class in the UI: `ui/src/lib/artifact-meta.ts` has a labeled entry, Artifact Detail uses a dedicated viewer, and the scene/project surfaces no longer force users through a generic JSON fallback.
- [ ] The existing export UI exposes Shot List CSV and Shot List PDF by calling the backend export routes. If no shot plans exist yet, the UI handles that state directly with disabled actions or clear explanatory copy instead of sending the user to a backend `404`.
- [ ] Browser verification covers the operator path end to end: open a scene, start shot planning, inspect the resulting shot plan in the UI, and download the shot-list export with no browser console errors.

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

- [ ] Decide the minimum honest execution scope for the Scene Workspace action: reuse the existing project-level `shot_planning` recipe as-is, or add the smallest typed scope filter needed so the UI does not misrepresent what will run.
- [ ] Extract a focused shot-planning surface out of `ui/src/pages/SceneWorkspacePage.tsx` and add a downstream `Shots` tab or equivalent scene-first surface that can show empty, running, and populated states.
- [ ] Create a dedicated `shot_plan` viewer component and reuse it from both Scene Workspace and Artifact Detail. Do not leave `shot_plan` as a raw-JSON-only artifact type.
- [ ] Extend the existing export UI plumbing (`ui/src/components/ExportModal.tsx` and `ui/src/lib/api/exports.ts`) to expose Shot List CSV and Shot List PDF with clear empty-state handling.
- [ ] Add the minimum discoverability wiring needed so users can find shot planning from existing scene/project surfaces without guessing: artifact metadata, readable labels, and any small navigation affordance required by the chosen UI.
- [ ] If execution or export scope needs backend support, add the smallest typed contract in the existing shot-planning/export path rather than inventing a UI-only side channel.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

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
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — only if scope filtering is required for honest Scene Workspace execution (1099)
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

To be written by `/build-story` after implementation planning, scope-choice confirmation, and file-level extraction plan.

## Work Log

20260313-1441 — story creation: traced the missing human-operability gap across Story 025, Story 058, Story 099, ADR-002, ADR-003, and the current UI files. Confirmed there is still no UI trigger, no readable `shot_plan` viewer, and no export-modal support for shot lists. Next step: `/build-story` on this story.
20260313-1449 — validation: reviewed story structure against create-story requirements, `ideal.md`, `spec.md`, ADR-002, and ADR-003. Story is implementation-ready and aligned to the missing product gap. Environment-level checks were attempted but blocked in this worktree because `.venv/bin/python` is absent and `ui/node_modules` is not installed, so repo-wide test/lint evidence is unavailable from this validation pass. Next step: `/build-story` for Story 132; re-run repo checks in a provisioned environment during implementation/validation of the actual code change.
