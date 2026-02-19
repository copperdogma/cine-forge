# Story 050 — Provider Resilience: Retries, Fallbacks, and Stage Resume

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done
**Depends on**: Story 038 (Multi-Provider Transport), Story 039 (Apply Model Selections)

## Goal

Harden CineForge pipeline reliability against upstream model API instability (for example Anthropic 529 overloads) so transient provider failures do not terminate user runs unnecessarily.

## Incident Context

Observed production failure on run `run-57b6c9d0` (`mvp_ingest`) at `2026-02-18T19:25:37Z`:

- `ingest`: success
- `normalize`: failed
- Error: `Anthropic HTTP error 529 ... overloaded_error`
- Downstream stages (`extract_scenes`, `project_config`) remained pending

This is a canonical transient-failure case: external provider overload, not deterministic input/schema failure.

## Why This Story

Current behavior allows transient API issues to surface as hard run failures too quickly. The system needs first-class resilience primitives:

- retry policy for transient failures
- stage-specific fallback model chains across providers
- resumable failed stages
- operator-visible failure metadata and UX
- reliability telemetry and alerts

## Promptfoo-Informed Fallback Matrix (MVP Ingest Path)

Use benchmark outcomes from Stories 036/039/047 and AGENTS eval catalog to define deterministic fallback order per stage.

### `normalize` (`script_normalize_v1`)

- Primary: `claude-sonnet-4-6` (current top overall for normalization-related evals)
- Fallback 1 (same provider, stronger): `claude-opus-4-6`
- Fallback 2 (cross-provider): `gpt-4.1`
- Fallback 3 (cross-provider): `gemini-3-flash-preview`

### `extract_scenes` (`scene_extract_v1`)

- Primary: `claude-sonnet-4-6` (top in scene extraction eval)
- Fallback 1 (same provider, stronger): `claude-opus-4-6`
- Fallback 2 (cross-provider): `gpt-5.2` (prior leader before Sonnet 4.6)
- Fallback 3 (cross-provider): `gemini-3-flash-preview`

### `project_config` (`project_config_v1`)

- Primary: `claude-haiku-4-5-20251001` (best in config detection eval)
- Fallback 1 (same provider, quality tier up): `claude-sonnet-4-6`
- Fallback 2 (same provider, strongest): `claude-opus-4-6`
- Fallback 3 (cross-provider): `gpt-4.1`

Notes:
- Fallback order must be configurable but defaulted in code from benchmark-backed recommendations.
- If provider-wide outages are detected, skip same-provider fallback and jump directly to cross-provider candidates.

## Acceptance Criteria

- [x] Transient classifier includes overload and capacity signals (`429`, `503`, `529`, timeouts, connection resets).
- [x] Retry policy implemented with exponential backoff + jitter and max attempt budget per stage.
- [x] Stage-level fallback chains are implemented and benchmark-backed defaults are encoded for `normalize`, `extract_scenes`, and `project_config`.
- [x] Provider-wide circuit breaker is implemented to avoid retry storms and skip known-unhealthy providers.
- [x] Run can be resumed from the failed stage without re-running already successful upstream stages.
- [x] UI run panel shows actionable transient failure states (retrying, fallback model/provider, retry countdown, final error class).
- [x] Structured telemetry captures: stage, attempt, provider, model, request_id, error_code, fallback decision, terminal reason.
- [x] Automated tests cover transient retries, fallback routing, circuit-breaker behavior, and stage-resume behavior.
- [x] `make test-unit` passes.
- [x] Story work log records production validation evidence and next operational actions.

## Non-Goals

- Rewriting the full pipeline architecture.
- Building dynamic cost optimization logic.
- Adding user-facing per-run manual model selection UI.

## Implementation Plan

1. **Transient Error Classification**
- Extend transient detection in `src/cine_forge/ai/llm.py` to include `529` and provider overload phrases.
- Normalize provider-specific error shapes into stable internal error classes.

2. **Retry Budget + Backoff**
- Implement exponential backoff with jitter and stage-level attempt caps.
- Ensure retries record attempt metadata in run events.

3. **Stage Fallback Orchestrator**
- Add fallback chain resolution in pipeline execution for AI-backed stages.
- Persist selected model/provider per attempt in stage metadata.

4. **Circuit Breaker**
- Track rolling provider failure rate.
- Open breaker on threshold breach; short-circuit retries to alternate providers for cooldown window.

5. **Resume from Failed Stage**
- Add API action to retry failed stage from run state.
- Guarantee idempotent reuse of successful upstream artifacts.

6. **UI Reliability UX**
- Surface transient classification and fallback progress in run timeline and chat status.
- Add explicit operator actions: `Retry Failed Stage`, `Retry Full Run`.

