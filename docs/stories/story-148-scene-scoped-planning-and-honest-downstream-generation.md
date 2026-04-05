---
id: "148"
title: "Scene-Scoped Planning and Honest Downstream Generation"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness per scene), R12 (transparency & control)"
spec_refs:
  - "spec:2.6"
  - "spec:5.5"
  - "spec:6.1"
  - "spec:6.2"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "025"
  - "028"
  - "099"
  - "132"
  - "143"
  - "144"
category_refs:
  - "spec:2"
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "creative_direction_and_chat"
  - "generation_and_visualization"
roadmap_tags:
  - "scene-scoped"
  - "quick-path"
legacy_system: ""
---

# Story 148 — Scene-Scoped Planning and Honest Downstream Generation

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness per scene), R12 (transparency & control)
**Spec Refs**: spec:2.6 (Two-Lane Architecture), spec:5.5 (Readiness Indicators), spec:6.1 (Shot Planning), spec:6.2 (Storyboards), spec:6.3 (Animatics / Previz Video), spec:7.1 (Render Adapter Layer), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace)
**Depends On**: Story 025 (Shot Planning), Story 028 (Render Adapter), Story 099 (Scene Workspace), Story 132 (Shot Planning UI), Story 143 (AI-Generated Low-Fidelity Previz), Story 144 (AI Previz Adoption Gate and Trust Guardrails)

## Goal

Make Scene Workspace honest about scope and prerequisites. Today CineForge looks scene-first but most planning and generation actions still run project-wide, and the operator can get trapped behind missing optional direction work or confusing downstream UI. This story adds explicit scene-scoped execution for concern-group planning and downstream film-lane actions, replaces hard blockers with preflight warnings where output is still meaningful, and collapses previz into one coherent scene-level surface so a user can take a single scene from script breakdown to shots, storyboard, previz, and render without pretending the whole project is ready.

## Acceptance Criteria

- [x] Scene Workspace actions for concern-group generation, shot planning, storyboard generation, deterministic previz, AI previz, and final render expose honest scope. The operator can choose `Current scene` or `All scenes` wherever the substrate supports both, and the UI/run metadata clearly states which scope ran.
- [x] A freshly broken-down project can open a scene and run downstream planning or generation without completing every direction slice first. Missing optional guidance is surfaced as preflight warnings with explicit quality tradeoffs, not fake prerequisites or dead-end disabled states.
- [x] Downstream scene-scoped runs build only the minimum required prerequisites for the selected scene when possible, and every auto-built placeholder or inferred upstream dependency is clearly marked. No silent project-wide side effects are triggered from a scene action.
- [x] The Scene Workspace `Previz` tab becomes a single scene-level panel with shared status, preflight, and scope controls. Deterministic and AI lanes remain visible inside that surface, but the UI no longer renders a third competing empty-state panel that duplicates or contradicts the lane cards.
- [x] Headless operation remains first-class: the API/runtime contract supports scene-scoped execution without UI-only hacks, and run state / events persist enough scope and prerequisite context for CLI or backend consumers to reason about what happened.
- [x] Browser verification covers the changed Scene Workspace flows in both desktop and mobile views, including the Direction phase details affordance, scope selection, preflight messaging, and the consolidated previz panel, with clean browser console output.

## Out of Scope

- Film-level assembly/export orchestration across multiple scenes
- New provider research, model benchmarking, or quality-tuning work for storyboard/previz/render output itself beyond what is necessary to make scope and prerequisites honest
- Implementing Character & Performance or Story World generation if those capabilities remain unshipped; this story is about making their absence non-blocking, not silently inventing them
- Replacing the project-wide run modes entirely; `All scenes` remains valid and discoverable

## Approach Evaluation

