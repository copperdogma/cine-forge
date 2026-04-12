---
id: "165"
title: "Scene Render Refresh Reuse Path"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "164"
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
  - "runtime"
  - "feature-completeness"
legacy_system: ""
---

# Story 165 — Scene Render Refresh Reuse Path

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.1, spec:7.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 164

## Goal

Reduce scene-render iteration latency by reusing the current healthy shot-planning substrate instead of silently rerunning the full `render_generation` recipe every time the operator clicks `Refresh Render`. Story 164 proved the surfaced Scene Workspace route can produce one real `generated_video` artifact honestly. The next missing product promise is the actual refine loop: once CineForge already has a healthy `shot_plan` and shared track substrate for the target scope, refreshing the render should jump straight to `render` plus `validate_media` rather than redoing `timeline`, `tracks`, and `shot_planning`.

## Acceptance Criteria

- [x] Scene-action preflight can recommend `start_from: render` for `render_generation` when the selected scope already has healthy `shot_plan` artifacts and the shared `track_manifest` substrate is healthy; stale or missing planning keeps the current full-path behavior.
- [x] The Scene Workspace Render action uses the backend-recommended `start_from` value on refresh, so healthy existing planning is reused for both current-scene and all-scene refreshes when safe, while unsafe states still run the full recipe.
- [x] The refresh path stays honest and inspectable: preflight or panel copy makes reuse legible, and the resulting run metadata / Run Detail show `start_from=render` with stage order `["render", "validate_media"]` when reuse is active.
- [x] Targeted tests cover healthy-vs-stale render-reuse recommendations and keep headless `start_from=render` render-generation runs green.
- [x] A mechanical runtime benchmark on an honest project state records the delta between full render refresh and the `start_from=render` reuse path. If that benchmark becomes a continuing detector, `docs/evals/registry.yaml` is updated in the same story.

## Out of Scope

- Redesigning first-time scene-render latency from a fresh post-ingest project
- Provider-floor benchmarking, model-quality tuning, or prompt-quality work whose only goal is better output rather than a tighter iteration loop
- Auto-generating missing upstream direction or keyframes before render refresh
- Multi-scene final-output assembly, export polish, or final-render workflow changes beyond what this story needs for one honest refresh path

## Approach Evaluation

- **Simplification baseline**: do nothing and keep full refresh behavior. Current repo evidence already shows this is the wrong operator loop: `ui/src/components/GeneratedVideoPanel.tsx` sends `force: true` whenever a `render_prompt` or `generated_video` already exists, but never forwards a preflight `start_from`; `src/cine_forge/pipeline/scene_actions.py` currently recommends reuse for `ai_previz_generation` only, not `render_generation`; and a 2026-04-12 baseline probe on a project with healthy `track_manifest` and `shot_plan` still returned `{"status": "warn", "start_from": None}` for `render_generation`, so the surfaced route cannot yet use the existing sliced render substrate.
- **AI-only**: wrong fit. The missing gap is orchestration and UI honesty, not creative reasoning.
- **Hybrid**: possible but unnecessary. Adding another chooser step would add logic and runtime just to save runtime; the existing preflight already owns this decision boundary.
- **Pure code**: best fit. `DriverEngine` already supports `start_from`, and integration coverage already proves `start_from="render"` works headlessly. The missing work is connecting that existing substrate to the surfaced Scene Workspace refresh action.
- **Repo constraints / ADRs**: ADR-002 favors explicit preflight truth instead of hidden backend magic, so reuse should be recommended through `SceneActionPreflight`, not re-derived in React. ADR-003 keeps render compilation scene-first and stateless, so this story should reuse the current render path rather than introduce a second render recipe or prompt-editing shortcut. This is a new story instead of reopening Story 164 because the subsystem is the same but the success surface changed from “first representative scene render exists” to “repeat render iteration is honest and fast enough to support refinement.”
- **Existing patterns to reuse**: Story 152 is the direct pattern: `scene_actions.py` preflight recommendation, surfaced `start_from` handoff, and honest UI disclosure. Reuse `GeneratedVideoPanel`, the existing `SceneActionPreflight.start_from` contract, `DriverEngine` stage slicing, `tests/unit/test_scene_actions.py`, and the existing `start_from="render"` integration coverage in `tests/integration/test_render_adapter_integration.py`.
- **Eval**: the distinguishing test is a mechanical runtime comparison on the same honest project state: full render refresh with `force=true` versus refresh with `start_from=render`. Browser verification on the real Scene Workspace route should also confirm the `/api/runs/start` payload carries `start_from: "render"` when reuse is safe. There is no dedicated render-refresh detector in `docs/evals/registry.yaml` today, so implementation should decide whether the measured slice merits a durable registry entry.

