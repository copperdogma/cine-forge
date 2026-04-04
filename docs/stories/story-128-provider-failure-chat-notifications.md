---
id: "128"
title: "Provider Failure Chat Notifications"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R12 (radical transparency)"
spec_refs:
  - "spec:1.6"
adr_refs: []
depends_on:
  - "050"
  - "083"
category_refs:
  - "spec:1"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 128 — Provider Failure Chat Notifications

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R12 (radical transparency)
**Spec Refs**: spec:1.6 (Metadata & Auditing)
**ADR Refs**: `docs/design/decisions.md` ("Inbox is a lens on actionable chat messages")
**Depends On**: Story 050 (Provider Resilience), Story 083 (Group Chat Architecture)

## Goal

Surface user-fixable provider failures directly in chat with enough context to act immediately. Today the system already has a narrow, string-matching notification path for some credit and rate-limit failures, but it is incomplete and inconsistent. Users should see "Gemini billing failed for stage X" or "Anthropic key expired" in chat without opening `run_state.json` or reading server logs.

## Acceptance Criteria

- [x] Quota, billing, auth-expiry, and provider rate-limit failures append an actionable chat message when a run fails.
- [x] The message includes provider, stage or run context when available, and a concrete next step the user can take.
- [x] Detection works whether the useful error string appears in the top-level exception or only inside `run_state.json` attempt metadata.
- [x] Failure notifications do not spam duplicates for the same failed run/stage.
- [x] Automated tests cover at least one billing/quota case and one auth/rate-limit case.

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

- [x] Audit the current run-failure notification path and enumerate user-fixable provider failures we already see in real traces.
- [x] Refactor provider-failure classification into a focused helper instead of growing the ad hoc substring block in `run_orchestrator.py`.
- [x] Expand notification templates to cover quota/billing/auth-expiry/rate-limit with provider-aware guidance.
- [x] Thread stage/provider context into the notification where available.
- [x] Add tests for classification and chat-message emission, preferably in a focused test file rather than enlarging existing oversized API tests further.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
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

### Eval / Baseline

- **Success test**: a focused temp-dir harness against `RunOrchestrator._handle_run_failure_chat_notification()` that seeds `run_state.json`, invokes the failure handler, and inspects the resulting `chat.jsonl` entries. This is the right eval for this story because the work is deterministic infrastructure, not model behavior.
- **Baseline run on 2026-04-03**:
  - cases: `billing_top_level`, `rate_limit_top_level`, `auth_expired_top_level`, `attempt_only_quota`, `duplicate_same_run`
  - current score: **3/5**
  - passes: billing from top-level exception, rate-limit from top-level exception, quota/billing from `run_state.json` attempt metadata
  - failures: auth-expiry emits **no** chat message; repeated handling for the same failed run emits **duplicate** messages because the current message id is random
- **Approach comparison**:
  - **AI-only**: reject. Provider-error classification and remediation copy are deterministic and already available in structured retry metadata.
  - **Hybrid**: unnecessary. A model-written explanation layer would add cost and ambiguity without improving detection.
  - **Pure code**: chosen. The repo already persists `provider`, `error_code`, `request_id`, `transient`, and per-stage attempt history; the missing work is deterministic normalization and operator-facing phrasing.

### Repo-Fit / Optimality Evidence

- Story 050 already did the hard substrate work this story should reuse: `run_state.json` stage attempts now carry `provider`, `error_code`, `request_id`, and `transient`, so Story 128 should stop acting like only raw exception text exists.
- `docs/design/decisions.md` makes chat the project journal and inbox a filtered view of actionable chat messages. User-fixable provider failures therefore belong in chat, not only in run logs or run detail.
- `ChatStore.append()` already gives idempotent upsert-by-id. Stable message ids are the repo-fit way to satisfy the story's "do not spam duplicates" criterion without inventing a second dedupe system.
- `ChatMessagePayload` already supports `actions`, `route`, and `needsAction`, so this story does **not** need new API models or UI schema changes if it stays within the existing chat message contract.
- The main alternative, growing the current inline substring block inside `run_orchestrator.py`, is wrong for this repo because that file is already oversized and would keep classification logic entangled with thread orchestration.

### Structural Health Check

