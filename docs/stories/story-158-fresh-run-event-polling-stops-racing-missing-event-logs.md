---
id: "158"
title: "Fresh Run Event Polling Stops Racing Missing Event Logs"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5"
  - "spec:5.6"
adr_refs:
  - "ADR-002"
depends_on: []
category_refs:
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "ux"
  - "run-progress"
  - "console-cleanliness"
  - "follow-up-from-157"
legacy_system: ""
---

# Story 158 — Fresh Run Event Polling Stops Racing Missing Event Logs

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5, spec:5.6
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md` and `docs/design/principles.md`
**Depends On**: None. Discovered during the 2026-04-10 FP1 recheck after Story 157 landed.

## Goal

Keep the canonical full-pipeline UI walkthrough technically clean when a fresh
run starts from the normal surfaced path. The Story 157 recheck proved that
completed-path chat CTAs are now honest, but the same walkthrough still emitted
one desktop `GET /api/runs/{id}/events` 404 for each newly started run
(`mvp_ingest`, then `world_building`) before the event log materialized. The
route recovered and the run completed, so this is not a reachability bug. It is
still a real product-truth failure because `spec:5.6` requires the canonical UI
path to stay polished and free of contradictory or noisy run state.

## Acceptance Criteria

- [x] Starting `mvp_ingest` from the surfaced Home/chat path on a fresh
  canonical `open-frequency` project does not produce `/api/runs/{id}/events`
  404 console or response noise while the run is initializing.
- [x] Starting `world_building` from the same surfaced path does not produce the
  same startup 404 noise, and the event log remains available once the run is
  live.
- [x] The chosen fix preserves live event-log behavior for active runs and the
  Run Detail page rather than simply hiding all `/events` failures.
- [x] New run IDs created by the shared lifecycle entrypoints (`start`,
  `resume`, and `retry_failed_stage`) do not diverge on event-log bootstrap
  semantics; a fresh run id should never begin life in a state where the UI can
  poll a missing event log for a real run.
- [x] Focused regression coverage exists for the startup-race path, and browser
  verification covers desktop plus the required mobile spot-check on the
  canonical fixture with clean console/page-error capture.

## Out of Scope

- Redesigning the run progress UX or replacing chat-driven progress with a
  different product surface
- Solving the separate historical missing-run `/state` polling bug tracked in
  Story 139
- Broad suppression of all 404s in the frontend without understanding ownership
- Changing the canonical FP1 walkthrough path itself unless the shipped product
  path changes for another reason

## Approach Evaluation

- **Simplification baseline**: This is deterministic startup sequencing, not a
  reasoning gap. The first question is whether the UI should tolerate a brief
  "event log not ready yet" window or the backend should make `/events` return
  an empty list until `pipeline_events.jsonl` exists. No LLM is needed to make
  that call.
- **AI-only**: Wrong fit. An LLM cannot make a polling race disappear, and
  adding model-written explanations would only hide a concrete contract failure.
- **Hybrid**: Unnecessary for the initial fix. A browser harness can reproduce
  the race and verify it is gone; there is no semantic judgment problem here.
- **Pure code**: Strong default. This is either frontend polling policy,
  backend startup contract behavior, or a narrow interaction between them.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` make chat
  the default interaction surface while Run Detail remains the power-user view.
  The fix cannot break live event logs on run detail or force users into the
  advanced surface just to avoid console noise. Avoid piling more sequencing
  logic into oversized `ui/src/lib/use-run-progress.ts`, `src/cine_forge/api/app.py`,
  or `src/cine_forge/api/run_orchestrator.py` unless a smaller seam proves
  insufficient.
- **Existing patterns to reuse**: `ui/src/lib/hooks/runs.ts`,
  `ui/src/lib/use-run-progress.ts`, `ui/src/pages/RunDetail.tsx`,
  `ui/src/pages/ProjectRun.tsx`, the `/api/runs/{id}/events` backend contract,
  and the Playwright smoke-script pattern in `scripts/story_157_chat_cta_smoke.py`.
