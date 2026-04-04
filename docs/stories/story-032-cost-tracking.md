---
id: "032"
title: "Cost Tracking and Budget Management"
status: "Done"
priority: "Unknown"
ideal_refs: []
spec_refs:
  - "spec:1.6"
  - "spec:8.1"
adr_refs: []
depends_on:
  - "002"
  - "014"
category_refs:
  - "spec:1"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 032: Cost Tracking and Budget Management

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:8.1 (Cost Transparency), spec:1.6 (Metadata & Auditing — cost data in artifacts)
**ADR Refs**: None found after search; design context: `docs/design/decisions.md` ("Run detail page for power users")
**Depends On**: Story 002 (pipeline foundation — cost recording hooks), Story 014 (role system — per-role cost attribution)

---

## Goal

Build the cost tracking and budget management system on top of the per-call cost hooks from Story 002. This includes cost dashboards, per-stage and per-run summaries, project/run budget caps, and cost report/export surfaces.

---

## Acceptance Criteria

### Cost Dashboard
- [x] Per-run cost summary:
  - [x] Total cost.
  - [x] Breakdown by stage.
  - [x] Breakdown by model (which AI models were used and their individual costs).
  - [x] Breakdown by role (which roles incurred what cost).
- [x] Per-project cost summary:
  - [x] Historical run costs.
  - [x] Cumulative project cost.
  - [x] Cost trends over time (are runs getting more or less expensive?).
- [x] Per-scene cost (how much did it cost to process each scene through the pipeline?).

### Budget Caps
- [x] Budget caps configurable:
  - [x] Per-project budget limit.
  - [x] Per-run budget limit.
- [x] When budget is approached:
  - [x] Warning at configurable threshold (e.g., 80%).
  - [x] Pipeline pauses at budget limit with clear message.
  - [x] User can increase budget and resume, or stop.
- [x] Budget enforcement does not corrupt state — pipeline stops cleanly between stages.

### Cost Data in Artifacts
- [x] Every AI-produced artifact includes cost data in its metadata (already hooked from Story 002).
- [x] Cost data includes: model used, input tokens, output tokens, estimated cost USD.
- [x] Cost data is auditable and queryable.

### Cost Reporting
- [x] Generate cost report artifact per run.
- [x] Export cost data (CSV/JSON) for external analysis.
- [x] Cost data available through Operator Console API.

### Schema
- [x] `CostSummary` Pydantic schema:
  ```python
  class StageCost(BaseModel):
      stage_id: str
      model: str
      input_tokens: int
      output_tokens: int
      estimated_cost_usd: float
      call_count: int

  class RunCostSummary(BaseModel):
      run_id: str
      total_cost_usd: float
      stages: list[StageCost]
      by_model: dict[str, float]
      by_role: dict[str, float]
      budget_limit_usd: float | None
      budget_remaining_usd: float | None
  ```
- [x] `BudgetConfig` schema.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for cost aggregation (per-stage, per-model, per-role).
- [x] Unit tests for budget cap enforcement (warning, pause, resume).
- [x] Unit tests for cost report generation.
- [x] Integration test: run pipeline with budget cap → pipeline pauses at limit.
- [x] Integration test: paused budget run resumes cleanly after budget increase.
- [x] Schema validation on all outputs.

---

## Design Notes

### Cost Transparency as Trust
For a personal project with real API costs, cost transparency is critical. The user needs to know before clicking "run" approximately what it will cost, and they need clear controls to prevent runaway spending. Budget caps are a safety net, not a feature.

### Model Visibility
Model usage should stay visible on cost surfaces so operators can reason about tradeoffs after a run. Configurable cost profiles, predictive cost comparison, and optional per-stage budget caps are tracked separately in [Story 138](/Users/cam/.codex/worktrees/9825/cine-forge/docs/stories/story-138-cost-profiles-model-comparison-stage-budgets.md).

---

## Approach Evaluation

