# Story 007b: Operator Console Lite (GUI for Project Start, Open, Run, and Artifact Review)

**Status**: Done
**Created**: 2026-02-12
**Spec Refs**: 2.5 (Human Control), 3.1 (Stage Progression), 4 (Ingestion/Normalization/Config), 20 (Metadata & Auditing), 21 (Operating Modes)
**Depends On**: Story 002 (pipeline foundation), Story 003 (ingestion), Story 004 (normalization), Story 005 (scene extraction), Story 006 (project config), Story 007 (MVP smoke)

---

## Goal

Add a thin GUI "Operator Console Lite" so a user can validate real usage and behavior before deeper platform stories. This story intentionally focuses on operational workflow, not full creative collaboration UX.

The GUI must support:
1. Starting a new project (including Story 006 project-config confirmation workflow).
2. Opening an existing project.
3. Running the MVP recipe from UI.
4. Monitoring stage progress and run events.
5. Browsing produced artifacts and version history.

## Acceptance Criteria

### App Shell and Navigation
- [x] A GUI app entrypoint exists and runs locally (desktop browser) with clear navigation surfaces for:
  - [x] `New Project`
  - [x] `Project Switcher` (startup inline + on-demand drawer for opening existing projects)
  - [x] `Run Pipeline`
  - [x] `Runs / Events`
  - [x] `Artifacts`
- [x] The UI uses existing backend outputs (`output/project`, `output/runs`) and does not fork a second state model.
- [x] Basic error presentation exists for filesystem/read/parse failures (actionable message, not raw tracebacks).

### New Project Workflow (Story 006 GUI Parity)
- [x] User can create a new project workspace from GUI (project name/path).
- [x] User can select input file and model/runtime params equivalent to CLI (`input_file`, `default_model`, `accept_config`, optional `qa_model`).
- [x] GUI exposes Story 006 draft/confirm flow:
  - [x] Show detected project config draft values.
  - [x] Allow user to accept directly.
  - [x] Allow user to edit key fields before confirmation.
  - [x] Save resulting confirmed `project_config` artifact through normal pipeline path.

### Open Existing Project Workflow
- [x] User can open an existing project directory.
- [x] GUI loads and displays:
  - [x] Latest artifact types/versions.
  - [x] Prior runs list from `output/runs/*`.
  - [x] Current stale/valid state indicators where available.
- [x] Invalid/missing project structure is detected and shown with remediation guidance.

### Run Pipeline from GUI
- [x] User can execute `recipe-mvp-ingest.yaml` from GUI.
- [x] GUI maps user form input to runtime params used by driver (no hidden hardcoded values).
- [x] Success and failure states are surfaced with run-id, failed stage (if any), and produced artifact summary.

### Progress, Events, and Artifact Browser
- [x] During run, stage status updates are visible (pending/running/done/failed/skipped).
- [x] GUI displays pipeline events from `pipeline_events.jsonl` in chronological order.
- [x] GUI shows artifact browser with:
  - [x] artifact type/entity/version list,
  - [x] artifact metadata summary (lineage, health, cost),
  - [x] raw JSON detail view.
- [x] User can inspect at least two versions of an artifact when present.

### Tests and Validation
- [x] Add integration/e2e coverage for:
  - [x] new project flow,
  - [x] open project flow,
  - [x] run + events visibility,
  - [x] project config accept/edit confirm flow.
- [x] Existing unit/integration tests remain green.
- [x] `make test-unit` and lint pass with GUI changes.

### Documentation
- [x] `README.md` updated with:
  - [x] how to launch GUI,
  - [x] how to start/open a project,
  - [x] how to run MVP pipeline from GUI,
  - [x] where run/events/artifacts are read from.

## Design Notes

- Keep this story intentionally thin to avoid adding GUI coupling to all downstream stories.
- Prefer an adapter layer that wraps existing driver/artifact APIs over introducing duplicate pipeline logic.
- Avoid implementing creative-session chat, role orchestration UI, or rich timeline editing here; those belong to later stories (including Story 019 scope).
- UI state should be reconstructable from filesystem artifacts/run-state to preserve auditability.