- **Simplification baseline**: A single LLM call can already generate one scene's concern-group guidance, shot plan, storyboard prompt, or render prompt from existing scene context. The missing value is not new reasoning capability; it is typed scope control, prerequisite handling, and honest UI/operator feedback.
- **AI-only**: Wrong fit for the main problem. A model can decide what is missing, but it should not own scope contracts, run orchestration, or whether a project-wide side effect is allowed from a scene action.
- **Hybrid**: Strong candidate. Use deterministic scope + prerequisite computation with AI still producing the scene artifacts. This lets the system warn honestly, auto-build minimal prerequisites when appropriate, and keep every inferred step transparent.
- **Pure code**: Plausible for the scope/preflight layer itself. The story is mostly orchestration, recipe wiring, artifact-health semantics, and UI flow cleanup over existing AI modules.
- **Repo constraints / ADRs**: ADR-002 explicitly says users must be able to trigger downstream work with proceed/warn/soft-block behavior rather than hidden hard gates, and it specifically calls out the need to diagnose missing upstream context instead of trapping the operator. ADR-003 makes Scene Workspace scene-first and says concern groups are navigational aids, not mandatory pipeline gates. The spec's depth-first path (`spec.md:842`) and Always-Playable Rule (`spec:10.3`) both push toward "take one scene farther now" instead of "finish the whole project first."
- **Existing patterns to reuse**: `useStartRun`, `useChatStore().setActiveRun`, the current Scene Workspace panels, `recipe-*generation.yaml` wiring, `run_orchestrator.py`, the pipeline graph/preflight substrate, and Story 143's existing previz lane components. Reuse them; do not create a second scene-action framework.
- **Eval**: This is primarily a product/orchestration story. Success is distinguished by typed scope contracts, targeted backend tests for scoped execution, targeted unit/integration tests for prerequisite behavior, and browser verification of the scene workspace flows on desktop and mobile. If implementation changes AI behavior materially, build-story should identify the narrow eval to rerun rather than assuming none is needed.

## Tasks

- [x] Add a typed scene-scope contract to run start/orchestration so backend, run state, and UI agree on `Current scene` vs `All scenes`.
- [x] Implement scene-scoped execution for the existing planning/generation path where it is currently project-wide only: concern-group direction runs, shot planning, storyboard generation, deterministic previz, AI previz, and final render.
- [x] Fold the tightly coupled sidecars into that scope work so `Current scene` does not secretly fan back out:
  - [x] keyframe extraction for deterministic previz
  - [x] media validation for AI previz / final render
  - [x] lightweight project-summary artifacts (`*_index`, `previz_reel`) that would otherwise be clobbered by partial reruns
- [x] Build a shared prerequisite/preflight seam for scene actions that distinguishes:
  - [x] optional upstream guidance that should warn
  - [x] minimum required substrate that can be auto-built for the selected scene
  - [x] truly meaningless requests that deserve a soft block
  - [x] a typed backend contract the UI and headless callers can share before starting a run
- [x] Consolidate the `Previz` tab into one panel with lane-internal states and remove the competing third empty-state panel.
- [x] Update Scene Workspace action copy, run-detail copy, and progress metadata so scene-scoped runs are labeled honestly and project-wide runs remain explicit.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

