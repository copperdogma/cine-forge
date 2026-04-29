---
id: "139"
title: "Long-Running Operation Black-Screen Recovery"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:1.6"
  - "spec:5.3"
  - "spec:5.6"
adr_refs:
  - "ADR-002"
depends_on:
  - "127"
category_refs:
  - "spec:1"
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "long-running-operations"
  - "chat-progress"
  - "production-qa"
legacy_system: ""
---

# Story 139 — Long-Running Operation Black-Screen Recovery

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:1.6 (Metadata & Auditing), spec:5.3 (Stage Progression), spec:5.6 (Full-Pipeline Manual Acceptance)
**ADR Refs**: ADR-002 (goal-oriented navigation and workflow-boundary next steps), `docs/design/decisions.md` ("Processing stays on the screenplay", "Progress via chat", "Live-updating run details")
**Depends On**: None (discovered during Story 127 validation on existing chat/run surfaces)

## Goal

Recover from the current production black-screen failure after long-running operations finish or transition. The original stale-run polling bug that created this story now has narrow guards in `useRunState` and `RunProgressCard`; the fresher product evidence is worse: after Script Breakdown, Deep Breakdown, Shot Planning, Generate Storyboards, and Render, the project can go black until refresh. Long-running operations must leave the screenplay/workspace visible, keep chat progress honest, and degrade to a recoverable message when the progress UI hits bad run state.

## Acceptance Criteria

- [x] Active run progress bookkeeping cannot crash the whole project shell when completion-time chat/status work encounters malformed, missing, or unexpected run data; it records a recoverable chat message and stops tracking the failing active run.
- [x] Historical progress cards still do not keep polling missing run IDs and still render a stable unavailable fallback when the run has been pruned or is otherwise unavailable.
- [x] The normal long-running operation path still preserves live progress, run-detail links, completion messages, and project/artifact invalidation for successful runs.
- [x] Focused regression coverage or a narrow harness exercises the progress-recovery seam without adding broad frontend test infrastructure.
- [x] Browser verification covers a representative project on desktop and mobile and confirms no black screen, no repeated missing-run polling loop, and no new console errors in the exercised flow.

## Out of Scope

- Rebuilding the run history UX or deleting old chat/progress messages from persisted journals
- Changing backend run-retention policy or synthesizing fake run state for missing historical runs
- Generic suppression of all 404s across the app
- Fixing separate production QA notes from the same inbox batch: missing XAI key, bad character resolution, image-generation quality, storyboard polling/moderation behavior, keyframes affordance, or final-render prompt/reference quality
- Broad refactors of `AppShell.tsx`, `use-run-progress.ts`, or the long-running action system beyond what this recovery guard requires

## Approach Evaluation

- **Simplification baseline**: keep the already-landed missing-run polling behavior intact. `useRunState` stops retry/refetch on 404 and `RunProgressCard` renders "Historical run details are unavailable" once the run list proves the run is gone, so do not reopen that path unless verification contradicts it.
- **AI-only**: wrong fit. No model reasoning is needed for UI crash containment, polling lifecycle control, or fallback rendering.
- **Hybrid**: unnecessary. Model-written status copy would not solve the shell failure and would add another long-running dependency.
- **Pure code**: strongest default. This is resilience around React query state, active-run chat bookkeeping, and completion/failure side effects.
- **Repo constraints / ADRs**: ADR-002 and the design decisions require progress and workflow-boundary next steps to appear in chat while the user stays on the screenplay/workspace. A black screen after every expensive operation directly violates that contract. Avoid growing oversized `AppShell.tsx` and `use-run-progress.ts` except for the narrow guard.
- **Existing patterns to reuse**: `ui/src/lib/use-run-progress.ts`, `ui/src/components/RunProgressCard.tsx`, `ui/src/lib/hooks/runs.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/ChatErrorBoundary.tsx`, `ui/src/lib/use-long-running-action.ts`, and the active-run restoration path in `AppShell.tsx`.
- **Eval**: this is UI/product-truth behavior, not a model-quality eval. Distinguish the fix with focused test coverage plus browser smoke on a real local project. A full paid production rerun is out of scope unless local verification reproduces only under real provider latency.

## Tasks

- [x] Recheck the stale missing-run path and confirm whether it is still the active failure source.
- [x] Implement the smallest active-run progress guard that prevents completion-time bookkeeping from taking down the project shell.
- [x] Preserve the existing historical missing-run fallback and active run live-polling behavior.
- [x] Add focused regression coverage for the chosen recovery seam without expanding oversized generic test files; prefer a new narrow Node test or helper seam.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
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