## Tasks

- [x] Extend scene-action preflight so `render_generation` can recommend `start_from=render` only when reuse is safe for the selected scope.
- [x] Wire `GeneratedVideoPanel` to honor the recommended render start stage and disclose reuse clearly enough that operators can tell CineForge is rerendering from the current plan instead of replanning the scene.
- [x] Add targeted backend coverage for healthy-vs-stale render reuse decisions, plus at least one end-to-end regression that keeps the sliced `start_from=render` path green.
- [x] Run a refresh benchmark on an honest project state, capture the measured delta, and decide whether a durable `docs/evals/registry.yaml` entry is warranted instead of burying the numbers only in the work log.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] Not applicable: agent tooling and project instructions were untouched, so `make skills-check` was not required.
- [x] Story metadata changed: `pnpm methodology:compile`
- [x] Not applicable: evals and goldens were unchanged, so `/improve-eval` and `docs/evals/registry.yaml` updates were not required.
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
- [x] Search all docs and update any related to what we touched.
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

- **Owning class/module**: the reuse recommendation belongs in `src/cine_forge/pipeline/scene_actions.py`, because that is already the shared preflight truth for UI and API scene actions. `ui/src/components/GeneratedVideoPanel.tsx` should consume the recommendation, not invent render-specific branching on its own. `DriverEngine` already supports `start_from` and should not gain new render-only policy logic.
- **Data contracts**: the existing `SceneActionPreflight.start_from` field and run contract already cover the cross-layer handshake. Baseline exploration confirmed `ui/src/lib/types.ts` already types both `SceneActionPreflight.start_from` and `RunStartPayload.start_from`, and `ui/src/pages/RunDetail.tsx` already surfaces run `start_from` / `stage_order` metadata, so no new schema or event work is expected.
- **File sizes**: `make check-size` currently reports `src/cine_forge/pipeline/scene_actions.py` at `563` lines, `ui/src/components/GeneratedVideoPanel.tsx` at `361`, `tests/unit/test_scene_actions.py` at `192`, and `tests/integration/test_render_adapter_integration.py` at `351`. The planned backend change is localized to `_recommended_generation_start_stage(...)` (`29` lines today), so this story should not require adding logic to a >100-line method. Oversized files adjacent to this work but best left untouched if possible: `src/cine_forge/driver/engine.py` at `1373`, `src/cine_forge/modules/generation/render_adapter_v1/main.py` at `1554`, `ui/src/lib/types.ts` at `762`, and `ui/src/pages/SceneWorkspacePage.tsx` at `951`.
- **Decision context**: reviewed ADR-002, ADR-003, Story 152, Story 164, `docs/spec.md` (`spec:5.3`, `spec:5.5`, `spec:6.1`, `spec:7.1`, `spec:10.3`), `configs/recipes/recipe-render-generation.yaml`, `ui/src/components/GeneratedVideoPanel.tsx`, `src/cine_forge/pipeline/scene_actions.py`, and the existing `start_from="render"` integration coverage. No other ADR was found that narrows render-refresh ownership more specifically.

## Files to Modify

- `docs/stories/story-165-scene-render-refresh-reuse-path.md` — track scope, plan, evidence, and closure status
- `src/cine_forge/pipeline/scene_actions.py` — recommend safe render-refresh reuse start stages from preflight (`563`)
- `ui/src/components/GeneratedVideoPanel.tsx` — use the preflight-recommended `start_from` value and disclose reuse in the action flow (`361`)
- `tests/unit/test_scene_actions.py` — cover healthy, missing, and stale render-reuse cases (`192`)
- Generated planning surfaces via `pnpm methodology:compile`: `docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json`

## Redundancy / Removal Targets

- The implicit “refresh render means rerun the whole recipe” behavior in `GeneratedVideoPanel`
- Any render-panel copy that implies CineForge always replans the scene on refresh even when the current shot plan is already healthy

