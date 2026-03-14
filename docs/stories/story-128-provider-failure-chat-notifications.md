# Story 128 — Provider Failure Chat Notifications

**Priority**: Medium
**Status**: Pending
**Ideal Refs**: R12 (radical transparency)
**Spec Refs**: 20 (metadata & auditing)
**ADR Refs**: `docs/design/decisions.md` ("Inbox is a lens on actionable chat messages")
**Depends On**: Story 050 (Provider Resilience), Story 083 (Group Chat Architecture)

## Goal

Surface user-fixable provider failures directly in chat with enough context to act immediately. Today the system already has a narrow, string-matching notification path for some credit and rate-limit failures, but it is incomplete and inconsistent. Users should see "Gemini billing failed for stage X" or "Anthropic key expired" in chat without opening `run_state.json` or reading server logs.

## Acceptance Criteria

- [ ] Quota, billing, auth-expiry, and provider rate-limit failures append an actionable chat message when a run fails.
- [ ] The message includes provider, stage or run context when available, and a concrete next step the user can take.
- [ ] Detection works whether the useful error string appears in the top-level exception or only inside `run_state.json` attempt metadata.
- [ ] Failure notifications do not spam duplicates for the same failed run/stage.
- [ ] Automated tests cover at least one billing/quota case and one auth/rate-limit case.

## Out of Scope

- Automatic retry after the user tops up credits or replaces a key
- A global provider-health dashboard
- Non-user-fixable failures such as schema bugs, parsing bugs, or internal exceptions
- Replacing Story 050 retry/fallback orchestration

## Approach Evaluation

- **AI-only**: Wrong fit. Error classification for operator guidance should not require a model call.
- **Hybrid**: Possible if we wanted model-written remediation text, but deterministic templates are cheaper and safer.
- **Pure code**: Most likely. Error normalization and actionable message templates are deterministic infrastructure.
- **Repo constraints / ADRs**: Story 050 already persists attempt metadata and error strings. `docs/design/decisions.md` says the inbox is a lens on actionable chat messages, so user-fixable provider failures belong in chat rather than buried in run artifacts. `src/cine_forge/api/run_orchestrator.py` is already >600 lines, so a helper extraction may be warranted.
- **Existing patterns to reuse**: `_handle_run_failure_chat_notification()` in `src/cine_forge/api/run_orchestrator.py`, Story 050 attempt metadata, existing chat-store append path, existing billing/rate-limit notification copy.
- **Eval**: No model eval required. Distinguish approaches with unit tests around classification coverage and a smoke test that verifies the expected chat message appears after a simulated failure.

## Tasks

- [ ] Audit the current run-failure notification path and enumerate user-fixable provider failures we already see in real traces.
- [ ] Refactor provider-failure classification into a focused helper instead of growing the ad hoc substring block in `run_orchestrator.py`.
- [ ] Expand notification templates to cover quota/billing/auth-expiry/rate-limit with provider-aware guidance.
- [ ] Thread stage/provider context into the notification where available.
- [ ] Add tests for classification and chat-message emission, preferably in a focused test file rather than enlarging existing oversized API tests further.
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
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: Failure-to-chat translation currently lives in `src/cine_forge/api/run_orchestrator.py`. If the logic grows beyond simple normalization, extract a focused helper instead of deepening that class.
- **Data contracts**: No new cross-layer artifact schema should be necessary unless we choose to persist structured provider-failure metadata. Current work can likely stay within run-state attempt metadata plus `ChatMessagePayload`.
- **File sizes**: `src/cine_forge/api/run_orchestrator.py` (613, large), `src/cine_forge/api/models.py` (360), `tests/unit/test_api.py` (978, large). `make check-size` flags `run_orchestrator.py` and `test_api.py` as files to avoid bloating further.
- **Decision context**: Reviewed Story 050, `docs/design/decisions.md`, and the existing notification implementation in `run_orchestrator.py`. No ADR change appears necessary.

## Files to Modify

- `src/cine_forge/api/run_orchestrator.py` — notification trigger path and possibly helper extraction (613)
- `src/cine_forge/api/models.py` — only if structured chat metadata is needed (360)
- `tests/unit/test_api.py` or a new focused provider-failure test file — classification and notification coverage (978 if expanded)

## Redundancy / Removal Targets

- The current ad hoc string-matching block inside `_handle_run_failure_chat_notification()` if a dedicated classifier/helper replaces it
- Any duplicated billing/rate-limit message templates created elsewhere during implementation

## Notes

There is already partial implementation in `src/cine_forge/api/run_orchestrator.py`, including billing and rate-limit detection, so this is a hardening follow-up rather than a greenfield feature. The quality bar is operator clarity, not architectural novelty.

## Plan

To be written by `/build-story` after implementation planning and file-level exploration.

## Work Log

20260313-1658 — triage: created from inbox item "Surface provider quota/billing errors in chat". Existing homes checked: Story 050 covers retry/fallback mechanics and the codebase already has a partial notification path, but no active story owns expanding it to full operator-facing coverage. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. This stays narrowly scoped to operator-facing failure translation rather than a larger resilience redesign.