- **Owning class/module**: `ui/src/lib/use-run-progress.ts` owns active-run chat/progress side effects and is the correct narrow recovery seam for completion-time failures. `ui/src/components/RunProgressCard.tsx` owns rendering of persisted progress messages; `ui/src/lib/hooks/runs.ts` owns query/polling policy. `ui/src/components/AppShell.tsx` should only be touched if shell-level recovery proves necessary.
- **Data contracts**: no new cross-layer schema should be necessary if the UI treats 404 as "historical run unavailable". If the backend ends up returning a structured tombstone instead, define typed models before wiring the UI.
- **File sizes**: `make check-size` on 2026-04-28 flags `ui/src/lib/use-run-progress.ts` at 755 lines and `ui/src/components/AppShell.tsx` at 841 lines, so the story should prefer a small guard/helper over a broad refactor. The same check also flags many existing backend large files; none are touched by this UI recovery slice.
- **Decision context**: reviewed ADR-002 and `docs/design/decisions.md` sections on chat as the primary navigation intelligence, processing staying on the screenplay, progress via chat, run detail for power users, and live-updating run details. No ADR change appears necessary.

## Files to Modify

- `ui/src/lib/use-run-progress.ts` — add active-run progress recovery guard around completion/status side effects without changing backend run contracts
- `ui/src/components/RunProgressCard.tsx` — verify existing historical missing-run fallback remains sufficient; edit only if verification exposes a gap
- `ui/src/lib/hooks/runs.ts` — verify existing missing-run-aware polling remains sufficient; edit only if verification exposes a gap
- `ui/src/components/AppShell.tsx` — only if shell-level recovery is required; prefer not to grow this oversized file further
- `ui/tests/run-progress-recovery.test.ts` or equivalent narrow Node test — cover recoverable chat message shape / active-run clearing seam without introducing broad UI test infra

## Redundancy / Removal Targets

- Any logic that treats persisted historical `run_progress_*` messages as proof of an active run
- Any repeated "Loading run progress..." state shown forever after a missing-run 404 is already known
- Any ad hoc component-level 404 swallowing if a cleaner hook-level polling guard replaces it
- Any active-run completion effect path that can keep crashing on every render/poll after one malformed run state

## Notes

This story started as a 2026-03-20 Story 127 follow-up: browser verification on `/the-mariner-36/artifacts` showed repeated `GET /api/runs/run-773d6ac0/state` and `GET /api/runs/run-e6f953a4/state` 404s tied to historical run-progress cards. That old hypothesis no longer matches the code: `useRunState` now treats 404 as a missing-run error that disables retry/refetch, and `RunProgressCard` renders a stable historical fallback when `useRuns(projectId)` proves the run is absent.

The newer production QA evidence in `docs/inbox.md` is broader and higher priority: after Script Breakdown, Deep Breakdown, Shot Planning, Generate Storyboards, and Render, the screen goes black until refresh. The likely local risk is `useRunProgressChat`, which is mounted from `AppShell` outside `ChatErrorBoundary` and performs many completion-time chat mutations, artifact invalidations, route-action builds, and stage/event scans whenever active run state changes. If that effect throws on unexpected terminal run data, React can leave the user with the exact black-screen recovery pattern reported from production.

## Plan

1. Promote Story 139 from stale Draft to an active production-resilience story, preserving the old missing-run evidence as historical context.
2. Add a narrow recovery helper to `useRunProgressChat`: if active-run progress bookkeeping throws, log the error, add one operator-visible chat recovery message with a Run Details link, clear the active run, and let the rest of the project shell keep rendering.
3. Add focused Node-level regression coverage for the helper behavior where possible, then run methodology compile/check, UI lint/build, and browser smoke on a representative local project.
4. Leave unrelated production QA notes in `docs/inbox.md` for later triage; this story only owns black-screen recovery around long-running operations.

## Work Log

20260320-1605 — created from Story 127 validation follow-up: captured the stale-project historical run polling bug in a dedicated Draft story instead of leaving it as an oral note. Evidence: browser validation on `/the-mariner-36/artifacts` showed repeated `/api/runs/{id}/state` 404s tied to historical run-progress cards. Next step: promote to `Pending` once the narrowest fix point and regression harness are confirmed.

20260428-1530 — promoted and reshaped from stale historical-polling Draft to active production black-screen recovery story after `/triage`. Evidence: `docs/inbox.md` now reports black screens after every long-running operation class; `docs/ui-scout.md` is stale relative to the 2026-04-28 date; `useRunState` and `RunProgressCard` already contain the old missing-run guards; `useRunProgressChat` remains an oversized AppShell-mounted active-run side-effect surface outside `ChatErrorBoundary`. `make check-size` flagged `ui/src/lib/use-run-progress.ts` (755) and `ui/src/components/AppShell.tsx` (841), so the implementation should be a narrow guard rather than a broad refactor. Next step: implement the recovery seam and verify it does not regress normal progress cards.