- **Eval**: The discriminating check is a fresh-run browser repro on the
  canonical fixture that captures console, page, and response errors while
  starting `mvp_ingest` and `world_building`, paired with a focused regression
  harness around the startup-race seam.

## Tasks

- [x] Reproduce the exact startup race deterministically and confirm whether the
  first `/api/runs/{id}/events` fetch can happen before `pipeline_events.jsonl`
  exists, or whether another owner is responsible.
- [x] Implement the smallest fix that keeps fresh-run event polling honest and
  quiet without regressing live event-log updates for active runs or Run Detail.
- [x] Apply the chosen event-log bootstrap semantics consistently across the
  run-lifecycle entrypoints that mint a new run id (`start`, `resume`,
  `retry_failed_stage`) so the UI does not need per-entrypoint exceptions.
- [x] Add focused regression coverage for the chosen ownership seam. Prefer a
  narrow hook/API test or a dedicated smoke script over expanding unrelated
  oversized files.
- [x] Check whether the chosen implementation makes any existing code, helper
  paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum:
    `PYTHONPATH=src make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint:
    `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI validation risk check:
    `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
    `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`
  (N/A — not touched)
- [x] If story metadata, ADR metadata, or methodology state changes:
  `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent
  mismatch investigation, classify all mismatches, and update
  `docs/evals/registry.yaml` (N/A — no eval or golden changes)
- [x] If UI is touched: verify the changed flow with browser tools in desktop
  and mobile views when possible (screenshots + console check); if blocked,
  follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
  (verified on fresh canonical-fixture project `open-frequency-2` created
  through `/new`; screenshots at `/tmp/story158-nextsteps-desktop-start.png`,
  `/tmp/story158-nextsteps-desktop-mid.png`,
  `/tmp/story158-nextsteps-desktop-end.png`,
  `/tmp/story158-nextsteps-mobile-home.png`, and
  `/tmp/story158-nextsteps-mobile-render.png`; `console_errors=[]`,
  `page_errors=[]`, `response_errors=[]`)
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

- **Owning class/module**: The likely frontend seams are `ui/src/lib/hooks/runs.ts`
  (`useRunEvents`) and `ui/src/lib/use-run-progress.ts` (always-mounted
  active-run progress tracker). The likely backend seam is
  `src/cine_forge/api/run_orchestrator.py` / `/api/runs/{id}/events` behavior
  during the first moments of a new run. Prefer changing the smallest contract
  owner rather than layering defensive logic into multiple callers.
- **Data contracts**: Existing typed contracts already cover
  `RunEventsResponse`. If the backend chooses to make "events not ready yet"
  behave differently, keep it within the existing schema or add a typed response
  update before crossing layers.
- **File sizes**:
  - `ui/src/lib/hooks/runs.ts` — 196 lines
  - `ui/src/lib/use-run-progress.ts` — 585 lines, oversized
  - `src/cine_forge/api/run_orchestrator.py` — 642 lines, oversized
  - `src/cine_forge/api/app.py` — 735 lines, oversized
  - `scripts/story_157_chat_cta_smoke.py` — 233 lines
  - `make check-size` confirms the three runtime-owner files above are already
    large, so the story should prefer extraction or a narrow helper over more
    in-place branching.
- **Decision context**: Reviewed ADR-002, `docs/design/decisions.md`
  ("Progress via chat, not a separate page", "Run detail page for power users",
  and "Live-updating run details"), `docs/design/principles.md`,
  `docs/spec.md#spec56--full-pipeline-manual-acceptance`, Story 156, Story 157,
  and Story 139. No dedicated ADR was found for startup semantics of the
  run-events endpoint.

## Files to Modify