7. **Observability + Alerting**
- Emit structured logs and counters for retry/fallback outcomes.
- Add dashboard/query examples for on-call diagnosis.

8. **Validation**
- Add deterministic tests for each failure class and fallback branch.
- Run `make test-unit`.
- Run a targeted live smoke with injected transient failures.

## Tasks

- [x] Create shared transient error taxonomy and map provider responses to it.
- [x] Patch transient classifier in `ai/llm.py` (`529` + overload patterns).
- [x] Implement retry backoff with jitter and per-stage attempt budgets.
- [x] Add stage-level fallback chain config and defaults for `normalize`, `extract_scenes`, `project_config`.
- [x] Implement provider circuit breaker with cooldown and health probing.
- [x] Persist retry/fallback attempt metadata in run state + events.
- [x] Add API endpoint for `retry failed stage` and service-layer orchestration.
- [x] Update UI run detail/chat surfaces for retry/fallback visibility and actions.
- [x] Add unit/integration tests for retry, fallback, circuit breaker, and stage resume.
- [x] Run `make test-unit` and record output.
- [x] Perform a production-like smoke scenario with injected provider overload and capture evidence.
- [x] Update `docs/stories.md` index metadata if status/priority changes during execution. (Completed at story closure.)
- [x] Add retry-attempt metadata fields to stage state shape in `src/cine_forge/driver/engine.py` (`attempt_count`, `attempts[]`, `final_error_class`).
- [x] Emit structured `stage_retrying` / `stage_fallback` events in `output/runs/<run_id>/pipeline_events.jsonl`.
- [x] Add resilience policy config object (defaults + per-stage override) in `src/cine_forge/driver/recipe.py` and plumb through runtime params.
- [x] Add provider-health in-memory tracker/circuit-breaker in `src/cine_forge/ai/llm.py` (rolling window, open/half-open/closed).
- [x] Extend `RunStartRequest` in `src/cine_forge/api/models.py` with optional `retry_failed_stage_for_run_id` request path.
- [x] Add API/service flow to replay failed stage using existing run metadata in `src/cine_forge/api/app.py` and `src/cine_forge/api/service.py`.
- [x] Update `ui/src/lib/types.ts` and `ui/src/lib/api.ts` for new run-state/run-events resilience fields.
- [x] Update `ui/src/pages/ProjectRun.tsx` and `ui/src/pages/RunDetail.tsx` to display retry/fallback progress and add a `Retry Failed Stage` action.
- [x] Add unit tests in `tests/unit/test_ai_llm.py` for transient classification (`529`), jitter backoff, and circuit breaker state transitions.
- [x] Add driver/api tests in `tests/unit/test_driver_engine.py` and `tests/unit/test_api.py` for retry/fallback events and failed-stage resume endpoint.

## Implementation Spike Findings

- Current transient classifier in `src/cine_forge/ai/llm.py` does not include explicit `529`, which explains fast-fail behavior for Anthropic overload incidents.
- Retry behavior currently lives inside `call_llm()` only. Stage-level retry/fallback telemetry should be emitted from `src/cine_forge/driver/engine.py` so UI can present operator-meaningful state.
- Run resume primitive already exists via `start_from` in `DriverEngine.run()` and `RunStartRequest`; this can be leveraged for `Retry Failed Stage` without redesigning pipeline execution.
- Existing API surface has `POST /api/runs/start`; adding a dedicated resume endpoint is optional, but a dedicated endpoint improves operator intent clarity and avoids overloading start semantics.
- UI already polls `run_state` and `run_events` (`ui/src/pages/ProjectRun.tsx`, `ui/src/pages/RunDetail.tsx`); resilience UX can be delivered by extending event mapping plus one new action button.

## Validation Strategy

- Unit scope:
  - `ai/llm.py`: transient taxonomy, retry decisioning, backoff jitter bounds, circuit breaker transitions.
  - `driver/engine.py`: retry/fallback event emission and stage metadata persistence.
  - `api/service.py`: failed-stage resume request validation and run bootstrap.
- Integration scope:
  - Simulated provider overload in normalize stage should result in retries, fallback to alternate model/provider, and non-terminal run continuation.
  - Simulated terminal failure should expose `Retry Failed Stage` and restart at failed stage only.
- Required command:
  - `make test-unit`

## Work Log

### 20260218-1303 — Initialized Story 050 and checklist scaffold

- **Action:** Created new story file for provider resilience and documented the production failure context (`run-57b6c9d0`, Anthropic 529 overload on `normalize`).
- **Result:** Success
- **Notes:** Story includes required sections (`Goal`, `Acceptance Criteria`, checkbox `Tasks`, `Work Log`) and explicit MVP-ingest reliability scope.
- **Next:** Encode benchmark-backed fallback ordering and map implementation tasks to concrete files.