### Chosen Stack (AI-first implementation reliability)

- Backend/UI bridge: **FastAPI** (Python) to expose minimal JSON endpoints over existing driver/artifact store operations.
- Frontend: **React + TypeScript + Vite**.
- Component styling: **Tailwind CSS** + lightweight component primitives (avoid heavy design-system lock-in in 007b).
- E2E testing: **Playwright** for key operator flows.

Rationale:
- React + FastAPI are widely used and well represented in AI training data, improving generation quality and debugging speed.
- Keeps core domain logic in Python while giving a robust browser UX.
- Avoids over-committing to a heavyweight frontend architecture during thin-slice validation.

## Tasks

- [x] Create GUI app scaffold and route/navigation structure for `New/Project Switcher/Run/Runs/Artifacts`.
- [x] Bootstrap FastAPI app with endpoints for project list/open, run start/status/events, and artifact browse/read.
- [x] Bootstrap React + TypeScript + Vite frontend shell connected to FastAPI.
- [x] Implement project path selector and new-project initialization flow.
- [x] Implement "Open existing project" flow (drawer/switcher + manual path) with project validation checks.
- [x] Add runtime-param form and map values to driver run invocation.
- [x] Implement run executor bridge for `configs/recipes/recipe-mvp-ingest.yaml`.
- [x] Implement stage progress panel backed by `run_state.json`.
- [x] Implement event feed panel backed by `pipeline_events.jsonl`.
- [x] Implement artifact browser (type/entity/version + metadata + JSON payload).
- [x] Implement Story 006 config draft/accept/edit confirm UI path.
- [x] Add automated tests for new/open/run/events/artifacts/config-confirm.
- [x] Add backend API tests for endpoint contracts and error payloads.
- [x] Update README with GUI launch + workflow docs.
- [x] Run `make test-unit PYTHON=.venv/bin/python` and `make lint PYTHON=.venv/bin/python`.
- [x] Capture validation evidence and open issues in this story work log.

### Story Builder Checklist (Actionable, 2026-02-12)

- [x] Add backend API package `src/cine_forge/operator_console/` with FastAPI app entrypoint and typed response models.
- [x] Implement `POST /api/projects/new` to initialize/open a project directory and return project summary.
- [x] Implement `POST /api/projects/open` with project-structure validation (`output/project`, `output/runs`) and remediation errors.
- [x] Implement `GET /api/projects/{project_id}/artifacts` with latest refs grouped by artifact type/entity.
- [x] Implement `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}` returning version list + metadata summaries.
- [x] Implement `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/{version}` returning raw artifact JSON payload.
- [x] Implement `POST /api/runs/start` mapping GUI form values to driver runtime params for `configs/recipes/recipe-mvp-ingest.yaml`.
- [x] Implement `GET /api/runs/{run_id}/state` backed by `output/runs/<run_id>/run_state.json`.
- [x] Implement `GET /api/runs/{run_id}/events` backed by `output/runs/<run_id>/pipeline_events.jsonl`.
- [x] Add API tests for success + filesystem error payloads in `tests/unit/` or `tests/integration/`.
- [x] Add frontend app under `ui/operator-console-lite/` with routes/navigation for `New/Project Switcher/Run/Runs/Artifacts` and API client wiring.
- [x] Implement Story 006 config draft/accept/edit confirm in GUI by setting runtime params (`accept_config`, optional `config_file`) before run start.
- [x] Add Playwright e2e flow for new/open/run/events/artifact browsing and config-confirm branch.
- [x] Update `README.md` with backend/frontend launch commands and route-to-workflow mapping.
- [x] Run `make test-unit PYTHON=.venv/bin/python` and `make lint PYTHON=.venv/bin/python`; capture command results and manual artifact inspection in this work log.

## Implementation Plan (Initial)

### Backend adapter slice