- **AI-only**: Rejected. This is deterministic ledgering, aggregation, budget enforcement, export, and UI plumbing.
- **Hybrid**: Not needed for the core story. The only plausible hybrid slice is speculative forecasting copy, but the trust-critical surfaces here should come from deterministic code.
- **Pure code**: Chosen. Cost aggregation, budget enforcement, and export are infrastructure work; deterministic code is simpler and more testable here.
- **Success measure**: Add focused deterministic tests for summary building, budget pause/resume behavior, API/export responses, and the runs/run-detail UI surfaces. No model eval or prompt comparison is needed for the core story.
- **Baseline**: `rg -n "class (RunCostSummary|ProjectCostSummary|BudgetConfig|CostReport)|def (get_run_cost|get_project_cost|export_cost)" src ui tests | wc -l` currently returns `0`, so there is no typed cost-summary / budget-report surface yet. Existing substrate is partial: current tests contain `16` `cost_usd` / `total_cost_usd` assertions across `tests/unit/test_driver_engine.py` and `tests/unit/test_api.py`, and `.venv/bin/python -m pytest tests/unit/test_driver_engine.py -q -k 'cost or budget'` currently passes (`1` test).
- **Repo-fit evidence**: `spec:8.1` requires per-stage and per-run cost transparency plus project/run budget caps. `spec:1.6` requires auditable metadata. `AGENTS.md` requires project-scoped settings in `project.json`. `docs/design/decisions.md` says the Run Detail view is the advanced surface for stage status, duration, cost, and models, so the right move is to deepen existing run/runs/settings surfaces rather than add a separate dashboard.
- **Rejected alternatives**:
  - Stuff more ad hoc cost fields into raw `run_state.json` and let the UI compute everything from dicts. Rejected because this skips schema-first layer contracts and pushes more logic into already oversized files.
  - Build a separate cost dashboard route. Rejected because it conflicts with the existing UI decision that run detail/runs are the power-user surfaces and the screenplay remains the center of gravity.
  - Use AI to generate cost reports or warnings. Rejected because this would add variability to a trust surface that can be computed exactly in code.

---

## Tasks