### 20260218-1306 — Added promptfoo-backed fallback matrix and implementation plan

- **Action:** Added stage-specific fallback chains for `normalize`, `extract_scenes`, and `project_config` using Story 036/039/047 benchmark outcomes and AGENTS eval catalog.
- **Result:** Success
- **Notes:** Fallback chain explicitly includes cross-provider routes to avoid provider-local outages becoming terminal run failures.
- **Next:** Align story index entry and hand off for execution approval.

### 20260218-1308 — Verified checklist completeness and updated story index

- **Action:** Verified `## Tasks` contains explicit checkbox items for all delivery work; added Story 050 row to `docs/stories.md`.
- **Result:** Success
- **Notes:** Checklist now fully actionable and testable, matching build-story workflow requirements.
- **Next:** Start implementation in priority order: transient classification, retry/backoff, then fallback orchestration.

### 20260218-1312 — Performed implementation spike and expanded actionable checklist

- **Action:** Audited concrete integration points across `ai/llm.py`, `driver/engine.py`, `api/{models,app,service}.py`, and UI run pages; expanded `## Tasks` with file-specific, testable work items.
- **Result:** Success
- **Notes:** Existing `start_from` resume mechanism provides a low-risk path for failed-stage retry; main gap is resilience telemetry and policy orchestration around provider failures.
- **Next:** Start coding phase 1: transient taxonomy + `529` handling + LLM-level retry/circuit primitives.

### 20260218-1333 — Implemented transient classifier hardening and exponential retry backoff

- **Action:** Updated `src/cine_forge/ai/llm.py` to classify overload/capacity errors as transient (including `529` and `overloaded_error`) and replaced linear retry sleep with exponential backoff + bounded jitter via `_retry_delay_seconds()`.
- **Result:** Success
- **Notes:** This directly addresses the observed production failure mode (`Anthropic HTTP 529 overloaded_error`) by making first-level retry behavior more resilient and less synchronized.
- **Next:** Implement stage-level fallback orchestration and resilience event telemetry in `driver/engine.py`.

### 20260218-1333 — Added unit coverage and validated suite

- **Action:** Added tests in `tests/unit/test_ai_llm.py` for `529` transient retry behavior and retry-delay backoff/jitter semantics; executed `make test-unit PYTHON=.venv/bin/python`.
- **Result:** Success
- **Notes:** Test results: `186 passed, 49 deselected`. Earlier plain `make test-unit` failed in this shell due system `python3` lacking `fastapi`; project-expected `.venv` path passes.
- **Next:** Begin driver/API implementation for fallback chain execution and failed-stage resume endpoint.

### 20260218-1335 — Implemented LLM-layer provider circuit breaker and expanded tests

- **Action:** Added in-memory provider circuit breaker primitives to `src/cine_forge/ai/llm.py` (`_record_provider_transient_failure`, `_is_circuit_breaker_open`, `_record_provider_success`), integrated checks into `call_llm()`, and added dedicated unit tests in `tests/unit/test_ai_llm.py`.
- **Result:** Success
- **Notes:** Circuit opens after 3 consecutive transient failures with cooldown, resets after cooldown/success; unit suite now reports `188 passed, 49 deselected` via `make test-unit PYTHON=.venv/bin/python`.
- **Next:** Implement driver-level fallback chain execution and emit resilience-specific run events (`stage_retrying`, `stage_fallback`).

### 20260218-1337 — Added driver-level fallback orchestration and resilience event/state tracking

- **Action:** Implemented stage-level model attempt planning and fallback execution in `src/cine_forge/driver/engine.py`, including benchmark-backed fallback defaults for `normalize`, `extract_scenes`, and `project_config`, plus stage metadata (`attempt_count`, `attempts`, `final_error_class`) and structured events (`stage_retrying`, `stage_fallback`).
- **Result:** Success
- **Notes:** Added regression coverage in `tests/unit/test_driver_engine.py` (`test_driver_falls_back_to_next_model_on_transient_stage_error`) to verify 529-triggered fallback from `claude-sonnet-4-6` to `claude-opus-4-6` with persisted event/state evidence.
- **Next:** Implement API endpoint/service flow for `Retry Failed Stage` and wire UI action surfaces.

### 20260218-1337 — Revalidated unit suite after driver fallback changes

- **Action:** Ran targeted suites (`tests/unit/test_ai_llm.py`, `tests/unit/test_driver_engine.py`) and full unit suite (`make test-unit PYTHON=.venv/bin/python`).
- **Result:** Success
- **Notes:** Full unit result now `189 passed, 49 deselected`.
- **Next:** Proceed to API + UI layer implementation for failed-stage resume controls.