- Reuse `DriverEngine` directly for run execution and artifact-store reads to avoid duplicate pipeline state logic.
- Add thin filesystem reader helpers for `run_state.json` and `pipeline_events.jsonl`.
- Keep API errors structured (`code`, `message`, `hint`) so GUI can surface remediation guidance.

### Endpoint contract v1

- `POST /api/projects/new`: create/open project workspace, return project path and detected latest artifacts.
- `POST /api/projects/open`: validate project layout and return run/artifact summary or remediation hints.
- `POST /api/runs/start`: start `recipe-mvp-ingest.yaml` with runtime params (`input_file`, `default_model`, `qa_model`, `accept_config`, optional `config_file`).
- `GET /api/runs/{run_id}/state`: return parsed run-state with stage statuses.
- `GET /api/runs/{run_id}/events`: return chronological event list from JSONL.
- `GET /api/artifacts`: return grouped artifact type/entity latest-version summary.
- `GET /api/artifacts/{artifact_type}/{entity_id}`: return version list and metadata summary.
- `GET /api/artifacts/{artifact_type}/{entity_id}/{version}`: return raw artifact payload for JSON viewer.

### Frontend slice order

- Phase 1: shell routes + shared project context.
- Phase 2: New/Open forms and project validation messaging.
- Phase 3: Run form + stage progress polling + events feed.
- Phase 4: Artifact browser with metadata cards and raw JSON pane.
- Phase 5: Story 006 config draft/accept/edit confirm branch and e2e coverage.

## Implementation Decisions (Confirmed)

- `project_id` mapping: use deterministic hash of normalized absolute project path (`sha256(path)`).
- Rationale: avoids exposing raw filesystem paths in API contracts while staying lightweight (no registry DB/file for 007b).
- Run execution model: `POST /api/runs/start` launches in-process background task/thread and returns `run_id` immediately.
- Rationale: keeps UX responsive and supports run-state/event polling without introducing external queue infrastructure.

## Out of Scope (For This Story)

- [ ] Multi-user collaboration and auth.
- [ ] Rich role-chat experiences (`@agent` sessions).
- [ ] Full timeline editing UI.
- [ ] Shot planning, storyboard, and render controls.

## Work Log

### 20260212-1733 — Created Story 007b scaffold and acceptance/task checklist
- **Result:** Success.
- **Notes:** Added new story file `docs/stories/story-007b-operator-console-lite.md` with house format (`Status`, `Goal`, `Acceptance Criteria`, `Tasks`, `Work Log`) and explicit requirements for new/open project, Story 006 GUI parity, run control, events, and artifact browsing.
- **Next:** Register Story 007b in `docs/stories.md` so it is visible in planning order and story index.

### 20260212-1733 — Expanded task checklist for actionable testable work
- **Result:** Success.
- **Notes:** Added concrete checkbox tasks covering GUI scaffold, runtime param mapping, run bridge, events/artifact panels, config-confirm UX, tests, docs, and verification commands.
- **Next:** Update `docs/stories.md` ordering and row metadata for Story 007b.

### 20260212-1733 — Updated story index to schedule 007b next
- **Result:** Success.
- **Notes:** Updated `docs/stories.md` recommended order and story table to include `007b` immediately after `007`, with status `To Do` and link to this story file. This ensures planning visibility and sequencing aligns with requested execution order.
- **Next:** Begin implementation spike for GUI stack choice and minimal run/artifact adapter design.

### 20260212-1733 — Performed initial GUI stack reconnaissance
- **Result:** Partial success.
- **Notes:** Searched repo for existing GUI/web stack markers (`streamlit`, `fastapi`, `flask`, `react`, `vite`, `next`, `electron`, `textual`) and found no established frontend framework or web service scaffold. This confirms Story 007b should include an explicit stack decision and minimal app bootstrap as first implementation step.
- **Next:** Decide GUI stack (recommended: minimal Python-served web UI vs lightweight SPA) and add a short ADR/note before coding.