- `make check-size` findings in direct blast radius:
  - `src/cine_forge/api/run_orchestrator.py` — **684** lines, oversized
  - `src/cine_forge/api/models.py` — **495** lines, near the oversize threshold
  - `tests/unit/test_api.py` — **1338** lines, oversized and should not absorb more story-specific cases
  - `ui/src/lib/use-run-progress.ts` — **539** lines, oversized; avoid touching unless the backend-only path proves insufficient
  - `src/cine_forge/driver/retry_policy.py` — **255** lines, healthy and a good source of existing error-code/provider helpers
  - `tests/unit/test_chat_store.py` — **183** lines, healthy reference for stable idempotent append behavior
- Plan implication:
  - extract provider-failure classification/message building into a new focused helper instead of growing `run_orchestrator.py`
  - add a new focused unit test file instead of enlarging `tests/unit/test_api.py`
  - avoid UI file edits unless the runtime smoke proves the existing chat rendering cannot surface the backend message cleanly
- No new event type is needed.
- No new cross-layer Pydantic model is required if the notification remains a normal chat message using the existing `ChatMessagePayload` shape.

### Implementation Sequence

#### Task 1 — Extract deterministic provider-failure classification

- **Files**:
  - new `src/cine_forge/api/provider_failure_notifications.py`
  - `src/cine_forge/api/run_orchestrator.py`
- **Changes**:
  - add a focused helper that:
    - reads the failed stage plus latest failed attempt from `run_state.json` when available
    - prefers structured metadata (`provider`, `error_code`, `error`, `request_id`) over raw top-level exception text
    - classifies user-fixable failures into at least:
      - quota / billing
      - auth-expiry / invalid credentials
      - provider rate-limit / overload
    - builds provider-aware, stage-aware notification text with a concrete next step
  - keep the classifier deterministic and token-based, but use `401` / `403` / `429` / `503` / `529` plus explicit auth/billing phrases instead of the current loose two-bucket substring scan
- **Could break**:
  - false positives if auth tokens are too broad
  - missed provider context if the helper ignores stage-attempt metadata
- **Done looks like**:
  - the handler can explain `Anthropic billing failed during normalize` or `OpenAI credentials failed during analyze_scenes` without reading server logs manually

#### Task 2 — Make notifications idempotent and actionable

- **Files**:
  - `src/cine_forge/api/run_orchestrator.py`
  - new `src/cine_forge/api/provider_failure_notifications.py`
- **Changes**:
  - replace the current random-id chat append with a stable message id keyed by failed run/stage/classification so repeated handling upserts instead of spamming
  - promote the notification to an actionable chat message using the existing chat shape:
    - `type: "ai_suggestion"` is preferred because this is operator guidance, not a conversational answer
    - include an internal `View Run Details` route action
    - keep provider-console instructions in message text instead of adding new external-link action machinery
  - preserve the existing generic failed-run summary from `use-run-progress.ts` unless runtime verification shows it becomes misleading; do not widen scope into UI dedupe unless needed
- **Could break**:
  - duplicate suppression if the stable id is too narrow or too broad
  - backward compatibility with persisted chat rendering if the message shape drifts outside the current chat contract
- **Done looks like**:
  - repeated handling of the same failed run/stage updates a single chat message
  - the message includes stage/provider context and a direct path to inspect the run

#### Task 3 — Add focused regression coverage

- **Files**:
  - new `tests/unit/test_provider_failure_notifications.py`
  - optionally `tests/unit/test_chat_store.py` only if a tiny idempotence assertion reuse is cleaner than repeating setup
- **Changes**:
  - add classification tests for:
    - top-level billing/quota
    - top-level auth-expiry / invalid key
    - top-level rate-limit / overload
    - attempt-metadata-only detection when the top-level exception is generic
  - add emission/idempotence tests for:
    - stable message id suppresses duplicate spam on repeat handler calls
    - provider/stage context appears in the emitted chat content
    - route action is present when a run id exists
- **Could break**:
  - brittle tests if they assert full markdown strings instead of the meaningful fields/tokens
- **Done looks like**:
  - Story 128 has a small dedicated test seam and does not add more weight to `tests/unit/test_api.py`

#### Task 4 — Verify runtime behavior and docs

- **Files**:
  - `docs/stories/story-128-provider-failure-chat-notifications.md`
  - any directly related docs only if implementation changes operator behavior enough to warrant it
- **Changes**:
  - run required backend checks:
    - `make test-unit PYTHON=.venv/bin/python`
    - `.venv/bin/python -m ruff check src/ tests/`
  - runtime smoke:
    - use the temp-dir harness to seed a failed run with attempt metadata and confirm the emitted chat message is correct and idempotent
    - start backend, hit `/api/health`, and, if no UI files changed, still verify the chat/inbox path in browser tools against a seeded project so the message renders and the run-detail route works
  - update the story work log and task evidence