- `src/cine_forge/api/run_orchestrator.py` — likely primary owner: synchronously
  bootstrap run metadata and the event-log file before returning a new run id
  from `start_run`, `resume_run`, and `retry_failed_stage` (642)
- `tests/integration/test_api_integration.py` — best candidate for an
  end-to-end contract test that posts `/api/runs/start` and immediately reads
  `/api/runs/{id}/events` before the run settles (140+)
- `tests/unit/test_api.py` — likely narrow API-regression seam if the bootstrap
  behavior needs a smaller deterministic harness alongside the integration test
  (1299, oversized; prefer a new narrow test file if practical)
- `scripts/story_158_run_events_startup_smoke.py` (new) or equivalent narrow
  browser smoke harness — verify the canonical UI path stays free of
  `/api/runs/{id}/events` response noise
- `ui/src/lib/hooks/runs.ts` and `ui/src/lib/use-run-progress.ts` — callers at
  risk to inspect during validation, but avoid modifying them unless backend
  bootstrapping proves insufficient (196 / 585)

## Redundancy / Removal Targets

- Any logic that treats a just-started run's missing `pipeline_events.jsonl` as
  a hard user-visible error instead of a short-lived startup state
- Any duplicate per-caller 404 swallowing if one shared run-events policy can
  own the transition cleanly
- Any scout-only workaround language once the canonical path is actually quiet

## Notes

- Scout evidence from `docs/ui-scout/2026-04-10-open-frequency-local-recheck.md`:
  the desktop walkthrough passed every surfaced route and verified Story 157's
  CTA fix, but recorded exactly two response errors:
  `http://127.0.0.1:5174/api/runs/run-20314e5e/events` and
  `http://127.0.0.1:5174/api/runs/run-a6ca1da5/events`.
- Immediately after the scout, both corresponding backend run folders existed
  under `output/runs/` with `pipeline_events.jsonl`, and direct backend requests
  to `http://127.0.0.1:8000/api/runs/<id>/events` returned HTTP 200. That makes
  a startup race more likely than a persistent missing-run bug.
- Story 139 remains separate. It is about historical `/state` polling on stale
  projects, not fresh-run `/events` startup noise on the canonical UI path.

## Plan

### Eval / Baseline

- **Primary success check**: the canonical FP1 browser walk on
  `open_frequency_short.fountain` must finish with `response_errors=[]` and no
  desktop console 404s for `/api/runs/{id}/events`.
- **Current baseline**:
  - UI scout rerun recorded exactly two desktop response errors, one for each
    fresh started run (`run-20314e5e`, `run-a6ca1da5`) in
    `docs/ui-scout/2026-04-10-open-frequency-local-recheck.md`.
  - Direct API repro on 2026-04-10: immediately after `POST /api/runs/start`,
    the first `GET /api/runs/run-1f059e10/events` returned `404`; the second
    request `100ms` later returned `200` with `pipeline_started` already
    present. This confirms a startup race rather than a persistent missing-run
    condition.
- **Approach class**: pure code. This is orchestration and contract timing, not
  an AI-capability problem.

### Chosen Approach

- **Preferred fix**: bootstrap an empty `pipeline_events.jsonl` synchronously in
  the backend run-lifecycle entrypoint before returning the new run id.
  Specifically, add a small shared helper in
  `src/cine_forge/api/run_orchestrator.py` that creates the run dir, writes
  `run_meta.json`, and touches `pipeline_events.jsonl` for every new run id
  created by `start_run`, `resume_run`, and `retry_failed_stage`.
- **Why this fits this repo best**:
  - `DriverEngine.run()` already writes `run_state.json` immediately with the
    explicit comment "so pollers don't 404 during discovery/validation." The
    event-log bootstrap is the same contract gap in the same runtime lane.
  - The bug is created before any frontend-specific logic; fixing it at the
    run-lifecycle owner keeps `Chat` progress, `Run Detail`, and `ProjectRun`
    consistent without duplicating guard logic in multiple callers.
  - It preserves the existing 404 for truly unknown run ids. Touching the file
    up front is more precise than teaching `/events` to return empty for any
    missing file, which would blur "real run still initializing" with
    "nonexistent run id".