## Notes

- Story 164 closed the first representative scene-render path. This story is the smallest honest follow-on from that baseline because the repo already supports `start_from="render"` headlessly, but the surfaced operator path still ignores it.
- Existing integration coverage already proves the render recipe can run from `start_from="render"` and still land `render_prompt`, `generated_video`, and `media_validation`. The missing gap is product wiring, not missing backend capability.
- Baseline exploration found that `ui/src/lib/types.ts` and `ui/src/pages/RunDetail.tsx` already carry the metadata this story needs, so the likely code changes are narrower than the original draft suggested.
- Baseline exploration also found that render preflight can still emit `Timeline` as an auto-build item even when `track_manifest` and scoped `shot_plan` are healthy. The reuse recommendation should therefore gate on healthy `track_manifest` plus healthy scoped `shot_plan`, not on timeline health.
- No dedicated render-refresh runtime detector currently exists in `docs/evals/registry.yaml`. If this story adds one, it should be a narrow mechanical detector for the refresh loop rather than a vague “render is fast” claim.

## Plan

1. Backend preflight recommendation
   Files: `src/cine_forge/pipeline/scene_actions.py`, `tests/unit/test_scene_actions.py`
   Change: extend `_recommended_generation_start_stage(...)` so `render_generation` returns `start_from="render"` only when `track_manifest` is healthy and every target scene already has a healthy latest `shot_plan`. Keep the current full-path fallback when either substrate is missing or stale.
   Repo-fit evidence: ADR-002 says scene-action truth should live in preflight, and Story 152 already uses this exact pattern for `ai_previz_generation`.
   Done looks like: render preflight recommends `render` in the healthy case, withholds it in stale/missing cases, and still leaves warnings like `Timeline` or missing creative-direction substrate visible when they are informative rather than blocking.

2. UI handoff and honesty
   Files: `ui/src/components/GeneratedVideoPanel.tsx`
   Change: forward `preflight?.start_from` into `/api/runs/start` for refresh actions and surface concise copy when CineForge is reusing the current shot plan instead of replanning. Keep the existing full refresh behavior when preflight does not recommend reuse.
   Repo-fit evidence: `GeneratedVideoPanel` already owns the surfaced render action, while Run Detail already exposes `start_from` / `stage_order`; duplicating policy in React or editing Run Detail would add code without closing a product gap.
   Done looks like: the Scene Workspace Render tab stays honest about what will happen before the operator clicks and the run payload reflects the backend recommendation.

3. Regression coverage
   Files: `tests/unit/test_scene_actions.py`, `tests/integration/test_render_adapter_integration.py`
   Change: add targeted unit cases for healthy, stale, and missing substrate, and keep one end-to-end sliced render test explicit so the headless `start_from="render"` path remains guarded.
   Impact / break risk: the main failure mode is accidentally recommending reuse on stale planning or missing track state; these tests are the hard guard against that regression.
   Done looks like: unit coverage proves the decision boundary, and integration coverage proves the sliced render path still lands prompt, video, and validation artifacts.

4. Runtime benchmark and detector decision
   Files: `docs/stories/story-165-scene-render-refresh-reuse-path.md`, optionally `docs/evals/registry.yaml`
   Change: measure one honest full refresh and one honest `start_from=render` refresh on the same representative project state, record run ids and durations, and decide whether the result belongs in the eval registry as a continuing detector.
   Repo-fit evidence: this story is about operator-loop latency, so a mechanical runtime comparison is the right baseline; no AI-model comparison is needed because the missing gap is orchestration.
   Done looks like: the work log records the delta with enough detail to reproduce it, and registry changes happen only if the benchmark is promoted into a maintained detector.

5. Verification and close-out
   Files: touched code plus any directly related docs
   Change: run backend tests/lint, UI lint/type/build if the panel changes, and browser verification on the real Scene Workspace route `/:projectId/scenes/:entityId` in both desktop and mobile layouts. Inspect the `/api/runs/start` payload, confirm clean console output, and capture the reuse note on a representative renderable scene.
   Done looks like: the surfaced route proves the operator can refresh a render from the current plan when safe, while headless and static checks keep the backend truth aligned.