- **UI verification plan**:
  - open a project seeded with the notification
  - confirm the chat shows the provider-aware failure card
  - click `View Run Details`
  - check browser console stays clean
  - if browser tooling is blocked, follow `docs/runbooks/browser-automation-and-mcp.md`
- **Done looks like**:
  - backend tests pass, runtime smoke proves the handler works end-to-end, and the user-visible chat path is verified without touching oversized UI files

### Redundancy Plan

- Delete the ad hoc inline substring/template block from `_handle_run_failure_chat_notification()` once the helper lands.
- Do **not** add a second provider-failure classifier in the UI; backend chat persistence remains the single source of truth.
- Avoid new API models unless implementation proves the existing chat message contract is insufficient.

### Scope Adjustment

- No large scope expansion found.
- Small, necessary clarification folded into the story plan: the implementation should use structured stage-attempt metadata and stable chat ids, not just broader substring matching. That is required to satisfy the existing acceptance criteria for stage/provider context and duplicate suppression.

### Human-Approval Blockers

- None expected if the story stays backend-first.
- No new dependencies.
- No public API changes required.
- No schema migration required.

## Work Log

20260313-1658 — triage: created from inbox item "Surface provider quota/billing errors in chat". Existing homes checked: Story 050 covers retry/fallback mechanics and the codebase already has a partial notification path, but no active story owns expanding it to full operator-facing coverage. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. This stays narrowly scoped to operator-facing failure translation rather than a larger resilience redesign.
20260403-1813 — exploration: traced the live failure path from `RunOrchestrator._run_pipeline()` into `_handle_run_failure_chat_notification()` and audited the existing chat append seam plus Story 050 retry metadata. Files that will change: `src/cine_forge/api/run_orchestrator.py` and a new focused helper for provider-failure classification; likely tests in a new `tests/unit/test_provider_failure_notifications.py`. Files at risk of breaking: chat message persistence semantics, repeated failure handling for the same run, and any code that assumes the current random `error_<run>_<uuid>` message shape. ADRs / decision docs consulted: `docs/ideal.md` (R12 / radical transparency), `docs/spec.md` (`spec:1.6`), Story 050, Story 083, and `docs/design/decisions.md` (`Chat panel — primary control surface`, `Inbox is a filtered view of chat`). Patterns to follow: reuse structured `run_state.json` attempt metadata (`provider`, `error_code`, `request_id`, `transient`), leverage `ChatStore.append()` idempotent upsert with stable IDs, and keep the UI contract unchanged by staying within `ChatMessagePayload.actions/route`. Potential cleanup target: delete the current inline two-bucket substring block from `run_orchestrator.py` rather than layering a second classifier on top. Baseline evidence from a temp-dir harness on 2026-04-03: current implementation scores 3/5 targeted cases — billing top-level, rate-limit top-level, and attempt-only quota pass; auth-expiry emits no message; repeated handling of the same failed run emits duplicate chat entries. Next=write the implementation plan and await approval before coding.
20260403-1825 — implementation: extracted provider-failure classification and message building into new helper `src/cine_forge/api/provider_failure_notifications.py`, rewired `RunOrchestrator._handle_run_failure_chat_notification()` to load `run_state.json` and emit stable `ai_suggestion` chat messages with `View Run Details` actions, and added focused regression coverage in `tests/unit/test_provider_failure_notifications.py`. Impact: auth-expiry is now surfaced, quota/auth/rate-limit notifications include provider plus stage context, attempt-metadata-only failures are recognized, and repeated handling for the same run/stage upserts a single message instead of spamming duplicates. Evidence checked: `.venv/bin/python -m pytest tests/unit/test_provider_failure_notifications.py -q` passed (`6 passed`), `make test-unit PYTHON=.venv/bin/python` passed (`658 passed, 142 deselected`), `.venv/bin/python -m ruff check src/ tests/` passed, and the original temp-dir smoke harness improved from **3/5** to **5/5** targeted cases (`billing_top_level`, `rate_limit_top_level`, `auth_expired_top_level`, `attempt_only_quota`, `duplicate_same_run`). Scope notes: no UI files changed, so UI lint/build/browser checks were not required; the existing chat action contract and `runs/:runId` route were preserved. Central tenets check: T0 yes, no destructive data path added; T1 yes, helper isolates deterministic logic and keeps the orchestration class thinner; T2 yes, no new AI call or extra schema layer added; T3 yes, logic moved out of oversized `run_orchestrator.py` into a focused file and tests avoided `tests/unit/test_api.py`; T4 yes, work log now captures baseline, implementation, and verification evidence; T5 yes, this moves provider-failure transparency into the chat surface the Ideal already wants. Next=`/validate`.
20260403-1835 — validation: reran the full required validation suite and a fresh runtime/browser pass. Fresh checks in this validation pass: `make test-unit PYTHON=.venv/bin/python` (`658 passed, 142 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/` (clean), `.venv/bin/python -m pytest tests/unit/test_provider_failure_notifications.py -q` (`6 passed`), `pnpm --dir ui run lint` (passes with five pre-existing React fast-refresh warnings in unrelated UI files), `cd ui && npx tsc -b` (clean), `./scripts/sync-agent-skills.sh --check` (`skills-check: OK`), and a rerun of the temp-dir provider-failure smoke harness (`5/5` targeted cases). Browser verification used seeded disposable project `story-128-validate-browser`: the chat panel rendered the provider-aware auth-expiry card, `View Run Details` navigated to `/story-128-validate-browser/runs/story-128-validate-run`, and the final console check after fixing a missing `runtime_params` field in the disposable validation fixture returned zero errors. Validation conclusion: implementation satisfies the story acceptance criteria and is ready for `/mark-story-done`. Non-blocking note for future cleanup: the existing generic failed-run suggestion path in `ui/src/lib/use-run-progress.ts` still exists and may coexist with the new provider-specific card during live failed runs, but that overlap was not reproduced in this seeded validation pass and does not block closure.
20260403-1850 — follow-up UX tightening: addressed the one remaining failure-UX drift risk by making provider-specific failure messages authoritative in the UI. Added shared helper `ui/src/lib/run-failure-messages.ts`, filtered shadowed generic `progress_<run>_failed` cards during chat load in `ui/src/lib/chat-store.ts`, and updated `ui/src/lib/use-run-progress.ts` to sync chat from the backend before adding the generic failed-run card so live runs only add that fallback when no provider-specific diagnosis exists. Fresh evidence for this follow-up: `make test-unit PYTHON=.venv/bin/python` passed (`658 passed, 142 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` passed with the same pre-existing five fast-refresh warnings, `cd ui && npx tsc -b` passed, `pnpm --dir ui run build` passed, and browser verification with a seeded disposable project whose `chat.jsonl` intentionally contained both `progress_story-128-validate-run_failed` and `provider_failure_story-128-validate-run_scene_analysis_auth_openai` showed only the provider-specific card (`hasGeneric=false`, `hasProvider=true`) with `View Run Details` navigation still working and zero browser console errors. Scope decision: this was a small, tightly coupled story expansion rather than a new story because it removes the exact overlap risk surfaced during validation. Next=`/validate` if you want a fresh formal validation pass after the UI follow-up, otherwise `/mark-story-done`.
20260403-2139 — validation rerun after the UI follow-up: reran the required checks against the current backend+UI delta and repeated browser verification with a disposable project seeded to contain both the generic failed-run card and the provider-specific failure card. Fresh results in this pass: `make test-unit PYTHON=.venv/bin/python` passed (`658 passed, 142 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/` passed, `.venv/bin/python -m pytest tests/unit/test_provider_failure_notifications.py -q` passed (`6 passed`), `pnpm --dir ui run lint` passed with the same five pre-existing React fast-refresh warnings in unrelated files, `cd ui && npx tsc -b` passed, `pnpm --dir ui run build` passed, and `./scripts/sync-agent-skills.sh --check` passed (`skills-check: OK`). Browser verification on `http://127.0.0.1:5174/story-128-validate-browser` confirmed the dedupe behavior holds in the actual UI: only the provider-specific auth-expiry card rendered (`hasGeneric=false`, `hasProvider=true`), `View Run Details` navigated to `/story-128-validate-browser/runs/story-128-validate-run`, and the final browser console error check was clean. Validation conclusion: the duplicate-failure drift risk is resolved and the story is ready for `/mark-story-done`.
20260403-2204 — close-out: marked Story 128 `Done` after the clean validation rerun, checked the story-level acceptance criteria and workflow gate, updated `docs/stories.md`, and added CHANGELOG entry `2026-04-03-03`. Closure evidence is the 20260403-2139 validation pass: backend tests, backend lint, targeted provider-failure pytest, UI lint/typecheck/build, skill sync, and browser verification were all clean. Next=`/check-in-diff`.