20260428-1734 — implementation and first verification: added `ui/src/lib/run-progress-recovery.ts` with a single recoverable chat message builder plus `recoverRunProgressUiError`, and wired `ui/src/lib/use-run-progress.ts` so synchronous active-run progress effect failures and asynchronous failed-run sync failures are caught, logged, reported once in chat with a Run Details action, and followed by `clearActiveRun(projectId)`. Added `ui/tests/run-progress-recovery.test.ts` for message shape, dedupe, logging, and active-run clearing. No backend schema, run API, historical progress card, or AppShell changes were needed; this preserves the existing missing-run fallback instead of reopening it. Verification: `node --test ui/tests/run-progress-recovery.test.ts` passed (`2 passed`), and `node --test ui/tests/*.test.ts` passed (`17 passed`); `pnpm --dir ui run lint` passed; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed with only the existing Vite chunk-size warning; `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=.venv/bin/python` passed (`816 passed, 179 deselected, 1 existing unknown acceptance mark warning`); `pnpm methodology:compile` and `pnpm methodology:check` passed with expected warnings for the existing `api_service_and_operator_console` finding and stale UI scout cadence. Browser smoke used local dev at `http://127.0.0.1:8000` and `http://127.0.0.1:5174` on `brick-steel-full-retired-2`: desktop and mobile project home stayed visible with no black screen; console had 0 errors and only the existing screenplay highlighting warnings (`parenthetical`, `transition`); server logs showed 200s for project/artifact/chat/run-state requests, including `GET /api/runs/run-3dbf94cd/state`, with no missing-run 404 loop. Residual risk after this pass: the helper hardened a plausible crash seam, but did not yet prove the actual black-screen root cause.

20260428-1752 — root-cause reproduction and narrowed fix: built a temporary no-provider `shot_planning` smoke recipe with 800 sequential `test.echo_v1` stages and ran it against `brick-steel-full-retired-2` to create a cheap long-running active run without paid providers. The first smoke reproduced the concrete browser failure class: Chromium logged repeated `net::ERR_INSUFFICIENT_RESOURCES` for active run state/events plus project artifact-group and artifact-detail requests. The server logs showed the same request storm while the run advanced. Root cause: `useRunEventSSE` and `useRunProgressChat` invalidated `['projects', projectId, 'artifacts']` during active progress; TanStack Query prefix matching also invalidated mounted artifact-detail queries like `canonical_script/project/1` and `scene/scene_001/1`, so every busy progress event/poll refetched the Project Home's heavy artifact details. Fix: remove in-progress artifact invalidation from the active-run progress effect and `artifact_saved` event handling, throttle SSE-driven run state/event invalidation to at most once per 750ms, rely on `AppShell`'s active-run artifact-group polling for live counts, and make terminal project/artifact/run invalidations exact. Verification rerun: forced `run-story139-smoke-3` completed all 800 echo stages, the Project Home stayed rendered, screenshot `story-139-smoke-after-fix.png` showed the normal screenplay/chat UI rather than a black screen, and the browser reported 0 console errors after the run. This now points to the request-exhaustion storm as the actual root-cause class for the reported black screen, with the recovery helper kept as a secondary guard for malformed terminal run data. Next step: rerun the focused UI/build checks after cleanup, then `/validate` can decide whether to exercise one paid production-like operation before marking done.

20260428-1812 — final local verification after cleanup: removed the temporary smoke recipe, reran focused UI and methodology checks, then repeated the mobile browser smoke. Evidence: `node --test ui/tests/*.test.ts` passed (`17 passed`); `pnpm --dir ui run lint` passed; `cd ui && npx tsc -b` passed with the existing npm `min-release-age` warning; `pnpm --dir ui run build` passed with only the existing Vite chunk-size warning; `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=.venv/bin/python` passed (`816 passed, 179 deselected, 1 existing unknown acceptance mark warning`); `pnpm methodology:compile` and `pnpm methodology:check` passed with the expected architecture-audit/UI-scout warnings. Mobile viewport `390x844` stayed rendered with the chat/progress dialog visible, screenshot `story-139-smoke-mobile-after-fix.png`, and browser console remained at 0 errors. Local conclusion: the cheap long-running repro no longer produces the black-screen/resource-exhaustion failure after the invalidation patch.

20260428-2022 — validation pass after user smoke: user reported the local server path seems to work, then `/validate` reran the required checks and browser verification. Fresh command evidence from this validation pass: `node --test ui/tests/*.test.ts` passed (`17 passed`); `.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=.venv/bin/python` passed (`816 passed, 179 deselected, 1 known unknown acceptance mark warning`); `pnpm --dir ui run lint` passed; `cd ui && npx tsc -b` passed with the existing npm `min-release-age` warning; `pnpm --dir ui run build` passed with the existing Vite chunk-size warning; `./scripts/sync-agent-skills.sh --check` passed (`32 skills, 32 gemini wrappers`). Browser verification used the running local dev server on `brick-steel-full-retired-2`: desktop `1440x900` screenshot `story-139-validate-desktop.png` and mobile `390x844` screenshot `story-139-validate-mobile.png` both showed rendered UI with chat/progress visible and 0 console errors. The first `pnpm methodology:check` correctly failed because this validation note made generated methodology output stale; after `pnpm methodology:compile`, final `pnpm methodology:check` passed with expected warnings for the open `api_service_and_operator_console` finding and stale UI scout cadence. Recommendation: implementation is complete; proceed with `/mark-story-done`.

20260429-0005 — closeout via `/mark-story-done`: Story 139 is marked Done after validation confirmed the implementation is complete. Evidence remains the fresh `/validate` pass above plus the reproduced no-provider 800-stage request-exhaustion run and post-fix desktop/mobile browser checks. CHANGELOG.md now records the shipped black-screen recovery work. Generated methodology surfaces were refreshed after the status change. Next step: `/check-in-diff`.
