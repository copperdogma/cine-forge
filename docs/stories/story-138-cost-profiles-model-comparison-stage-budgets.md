---
id: "138"
title: "Cost Profiles, Model Comparison, and Stage Budget Controls"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R12 (Transparency & Control), vision-level preference: Radical transparency"
spec_refs:
  - "spec:8.1"
  - "spec:8.3"
adr_refs: []
depends_on:
  - "032"
category_refs:
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 138 — Cost Profiles, Model Comparison, and Stage Budget Controls

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R12 (Transparency & Control), vision-level preference: Radical transparency
**Spec Refs**: spec:8.1 (Cost Transparency), spec:8.3 (Subsumption-Based Model Strategy)
**ADR Refs**: None found after search; design context: `docs/design/decisions.md` ("Run detail page for power users")
**Depends On**: Story 032 (cost tracking and budget management)

## Goal

Extend the landed cost-tracking substrate with operator-facing decision tools: configurable cost profiles per stage or role, honest run-cost comparison across model choices, and optional per-stage budget caps. This story exists so CineForge can help users choose tradeoffs before they spend money, not just explain spend after the fact.

## Acceptance Criteria

- [ ] Cost profiles can be configured at project level and overridden per stage or per role using typed backend contracts rather than ad hoc UI state.
- [ ] Run planning surfaces show estimated cost differences for at least two model configurations, with the estimation method and uncertainty made explicit.
- [ ] Optional per-stage budget caps warn and pause cleanly between stages without corrupting run state, and resume behavior is preserved.
- [ ] Browser verification covers the updated Project Settings and Runs / Run Detail flows, and focused backend tests cover profile selection, comparison math, and stage-cap enforcement.

## Out of Scope

- Rebuilding the existing run/project cost summary, export, or report artifact paths from Story 032
- Provider benchmarking or eval-registry refresh beyond what is strictly needed to ground comparison assumptions
- AI-generated budgeting advice that is not backed by deterministic pricing and run-history data

## Approach Evaluation

- **Simplification baseline**: first verify whether deterministic pricing + existing stage history already produce a useful comparison without any new forecasting model. If that answers the operator question, do not add AI explanation layers.
- **AI-only**: weak fit. A model can describe tradeoffs, but it should not own authoritative cost planning or budget-cap logic.
- **Hybrid**: plausible for explanatory copy only: deterministic estimates and cap logic underneath, optional AI narration on top if the deterministic surface proves too dry.
- **Pure code**: strongest default candidate because pricing, precedence, and budget enforcement are trust surfaces that should remain exact and testable.
- **Repo constraints / ADRs**: reuse Project Settings, Runs, and Run Detail instead of adding a separate dashboard; keep project-scoped settings in `project.json`; define typed contracts before API/UI wiring; avoid growing `src/cine_forge/api/service.py`, `src/cine_forge/api/run_orchestrator.py`, `ui/src/pages/RunDetail.tsx`, or `ui/src/lib/types.ts` without extraction.
- **Existing patterns to reuse**: `src/cine_forge/services/cost_tracking.py`, `src/cine_forge/schemas/cost_tracking.py`, `src/cine_forge/driver/budget_guard.py`, the model-slot settings path in `project.json`, and the existing cost panels in Runs / Run Detail / Project Settings.
- **Eval**: deterministic fixture tests for comparison math and cap enforcement, plus browser verification for settings and runs surfaces. If any AI explanation layer is added, add a focused eval or explicit reasoning probe before defaulting it on.

## Tasks

- [ ] Define typed schemas for cost profiles, comparison inputs/outputs, and optional stage budget caps before wiring APIs or UI.
- [ ] Extend cost aggregation / planning services with deterministic comparison math grounded in model pricing and known run-stage data.
- [ ] Add project settings persistence plus Runs / Run Detail UI for profile selection, comparison display, and optional stage-cap status.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
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
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: extend the focused cost-tracking service/schema layer from Story 032; add a dedicated planner/comparison helper if comparison logic starts to bloat `CostTrackingService`. Stage-cap enforcement should extend `budget_guard.py` rather than grow more inline engine conditionals.
- **Data contracts**: new Pydantic models will be required for profile selection, comparison results, and per-stage cap settings/status before any API/UI wiring.
- **File sizes**: likely touch points already include large files: `src/cine_forge/services/cost_tracking.py` (`775`), `src/cine_forge/api/service.py` (`1082`), `src/cine_forge/api/run_orchestrator.py` (`668`), `ui/src/pages/RunDetail.tsx` (`512`), and `ui/src/lib/types.ts` (`552`). `/build-story` must run `make check-size` and extract rather than pile on.
- **Decision context**: reviewed `docs/ideal.md`, `docs/spec.md` (`spec:8.1`, `spec:8.3`), and `docs/design/decisions.md`. No dedicated ADR governs this slice; the main constraints are existing power-user surfaces and project-scoped settings rules.

## Files to Modify

- `src/cine_forge/schemas/cost_tracking.py` — add profile/comparison/stage-cap contracts (`190`)
- `src/cine_forge/services/cost_tracking.py` — comparison math and profile resolution, or extract a planner helper if this file grows further (`775`)
- `src/cine_forge/driver/budget_guard.py` — optional per-stage cap enforcement (`76`)
- `src/cine_forge/api/models.py` — typed request/response models for settings and comparisons (`475`)
- `src/cine_forge/api/service.py` — thin settings/comparison plumbing only; prefer helper-backed logic (`1082`)
- `src/cine_forge/api/run_orchestrator.py` — thread resolved profile/cap settings into runtime params when needed (`668`)
- `ui/src/components/ProjectSettings.tsx` — host extracted settings controls, not more inline fields (`449`)
- `ui/src/components/ProjectBudgetSettingsSection.tsx` — extend with profile/stage-cap inputs (`74`)
- `ui/src/pages/ProjectRuns.tsx` — add project-level comparison entry points (`150`)
- `ui/src/pages/RunDetail.tsx` — show comparison and per-stage cap state via extracted child components (`512`)
- `ui/src/lib/types.ts` — frontend types for profiles and comparison payloads (`552`)

## Redundancy / Removal Targets

- Any duplicated model-cost comparison logic split across UI components and backend services
- Any second budget-cap enforcement path outside `budget_guard.py`
- Any stale Story 032 notes that still imply cost-profile comparison is part of the shipped base slice

## Notes

This story was split out during Story 032 close-out so the landed trust surface could close cleanly. It owns the deferred scope from Story 032: configurable cost profiles, predictive model-cost comparison, and optional per-stage budget caps.

## Plan

To be written during `/build-story`.

## Work Log

20260319-1505 — created during Story 032 close-out: captured the deferred cost-profile/model-comparison/per-stage-cap scope in a dedicated Draft story so Story 032 can narrow to the shipped cost-tracking slice. Evidence: Story 032 validation and resume-proof follow-up test. Next step: promote to `Pending` when the comparison and stage-cap design is concrete enough to build.