### 20260212-1736 — Selected implementation stack for AI-first delivery
- **Result:** Success.
- **Notes:** Chose `FastAPI + React + TypeScript + Vite + Tailwind` for Story 007b. This balances AI coding reliability (highly represented stack), rapid iteration, and clean integration with existing Python runtime/artifact code. Updated design notes and tasks to include explicit FastAPI endpoint bootstrap, frontend bootstrap, and backend API contract tests.
- **Next:** Start implementation with backend adapter endpoints first, then wire minimal frontend views (`New/Open/Run/Runs/Artifacts`).

### 20260212-1737 — Verified checklist completeness and tightened actionable task coverage
- **Result:** Success.
- **Notes:** Re-opened `docs/stories/story-007b-operator-console-lite.md` and verified house format sections are present (`Status`, `Goal`, `Acceptance Criteria`, `Tasks`, `Work Log`). Existing checklist items were valid but broad, so added `Story Builder Checklist (Actionable, 2026-02-12)` to break work into explicit backend endpoint, frontend route, and test deliverables without removing prior tasks.
- **Next:** Use checklist order to implement backend adapter package first (`src/cine_forge/operator_console/`) and lock endpoint contracts with tests before frontend wiring.

### 20260212-1737 — Completed implementation-planning spike against current runtime/artifact code
- **Result:** Success.
- **Notes:** Ran reconnaissance across `src/cine_forge/driver/engine.py`, `src/cine_forge/artifacts/store.py`, `src/cine_forge/driver/__main__.py`, and `tests/integration/test_mvp_recipe_smoke.py` to confirm existing run-state/event/artifact integration points. Added `Implementation Plan (Initial)` with endpoint contract v1 and phased frontend rollout aligned to these code paths.
- **Next:** Begin coding backend FastAPI endpoints using `DriverEngine` and artifact-store adapters, then add API contract tests for filesystem and parse-error cases.

### 20260212-1740 — Locked story implementation decisions for project identity and run execution
- **Result:** Success.
- **Notes:** Confirmed two planning decisions for Story 007b: (1) `project_id` will be a deterministic hash of normalized absolute project path; (2) run start endpoint will execute pipeline in an in-process background task and return `run_id` for polling via run-state/events endpoints. This narrows API and backend implementation choices and reduces ambiguity for next coding steps.
- **Next:** Implement backend adapter package and endpoint contracts using these decisions as fixed constraints.

### 20260212-1745 — Implemented Operator Console Lite backend API slice
- **Result:** Success.
- **Notes:** Added backend package `src/cine_forge/operator_console/` with FastAPI app and entrypoint (`app.py`, `service.py`, `models.py`, `__main__.py`, `__init__.py`). Implemented project session/open/new APIs, background run start API wired to `DriverEngine` + `configs/recipes/recipe-mvp-ingest.yaml`, run state/events polling APIs backed by `output/runs/<run_id>/`, and artifact group/version/detail APIs over immutable project artifacts. Structured error payloads now return `code`, `message`, and `hint`.
- **Next:** Begin frontend shell implementation (`ui/operator-console-lite/`) and connect views to these endpoint contracts.

### 20260212-1745 — Added API contract tests and verification evidence
- **Result:** Success.
- **Notes:** Added `tests/unit/test_operator_console_api.py` covering new/open project flow, artifact listing/version/detail endpoints, run start + polling flow (stubbed launcher), and unknown-project error behavior. Updated dependencies in `pyproject.toml` (`fastapi`, `uvicorn`, `httpx`) and added README launch/workflow docs for the API. Verification commands:
  - `.venv/bin/python -m pip install -e '.[dev]'`
  - `make test-unit PYTHON=.venv/bin/python` -> `99 passed, 23 deselected`
  - `make lint PYTHON=.venv/bin/python` -> `All checks passed`
- **Next:** Implement React/Vite frontend routes (`New/Open/Run/Runs/Artifacts`) and add e2e coverage against this backend.