Repo-fit / optimality evidence:
- The repo already has the exact substrate this story needs: `SceneActionPreflight.start_from`, `RunStartPayload.start_from`, and integration coverage proving `start_from="render"` works. The missing gap is only recommendation plus surfaced handoff.
- ADR-002 favors explicit preflight truth over hidden backend branching, so a UI-local heuristic is the wrong design here.
- ADR-003 keeps render generation scene-first and stateless; adding a second render recipe or a render-only orchestration path would duplicate ownership instead of reusing the existing recipe slice.
- AI-only and hybrid alternatives were rejected because this story is not a reasoning-quality problem. Extra chooser logic or model work would add runtime and code without moving the product boundary.

Structural health check:
- `src/cine_forge/pipeline/scene_actions.py` is already `563` lines, so implementation should stay localized to `_recommended_generation_start_stage(...)` and at most one small helper. Do not broaden the change into a larger scene-actions refactor in this story.
- `ui/src/components/GeneratedVideoPanel.tsx` is `361` lines. Keep the UI diff tight: `handleStartRender()`, one computed label/note, and no Scene Workspace page refactor.
- `tests/unit/test_scene_actions.py` is `192` lines and is the right place for the decision matrix.
- `tests/integration/test_render_adapter_integration.py` is `351` lines and already owns sliced render substrate evidence.
- No new cross-layer schema or event type is expected. If implementation reveals otherwise, stop and add the schema-first task before writing the call site.

Redundancy plan:
- Remove or rewrite any render-panel copy that implies refresh always replans the scene when reuse is active.
- Do not add a second render-reuse heuristic in the UI; the panel should render backend truth, not duplicate it.

Human blockers / scope adjustments:
- Small scope adjustment already folded in: no planned changes to `ui/src/lib/types.ts` or `ui/src/pages/RunDetail.tsx`, because exploration confirmed both already support this path.
- No approval blocker is currently visible. No new dependency, public API shape change, or ADR update appears necessary.

## Work Log