- **Owning class/module**: Scene-scoped execution should stay centered on the existing run orchestration and Scene Workspace panels. Do not introduce a second action runner or a UI-only scope abstraction.
- **Data contracts**: The scene-scope request/response data crossing UI -> API -> run state must be typed before implementation. A stringly typed `config_overrides` blob is not sufficient for a project-wide behavior change like execution scope.
- **File sizes**: Current likely touch points are already large and need disciplined integration:
  - `src/cine_forge/api/models.py` — `495`
  - `src/cine_forge/api/run_orchestrator.py` — `640`
  - `src/cine_forge/pipeline/graph.py` — `722`
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — `1104`
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1532`
  - `ui/src/components/PrevizPanel.tsx` — `528`
  - `ui/src/pages/SceneWorkspacePage.tsx` — `808`
  - `ui/src/lib/types.ts` — `640`
  Extraction or helper-first work may be necessary before adding more branching.
- **Decision context**: Reviewed ADR-002 and ADR-003 while drafting. They both push toward scene-first work with warnings and explicit tradeoffs, not project-wide gating from hidden assumptions.

## Files to Modify

- `src/cine_forge/schemas/runtime_params.py` — typed scene-execution scope carried through the engine (`52`)
- `src/cine_forge/api/models.py` — typed run-scope and preflight request/response contracts (`495`)
- `src/cine_forge/api/run_orchestrator.py` — persist scene scope and prerequisite context in run state/runtime params (`640`)
- `src/cine_forge/api/service.py` — expose shared scene-action preflight / start-run helpers without UI-only logic (`1103`)
- `src/cine_forge/api/routers/scene_actions.py` — new focused route surface for scene-action preflight and headless consumers (`new`)
- `src/cine_forge/driver/engine.py` — scope-aware `store_inputs_all` filtering and run-state/event persistence (`1351`)
- `src/cine_forge/pipeline/scene_actions.py` — new focused prerequisite/preflight helper instead of widening `pipeline/graph.py` (`new`)
- `src/cine_forge/modules/creative_direction/editorial_direction_v1/main.py` — scoped `Rhythm & Flow` generation plus honest index rebuild (`490`)
- `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` — scoped `Look & Feel` generation plus honest index rebuild (`646`)
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — scoped `Sound & Music` generation plus honest index rebuild (`616`)
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — honor scene scope and keep timeline/track side effects honest (`1104`)
- `src/cine_forge/modules/visualization/storyboard_v1/main.py` — scoped storyboard generation (`240`)
- `src/cine_forge/modules/visualization/animatic_v1/main.py` — scoped deterministic previz generation plus honest project-reel rebuild (`499`)
- `src/cine_forge/modules/visualization/keyframe_v1/main.py` — keep deterministic previz keyframes aligned to selected scenes (`332`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — scoped AI previz / final render generation plus targeted track updates (`1532`)
- `src/cine_forge/modules/qa/media_validation_v1/main.py` — validate only the selected scene outputs for scoped runs (`242`)
- `configs/recipes/recipe-creative-direction.yaml` — scope/preflight wiring for concern-group runs (`55`)
- `configs/recipes/recipe-shot-planning.yaml` — scope/preflight wiring (`40`)
- `configs/recipes/recipe-storyboard-generation.yaml` — scope/preflight wiring (`54`)
- `configs/recipes/recipe-animatics-generation.yaml` — scope/preflight wiring (`75`)
- `configs/recipes/recipe-ai-previz-generation.yaml` — scope/preflight wiring (`74`)
- `configs/recipes/recipe-render-generation.yaml` — scope/preflight wiring (`65`)
- `ui/src/pages/SceneWorkspacePage.tsx` — scene-action affordances and thinner concern-group wiring only (`808`)
- `ui/src/components/ShotPlanningPanel.tsx` — scene vs project scope controls and preflight copy (`290`)
- `ui/src/components/StoryboardPanel.tsx` — scene vs project scope controls and preflight copy (`277`)
- `ui/src/components/PrevizPanel.tsx` — single-panel previz surface with shared status, scope, and lane-internal states (`528`)
- `ui/src/components/GeneratedVideoPanel.tsx` — render scope / preflight flow (`338`)
- `ui/src/components/PreflightCard.tsx` or a new shared scene-action preflight component — reuse or refactor instead of duplicating warning UI (`58`)
- `ui/src/lib/types.ts` — typed scope and preflight contracts (`640`)
- `ui/src/lib/api/runs.ts` — send the new scope contract (`69`)
- `ui/src/lib/api/scene-actions.ts` — new typed client for shared preflight lookups (`new`)
- `ui/src/lib/hooks.ts` — shared hook for scene-action preflight / scope state (`new or small extension`)
- `ui/src/pages/RunDetail.tsx` — render explicit scope / prerequisite metadata for completed and running runs (`522`)
- `ui/src/lib/use-run-progress.ts` — progress copy and chat metadata for scoped runs (`567`)
- `ui/src/lib/constants.ts` — honest scoped recipe labels / stage wording (`192`)

## Redundancy / Removal Targets

- Hard-coded `Runs for all scenes` copy on scene-level planning/generation surfaces when scene scope becomes real
- Any duplicate empty-state UI in `PrevizPanel` that competes with the deterministic and AI lane cards
- Any project-wide-only run labels or helper text that become misleading once scope is explicit
- Any UI-only prerequisite heuristics that become redundant after a shared backend preflight contract lands

## Notes

- This story is the concrete expression of the "depth-first / sizzle reel" path in the spec. A user should be able to take one scene farther without pretending they have already authored every upstream decision across the project.
- Story 132 and Story 143 intentionally shipped honest project-wide actions at the time. This story is not churn for churn's sake; it is the next product surface after that substrate proved out.
- Real-world failure evidence already exists:
  - scene routes showed project-wide-only action language even inside Scene Workspace
  - `run-730f1fd8` failed in the AI-previz path after building shot plans, which exposed how fragile the current prerequisite/orchestration path still is
  - the current `Previz` tab presents two lane cards plus a third scene-level empty state, which is visually redundant and easy to misread
- Character & Performance and Story World remain important, but their absence should not keep an operator from running shots, storyboard, previz, or render for one scene when the output is still meaningful with warnings.

## Plan

### Eval / Baseline Gate

- This is primarily orchestration, contract, and UI work over already-proven AI modules. The gating eval is scoped-run correctness, not prompt quality or model benchmarking.
- Baseline evidence from exploration:
  - `RunStartRequest`, `RunStartPayload`, and `RuntimeParams` currently have no typed scene-scope field.
  - `SceneWorkspacePage` and the downstream scene panels all start project-wide recipes today. Concern-group runs narrow by stage id only (`start_from` / `end_at`), not by scene id.
  - `editorial_direction_v1`, `look_and_feel_v1`, `sound_and_music_v1`, `shot_plan_v1`, `storyboard_v1`, `animatic_v1`, `keyframe_v1`, and `render_adapter_v1` all iterate every scene or shot plan they receive.
  - `media_validation_v1` validates every latest video artifact loaded via `store_inputs_all`, so a scene-scoped render would still fan back out unless scope reaches the engine or validation inputs.
  - Live operator evidence overturned Story 132's earlier "honest project-wide CTA is enough" choice: the scene routes now need real current-scene execution, not just copy, because the user is trying to push one scene forward and the current substrate still reruns unrelated work.
  - Failure evidence already exists (`run-730f1fd8`), and fresh evidence (`run-1354a2b6`) proves the pipeline is close enough that scope/prerequisite honesty is now the main gap rather than missing substrate.
- Success measures to add first in implementation:
  - API / schema tests proving `Current scene` vs `All scenes` survives UI -> API -> runtime params -> run state.
  - Backend unit/integration tests proving current-scene runs only regenerate the targeted scene artifacts, only replace the targeted timeline / track rows, and do not validate unrelated scenes.
  - Browser verification in desktop and mobile views for scope selection, preflight messaging, direction hover/tap details, consolidated previz, and clean console output.

### Approach Choice

- **AI-only:** rejected. The gap is not "can a model reason about one scene"; the gap is deterministic execution scope, prerequisite policy, and honest operator metadata.
- **UI-only / copy-only:** rejected. Story 132 intentionally chose that earlier, but real operator use has now disproved it. The current Scene Workspace looks scene-first while the runtime still behaves project-wide.
- **Engine-only filtering:** rejected as the sole answer. Filtering `store_inputs_all` helps, but it does not solve project-level containers like `scene_index`, `timeline`, `track_manifest`, concern-group indexes, or `previz_reel`.
- **Chosen approach: typed scope contract + shared preflight + stage-aware scoped execution.**
  - Add a first-class typed scene-scope contract to the request/runtime path.
  - Add a focused scene-action preflight helper/API so warnings and soft blocks are shared instead of duplicated across panels.
  - Use engine-level filtering for entity-scoped `store_inputs_all` where safe.
  - Use module-level helpers for project-level containers and derived summary artifacts, so current-scene runs only regenerate selected heavy artifacts while still rebuilding lightweight project summaries honestly from the latest stored mix.

### Repo-Fit / Optimality Evidence

- ADR-002 requires proceed / warn / soft-block behavior instead of hidden hard gates. A shared preflight seam directly matches that decision; duplicated panel-local heuristics do not.
- ADR-003 makes Scene Workspace scene-first and treats concern groups as navigational aids, not mandatory project-wide gates. Real current-scene execution aligns with that; project-wide reruns from a scene tab do not.
- Spec `5.5`, `6.1`, `6.2`, `6.3`, `7.1`, and `10.3` all point toward "push one scene farther now, with clear tradeoffs." This story is the direct productization of that rule, not speculative infrastructure.
- Existing modules already update project-level timeline / track-manifest entries by replacing only the scene ids present in the current batch. That means scoped execution fits the repo naturally if the input batch is filtered correctly.
- The only places where scoped reruns would still lie are the derived project summaries (`*_index`, `previz_reel`) and validation sidecars. Folding those into this story is the smallest coherent expansion; leaving them out would create partial reruns that still clobber or revalidate unrelated scenes.

### Structural Health Check

- `make check-size` confirms this story touches several already-large files:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1532`
  - `src/cine_forge/driver/engine.py` — `1351`
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — `1104`
  - `src/cine_forge/api/service.py` — `1103`
  - `ui/src/pages/SceneWorkspacePage.tsx` — `808`
  - `src/cine_forge/api/app.py` — `727`
  - `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` — `646`
  - `src/cine_forge/api/run_orchestrator.py` — `640`
  - `ui/src/lib/types.ts` — `640`
  - `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — `616`
  - `ui/src/lib/use-run-progress.ts` — `567`
  - `ui/src/components/PrevizPanel.tsx` — `528`
  - `ui/src/pages/RunDetail.tsx` — `522`
- Plan consequence:
  - Do not widen `pipeline/graph.py`; extract scene-action preflight to a focused file.
  - Do not add more inline branching to `SceneWorkspacePage.tsx`; keep it as a thin host and move reusable scene-action controls/preflight UI into focused components/hooks.
  - Keep new inter-layer data typed before use. The scene-scope contract must be schema-first, not buried in `config_overrides`.

### Implementation Order

1. **Schema-first scope contract**
   - Files: `src/cine_forge/schemas/runtime_params.py`, `src/cine_forge/api/models.py`, `src/cine_forge/api/run_orchestrator.py`, `src/cine_forge/api/service.py`, `ui/src/lib/types.ts`, `ui/src/lib/api/runs.ts`.
   - Change: add a typed `Current scene` / `All scenes` contract, thread it into runtime params, and persist it into `run_state.json` so backend and UI agree on what a run targeted.
   - Done looks like: direct API calls can start scoped runs without UI-only hacks, and run state visibly records the chosen scope plus selected scene ids.

2. **Shared preflight seam**
   - Files: `src/cine_forge/pipeline/scene_actions.py` (new), `src/cine_forge/api/routers/scene_actions.py` (new), `src/cine_forge/api/service.py`, `ui/src/lib/api/scene-actions.ts` (new), `ui/src/lib/hooks.ts`, `ui/src/components/PreflightCard.tsx` or a new shared scene-action preflight component.
   - Change: add a typed preflight contract that classifies optional guidance warnings, minimum substrate that can be auto-built, and true soft blocks. Reuse it across scene actions instead of panel-specific heuristics.
   - Done looks like: the same scope/prerequisite explanation is available to the Scene Workspace UI and to headless callers before a run starts.

3. **Scene-scoped concern-group runs**
   - Files: `configs/recipes/recipe-creative-direction.yaml`, `src/cine_forge/modules/creative_direction/editorial_direction_v1/main.py`, `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py`, `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py`, `ui/src/pages/SceneWorkspacePage.tsx`.
   - Change: current-scene concern-group runs should analyze only the selected scene, keep placeholders (`Performance`, `Story World`) explicitly non-blocking, and rebuild the lightweight project index from the latest stored per-scene mix instead of overwriting it with a partial index.
   - Done looks like: running `Look & Feel` from a scene produces one scene artifact plus an honest project-level index view, without regenerating unrelated scenes.

4. **Scene-scoped downstream planning and generation**
   - Files: `src/cine_forge/driver/engine.py`, `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `src/cine_forge/modules/visualization/storyboard_v1/main.py`, `src/cine_forge/modules/visualization/animatic_v1/main.py`, `src/cine_forge/modules/visualization/keyframe_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/qa/media_validation_v1/main.py`, plus the five downstream recipe files.
   - Change:
     - filter entity-scoped `store_inputs_all` collections at the engine boundary when a run is scene-scoped
     - filter project-level scene containers inside the relevant modules
     - keep `timeline` / `track_manifest` updates targeted to selected scene ids only
     - rebuild `previz_reel` from the latest stored animatic mix so project assembly remains honest without rerendering unrelated scenes
     - validate only the selected scene outputs for scoped AI-previz/render runs
   - Done looks like: `Current scene` shots/storyboard/previz/render only regenerate the targeted scene's heavy artifacts, while assembly-side summaries stay honest and unrelated scenes are untouched.