### 20260212-1753 — Implemented frontend Operator Console Lite and wired backend APIs
- **Result:** Success.
- **Notes:** Added frontend app at `ui/operator-console-lite/` (React + TypeScript + Vite) with route-level views for `New Project`, `Open Project`, `Run Pipeline`, `Runs / Events`, and `Artifacts`. Implemented runtime param form mapping (`input_file`, `default_model`, `qa_model`, `accept_config`) and stage progress/event/artifact browsing UI over backend APIs. Added Story 006 draft-review-edit-confirm path in `Run Pipeline` view using `config_overrides` submitted to `POST /api/runs/start`.
- **Next:** Verify full flow coverage with integration tests and finalize docs/story checklist status.

### 20260212-1753 — Extended backend run API for config override confirmations
- **Result:** Success.
- **Notes:** Updated backend `RunStartRequest` and service to accept inline `config_overrides`; server now writes overrides into run-scoped config payload and passes resulting `config_file` through normal `project_config_v1` flow. Added CORS middleware for local frontend origin (`127.0.0.1:5173`/`localhost:5173`) to support split frontend/backend dev servers.
- **Next:** Execute integration coverage for new/open/run/events and config edit-confirm flow.

### 20260212-1753 — Added integration and e2e test coverage for operator flows
- **Result:** Success.
- **Notes:** Added integration test suite `tests/integration/test_operator_console_integration.py` covering: new/open project, run execution + events visibility, and draft-edit-confirm config flow resulting in confirmed `project_config` artifact updates. Added frontend Playwright e2e scaffold under `ui/operator-console-lite/e2e/operator-console.spec.ts` with mocked API routes to exercise new/open/run/review/runs/artifacts navigation flows.
- **Next:** Run required project verification commands and capture output evidence.

### 20260212-1753 — Verified Story 007b implementation and checks
- **Result:** Success.
- **Notes:** Executed:
  - `make test-unit PYTHON=.venv/bin/python` -> `99 passed, 25 deselected`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_operator_console_integration.py` -> `2 passed`
  - `make lint PYTHON=.venv/bin/python` -> `All checks passed`
  - `cd ui/operator-console-lite && npm run build` -> production bundle built successfully
  - `cd ui/operator-console-lite && npx playwright test --list` -> discovered e2e spec (`1 test`)
  Also manually inspected run-state/event/artifact JSON payloads via API routes exercised in integration tests (`/api/runs/{run_id}/state`, `/api/runs/{run_id}/events`, `/api/projects/{project_id}/artifacts/...`) to confirm produced artifacts are persisted and browsable.
- **Next:** Story complete; hand off with remaining out-of-scope items preserved.

### 20260212-1755 — Executed Playwright browser e2e flow successfully
- **Result:** Success.
- **Notes:** Installed Playwright Chromium browser runtime via `cd ui/operator-console-lite && npx playwright install chromium`, then executed `cd ui/operator-console-lite && npx playwright test` -> `1 passed`. This verifies the UI route flow scaffold (`new/open/run/review-edit/runs/artifacts`) executes end-to-end in a browser context with mocked API responses.
- **Next:** No blockers remain for Story 007b scope; maintainers can proceed to downstream stories.

### 20260212-1801 — Closed validation gaps from post-implementation review
- **Result:** Success.
- **Notes:** Addressed remaining quality gaps identified in requirements validation:
  - Project-scoped runs: `/api/projects/{project_id}/runs` now filters by project via run metadata + artifact ownership fallback (`src/cine_forge/operator_console/service.py`, `src/cine_forge/operator_console/app.py`), with new unit coverage in `tests/unit/test_operator_console_api.py`.
  - Draft review race: Run view now polls for draft artifact availability before presenting edit-confirm controls (`ui/operator-console-lite/src/App.tsx`).
  - Outcome visibility: added explicit run summary for produced artifact count + failed-stage detection (`ui/operator-console-lite/src/App.tsx`).
  - Artifact metadata summary UX: added dedicated metadata summary panel (health, lineage count, cost, producing module) next to raw JSON (`ui/operator-console-lite/src/App.tsx`).
  - Generated artifact hygiene: removed generated UI outputs from working-set scope and added ignore rules for build/test intermediates in `.gitignore`.
  Verification reruns:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_operator_console_api.py` -> `5 passed`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_operator_console_integration.py` -> `2 passed`
  - `make test-unit PYTHON=.venv/bin/python` -> `99 passed, 26 deselected`
  - `make lint PYTHON=.venv/bin/python` -> `All checks passed`
  - `cd ui/operator-console-lite && npm run build` -> success
  - `cd ui/operator-console-lite && npx playwright test` -> `1 passed`
- **Next:** Story remains complete; no open blockers for Story 007b scope.

### 20260212-1809 — Performed manual UX audit (desktop + mobile) and applied polish fixes
- **Result:** Success.
- **Notes:** Ran an explicit manual UI verification pass using live backend + frontend servers and captured visual evidence under `output/manual-ui-checks/20260212-visual/`:
  - Desktop: `desktop-new-ux2.png`, `desktop-run-ux2.png`, `desktop-artifacts-ux2.png`
  - Mobile: `mobile-run-ux2.png`
  Checked route clarity, spacing hierarchy, readability, and interaction affordances. Identified and fixed UX issues:
  - Added active-route highlighting for nav to improve orientation.
  - Disabled action buttons when prerequisite state is missing (no active project, no selected run) to reduce invalid action attempts.
  - Removed transient post-start “run state not found” flash by adding initial run-state retry before surfacing errors.
  Updated files: `ui/operator-console-lite/src/App.tsx`, `ui/operator-console-lite/src/styles.css`, `AGENTS.md` (manual UI verification policy).
  Re-verified with:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_operator_console_api.py tests/integration/test_operator_console_integration.py` -> `7 passed`