### 20260218-1340 — Added failed-stage resume API endpoint and service orchestration

- **Action:** Implemented `POST /api/runs/{run_id}/retry-failed-stage` in `src/cine_forge/api/app.py` and `OperatorConsoleService.retry_failed_stage()` in `src/cine_forge/api/service.py`.
- **Result:** Success
- **Notes:** Endpoint resolves failed stage from existing run state, reuses prior runtime params + recipe, and starts a new run from the failed stage with preserved project context.
- **Next:** Wire UI action (`Retry Failed Stage`) to this endpoint in run detail surfaces.

### 20260218-1340 — Added API regression test and revalidated unit suite

- **Action:** Added `test_retry_failed_stage_endpoint_returns_new_run_urls` in `tests/unit/test_api.py` (marked `@pytest.mark.unit`), then ran `make test-unit PYTHON=.venv/bin/python`.
- **Result:** Success
- **Notes:** Full unit result now `190 passed, 49 deselected`.
- **Next:** Implement UI affordance and display resilience telemetry from run state/events.

### 20260218-1342 — Wired UI retry action to failed-stage resume API

- **Action:** Added `retryFailedStage()` API client function in `ui/src/lib/api.ts`, `useRetryFailedStage()` hook in `ui/src/lib/hooks.ts`, and a `Retry Failed Stage` action in `ui/src/pages/RunDetail.tsx` that starts a resumed run and navigates to the new run route.
- **Result:** Success
- **Notes:** This delivers operator control for failed-stage resume from the run detail surface. Chat-surface retry messaging is still pending.
- **Next:** Extend `ProjectRun`/chat progress surfaces to show `stage_retrying` and `stage_fallback` events explicitly.

### 20260218-1342 — Validation after API + UI retry wiring

- **Action:** Ran `make test-unit PYTHON=.venv/bin/python` and `npm run build` in `ui/`.
- **Result:** Success
- **Notes:** Backend unit suite remains green (`190 passed, 49 deselected`); frontend TypeScript+Vite build passes.
- **Next:** Implement remaining observability UX (event mapping for retry/fallback and stage attempt metadata rendering).

### 20260218-1344 — Added resilience event rendering and stage-attempt visibility in UI

- **Action:** Updated run event transformation in `ui/src/pages/ProjectRun.tsx` and `ui/src/pages/RunDetail.tsx` to map backend `stage_retrying`/`stage_fallback` events into user-readable warning events; added stage attempt count display in `RunDetail`; updated `StageState` typing in `ui/src/lib/types.ts`.
- **Result:** Success
- **Notes:** Run detail and live progress views now surface fallback behavior explicitly instead of generic JSON event payloads.
- **Next:** Wire chat-status messaging to these resilience events for conversational surface parity.

### 20260218-1344 — Final validation after resilience UI updates

- **Action:** Re-ran `make test-unit PYTHON=.venv/bin/python` and `npm run build` in `ui/`.
- **Result:** Success
- **Notes:** Backend unit suite remains green (`190 passed, 49 deselected`), and UI build remains green after event/type updates.
- **Next:** Implement remaining story items: explicit resilience policy object plumbing and production-like injected-overload smoke scenario.

### 20260218-1348 — Added recipe-level resilience policy object and override plumbing

- **Action:** Added `RecipeResilience` to `src/cine_forge/driver/recipe.py` (including `stage_fallback_models` + retry knobs) and plumbed resolved resilience config through recipe runtime resolution and driver fallback planning.
- **Result:** Success
- **Notes:** Fallback behavior is no longer hardcoded-only; recipes can now override stage fallback chains explicitly.
- **Next:** Validate with deterministic tests that recipe overrides are honored during transient failures.

### 20260218-1348 — Added fallback-override and injected-overload smoke coverage

- **Action:** Added unit test `test_driver_uses_recipe_resilience_fallback_override` in `tests/unit/test_driver_engine.py` and integration smoke test `test_injected_provider_overload_falls_back_and_completes` in `tests/integration/test_pipeline_integration.py`.
- **Result:** Success
- **Notes:** Integration test simulates `Anthropic HTTP error 529: overloaded_error`, verifies `stage_retrying` + `stage_fallback` events, and confirms stage completion via fallback model.
- **Next:** Close remaining UI/chat parity item for resilience status messaging.

### 20260218-1348 — Extended start-run schema for retry path and revalidated suite

- **Action:** Added optional `retry_failed_stage_for_run_id` to `RunStartRequest` (`src/cine_forge/api/models.py`) and routed `POST /api/runs/start` through retry orchestration when provided (`src/cine_forge/api/app.py`); added unit test `test_start_run_accepts_retry_failed_stage_for_run_id` in `tests/unit/test_api.py`.
- **Result:** Success
- **Notes:** Revalidation command `make test-unit PYTHON=.venv/bin/python` now passes at `192 passed, 50 deselected`.
- **Next:** Decide whether to expose this alternate retry path in UI or keep dedicated `POST /api/runs/{run_id}/retry-failed-stage` as primary operator action.