20260412-1306 — story-created: opened Story 165 as the smallest honest continuation of the `scene-generation-completion` campaign after confirming the surfaced render route is real but the refresh loop still reruns unnecessary substrate. Evidence: reviewed `docs/methodology/state.yaml`, `docs/stories.md`, ADR-002, ADR-003, Story 152, Story 164, `configs/recipes/recipe-render-generation.yaml`, `ui/src/components/GeneratedVideoPanel.tsx`, `src/cine_forge/pipeline/scene_actions.py`, and the existing `start_from="render"` integration coverage. Key conclusion: this should be a new `Pending` story rather than reopening Story 164 because the subsystem is the same but the success surface shifted from “first real render exists” to “render refresh supports the generate-react-refine loop honestly.” Next step: regenerate methodology surfaces so the active campaign has a real follow-up owner.
20260412-1424 — exploration-notes: narrowed the likely implementation blast radius to `scene_actions.py`, `GeneratedVideoPanel.tsx`, and targeted render-refresh tests after tracing the real call path and existing substrate. Evidence: reviewed ADR-002, ADR-003, Story 152, Story 164, `ui/src/components/GeneratedVideoPanel.tsx`, `src/cine_forge/pipeline/scene_actions.py`, `tests/unit/test_scene_actions.py`, `tests/integration/test_render_adapter_integration.py`, `ui/src/lib/types.ts`, `ui/src/pages/RunDetail.tsx`, `ui/src/App.tsx`, and `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`; ran `make check-size`; and ran a baseline preflight probe with healthy `track_manifest` + healthy `shot_plan` that still returned `{'status': 'warn', 'start_from': None, 'labels': ['Timeline', 'Continuity tracking missing', 'Rhythm & Flow missing', 'Look & Feel missing', 'Sound & Music missing', 'Keyframes missing']}` for `render_generation`. Patterns to follow: Story 152 preflight reuse, existing `start_from="render"` integration coverage, and Scene Workspace verification on `/:projectId/scenes/:entityId`. Surprise / risk: timeline can still auto-build while render reuse is otherwise safe, so the reuse gate should key off healthy `track_manifest` plus healthy scoped `shot_plan`, not a healthy timeline. Next step: stop at the human gate with the refined implementation plan.
20260412-1434 — implementation-start: user approved the Story 165 plan, so the story status moved to `In Progress` before code changes and the first active task is the backend preflight recommendation. Next step: regenerate methodology surfaces so generated planning views reflect the live execution lane, then land the `render_generation` reuse recommendation and wire the Render panel to honor it.
20260412-1458 — implementation: landed render-refresh reuse at the shared preflight boundary and wired the Scene Workspace Render panel to honor it. Evidence: `src/cine_forge/pipeline/scene_actions.py` now recommends `start_from="render"` for `render_generation` only when `track_manifest` and scoped `shot_plan` artifacts are healthy, and it now respects live graph health so stale shot plans no longer appear reusable just because artifact metadata stayed `valid`; `ui/src/components/GeneratedVideoPanel.tsx` now forwards `preflight.start_from`, changes the success toast to mention current-shot-plan reuse when active, and surfaces a visible reuse note in the Render panel; `tests/unit/test_scene_actions.py` now covers healthy current-scene reuse, healthy all-scenes reuse, stale/missing substrate suppression, and graph-stale suppression. Practical effect: the Render tab now tells the truth about when CineForge can skip replanning, and stale projects stop advertising a render-only fast path the engine would reject anyway. Next step: rerun targeted and full validation, then capture representative browser evidence on one reuse-positive project and one stale no-reuse project.
20260412-1518 — validation: backend and UI checks passed, representative browser verification passed on both the positive and negative reuse boundaries, and the refresh-latency benchmark was recorded as a same-scene proxy without promoting it to a durable eval. Static evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_scene_actions.py -q` passed (`11 passed`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/integration/test_render_adapter_integration.py -q` passed (`2 passed`); `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`727 passed, 160 deselected, 1 warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed after linking this worktree’s `ui/node_modules` to the main checkout’s existing dependency tree because the worktree had no local frontend install. Runtime/API evidence: backend started with worktree code on `http://127.0.0.1:8000` and `curl -sf http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.04.12-02\"}`; browser verification used Vite on `http://127.0.0.1:5174` with real project paths opened through `/api/projects/open`; desktop verification on `/:projectId/scenes/:entityId?tab=render` for `the-mariner-64` scene `scene_004` showed the Render tab copy `Reuse path: CineForge will keep the current shot plan and rerun only render plus media validation.` and an intercepted `/api/runs/start` payload containing `start_from:\"render\"` plus `scene_scope:{mode:\"current_scene\",scene_ids:[\"scene_004\"]}` with zero console errors after stubbing the mocked run state/events; mobile verification on `story-132-shot-plan-ui-clean` scene `scene_001` showed no reuse note, showed `Shot planning` in warnings, and sent `/api/runs/start` without `start_from`, again with zero console errors after stubbing the mocked run polling endpoints. Benchmark evidence: on the same honest project/scene (`the-mariner-64`, `scene_004`), a fresh render-only rerun executed `render` + `validate_media` in `0.8462s` total (`0.0524s` render + `0.7938s` validation) using patched provider calls against a copied real project; the upstream full-refresh overhead on that same scene is available from historical current-scene run `output/runs/run-b3c317a9/run_state.json` (`timeline 0.0240s`, `tracks 0.0303s`, `shot_planning 24.6132s`), yielding a proxy full-refresh equivalent of `25.5137s` and an approximate `30.15x` speedup for the render-only reuse path. Decision: do not update `docs/evals/registry.yaml` because this is useful implementation evidence but not yet a maintained detector with its own harness. Residual note: the proxy benchmark is strong enough for this story’s implementation handoff, but a future maintained detector should benchmark a fresh full render refresh and a sliced render refresh under one dedicated harness rather than combining a historical upstream run with a fresh render-only pass. Next step: hand off for `/validate`; keep Story 165 `In Progress` with Build complete checked and formal validation/closure pending.
20260412-1633 — validation-followup: formal `/validate` reran the methodology guardrail and reviewed the implementation against Story 165’s explicit close criteria. Fresh evidence rerun in this validation pass: `pnpm methodology:check` initially failed because the story validation note changed the generated graph inputs, so `pnpm methodology:compile` was rerun and a second `pnpm methodology:check` passed with the existing non-story warning `Architecture audit domains due or carrying open findings: ingest_and_world_building`; a direct headless sliced-render probe using `DriverEngine.run(..., start_from=\"render\")` on a seeded render fixture reconfirmed `stage_order == [\"render\", \"validate_media\"]` with both stages `done`; browser/API verification from the prior validation note remains the fresh surfaced-path evidence for the Render tab disclosure and `/api/runs/start` payload. Validation outcome: keep the story open. The implementation is sound, but acceptance is still short in two places: the story promises that resulting run metadata or Run Detail will show `start_from=render`, and this validation pass found only stage-order proof plus request-payload proof, not a surfaced run-detail rendering of `start_from`; and the recorded runtime comparison is still a proxy that combines a fresh render-only run with historical upstream timings instead of a fresh paired full-refresh vs reuse benchmark under one harness. Practical effect: operators now get the faster honest reuse path in the Render tab, but the story should not close until the surfaced run-details evidence and benchmark evidence are upgraded from inferred/proxy to direct proof. Next step: patch the run-detail metadata visibility for `start_from` and capture one fresh paired benchmark, then rerun `/validate`.
20260412-2058 — implementation-followup: closed the remaining acceptance gaps by persisting sliced-run metadata into `RuntimeParams`, surfacing it in Run Detail, and replacing the proxy runtime note with one fresh paired benchmark on copied real project state. Code evidence: `src/cine_forge/schemas/runtime_params.py` now carries `start_from` / `end_at`; `src/cine_forge/api/run_orchestrator.py` now writes `start_from` into fresh, resumed, and retried run `runtime_params`; `ui/src/pages/RunDetail.tsx` now shows `start_from=…`, `stage_order=[…]`, and a human-readable execution summary in the Execution Scope card; `ui/src/lib/types.ts` now types those runtime params; `tests/unit/test_runtime_params.py` and `tests/unit/test_api.py` now pin the persisted metadata for fresh runs and retry flows. Practical effect: when CineForge reuses a healthy shot plan, operators can see the sliced execution boundary directly in run details instead of inferring it from stage status alone. Benchmark evidence: on copied `the-mariner-64` scene `scene_004` state opened through the real service path with provider/model calls patched but real project substrate intact, full refresh run `run-981a1b1a` executed `timeline -> tracks -> shot_planning -> render -> validate_media` in `1.3169s`, while sliced reuse run `run-a8191778` executed `render -> validate_media` with persisted `start_from:\"render\"` in `1.0083s`; measured delta `0.3086s`, about `1.31x` faster under the same harness. Next step: rerun full checks and browser validation, then reassess closure.
20260412-2102 — validation-rerun: Story 165 now validates cleanly. Fresh checks rerun in this pass: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_runtime_params.py tests/unit/test_api.py -q` passed (`39 passed`); `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`728 passed, 160 deselected, 1 warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed (build emitted only the existing Vite chunk-size warning). Fresh runtime/browser evidence: backend on `http://127.0.0.1:8000` returned `{\"status\":\"ok\",\"version\":\"2026.04.12-02\"}`; desktop Scene Workspace verification on `http://127.0.0.1:5174/the-mariner-64/scenes/scene_004?tab=render` showed the reuse note and, on an intercepted run-start click, sent payload `{\"recipe_id\":\"render_generation\",\"start_from\":\"render\",\"scene_scope\":{\"mode\":\"current_scene\",\"scene_ids\":[\"scene_004\"]},...}`; a fresh reload of the same route had zero console errors; desktop and mobile Run Detail verification on `http://127.0.0.1:5174/the-mariner-64/runs/run-a8191778` showed `start_from=render`, `stage_order=[render, validate_media]`, and explanatory copy `This run resumed at Render. Executed stages: Render -> Validate Media.` with zero console errors in both layouts. Evidence artifacts: `story-165-render-tab-desktop.png`, `story-165-run-detail-desktop.png`, and `story-165-run-detail-mobile.png`. Closure result: the remaining validation gaps are resolved; the only remaining work is story close-out via `/mark-story-done`.
20260412-2138 — close-out: marked Story 165 `Done` after verifying all acceptance criteria against the landed implementation and fresh evidence already recorded above. Closure evidence remains the same clean validation set: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`, `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, desktop/mobile browser verification on the surfaced Scene Workspace and Run Detail routes, plus the paired full-refresh vs reuse benchmark on copied real `the-mariner-64` scene state. Practical effect: the render-refresh reuse slice is now fully closed and recorded in methodology/changelog surfaces instead of living only in implementation notes. Next step: `/check-in-diff`.