- `make lint PYTHON=.venv/bin/python` -> `All checks passed`
- **Next:** Story complete with manual UX evidence captured; proceed to next story.

### 20260212-1828 — Reworked project UX to script-first flow with persistent sidebar
- **Result:** Success.
- **Notes:** Implemented UX refactor so project onboarding starts from story/script input instead of raw project path. Added persistent project sidebar with recent-project list and one-click activation, removed primary `Open Project` page dependency, and introduced project-name -> workspace-path derivation under `output/` for clearer intent. Updated backend with `GET /api/projects/recent` and frontend layout/flows in `ui/operator-console-lite/src/App.tsx`, `ui/operator-console-lite/src/api.ts`, `ui/operator-console-lite/src/types.ts`, and `ui/operator-console-lite/src/styles.css`.
- **Next:** Validate CORS/network error handling in live browser and update docs/tests accordingly.

### 20260212-1828 — Fixed root cause of “Failed to fetch” and completed live browser verification
- **Result:** Success.
- **Notes:** Identified CORS mismatch as root cause when Vite auto-switched from port `5173` to `5174`; backend had only allowlisted `5173`. Updated CORS policy to allow localhost/127.0.0.1 across local dev ports via regex in `src/cine_forge/operator_console/app.py`. Improved frontend fetch error copy with explicit backend-start guidance. Executed live manual UI checks (real backend + real frontend) and captured new screenshots:
  - `output/manual-ui-checks/20260213-ux-refresh/desktop-new-script-first.png`
  - `output/manual-ui-checks/20260213-ux-refresh/desktop-run-script-first.png`
  - `output/manual-ui-checks/20260213-ux-refresh/desktop-artifacts-sidebar.png`
  - `output/manual-ui-checks/20260213-ux-refresh/mobile-run-sidebar.png`
  Verification commands:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_operator_console_api.py tests/integration/test_operator_console_integration.py` -> `8 passed`
  - `make test-unit PYTHON=.venv/bin/python` -> `99 passed, 27 deselected`
  - `make lint PYTHON=.venv/bin/python` -> `All checks passed`
  - `cd ui/operator-console-lite && npm run build` -> success
- `cd ui/operator-console-lite && npx playwright test` -> `1 passed`
- **Next:** Story ready for final handoff; monitor for additional UX iteration requests.

### 20260212-2350 — Reworked onboarding to file picker + drag/drop and collapsed project switching
- **Result:** Success.
- **Notes:** Implemented UX redesign to remove manual script-path entry as primary onboarding. New-project flow now uses drag/drop or file picker, uploads selected file into project workspace, and auto-wires `Run Pipeline` input to uploaded path. Added backend upload API `POST /api/projects/{project_id}/inputs/upload` (`src/cine_forge/operator_console/app.py`, `src/cine_forge/operator_console/service.py`, `src/cine_forge/operator_console/models.py`) and frontend client integration (`ui/operator-console-lite/src/api.ts`, `ui/operator-console-lite/src/types.ts`). Replaced persistent sidebar with project switcher drawer: inline at startup when no active project, on-demand overlay when a project is active (`ui/operator-console-lite/src/App.tsx`, `ui/operator-console-lite/src/styles.css`).
- **Notes:** Updated tests for upload and redesigned UX (`tests/unit/test_operator_console_api.py`, `tests/integration/test_operator_console_integration.py`, `ui/operator-console-lite/e2e/operator-console.spec.ts`) and updated docs (`README.md`).
- **Notes:** Manual browser verification completed after changes with screenshots:
  - `output/manual-ui-checks/20260213-file-first-redesign/desktop-new-file-first.png`
  - `output/manual-ui-checks/20260213-file-first-redesign/desktop-run-after-create.png`
  - `output/manual-ui-checks/20260213-file-first-redesign/desktop-project-switcher-overlay.png`
  - `output/manual-ui-checks/20260213-file-first-redesign/mobile-new-file-first.png`
- **Next:** Keep drawer behavior and upload flow as baseline; refine visual polish based on operator feedback.

### 20260213-0005 — Improved artifact selection UX and validated generated artifacts against PDF run
- **Result:** Partial success.
- **Notes:** Updated `Artifacts` view selection behavior in `ui/operator-console-lite/src/App.tsx` and `ui/operator-console-lite/src/styles.css`:
  - selected artifact group now remains visibly highlighted,
  - selected version is visibly highlighted,
  - version list auto-selects latest (and therefore auto-opens single-version groups).
  Manual UI verification screenshot captured at `output/manual-ui-checks/20260213-artifact-select/artifacts-selected-state.png`.
- **Notes:** Performed manual artifact inspection for project `output/the_mariner` (input file `output/the_mariner/inputs/e916a3c2_The_Mariner.pdf`). Findings:
  - `raw_input` artifact contains substantial extracted PDF text and correct source metadata (`file_format=pdf`), but classifier labeled it as `prose`.
  - `canonical_script`, `scene`, and `scene_index` artifacts do not match script reality: only 2 placeholder scenes with `UNKNOWN LOCATION` and `NARRATOR`.
  - `project_config` therefore reflects placeholder-derived values (2-minute runtime, unknown location, single narrator character) and is not production-accurate for this source.
  - Root cause is likely mock-model deterministic normalization/extraction behavior for this run (`normalization.rationale` indicates mock deterministic path), compounded by degraded PDF text spacing.
- **Next:** For correctness validation on real scripts, rerun with non-mock models and/or improved PDF OCR/text normalization before scene extraction; then re-inspect artifacts.

### 20260213-0019 — Aligned story acceptance with approved UX and closed validation hygiene gaps
- **Result:** Success.
- **Notes:** Updated Story 007b acceptance/tasks language to match approved UI behavior (project switcher drawer replaces dedicated `Open Project` route/view requirement while preserving existing-project open capability). Stabilized Playwright config for deterministic startup (`ui/operator-console-lite/playwright.config.ts`: strict port, disable reuse, explicit timeout). Removed stray root artifact file generated during package install (`=0.0.9`).
- **Next:** Re-run validation checks and re-score Story 007b against updated acceptance language.