5. **UI consolidation and honest run metadata**
   - Files: `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/components/ShotPlanningPanel.tsx`, `ui/src/components/StoryboardPanel.tsx`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/pages/RunDetail.tsx`, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/constants.ts`.
   - Change:
     - add shared scope controls and preflight UI to direction, shots, storyboard, previz, and render
     - collapse previz into one panel with lane-internal states and a single empty state
     - remove hard-coded `Runs for all scenes` language where scope is now selectable
     - surface explicit scope and prerequisite notes in toasts, banners, progress cards, and run detail
   - Done looks like: the operator can choose `Current scene` or `All scenes`, sees the same warning semantics everywhere, and the previz tab reads as one coherent surface instead of three competing panels.

6. **Verification and cleanup**
   - Tests likely affected: add targeted backend coverage around scope persistence, scoped module filtering, and validation fan-out; keep existing shot-planning integration coverage updated for the selected-scene path.
   - Static checks: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`.
   - Runtime / browser checks:
     - Desktop: Scene Workspace route such as `/{projectId}/scenes/{sceneId}`, hover the top `Direction` phase details, run one concern-group action as `Current scene`, then run shots/previz/render with warning states visible.
     - Mobile: same route in a narrow viewport, tap `Direction` for the sheet, confirm scope selection and the consolidated previz panel remain usable.
     - Check browser console output in both views.
     - Headless: `POST /api/runs/start` directly with the typed scope payload to prove the contract is not UI-only.
   - Redundancy pass:
     - remove panel-local duplicated prerequisite heuristics that the shared preflight seam replaces
     - remove the duplicate third previz empty state
     - remove stale copy that still implies every scene run is project-wide

### Human Approval Blockers / Scope Adjustments

- **Public API change:** `/api/runs/start` gains a typed scene-scope field, and this plan likely adds a new scene-action preflight route. There is no compatibility requirement in this repo, so the plan is to change the contract directly rather than shim it.
- **Scope expansion folded into this story:** keyframe extraction, media validation, concern-group project indexes, and `previz_reel` updates are now explicitly in scope. This is a tightly coupled expansion, not a separate story, because otherwise `Current scene` would still fan back out or overwrite misleading project summaries.
- **Relative effort:** `L`. The blast radius is real, but it is still one coherent subsystem: scene-first execution and honest downstream generation from Scene Workspace.

## Work Log

20260404-2125 — story creation: added a build-ready story for scene-scoped planning and downstream generation after validating that the current gap is orchestration/product semantics rather than missing substrate. Evidence: Scene Workspace actions still run project-wide in several panels, the user-reported `run-730f1fd8` exposed fragile previz prerequisites, and ADR-002/ADR-003 both support warn-not-block scene-first flow. Next step: `/build-story 148`.
20260404-2137 — exploration: read `docs/ideal.md`, spec refs (`spec:2.6`, `5.5`, `6.1`, `6.2`, `6.3`, `7.1`, `10.3`), `docs/methodology/state.yaml`, ADR-002, ADR-003, and dependency stories 025 / 028 / 099 / 132 / 143 / 144. Traced the current code path through `SceneWorkspacePage`, all four downstream scene panels, `RunStartRequest` / `RuntimeParams` / `run_orchestrator`, `driver/engine.py`, the creative-direction modules, `shot_plan_v1`, `storyboard_v1`, `animatic_v1`, `keyframe_v1`, `render_adapter_v1`, `media_validation_v1`, and the five downstream recipes. Confirmed the real gap is now typed scope + shared preflight + stage-aware partial updates: scene tabs still launch project-wide recipes, there is no first-class scene-scope contract, derived sidecars (`keyframe`, `media_validation`, `*_index`, `previz_reel`) would still fan back out or clobber summaries, and Story 132's earlier project-wide-only scope choice is no longer sufficient after live operator testing. Evidence checked: source code, `make check-size`, historical `run-730f1fd8`, and fresh `run-1354a2b6` crossing the old AI-previz failure boundary. Next step: present the approval-gated implementation plan before writing code.
20260404-2228 — implementation: landed the typed scene-scope contract and shared scene-action preflight path end to end across API, runtime params, orchestrator, engine filtering, generation modules, and Scene Workspace. Added `scene_scope.py`, the `/api/scene-actions/preflight` router, `pipeline/scene_actions.py`, scene-aware runtime typing in both backend and UI, and a shared `SceneActionControls` surface so concern-group runs plus shots/storyboards/previz/render all expose `Current scene` vs `All scenes` with honest warnings. Scoped the heavy modules (`editorial_direction_v1`, `look_and_feel_v1`, `sound_and_music_v1`, `shot_plan_v1`, `storyboard_v1`, `animatic_v1`, `keyframe_v1`, `render_adapter_v1`, `media_validation_v1`) so partial runs only regenerate the targeted scene while still rebuilding lightweight summaries (`*_index`, `previz_reel`) honestly from the latest stored mix. Also fixed the engine regression this surfaced by passing `runtime_params` through `_preload_upstream_reuse()` so scoped reuse and downstream fan-in use the same contract. Evidence: targeted API/runtime/module tests passed, scene run metadata now persists typed scope in `run_state.json`, and the Scene Workspace panels plus Run Detail copy all render explicit scope / prerequisite context. Next step: run the full static suite and browser verification, then compile methodology surfaces and hand off to `/validate`.
20260404-2236 — verification: full build-story validation suite is green and runtime/browser evidence is recorded. Static checks: `pnpm --dir ui exec tsc --noEmit`, `make test-unit PYTHON=.venv/bin/python` (`665 passed, 150 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, and `pnpm --dir ui run build` all passed after the engine reuse fix and a small `AppShell` nullability cleanup. Runtime smoke: restarted backend on `http://127.0.0.1:8000`, confirmed `curl -sf http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.04.04-05\"}`, and confirmed the Vite app served `http://127.0.0.1:5174/`. Browser verification: Playwright MCP remained unavailable (`Transport closed`) even after `python3 scripts/reset_playwright_mcp.py`, so I followed the runbook fallback and used a throwaway local Playwright workspace to exercise the changed UI in both desktop and mobile views. Evidence lives in `tmp/story-148-browser/`: `desktop-overview.png` shows the restored desktop Direction hover details; `desktop-shots-clicked.png`, `desktop-previz-clicked.png`, and `desktop-render-clicked.png` show scoped scene actions and the consolidated previz panel; `mobile-overview-direction.png`, `mobile-shots.png`, and `mobile-previz.png` show the mobile Direction bottom sheet, scoped execution controls, and the single previz surface. Both desktop and mobile probes reported clean console/page-error output, and the mobile checks explicitly verified that the duplicate `No previz for this scene yet` panel is gone. Next step: rerun `pnpm methodology:compile` so generated planning surfaces reflect the updated story artifact, then hand off for `/validate`.
20260404-2238 — methodology sync: reran `pnpm methodology:compile` after updating the story gates/work log, which regenerated `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`, then ran `pnpm methodology:check` to confirm the generated surfaces are current. Evidence: both commands exited successfully and the story now carries `Build complete` while staying `In Progress`, preserving the proper `/build-story` handoff boundary. Next step: `/validate` this story against the current diff and runtime evidence.
20260404-2258 — validate: reran the required validation suite fresh for Story 148. Checks passed: `make test-unit PYTHON=.venv/bin/python` (`665 passed, 150 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/`, story-targeted pytest (`89 passed` across scene-action/API/runtime/media-validation/shot-planning/pipeline-graph/cost-tracking coverage), `pnpm --dir ui run lint` (0 errors, 6 existing warnings), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `./scripts/sync-agent-skills.sh --check`, and `pnpm methodology:check`. Runtime smoke passed again via `curl -sf http://127.0.0.1:8000/api/health` and direct HTML fetch of `http://127.0.0.1:5174/`. Browser validation was rerun in this pass for desktop and mobile routes covering Direction, Shots, Previz, and Render; Playwright MCP still failed with `Transport closed` even after `python3 scripts/reset_playwright_mcp.py`, so I followed the runbook fallback and used local Playwright. Fresh evidence is in `tmp/validate-story-148-browser/` with clean console/page-error output in every probe. Result: no new implementation findings; recommend `/mark-story-done`.
20260404-2330 — close-out: marked Story 148 `Done` after confirming the workflow gates, acceptance criteria, and validation evidence remained current. Added the Story 148 changelog entry, kept the unrelated `docs/deploy-log.md` change out of the landing plan, and will recompile methodology surfaces so the generated dashboards reflect closure before check-in. Evidence: build + validation gates checked in this story, fresh validation suite already green, and no Story 148 changelog entry existed before this close-out pass. Next step: `/check-in-diff`.