### 20260218-1350 — Added chat-surface resilience messaging parity

- **Action:** Updated `ui/src/lib/use-run-progress.ts` to consume run events and emit chat updates for `stage_retrying` and `stage_fallback` events with deduping, including a persistent `View Details` route action.
- **Result:** Success
- **Notes:** Chat panel now reflects automatic retry/fallback behavior in near real-time, matching the visibility already added to run detail/progress views.
- **Next:** Optional UX polish: add stage-specific retry/fallback copy templates in `chat-messages.ts` if we want tighter narrative tone consistency.

### 20260218-1350 — Validation after chat parity update

- **Action:** Ran `npm run build` in `ui/` and `make test-unit PYTHON=.venv/bin/python`.
- **Result:** Success
- **Notes:** UI build and backend unit suite remain green (`192 passed, 50 deselected`).
- **Next:** Keep Story 050 open for final operator validation against a live failed run before status transition.

### 20260218-1357 — Closed telemetry/countdown/half-open remaining gaps

- **Action:** Added half-open probe behavior to LLM circuit breaker (`src/cine_forge/ai/llm.py`), enriched driver retry/fallback telemetry with `provider`, `error_code`, `request_id`, and `retry_delay_seconds` (`src/cine_forge/driver/engine.py`), and surfaced retry-delay/final-error details in UI run/chat surfaces (`ui/src/pages/ProjectRun.tsx`, `ui/src/pages/RunDetail.tsx`, `ui/src/lib/use-run-progress.ts`).
- **Result:** Success
- **Notes:** This closes the previously-partial acceptance items around structured telemetry and actionable retry UX detail.
- **Next:** Keep story open per operator request; run live production validation against a real failed run before any status transition.

### 20260218-1357 — Revalidated after final resilience hardening

- **Action:** Ran targeted tests (`tests/unit/test_ai_llm.py`, `tests/unit/test_driver_engine.py`, `tests/integration/test_pipeline_integration.py`), UI build (`npm run build`), and full unit suite (`make test-unit PYTHON=.venv/bin/python`).
- **Result:** Success
- **Notes:** Full unit result now `193 passed, 50 deselected`; integration fallback smoke remains green.
- **Next:** Optional: capture one live Fly run failure/retry transcript as operator evidence artifact in this story.

### 20260218-1406 — Closed validation gaps: terminal telemetry, attempt budget, and service-level resume tests

- **Action:** Added explicit resilience attempt-budget config in `src/cine_forge/driver/recipe.py` (`max_attempts_per_stage`, `stage_max_attempts`) and enforced budget truncation in `src/cine_forge/driver/engine.py` model attempt planning.
- **Result:** Success
- **Notes:** Stage fallback plans are now bounded by a first-class recipe policy instead of implicit fallback-list length only.
- **Next:** Verify budget enforcement via failing transient stage test and ensure no fallback event is emitted when budget is 1.

### 20260218-1406 — Added structured terminal stage-failure telemetry fields

- **Action:** Enriched `stage_failed` event emission in `src/cine_forge/driver/engine.py` with `error_class`, `error_code`, `request_id`, `provider`, `model`, `attempt_count`, and `terminal_reason`.
- **Result:** Success
- **Notes:** Failure events now carry machine-readable diagnosis fields needed for operator analysis and alerting.
- **Next:** Confirm event payloads in unit tests and ensure terminal reason semantics are stable for transient vs non-retryable failures.

### 20260218-1406 — Added direct service-layer tests for failed-stage resume orchestration

- **Action:** Added tests in `tests/unit/test_api.py` that exercise real `OperatorConsoleService.retry_failed_stage()` behavior from run-state/run-meta fixtures, including successful worker bootstrap and no-failed-stage rejection.
- **Result:** Success
- **Notes:** This closes the prior test gap where only endpoint stubs were validated.
- **Next:** Run targeted and full unit suites and re-validate Story 050 checklist status.

### 20260218-1407 — Fixed run-state schema drift and revalidated suites

- **Action:** Added resilience fields to persisted stage schema in `src/cine_forge/driver/state.py` (`attempt_count`, `attempts`, `final_error_class`) after validation exposed that serialization was dropping these fields from `run_state.json`.
- **Result:** Success
- **Notes:** This aligns runtime state, persisted state, and UI/API expectations for resilience metadata.
- **Next:** Keep story open and run a final requirements validation pass before any status transition.

### 20260218-1407 — Validation after gap-closure implementation