- **Alternatives rejected**:
  - Frontend-only retry/backoff in `useRunEvents`: would patch symptoms in one
    caller path, leaves other `/events` consumers exposed, and grows UI logic
    for a backend contract problem.
  - Backend `read_run_events()` special-casing missing files to `[]`: better
    than frontend swallowing, but less precise than creating the real file for
    real runs and keeping missing-run 404s intact.

### Scope Adjustment Folded Into This Story

- **Small, tightly coupled expansion**: apply the same bootstrap helper to
  `resume_run` and `retry_failed_stage`, not just `start_run`.
- **Why it stays in this story**: these methods mint new run ids in the same
  runtime subsystem and would otherwise preserve divergent startup semantics for
  the same `/events` contract. Relative effort: `XS`.
- **Additional `XS` validation-unblock expansion**: normalize bootstrap-only
  chat history so a fresh imported project always surfaces the current CTA
  instead of persisting stale placeholder bootstrap copy.
- **Why it stays in this story**: Story 158 acceptance is defined on the normal
  Home/chat path. Once the backend `/events` race was fixed, this adjacent UI
  truth bug became the only remaining blocker to honest validation of the same
  path, so it was cheaper and clearer to fold the fix into the active story
  than to leave Story 158 artificially blocked on known stale bootstrap state.

### Structural Health Check

- `make check-size` run during planning.
- Files likely to change and current size:
  - `src/cine_forge/api/run_orchestrator.py` — 642 lines, oversized
  - `tests/integration/test_api_integration.py` — small enough to extend
  - `tests/unit/test_api.py` — 1299 lines, oversized; avoid unless a narrow
    API-only seam is clearly better than a new test file
  - `ui/src/lib/hooks/runs.ts` — 196 lines, inspect only unless backend fix is
    insufficient
  - `ui/src/lib/use-run-progress.ts` — 585 lines, oversized; avoid adding logic
  - `ui/src/lib/chat-messages.ts` — 356 lines after the validation-unblock fix
  - `ui/src/lib/chat-store.ts` — 431 lines after the validation-unblock fix
  - `ui/src/lib/hooks/chat.ts` — 81 lines after the validation-unblock fix
  - `ui/src/components/ChatPanel.tsx` — 407 lines after the validation-unblock
    fix; keep the change render-only and avoid piling more flow logic into the
    component
- Plan risk: `run_orchestrator.py` is already oversized, so any new logic there
  should be a small shared helper rather than repeated inline setup in three
  methods.
- No new schema or event type is needed. This story changes run bootstrap timing
  for an existing file/endpoint contract.

### Implementation Order

1. **Backend bootstrap helper**
   - Files: `src/cine_forge/api/run_orchestrator.py`
   - Add a focused helper that prepares the run dir, writes run metadata, and
     ensures an empty `pipeline_events.jsonl` exists before returning a new run
     id.
   - Replace the duplicated `run_dir.mkdir(...)+_write_run_meta(...)` setup in
     `start_run`, `resume_run`, and `retry_failed_stage` with that helper.
   - Done when a direct immediate `GET /api/runs/{id}/events` after each new run
     id is able to return `200` rather than a startup `404`.

2. **Regression coverage**
   - Files: `tests/integration/test_api_integration.py` and possibly a new
     narrow unit test file if needed
   - Add an end-to-end test that posts `/api/runs/start`, immediately requests
     `/api/runs/{id}/events`, and asserts `200` plus a JSON `events` array even
     before the run finishes.
   - If practical, add a second narrow assertion for resume/retry bootstrap
     semantics without bloating existing oversized files.
   - Done when the race is reproducible on current code and green after the fix.

