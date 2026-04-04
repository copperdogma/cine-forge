---
id: "139"
title: "Historical Run Progress Cards Stop Polling Missing Runs"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R12 (radical transparency)"
spec_refs:
  - "spec:1.6"
adr_refs: []
depends_on:
  - "127"
category_refs:
  - "spec:1"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 139 — Historical Run Progress Cards Stop Polling Missing Runs

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R12 (radical transparency)
**Spec Refs**: spec:1.6 (Metadata & Auditing)
**ADR Refs**: `docs/design/decisions.md` ("Right Panel — Chat primary interaction surface", "Run detail page for power users", "Live-updating run details")
**Depends On**: None (discovered during Story 127 validation on existing chat/run surfaces)

## Goal

Prevent persisted run-progress messages in chat from behaving like live runs when their referenced run state no longer exists. On older or stale projects, historical `run_progress_*` messages currently keep querying `/api/runs/{id}/state`, which spams console/network errors on artifact pages even though no run is active. The UI should preserve useful historical context without masking active run progress or degrading stale-surface trust.

## Acceptance Criteria

- [ ] Opening a project whose chat history contains progress messages for missing runs does not keep repeatedly requesting `/api/runs/{id}/state` after the missing-run condition is known.
- [ ] Historical progress messages render a stable unavailable/archived fallback, or otherwise stop presenting themselves as live run monitors, while active runs and run detail pages keep their current live polling behavior.
- [ ] Browser verification on a known stale project surface confirms the repeated run-state 404 console noise is gone, and focused regression coverage exists for the chosen guard path.

## Out of Scope

- Rebuilding the run history UX or deleting old chat/progress messages from persisted journals
- Changing backend run-retention policy or synthesizing fake run state for missing historical runs
- Generic suppression of all 404s across the app
- Broad refactors of `AppShell.tsx`, `use-run-progress.ts`, or the long-running action system beyond what this bug requires

## Approach Evaluation

- **Simplification baseline**: first confirm the bug is only historical chat progress cards calling live polling hooks after the run has disappeared. If a small UI-side guard fixes it without changing API contracts, prefer that over any backend work.
- **AI-only**: wrong fit. No model reasoning is needed for polling lifecycle control or fallback rendering.
- **Hybrid**: unnecessary. Adding model-written explanations to a missing-run trust surface would increase complexity without solving the bug.
- **Pure code**: strongest default candidate. This is query/polling lifecycle control plus fallback rendering.
- **Repo constraints / ADRs**: chat is the primary right-panel surface, but live power-user polling belongs on run detail. Historical chat context should not impersonate an active run. Avoid growing oversized `ui/src/components/AppShell.tsx` or `ui/src/lib/use-run-progress.ts` if a smaller seam exists.
- **Existing patterns to reuse**: `ui/src/components/RunProgressCard.tsx`, `ui/src/lib/hooks/runs.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/AppShell.tsx`, `ui/src/pages/RunDetail.tsx`, and the existing active-run restoration path.
- **Eval**: distinguish the fix with a browser repro on a known stale project plus focused regression coverage around the missing-run refetch behavior. If no frontend unit harness exists, use the smallest extracted helper or browser automation check instead of adding broad new test infrastructure.

## Tasks

- [ ] Reproduce and document the missing-run polling path on a deterministic stale project, including which component owns the repeated requests after the first 404.
- [ ] Implement the smallest guard that stops refetching unresolved historical run IDs while preserving live polling for active runs and run detail pages.
- [ ] Add a stable historical fallback for progress cards whose runs are unavailable, or explicitly collapse them if that proves cleaner while keeping historical context readable.
- [ ] Add focused regression coverage for the chosen guard path without expanding oversized generic test files; prefer a new narrow test file or helper seam.
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

- **Owning class/module**: `ui/src/components/RunProgressCard.tsx` owns rendering of persisted progress messages; `ui/src/lib/hooks/runs.ts` owns query/polling policy. `ui/src/components/AppShell.tsx` should only be touched if active-run restoration is reviving dead runs.
- **Data contracts**: no new cross-layer schema should be necessary if the UI treats 404 as "historical run unavailable". If the backend ends up returning a structured tombstone instead, define typed models before wiring the UI.
- **File sizes**: `ui/src/components/RunProgressCard.tsx` (136), `ui/src/lib/hooks/runs.ts` (169), `ui/src/lib/chat-store.ts` (392), `ui/src/components/AppShell.tsx` (683, oversized), `ui/src/lib/use-run-progress.ts` (536, oversized). `make check-size` also flags `tests/unit/test_api.py` (1299), so the story should avoid piling this regression into generic oversized test files.
- **Decision context**: reviewed `docs/design/decisions.md` sections on chat as the default interaction surface and live-updating run details, plus Story 127 validation evidence. No ADR change appears necessary.

## Files to Modify

- `ui/src/components/RunProgressCard.tsx` — stop historical cards from acting like live run monitors and render a stable missing-run fallback (136)
- `ui/src/lib/hooks/runs.ts` — add missing-run-aware polling behavior or caller options for historical run-state consumers (169)
- `ui/src/components/AppShell.tsx` — only if active-run restoration needs a dead-run guard; prefer not to grow this oversized file further (683)
- `ui/src/lib/use-run-progress.ts` — only if the active-run tracker is leaking historical state into the chat surface; prefer not to grow this oversized file further (536)
- `ui/src/lib/hooks/runs.missing-run.test.ts` or equivalent narrow regression harness — cover the chosen polling/fallback seam without introducing broad UI test infra

## Redundancy / Removal Targets

- Any logic that treats persisted historical `run_progress_*` messages as proof of an active run
- Any repeated "Loading run progress..." state shown forever after a missing-run 404 is already known
- Any ad hoc component-level 404 swallowing if a cleaner hook-level polling guard replaces it

## Notes

This bug was discovered on 2026-03-20 during Story 127 validation. Browser verification on `/the-mariner-36/artifacts` showed repeated `GET /api/runs/run-773d6ac0/state` and `GET /api/runs/run-e6f953a4/state` 404s while the stale badges themselves rendered correctly. The current likely failure path is: historical chat progress cards render `RunProgressCard`, `RunProgressCard` calls `useRunState(runId)`, and `useRunState` keeps refetching every 2 seconds whenever `data?.state?.finished_at` is absent, which includes 404 cases. The fix should stay narrow and avoid inventing backend tombstones unless a UI-side guard proves insufficient.

## Plan

To be written during `/build-story`.

## Work Log

20260320-1605 — created from Story 127 validation follow-up: captured the stale-project historical run polling bug in a dedicated Draft story instead of leaving it as an oral note. Evidence: browser validation on `/the-mariner-36/artifacts` showed repeated `/api/runs/{id}/state` 404s tied to historical run-progress cards. Next step: promote to `Pending` once the narrowest fix point and regression harness are confirmed.