- **Action:** Ran targeted tests for new gap-closure behavior and full unit suite: `tests/unit/test_driver_engine.py::test_driver_respects_max_attempts_per_stage_budget`, `tests/unit/test_api.py::{test_service_retry_failed_stage_bootstraps_new_run_from_failed_stage,test_service_retry_failed_stage_rejects_runs_without_failed_stage}`, `make test-unit PYTHON=.venv/bin/python`, and fallback integration smoke `tests/integration/test_pipeline_integration.py::test_injected_provider_overload_falls_back_and_completes`.
- **Result:** Success
- **Notes:** Unit suite now passes at `196 passed, 50 deselected`; targeted integration fallback smoke remains green.
- **Next:** Re-run full work-vs-requirements validation and decide checkbox updates with operator approval.

### 20260218-1411 — Captured production failure evidence and identified deployment gap

- **Action:** Queried Fly app status/logs and fetched production run events for `run-57b6c9d0` from `https://cineforge.copper-dog.com/api/runs/run-57b6c9d0/events`.
- **Result:** Partial success
- **Notes:** Confirmed canonical production failure transcript: `normalize` failed with `Anthropic HTTP error 529 ... overloaded_error` and request id `req_011CYG5mNPCkcXrgnabnHoPS`. Attempt to call `POST /api/runs/{run_id}/retry-failed-stage` returned `405 Method Not Allowed`, indicating the currently deployed image does not yet expose this new endpoint.
- **Next:** Deploy the current branch to Fly, then re-run live failed-stage retry and capture post-deploy resilience event evidence (`stage_retrying`, `stage_fallback`, enriched `stage_failed`).

### 20260218-1412 — Captured local smoke transcripts for resilience telemetry contracts

- **Action:** Ran two local injected-overload smoke executions via `DriverEngine` in a temp workspace: one fallback-success path (`max_attempts_per_stage: 4`) and one terminal path (`max_attempts_per_stage: 1`).
- **Result:** Success
- **Notes:** Success transcript showed `attempt_count=2`, fallback from `claude-sonnet-4-6` to `gpt-4.1`, and `stage_retrying`/`stage_fallback` events with `error_code=529`, `request_id`, and `retry_delay_seconds`. Terminal transcript showed structured `stage_failed` payload with `attempt_count`, `provider`, `model`, `request_id`, `error_code`, and `terminal_reason=retry_budget_exhausted_or_no_fallback`.
- **Next:** Use these transcripts as pre-deploy contract evidence; replace with live production retry transcript after deploying the resilience build.

### 20260218-1437 — Deployed resilience branch to Fly and completed smoke suite

- **Action:** Deployed current `main` working tree to Fly with `fly deploy --depot=false --yes` (user-approved override: skip "must be checked in" gate), then ran API and HTTP UI smoke checks.
- **Result:** Success
- **Notes:** API checks passed (`/api/health`, `/api/recipes`, `/api/projects/recent`, `/api/changelog`); UI fallback checks passed (`<title>CineForge</title>`, JS bundle `assets/index-UBJ_neA4.js` returned `200`). Browser MCP was unavailable in-session, so screenshot/console-browser verification was not performed.
- **Next:** Validate live failed-stage retry behavior against the original production failure run.

### 20260218-1437 — Live failed-stage retry validation found production blocker

- **Action:** Called `POST /api/runs/run-57b6c9d0/retry-failed-stage` on production; endpoint now exists and returned new run `run-57b6c9d0-retry-b277`. Polled `/api/runs/run-57b6c9d0-retry-b277/state` and `/events`.
- **Result:** Failure
- **Notes:** New run never progressed, `/events` returned `run_events_not_found`, and state response reported `background_error`: `Cannot resume from selected stage because upstream 'ingest' has no reusable artifact cache.` This indicates `retry_failed_stage()` currently depends on cache reuse availability, which is not guaranteed for historical failed runs.
- **Next:** Fix resume path in engine/service to hydrate upstream dependencies from prior run artifact refs (or direct store resolution) rather than requiring stage cache entries, then redeploy and re-test `run-57b6c9d0` retry end-to-end.

### 20260218-1443 — Patched production replay cache-dependency bug and redeployed

- **Action:** Implemented resume fallback path to hydrate upstream stage outputs from prior-run artifact refs when stage cache is missing (`src/cine_forge/api/service.py`, `src/cine_forge/driver/engine.py`), added coverage (`tests/unit/test_driver_engine.py`, `tests/unit/test_api.py`), and redeployed to Fly.
- **Result:** Success
- **Notes:** Local validation passed (`pytest -m unit`, `ruff check`). Post-deploy smoke checks passed again (`/api/health`, `/api/recipes`, `/api/projects/recent`, `/api/changelog`, HTML title + JS bundle 200).
- **Next:** Re-run live `run-57b6c9d0` retry to verify resume behavior now progresses without stage-cache precondition failures.