3. **Browser smoke on canonical path**
   - Files: `scripts/story_158_run_events_startup_smoke.py` (new) or an adapted
     local harness
   - Exercise `/new` → `/open-frequency` → `Break Down Script` → wait →
     `Deep Breakdown`, while collecting `console_errors`, `page_errors`, and
     `response_errors`.
   - Desktop is the primary path; mobile spot-check remains Home plus Render per
     the runbook.
   - Done when the browser capture is clean and still reaches the same honest
     downstream boundary.

4. **Close-out and redundancy**
   - Search for docs or comments that imply `/events` may legitimately 404 for
     fresh real runs and update them if needed.
   - Keep frontend callers unchanged unless the backend fix proves insufficient;
     if backend bootstrap is enough, that is the redundancy win because it
     avoids caller-specific guard code entirely.

### Impact / Risks

- **Could break**:
  - Resume/retry flows if the new helper accidentally changes run-meta handling
    or path setup
  - Tests that implicitly assume `pipeline_events.jsonl` is created only on the
    first emitted event
- **Low-risk areas**:
  - No public API shape change
  - No schema change
  - No project data migration
- **Main verification dependency**: the browser smoke must use the normal API
  and chat-driven path on a fresh canonical project, not a hand-seeded run dir.

### Verification Plan

- Static:
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Runtime / browser:
  - backend health `GET /api/health`
  - run the canonical desktop flow and required mobile spot-check
  - capture screenshots plus `console_errors`, `page_errors`, `response_errors`
  - confirm the changed path is produced through the normal `/new` → chat CTA
    route
- Methodology:
  - rerun `pnpm methodology:compile` only if story metadata or planning state
    changes during implementation

### Approval / Blockers

- No human approval blocker is known for the preferred approach.
- The only explicit scope adjustment is the folded `XS` consistency fix for
  `resume`/`retry` run-id bootstrap semantics plus the `XS` bootstrap-chat
  normalization needed to exercise the surfaced validation path honestly.

## Work Log