- [x] Design and implement `RunCostSummary`, `StageCost`, `BudgetConfig` schemas.
- [x] Register schemas in schema registry.
- [x] Implement cost aggregation from existing per-call hooks.
- [x] Implement per-run cost summary generation.
- [x] Implement per-project cost tracking (historical).
- [x] Implement budget cap configuration.
- [x] Implement budget enforcement (warning, pause, resume).
- [x] Implement cost report artifact generation.
- [x] Implement cost export (CSV/JSON).
- [x] Wire into Operator Console API.
- [x] Add typed cost ledger / summary contracts before any new API/UI wiring.
- [x] Capture `run_id` / `stage_id` / best-available scene-or-entity context on role-cost records so by-role summaries are attributable per run.
- [x] Extract budget enforcement from `DriverEngine._execute_single_stage` before adding new warning / pause logic.
- [x] If per-scene cost is derived from a shared multi-scene call, expose the allocation method instead of implying exact attribution.
- [x] Check whether the chosen implementation makes existing cost calculations or UI summaries redundant; remove them or create a concrete follow-up.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run required checks for touched scope: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`.
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
- [x] Search all docs and update any related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

---

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning module/service**: cost aggregation and report generation should live in a focused backend helper/service plus schema file; project-level budget persistence should stay on the existing project settings path; budget pause/warning logic should be extracted behind a dedicated guard/helper instead of expanded inline in the engine.
- **Data contracts**: new Pydantic models must exist in a schema file before API/UI wiring: budget config/status plus typed run/project cost summaries and, if persisted, a `cost_report` artifact schema.
- **File sizes**: `src/cine_forge/driver/engine.py` is `1159` lines and `_execute_single_stage` spans lines `299-512` (`214` lines), so extraction is mandatory before new logic lands there. Other large touched files are `src/cine_forge/api/service.py` (`1077`), `src/cine_forge/api/run_orchestrator.py` (`613`), `ui/src/pages/RunDetail.tsx` (`466`), `ui/src/components/ProjectSettings.tsx` (`444`), and `ui/src/lib/types.ts` (`419`).
- **Decision context**: reviewed `docs/ideal.md`, `docs/spec.md` (`spec:1.6`, `spec:8.1`), Stories 002 and 014, `docs/design/decisions.md`, `docs/build-map.md`, and `AGENTS.md`. No ADR directly governs cost tracking; `docs/design/decisions.md` and `AGENTS.md` provide the relevant UI and project-settings constraints.

## Files to Modify

- `src/cine_forge/schemas/cost_tracking.py` — NEW: typed cost summary, budget, allocation, and report contracts
- `src/cine_forge/schemas/__init__.py` — `276`: export new schemas
- `src/cine_forge/driver/schema_registry.py` — `106`: register `cost_report` if the report is persisted as an artifact
- `src/cine_forge/driver/state.py` — `56`: minimally extend run-state schema if budget status must be persisted there
- `src/cine_forge/driver/engine.py` — `1159`: hook extracted budget/cost helpers only, not more inline orchestration
- `src/cine_forge/driver/budget_guard.py` — NEW: warning and cap enforcement at clean stage boundaries
- `src/cine_forge/services/cost_tracking.py` — NEW: aggregate run/project summaries and cost exports from run state, role logs, and artifact metadata
- `src/cine_forge/roles/runtime.py` — `373`: persist run/stage/entity context with role cost logs
- `src/cine_forge/api/models.py` — `459`: typed responses/requests for cost summary and budget settings
- `src/cine_forge/api/service.py` — `1077`: minimal project settings plumbing for budget config; prefer helper-backed logic
- `src/cine_forge/api/run_orchestrator.py` — `613`: thread run budget overrides into runtime params and keep run listings aligned
- `src/cine_forge/api/routers/costs.py` — NEW: run/project cost summary endpoints
- `src/cine_forge/api/routers/export.py` — `361`: cost CSV/JSON download endpoints
- `src/cine_forge/export/cost_report.py` — NEW: deterministic CSV/JSON rendering helpers
- `ui/src/lib/types.ts` — `419`: frontend cost summary and budget types
- `ui/src/lib/api/runs.ts` — `55`: typed cost-summary fetchers
- `ui/src/lib/hooks/runs.ts` — `126`: queries/mutations for new summary data
- `ui/src/lib/api/exports.ts` — `78`: cost export URLs
- `ui/src/pages/ProjectRuns.tsx` — `133`: project-level cost history / cumulative cost / trend surface
- `ui/src/pages/RunDetail.tsx` — `466`: per-run stage/model/role/budget view, likely via an extracted cost-summary child component
- `ui/src/components/ProjectSettings.tsx` — `444`: project budget controls, ideally via an extracted child section/component
- `tests/unit/test_cost_tracking.py` — NEW: summary builder and allocation-policy tests
- `tests/unit/test_budget_guard.py` — NEW: warning / cap / resume semantics
- `tests/unit/test_cost_export.py` — NEW: CSV/JSON export tests
- `tests/integration/test_cost_budget_pause.py` — NEW: run pauses cleanly at cap between stages
- `tests/unit/test_schema_registry.py` — `82`: registry coverage for any new artifact type

## Redundancy / Removal Targets

- Any duplicate frontend total-cost math that becomes stale once backend summaries are authoritative
- Any second path for cost report generation outside the shared summary-builder/export helpers
- Any unsynced split between project budget settings in `project.json`, runtime params, and UI-local state

## Plan

1. **Schema-first backend foundation**
   - Create `src/cine_forge/schemas/cost_tracking.py` with typed budget/status, run/project summary, allocation, and report contracts.
   - Export the models via `src/cine_forge/schemas/__init__.py`; register `cost_report` in `src/cine_forge/driver/schema_registry.py` if we persist a report artifact.
   - Add focused schema and registry tests before API/UI wiring so downstream code has stable contracts.
   - Done looks like: a synthetic run-cost fixture validates cleanly through the new models and the registry knows about any new artifact type.

2. **Build the cost attribution substrate**
   - Add `src/cine_forge/services/cost_tracking.py` to aggregate summaries from `run_state.json`, role invocation logs, and artifact metadata instead of teaching `api/service.py` or the UI to compute them ad hoc.
   - Extend `src/cine_forge/roles/runtime.py` to persist explicit `run_id`, `stage_id`, and best-available entity / scene context with each cost-bearing invocation. This is a small scope expansion folded into the story because accurate by-role summaries are not possible otherwise.
   - If per-scene numbers depend on shared multi-scene calls, record and surface the allocation method rather than implying exact attribution.
   - Impact / risk: existing `role_invocations.jsonl` entries do not cleanly map back to runs today, so summary code must tolerate legacy records without context.
   - Done looks like: fixture-backed summary code produces stable by-model, by-role, per-stage, and project-history outputs from real repo data shapes.

3. **Add budget enforcement without bloating the engine**
   - Extract a focused helper (for example `src/cine_forge/driver/budget_guard.py`) before modifying `DriverEngine._execute_single_stage`.
   - Thread project and per-run budget config through project settings and runtime params, then enforce warning / pause decisions at stage boundaries so the run stops cleanly and the existing resume flow can be reused.
   - Keep direct changes to `src/cine_forge/driver/engine.py` small: hook helper calls and persist only the minimal state needed for warnings or paused-at-budget messaging.
   - Impact / risk: `src/cine_forge/driver/engine.py` is already oversized and `_execute_single_stage` is `214` lines, so extraction is mandatory. `src/cine_forge/api/run_orchestrator.py` is also large enough that new request/summary fields should stay thin.
   - Done looks like: a run fixture or integration test shows warning emitted at threshold, pause at cap between stages, resume after budget increase, and no corrupted run state.

4. **Expose typed API and export surfaces**
   - Add typed run/project cost endpoints via a new focused router (`src/cine_forge/api/routers/costs.py`) rather than growing `src/cine_forge/api/app.py`.
   - Extend `src/cine_forge/api/models.py` with cost summary and budget request/response models. Persist project budget settings via the existing `project.json` update path in `src/cine_forge/api/service.py`.
   - Add deterministic CSV/JSON export helpers and wire them into `src/cine_forge/api/routers/export.py`, following the existing shot-list export pattern.
   - Impact / risk: cost exports and typed API responses must come from the same summary builder so the UI and downloaded reports cannot drift.
   - Done looks like: API tests can fetch run/project summaries, project settings round-trip budget config, and cost CSV/JSON downloads return stable content.

5. **Surface the data on existing UI routes**
   - Reuse `ui/src/pages/ProjectRuns.tsx` for project history / cumulative cost / trend and `ui/src/pages/RunDetail.tsx` for stage, model, role, and budget breakdown. Do not add a separate dashboard route.
   - Add project budget controls to `ui/src/components/ProjectSettings.tsx`, ideally via an extracted child section to avoid further inflating the dialog.
   - Update `ui/src/lib/types.ts`, `ui/src/lib/api/runs.ts`, `ui/src/lib/hooks/runs.ts`, and `ui/src/lib/api/exports.ts` so the UI consumes typed summaries instead of manual ad hoc totals where possible.
   - Impact / risk: `ui/src/pages/RunDetail.tsx`, `ui/src/lib/types.ts`, and `ui/src/components/ProjectSettings.tsx` are already large; extract focused cost/budget components instead of stacking more JSX in place. Also verify whether the legacy `/run/:runId` surface in `ui/src/pages/ProjectRun.tsx` needs a small compatibility pass so cost displays do not drift.
   - UI verification plan: use browser tools on `/{projectId}/runs` (history + trend), `/{projectId}/runs/{runId}` (stage/model/role/budget breakdown), and the project settings dialog (save a budget change, re-open, and confirm persistence). Download cost CSV/JSON once and confirm the browser console stays clean. If browser tooling is unavailable, follow `docs/runbooks/browser-automation-and-mcp.md`.
   - Done looks like: the UI reads typed backend data, renders the new trust surfaces without console errors, and cost export is discoverable from the existing runs flow.

6. **Validate, clean up, and update docs**
   - Add focused backend tests instead of growing `tests/unit/test_api.py` or `tests/unit/test_driver_engine.py` further: summary builder, budget guard, API/router, export, and one integration-style budget pause scenario.
   - Run the required backend/UI checks during implementation and at handoff, then update docs and the story work log with the chosen allocation and budget policies.
   - Redundancy plan: remove any duplicate frontend cost math that becomes stale once backend summaries are authoritative, and avoid leaving parallel report-generation paths outside the shared builder/export helpers.
   - Done looks like: all acceptance-criterion surfaces have direct test evidence or browser evidence, docs reflect the new routes/settings, and the work log records the decisions clearly enough for handoff.

### Human Approval / Scope Notes

- **Folded-in small scope expansion (`S`)**: extend role-cost logging with run/stage/entity context. Without this, by-role summaries are not attributable per run, so this is necessary to satisfy the story rather than a separate follow-up.
- **Decision needed before implementation**: per-scene cost for batched multi-scene calls should be shown as a transparent allocated estimate unless you want a larger `M` push for exacter attribution plumbing.
- **Applied scope trim**: keep project and per-run budget caps in the initial implementation; move optional per-stage budget caps plus configurable cost-profile/model-comparison work into [Story 138](/Users/cam/.codex/worktrees/9825/cine-forge/docs/stories/story-138-cost-profiles-model-comparison-stage-budgets.md).

## Work Log

*(append-only)*
20260319-1325 — exploration: confirmed Story 032 is buildable but stale relative to current substrate. Existing repo already tracks per-call artifact cost, per-stage/run totals, project model defaults, and advanced run-detail cost UI, so the missing work is typed cost summaries, project-level history, budget enforcement, export/report surfaces, and accurate by-role/by-scene attribution. Files likely to change: schema layer, engine/run orchestration, role runtime logs, API models/routes, export router, and runs/run-detail/settings UI. Files at risk: oversized `src/cine_forge/driver/engine.py`, `src/cine_forge/api/service.py`, `src/cine_forge/api/run_orchestrator.py`, `ui/src/pages/RunDetail.tsx`, `ui/src/components/ProjectSettings.tsx`, and `ui/src/lib/types.ts`. Consulted `docs/ideal.md`, `docs/spec.md` (`spec:1.6`, `spec:8.1`), Stories 002/014, `docs/design/decisions.md`, `docs/build-map.md`, and `AGENTS.md`; no ADR directly governs cost tracking. Patterns to reuse: project-scoped settings in `project.json`, existing `role_invocations.jsonl`, run-detail/runs power-user surfaces, and shot-list export routing. Surprise/risk: exact by-role and per-scene summaries are not derivable from current run-state totals alone, so the plan folds in explicit run/stage attribution on cost records and will need a transparent allocation policy for batched scene work. Next step: human review of the plan before implementation.
20260319-1343 — implementation start: promoted story to `In Progress` and started on the schema-first backbone before touching API/UI wiring. First slice is the typed cost/budget contracts plus the run-stage state additions needed to carry tokens, pause reasons, and budget context safely through the engine. Next step: land the new schema/service files and hook them into engine/runtime cost recording.
20260319-1448 — implementation: landed the core cost-transparency slice end to end. Added schema-first cost/budget/report contracts (`src/cine_forge/schemas/cost_tracking.py`), aggregation/report helpers (`src/cine_forge/services/cost_tracking.py`, `src/cine_forge/export/cost_report.py`), extracted budget enforcement (`src/cine_forge/driver/budget_guard.py`), and thin API routes (`src/cine_forge/api/routers/costs.py`) instead of pushing more logic into `DriverEngine` or the UI. Extended role-cost logging with `run_id`, `stage_id`, and best-available scene/entity context so by-role summaries are attributable per run, then reused existing runs/run-detail/settings surfaces with extracted UI panels instead of adding a new dashboard route. Evidence: focused tests passed for summary building, budget enforcement, exports, API wiring, registry coverage, and the clean pause-at-budget integration path; redundant ad hoc totals were removed by switching run surfaces to the typed backend summaries. Next step: full project checks plus runtime/browser smoke on an isolated seeded project.
20260319-1532 — verification: static and runtime verification completed for the implemented slice. Backend checks: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_cost_tracking.py tests/unit/test_budget_guard.py tests/unit/test_cost_export.py tests/unit/test_api_costs.py tests/unit/test_schema_registry.py tests/integration/test_cost_budget_pause.py -q` passed; `make test-unit PYTHON=.venv/bin/python` passed (`584 passed, 135 deselected, 1 pre-existing warning`); `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/` passed. UI checks: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed (lint still reports the pre-existing `react-refresh/only-export-components` warnings outside this story’s files; Vite still reports the existing large-chunk warning). Runtime smoke: isolated backend on `127.0.0.1:8001` answered `/api/health` with `{\"status\":\"ok\",\"version\":\"2026.03.19-01\"}`; seeded smoke project `story-032-ui-smoke` rendered cleanly at `/story-032-ui-smoke/runs` and `/story-032-ui-smoke/run/run-story-032`; browser console ended with `0` errors and `0` warnings after adding a missing description to the touched `ProjectSettings` dialog; exports responded at `/api/projects/story-032-ui-smoke/export/costs.csv` and `/api/projects/story-032-ui-smoke/export/costs.json`; screenshots captured the run history and run detail surfaces under Playwright output. Repo-wide `make lint PYTHON=.venv/bin/python` still fails on unrelated pre-existing issues in `.agents/skills/webapp-testing/scripts/with_server.py`, `benchmarks/scorers/*`, `scripts/check-compromises.py`, and `scripts/discover-models.py`, so the story-specific lint evidence is the scoped Ruff pass on `src/` and `tests/`. Remaining gap versus the original story text: cost-quality profile configuration/comparison is still open and should be treated as the main validation question for whether this story stays open or is rescaled before closure. Next step: `/validate`.
20260319-1447 — validation: implementation quality is solid for the shipped cost-tracking slice, but the story is not cleanly closable as written. Evidence rerun during validation: `make test-unit PYTHON=.venv/bin/python` passed (`584 passed, 135 deselected, 1 pre-existing warning`); `.venv/bin/python -m ruff check src/ tests/` passed; targeted backend tests passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed; browser verification on `/story-032-ui-smoke/runs`, `/story-032-ui-smoke/run/run-story-032`, and Settings > Pipeline ended with `0` console warnings/errors; API spot checks returned expected cost totals, budget status, and allocated per-scene attribution. Findings: the story still leaves explicit cost-quality profile/comparison acceptance criteria and related tests unchecked, and the "increase budget and resume" path is only partially evidenced because integration coverage stops at pause-at-cap while API coverage only verifies forwarding the resume override. Additional doc drift: `docs/build-map.md` still says no active stories are in progress. Recommended disposition: `Rescope then close` — trim the unimplemented cost-quality profile/comparison slice into a follow-up story, add or explicitly waive end-to-end resume evidence, then run `/mark-story-done`.
20260319-1509 — rescope: narrowed Story 032 to the shipped cost-tracking slice and moved deferred scope into [Story 138](/Users/cam/.codex/worktrees/9825/cine-forge/docs/stories/story-138-cost-profiles-model-comparison-stage-budgets.md). Added end-to-end resume evidence via `tests/integration/test_cost_budget_pause.py`, which now proves a paused run can resume with a higher budget and complete cleanly through the API. Next step: rerun close-out checks and, if clean, mark the story done.
20260319-1547 — completion: Story 032 closed after rescoping to the shipped trust surface, creating [Story 138](/Users/cam/.codex/worktrees/9825/cine-forge/docs/stories/story-138-cost-profiles-model-comparison-stage-budgets.md) for the deferred planning/tuning work, and adding end-to-end resume proof. Final evidence: `make test-unit PYTHON=.venv/bin/python` passed (`584 passed, 136 deselected, 1 pre-existing warning`); `.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed; browser verification from validation remains clean with `0` console warnings/errors. Backlog bookkeeping updated so Story 030 is no longer blocked on Story 032. Next step: `/check-in-diff`.