### 20260218-1443 — Live retry after redeploy: resume bug fixed, downstream data-path failure remains

- **Action:** Triggered `POST /api/runs/run-57b6c9d0/retry-failed-stage` producing `run-57b6c9d0-retry-21c4`; captured state/events and Fly logs.
- **Result:** Partial success
- **Notes:** Previous blocker (`Cannot resume ... no reusable artifact cache`) is resolved. Retry now runs `normalize` and `extract_scenes` successfully, but run ends with `background_error`: `Missing required upstream outputs for 'project_config': dependency 'extract_scenes'` because `extract_scenes` finished with zero artifacts on this screenplay input. This appears to be a downstream module/data-path issue rather than replay orchestration.
- **Next:** Triage why `extract_scenes` returns zero artifacts for this input (likely parser/classification edge case), then rerun retry to completion for full production confirmation.

### 20260218-1451 — Hardened empty-script guards in normalize/extract modules

- **Action:** Added explicit non-empty output validation in `script_normalize_v1` (`_require_non_empty_script_text`) and early non-empty canonical input validation in `scene_extract_v1` (`_extract_canonical_script`), then added regression tests in `tests/unit/test_script_normalize_module.py` and `tests/unit/test_scene_extract_module.py`.
- **Result:** Success
- **Notes:** This closes the silent-success path where blank script content could flow into scene extraction and downstream dependency checks; modules now fail fast with actionable errors.
- **Next:** Redeploy to Fly and re-run `POST /api/runs/run-57b6c9d0/retry-failed-stage` to confirm failure behavior is explicit and/or retry completes with valid extracted artifacts.

### 20260218-1455 — Deployed module guard hardening and revalidated live retry behavior

- **Action:** Deployed updated branch to Fly (`fly deploy --depot=false --yes`), reran production smoke checks (`/api/health`, `/api/recipes`, `/api/projects/recent`, `/api/changelog`, HTML title + JS bundle 200), and retried `POST /api/runs/run-57b6c9d0/retry-failed-stage` producing `run-57b6c9d0-retry-a0ea`.
- **Result:** Partial success
- **Notes:** Retry no longer fails late with missing downstream outputs; it now fails immediately at `normalize` with explicit non-retryable error: `script_normalize_v1 requires non-empty raw_input content...`. Run events include structured `stage_failed` payload (`error_class=ValueError`, `provider=code`, `model=code`, `terminal_reason=non_retryable_error`). Confirmed root source data remains empty: `GET /api/projects/the-body-4/inputs/d93d9cc3_The_Body.pdf` returns `content-length: 2` (blank body).
- **Next:** Fix/verify PDF extraction path in ingest for this project input so `raw_input.content` is non-empty, then rerun retry flow to confirm end-to-end completion through `project_config`.

### 20260218-1508 — Added ingest extraction failure guards and retry step-back recovery

- **Action:** Updated `story_ingest_v1` to fail on blank extracted source text, updated API input preview to return `422 input_extraction_failed` on blank extraction (`src/cine_forge/api/service.py`), and updated `retry_failed_stage()` to step back to `ingest` when prior `ingest` artifacts contain empty `raw_input.content`. Added Fly runtime dependency `poppler-utils` (`pdftotext`) in `Dockerfile`.
- **Result:** Success
- **Notes:** This removes silent-empty extraction behavior, gives operators actionable errors, and allows historical failed runs with bad cached ingest output to regenerate `raw_input` under current extraction logic.
- **Next:** Deploy to Fly, trigger `POST /api/runs/run-57b6c9d0/retry-failed-stage`, and validate whether `ingest` now produces non-empty `raw_input` for `The_Body.pdf`.

### 20260218-1511 — Deployed ingest recovery patch and validated production failure mode shift

- **Action:** Deployed to Fly with `poppler-utils` included, verified `pdftotext` exists in-machine (`/usr/bin/pdftotext`), validated project input preview now returns explicit `422 input_extraction_failed`, and triggered retry (`run-57b6c9d0-retry-a408`).
- **Result:** Partial success
- **Notes:** `retry_failed_stage` now correctly stepped back to `ingest` (instead of reusing bad `raw_input`) and failed fast with actionable message: `story_ingest_v1 could not extract readable text ... Extractor path: fallback_sparse`. Events are structured (`stage_started: ingest`, `stage_failed` with `error_class=ValueError`, `terminal_reason=non_retryable_error`).
- **Next:** Add OCR-capable extraction path in production image (or re-upload as text-selectable PDF/DOCX) so `ingest` can produce non-empty `raw_input` for this document and the run can complete end-to-end.