20260410-1430 — created from the FP1 Story 157 recheck: confirmed the canonical
path now archives stale completed-path CTAs, but the desktop walkthrough still
records one `/api/runs/{id}/events` 404 per fresh run during startup. Evidence:
`docs/ui-scout/2026-04-10-open-frequency-local-recheck.md`, backend `curl 200`
for both run ids after the race window, and existing event-log files under
`output/runs/`. Next step: build the narrowest fix and re-run the canonical
desktop/mobile scout with clean console capture.
20260410-1458 — exploration/planning: traced the race from
`startTrackedRun()`/`setActiveRun()` into the always-mounted
`useRunProgressChat()` hook, then into `useRunEvents()` and
`GET /api/runs/{id}/events`. Confirmed repo-fit owner is backend bootstrap, not
frontend swallowing: `DriverEngine.run()` already writes `run_state.json`
immediately "so pollers don't 404," but `RunOrchestrator.start_run()` returns
before `pipeline_events.jsonl` exists. Direct API repro: first immediate
`/events` request after `POST /api/runs/start` returned `404`, second request
`100ms` later returned `200`. Files likely to change: `src/cine_forge/api/run_orchestrator.py`,
`tests/integration/test_api_integration.py`, optional narrow regression test,
and a browser smoke harness. Callers at risk but likely unchanged:
`ui/src/lib/hooks/runs.ts`, `ui/src/lib/use-run-progress.ts`,
`ui/src/pages/RunDetail.tsx`, `ui/src/pages/ProjectRun.tsx`. ADRs/docs
consulted: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`,
`docs/spec.md#spec56`, `docs/methodology/state.yaml`, ADR-002,
`docs/design/decisions.md`, `docs/design/principles.md`, Story 156, Story 157,
Story 139. Redundancy target: avoid caller-specific 404 swallowing by fixing
the shared run bootstrap contract once. Next step: human gate on the plan, then
implementation if approved.
20260410-1536 — implementation: added `RunOrchestrator._bootstrap_run_dir()` in
`src/cine_forge/api/run_orchestrator.py` so `start_run`, `resume_run`, and
`retry_failed_stage` all create the run directory, write `run_meta.json`, and
touch `pipeline_events.jsonl` before returning a real run id. This keeps
unknown-run 404 semantics intact while eliminating the startup window where a
fresh real run id lacked an event log. Added regression coverage in
`tests/integration/test_api_integration.py` (immediate `/events` after
`/start`), `tests/integration/test_cost_budget_pause.py` (immediate `/events`
after `/resume`), and `tests/unit/test_api.py` (retry bootstrap now asserts
`pipeline_events.jsonl` exists). Next step: run full checks and then re-run the
representative browser path.
20260410-1558 — verification: `PYTHONPATH=src make test-unit
PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed
(`693 passed, 157 deselected, 1` pre-existing warning). `PYTHONPATH=src
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/
tests/` passed. `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
`pnpm --dir ui run build` all exited cleanly for this story's scope; lint still
reports the repo's existing warnings only. Restarted the backend with patched
local code via `PYTHONPATH=src
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m cine_forge.api
--no-reload --port 8000` and confirmed `GET /api/health` returned
`{"status":"ok","version":"2026.04.10-10"}`. Next step: re-run the canonical
desktop/mobile browser verification against the fresh surfaced path.
20260410-1614 — runtime verification attempt: the Story 158 backend contract
fix is in place, but full surfaced-path acceptance is blocked by an unrelated
fresh-import Home/chat truth bug. On a fresh `/open-frequency` project, the
screenplay content renders in the main canvas and the backend reports imported
inputs (`GET /api/projects/open-frequency` shows `has_inputs: true`;
`GET /api/projects/open-frequency/inputs` returns the expected file), yet the
right-panel CTA advertises `Upload Screenplay` instead of `Break Down Script`.
That prevents representative desktop/mobile click-through validation of
`mvp_ingest` and `world_building` from the normal surfaced path even though the
original `/api/runs/{id}/events` startup race is no longer the observed blocker.
Next step: hand off Story 158 as build-complete but not validated, and triage
the fresh-import CTA issue separately if we want to unblock the canonical UI
acceptance lane.
20260410-1624 — validation: reran the full validation suite in a fresh pass.
`PYTHONPATH=src make test-unit
PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed again
(`693 passed, 157 deselected, 1` pre-existing warning); `PYTHONPATH=src
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/
tests/` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
`pnpm --dir ui run build` all passed, and `pnpm methodology:check` reported no
graph drift beyond the expected unresolved FP1 warning. Targeted regressions:
`tests/integration/test_api_integration.py -k new_open_run_events_and_artifacts_flow`
passed, `tests/unit/test_api.py -k retry_failed_stage_bootstraps_new_run_from_failed_stage`
passed, and the resume integration passed on rerun plus five standalone repeats,
although the first validation attempt hit an intermittent empty-`run_state.json`
read during `/api/runs/{id}/state` polling. Browser verification was rerun on
desktop and mobile with screenshots at `/tmp/story158-validate-home-desktop.png`
and `/tmp/story158-validate-home-mobile.png`: both routes loaded the screenplay
cleanly with no console/page/response errors, but the surfaced Home/chat action
was still `Upload Screenplay` instead of `Break Down Script` even though the
project API reported `has_inputs: true`. Validation outcome: keep Story 158
open. The `/events` fix is implemented and tested, but the canonical acceptance
path still cannot prove AC1/AC2/AC5 because the fresh-import CTA issue blocks
the honest user flow before run start.
20260410-1651 — validation unblock + runtime verification: folded a tightly
coupled UI fix into the active story so bootstrap-only chat history no longer
pins fresh imported projects to stale placeholder CTAs. Updated
`ui/src/lib/chat-messages.ts`, `ui/src/lib/chat-store.ts`,
`ui/src/lib/hooks/chat.ts`, and `ui/src/components/ChatPanel.tsx` to give the
bootstrap welcome/suggestion pair stable IDs, detect bootstrap-only history,
replace stale bootstrap messages when project state advances, and hide legacy
placeholder bootstrap duplicates during render. Re-ran the honest surfaced path
through `/new` using `tests/fixtures/ingest_inputs/open_frequency_short.fountain`;
because `open-frequency` already existed locally, the normal deduped route
resolved to `open-frequency-2`. Desktop verification passed end-to-end:
fresh import immediately surfaced `Break Down Script` instead of `Upload
Screenplay`, `Break Down Script` launched `mvp_ingest`, `Deep Breakdown`
launched `world_building`, and the Home route eventually showed `All 69
artifacts are current`. Mobile spot-check on the same project passed on Home
plus `/scenes/scene_001?tab=render`. Evidence: screenshots at
`/tmp/story158-nextsteps-desktop-start.png`,
`/tmp/story158-nextsteps-desktop-mid.png`,
`/tmp/story158-nextsteps-desktop-end.png`,
`/tmp/story158-nextsteps-mobile-home.png`, and
`/tmp/story158-nextsteps-mobile-render.png`; backend API confirms
`open-frequency-2` reached `run_count: 2`, `artifact_groups: 69`; browser
capture was clean with `console_errors=[]`, `page_errors=[]`,
`response_errors=[]`, including no `/api/runs/{id}/events` startup 404s on the
two fresh started runs. Next step: rerun `/validate` against the updated diff
so the story can close on current evidence instead of the earlier blocked pass.
20260410-1728 — validation rerun: reran the full required check suite against
the updated diff. Because the worktree-local `.venv/bin/python` and
`.venv/bin/ruff` do not exist here, validation used the shared project venv at
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`. Fresh results:
`PYTHONPATH=src make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
passed (`693 passed, 157 deselected, 1` pre-existing pytest mark warning);
`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
passed; targeted regressions for start/resume/retry bootstrap semantics all
passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
`pnpm --dir ui run build` all passed with only the repo’s existing six UI lint
warnings plus the existing Vite chunk-size warning; `pnpm methodology:check`
passed with the expected stale ui-scout warning that still points at Story 158.
Fresh browser verification used the normal `/new` flow and canonical fixture
again, creating `open-frequency-3`: desktop surfaced `Break Down Script`, then
`Deep Breakdown`, and mobile spot-check passed on Home plus
`/scenes/scene_001?tab=render`; screenshots are at
`/tmp/story158-validate2-desktop-home.png`,
`/tmp/story158-validate2-desktop-mid.png`,
`/tmp/story158-validate2-mobile-home.png`, and
`/tmp/story158-validate2-mobile-render.png`. Browser capture stayed clean with
`console_errors=[]`, `page_errors=[]`, and `response_errors=[]`. Live API
confirmation on the fresh validation project showed both fresh run ids serving
`/api/runs/{id}/events` with HTTP 200 and non-empty event arrays. Validation
outcome: implementation is complete for this story. Next step: `/mark-story-done`;
when closing, refresh the ui-scout/methodology lane so planning surfaces stop
advertising Story 158 as unresolved.
20260410-1742 — close-out: marked Story 158 `Done` after the fresh validation
pass confirmed the backend `/events` bootstrap contract, the fresh-import Home
CTA truth fix, and the representative desktop/mobile surfaced-path walkthrough.
Close-out also records the clean FP1 rerun in the ui-scout lane, updates
methodology state/generated views so the story is no longer flagged as the
active unresolved follow-up, and adds the Story 158 changelog entry. Evidence:
fresh validation outputs in this story plus the clean scout report
`docs/ui-scout/2026-04-10-open-frequency-local-validation.md`. Next step:
`/check-in-diff`.