### 20260218-1520 — Re-uploaded text-selectable DOCX and completed immediate production retry

- **Action:** Opened project `the-body-4`, uploaded `sample_script.docx` to `/api/projects/the-body-4/inputs/upload`, then started a fresh run with the new stored input path via `/api/runs/start`.
- **Result:** Success
- **Notes:** New run `run-7551301e` completed end-to-end on production: `ingest=done`, `normalize=done`, `extract_scenes=done`, `project_config=done`, `background_error=null`. This validates that the pipeline and resilience changes are functioning when source text extraction is non-empty.
- **Next:** For the original `The_Body.pdf` file, decide between OCR-capable extraction enablement for that specific file path vs replacing the source input with a text-selectable document.

### 20260218-1609 — Implemented provider-health fallback pruning and expanded OCR runtime stack

- **Action:** Updated driver fallback orchestration to skip models on known-unhealthy providers (`src/cine_forge/driver/engine.py`) and added unit coverage (`test_driver_skips_unhealthy_provider_models_in_attempt_plan` in `tests/unit/test_driver_engine.py`). Expanded production image dependencies in `Dockerfile` to include OCR tooling (`ocrmypdf`, `tesseract-ocr`, `tesseract-ocr-eng`, `ghostscript`) alongside `poppler-utils`.
- **Result:** Success
- **Notes:** This closes the remaining partial acceptance criterion around skipping unhealthy providers when outages are detected. Full unit suite revalidated: `203 passed, 51 deselected`.
- **Next:** Deploy to Fly and verify OCR tool availability in-machine, then re-test `the-body-4` PDF preview/retry path for `The_Body.pdf`.

### 20260218-1613 — Deployed OCR runtime stack and validated production PDF text extraction

- **Action:** Deployed current `main` working tree to Fly (`fly deploy --depot=false --yes`) with OCR dependencies in image, reran production smoke checks, verified OCR binaries in-machine (`pdftotext`, `ocrmypdf`, `tesseract`, `gs`), and rechecked problematic input endpoint `GET /api/projects/the-body-4/inputs/d93d9cc3_The_Body.pdf`.
- **Result:** Success
- **Notes:** API smoke checks passed (`/api/health`, `/api/recipes`, `/api/projects/recent`, `/api/changelog`). HTTP UI fallback checks passed (`<title>CineForge</title>`, JS bundle `assets/index-UBJ_neA4.js` HTTP 200). The previously blank PDF preview now returns non-empty extracted text (`content-length: 16592`) with screenplay dialogue content, confirming production extraction for this path is now readable.
- **Next:** Trigger a fresh production run for `the-body-4` using `The_Body.pdf` and verify full end-to-end completion through `project_config`.

### 20260218-1615 — Live OCR-path run shows extraction fixed, normalization classification gate still blocks completion

- **Action:** Started fresh production run `run-37a6aa0e` on `/app/output/the-body-4/inputs/d93d9cc3_The_Body.pdf`, captured run state/events, and inspected generated artifacts (`raw_input v3`, `canonical_script v3`) on Fly machine.
- **Result:** Partial success
- **Notes:** OCR extraction is now working (`raw_input.content` non-empty, `pdf_extractor_selected=ocrmypdf`, output length ~16.4k chars), but `script_normalize_v1` classified input as `prose` (`confidence=0.35`) and emitted rejected canonical artifact with empty `script_text`. `extract_scenes` then failed fast as designed (`scene_extract_v1 requires non-empty canonical script text`).
- **Next:** Adjust normalization/classification heuristics for OCR-noisy screenplay PDFs (or add OCR-cleanup pre-normalization) so this document is treated as screenplay and yields non-empty canonical script.

### 20260218-1621 — Deferred PDF/OCR normalization follow-up to Story 049

- **Action:** Moved remaining OCR/noisy-PDF normalization gap out of Story 050 execution scope and into Story 049 backlog/tasks.
- **Result:** Success
- **Notes:** Story 050 remains scoped to provider resilience/retry/fallback/resume behavior. PDF/OCR extraction and OCR-noisy normalization quality tuning is now tracked under `docs/stories/story-049-import-normalization-format-suite.md`.
- **Next:** Re-validate Story 050 against resilience acceptance criteria only.

### 20260218-1630 — Marked Story 050 done with operator sign-off

- **Action:** Updated Story 050 status to `Done`, checked remaining conditional index-update task, and updated `docs/stories.md` row status for Story 050.
- **Result:** Success
- **Notes:** Operator explicitly approved closure despite dependency Story 039 remaining `To Do`; dependency accepted as non-blocking for this story's scoped deliverables.
- **Next:** Continue deferred OCR/noisy-PDF normalization work under Story 049.
