# Story 127 — Artifact Health Semantics + Chat Model Disclosure

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R11 (readiness clarity), R12 (radical transparency)
**Spec Refs**: spec:1.3 (change propagation / stale state), spec:1.6 (Metadata & Auditing)
**ADR Refs**: ADR-002, `docs/design/decisions.md` ("Inline stale indicators")
**Depends On**: Story 083 (Group Chat Architecture), Story 088 (Staleness UX), Story 126 (Frontend Chat and Data-Layer Decomposition)

## Goal

Finish the remaining transparency gap for Story 127. Story 031 already landed the shared artifact-health wording and stale explanation path that originally motivated the first half of this story, but chat responses still do not tell the user which model is speaking. The remaining work is to make chat provenance understandable at a glance while re-verifying that the shared health semantics stay authoritative across the UI.

## Acceptance Criteria

- [x] Shared artifact-health rendering uses user-facing language across entity pages, artifact pages, and list pages. Bare `valid` labels with no explanation are eliminated. Verified during 20260320 exploration; landed earlier via Story 031 / commit `5456d31`.
- [x] Stale badges expose an explanation affordance everywhere health appears. Where a concrete stale reason exists, the tooltip shows it; otherwise the copy explains what stale means and what action the user can take. Verified during 20260320 exploration; shared `HealthBadge` + `health.ts` already carry this path.
- [x] `ui/src/pages/ProjectArtifacts.tsx` no longer maintains a parallel health badge implementation; all health semantics flow through the shared component path. Verified during 20260320 exploration; duplicate local badge path is already gone.
- [x] Chat messages persist model metadata for AI speakers, and the UI shows that model once per response group in a subtle, non-repetitive way. Verified on 2026-03-20 via backend/unit coverage plus browser smoke on `/project_smoke_mvp_stale/artifacts`, where the assistant response rendered a `Claude Sonnet 4.6` badge.
- [x] Browser verification re-checks at least one current/stale health surface and one chat thread. No new console errors are introduced. Verified on 2026-03-20 against local project `project_smoke_mvp_stale`; artifacts list rendered `Current` badges and the chat panel stayed console-clean.

## Out of Scope

- Reworking staleness propagation itself or semantic change assessment
- Exposing token/cost usage on every chat message
- Full chat transcript redesign or per-tool model attribution
- Renaming artifact health enums in stored data

## Side Requirement

- Validation on 2026-03-20 found unrelated stale-project historical run-progress cards repeatedly polling missing `/api/runs/{id}/state` endpoints. Story 127 does not absorb that implementation, but it now explicitly requires the bug to be tracked as follow-up [Story 139](story-139-historical-run-progress-cards-stop-polling-missing-runs.md) rather than silently dropped.

## Approach Evaluation

- **AI-only**: Not appropriate. This is a UI semantics and metadata plumbing problem, not a reasoning problem.
- **Hybrid**: Possible if we wanted AI-written tooltip copy from stale causes, but that adds needless variability to a trust surface.
- **Pure code**: Most likely. Health semantics, tooltip copy, and chat model attribution should be deterministic.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` already require inline stale indicators with hover explanation. The shared `HealthBadge` is now the single source of truth for health semantics, so this story should not reintroduce any parallel badge path. `src/cine_forge/ai/chat.py` is already oversized, so any model-metadata change should stay surgical and keep presentation logic in the UI.
- **Existing patterns to reuse**: `ui/src/components/HealthBadge.tsx`, `ui/src/components/chat/ChatMessageItem.tsx`, `ui/src/components/ChatPanel.tsx`, `ui/src/lib/chat-store.ts`, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/api/chat.ts`, `ChatMessagePayload`.
- **Eval / baseline**: No model eval needed. This is deterministic plumbing/UI work. Baseline as of 2026-03-20: the first 3 acceptance criteria already pass in current HEAD, but the remaining chat provenance criteria fail because `ChatMessagePayload`, `ChatMessage`, and streamed chat chunks do not carry a `model` field, and `ChatMessageItem.tsx` renders no model metadata.

## Tasks

- [x] Audit all artifact-health surfaces and document where semantics still diverge from Story 088. Exploration on 2026-03-20 found the divergence already closed by Story 031 / commit `5456d31`.
- [x] Extend the shared health-badge path to support explanatory tooltip text and stale-reason plumbing where available. Verified in current HEAD during 2026-03-20 exploration.
- [x] Remove the duplicate local `HealthBadge` implementation from `ui/src/pages/ProjectArtifacts.tsx`. Verified in current HEAD during 2026-03-20 exploration.
- [x] Add model metadata to persisted/streamed chat messages and thread it through frontend types. Implemented via `ChatMessagePayload`, streamed chat chunks, frontend types, store updates, and persisted finalized chat messages.
- [x] Render a subtle model label in the chat UI without repeating it on every bubble from the same response group. Implemented in `ui/src/components/chat/ChatMessageItem.tsx` using a compact metadata badge next to the role label.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up. Result: no frontend speaker/model inference added; updated stale character-model comments so code/docs match runtime behavior.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui install --frozen-lockfile`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Capture unrelated validation-discovered stale-project historical run polling noise as a dedicated follow-up story rather than leaving it implicit. Done via Story 139.
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

- **Owning class/module**: Shared UI status remains owned by `ui/src/components/HealthBadge.tsx`; this story should only regression-check that path. Chat provenance rendering belongs in `ui/src/components/chat/ChatMessageItem.tsx`, with `ui/src/components/ChatPanel.tsx` and `ui/src/lib/chat-store.ts` responsible for preserving streamed metadata.
- **Data contracts**: `ChatMessagePayload`, streamed chat chunk types, and `ui/src/lib/types.ts` need an optional `model` field if actual runtime model attribution is surfaced. No artifact schema change is required for health semantics.
- **File sizes**: `ui/src/components/chat/ChatMessageItem.tsx` (236), `ui/src/lib/api/chat.ts` (143), `ui/src/lib/chat-store.ts` (379), `ui/src/components/ChatPanel.tsx` (377), `ui/src/lib/types.ts` (598, oversized), `ui/src/lib/use-run-progress.ts` (532, oversized), `src/cine_forge/api/models.py` (479), `src/cine_forge/api/app.py` (1045, oversized), `src/cine_forge/ai/chat.py` (2202, oversized). `make check-size` confirms the large-file risk, so implementation must stay field-plumbing-only in those oversized files.
- **Decision context**: Reviewed ADR-002, `docs/design/decisions.md`, Story 088, and the UI reuse directives in `AGENTS.md`. No new ADR appears necessary because this is correcting drift from existing decisions.

## Files to Modify

- `docs/stories/story-127-artifact-health-semantics-chat-model-disclosure.md` — record exploration findings, residual scope, and implementation plan (147)
- `ui/src/components/chat/ChatMessageItem.tsx` — add subtle model attribution rendering (236)
- `ui/src/lib/api/chat.ts` — add stream chunk support for model metadata (143)
- `ui/src/lib/chat-store.ts` — preserve model metadata through streaming and persistence helpers (379)
- `ui/src/components/ChatPanel.tsx` — thread streamed model metadata into the visible thread state (377)
- `ui/src/lib/types.ts` — add frontend type support for chat model metadata (598)
- `ui/src/lib/use-run-progress.ts` — keep automated insight messages aligned if they share the same renderer path (532)
- `src/cine_forge/api/models.py` — extend `ChatMessagePayload` if runtime model is persisted (479)
- `src/cine_forge/api/app.py` — include model metadata in streamed event payloads where chat chunks are serialized (1045)
- `src/cine_forge/ai/chat.py` — emit actual runtime model metadata with streamed/persisted messages only; avoid broader churn (2202)
- `tests/unit/test_chat_store.py` — cover round-trip persistence for the new optional chat message field
- `tests/unit/test_chat_stream_provenance.py` — assert model metadata is emitted on streamed role/text chunks

## Redundancy / Removal Targets

- Any frontend-only model inference derived from speaker name instead of persisted/streamed `model`
- Any duplicate chat metadata rendering that repeats the model on every bubble
- No new health-badge duplication should be introduced; the existing shared `HealthBadge` path stays authoritative

## Notes

User report that prompted triage: the entity page showed `Stale` without saying what it means, and `valid` sounded like a validation result rather than "current". Exploration on 2026-03-20 found that health-semantics fix already landed in Story 031; the remaining live gap is chat model disclosure. Candidate wording to test during implementation remains subtle rather than loud, because the user needs provenance, not a transcript redesign.

## Plan

1. **Residual scope adjustment**
   - Treat the artifact-health portion of Story 127 as already satisfied by Story 031 / commit `5456d31`, and keep this story focused on the remaining chat provenance gap plus a browser regression pass over one health surface.
   - This is the smallest coherent scope because re-implementing health semantics would duplicate code that already exists, while shipping chat model disclosure is still required to satisfy the original transparency goal.
   - Done when the story text, acceptance criteria, and tasks no longer imply unfinished health-badge work that current HEAD already satisfies.

2. **Backend provenance plumbing**
   - Files: `src/cine_forge/api/models.py`, `src/cine_forge/api/app.py`, `src/cine_forge/ai/chat.py`, `tests/unit/test_chat_store.py`.
   - Add an optional `model` field to `ChatMessagePayload`, emit the actual runtime model on AI chat chunks, and persist that field in stored chat messages without changing user-message payloads.
   - Repo fit: this keeps provenance at the data-contract boundary that already exists instead of inventing a second provenance lookup path. It also avoids frontend guesswork, which would be wrong in this repo because `src/cine_forge/ai/chat.py` comments currently imply a character-model split that the live call path does not consistently enforce.
   - Risks / impact: streamed event payload shape changes, saved chat JSONL records gain one optional field, and oversized files (`src/cine_forge/api/app.py`, `src/cine_forge/ai/chat.py`) must be touched conservatively.
   - Done when both live-streamed and persisted AI messages expose the same `model` value.

3. **Frontend metadata threading**
   - Files: `ui/src/lib/api/chat.ts`, `ui/src/lib/types.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/ChatPanel.tsx`, `ui/src/lib/use-run-progress.ts`.
   - Extend streamed chunk types and chat message types with optional `model`, preserve that field through the streaming placeholder lifecycle, and keep auto-insight messages aligned if they use the same renderer path.
   - Repo fit: this follows the existing Story 126 decomposition by threading one field through the established API/store/component pipeline instead of adding a parallel chat-provenance helper.
   - Structural health: `ui/src/lib/types.ts` (598) and `ui/src/lib/use-run-progress.ts` (532) are already oversized, so this task should remain a narrow field-plumbing edit only. If the change wants a broader refactor, stop and split it.
   - Done when reloading a chat thread retains the model metadata and UI builds/typechecks cleanly.

4. **Chat UI disclosure**
   - Files: `ui/src/components/chat/ChatMessageItem.tsx`.
   - Render the model label once per grouped AI response in the existing metadata band near speaker/context information. Do not repeat it on every bubble, do not surface it for user messages, and do not add token/cost chrome in this story.
   - Repo fit: the current chat item already owns speaker and context display, so colocating model provenance there is simpler and more legible than inventing a header/footer layer.
   - Rejected alternatives: frontend inference from speaker names would drift from reality, per-tool attribution is out of scope, and a new provenance endpoint/service would duplicate data already moving through the chat payloads.
   - Done when grouped AI responses show a subtle model tag without making the transcript noisier.

5. **Verification, redundancy, and docs**
   - Required checks: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`.
   - Browser verification: run the app, re-check one health surface (`/artifacts` or an entity/detail page) to confirm no regression, then open a chat thread, send one prompt, verify the streamed response shows the model label, capture a screenshot, and confirm the JS console stays clean. If browser tooling fails, use `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
   - Redundancy plan: remove any temporary/frontend-only model inference or repeated metadata rendering if it appears during implementation; otherwise record a concrete follow-up instead of leaving ambiguous helper paths behind.
   - Docs impact: search for story/docs text that claims chat provenance already exists or that health semantics are still missing, and update only the files actually made stale by this work.
   - Done when the remaining unchecked acceptance criteria pass, runtime smoke evidence is in the work log, and no redundant metadata path remains.

**Structural health check**

- `make check-size` run on 2026-03-20. Oversized files relevant to this story: `src/cine_forge/ai/chat.py` (2202), `src/cine_forge/api/app.py` (1045), `ui/src/lib/types.ts` (598), `ui/src/lib/use-run-progress.ts` (532).
- Schema-first requirement applies: `ChatMessagePayload` must define `model` before backend/API/UI code consumes it.
- No new event types, dependencies, or migrations are expected.

**Human gate / approval ask**

- Recommended scope adjustment: keep Story 127 open only for chat model provenance and regression verification of the already-landed health semantics. Relative effort: `S`.
- No new dependency or ADR blocker is expected.

## Work Log

20260313-1658 — triage: created from inbox items "Stale: why is this entity listed as stale?" and "show what model is actually doing the chatting". Existing homes checked: Story 088 covers pipeline/inbox stale UX but not entity/detail/list badges; no existing story owns chat model disclosure. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. Acceptance criteria, decision context, and touched-file map are already concrete enough for `/build-story`.
20260320-1440 — exploration: reviewed `docs/ideal.md`, ADR-002, `docs/design/decisions.md`, Story 088, Story 126, and the live chat/health code paths. Verified that Story 031 / commit `5456d31` already landed shared health semantics (`ui/src/lib/health.ts`, `ui/src/components/HealthBadge.tsx`, `ui/src/pages/ProjectArtifacts.tsx`), so the remaining gap is chat model disclosure only. Files expected to change for implementation: `src/cine_forge/api/models.py`, `src/cine_forge/api/app.py`, `src/cine_forge/ai/chat.py`, `ui/src/lib/api/chat.ts`, `ui/src/lib/types.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/ChatPanel.tsx`, `ui/src/lib/use-run-progress.ts`, `ui/src/components/chat/ChatMessageItem.tsx`, `tests/unit/test_chat_store.py`. Risks: oversized files in `chat.py`, `app.py`, `types.ts`, and `use-run-progress.ts`; current `chat.py` comments about character-model usage do not fully match the live call path, so provenance must come from emitted runtime data, not frontend inference. Next=human approval on the residual-scope implementation plan.
20260320-1448 — implementation start: set story to `In Progress` and began the chat provenance slice. Active path is schema-first `model` plumbing from backend stream/persistence through frontend store/rendering, with no runtime-model inference in the UI. Next=land backend + frontend field threading, then render the subtle model label and run required checks.
20260320-1508 — implementation complete: added optional `model` to `ChatMessagePayload`, streamed chat chunks, frontend chat types, and the in-memory chat store; rendered a compact model badge in `ChatMessageItem`; and added stream-provenance unit coverage in `tests/unit/test_chat_stream_provenance.py`. Evidence: targeted tests `12 passed`; full unit suite `603 passed, 139 deselected`; Ruff `All checks passed!`; UI type/build checks passed after installing missing local `ui` dependencies with `pnpm --dir ui install --frozen-lockfile`; lint reported 5 pre-existing `react-refresh/only-export-components` warnings in unrelated files but no errors. Runtime smoke: backend health `{"status":"ok","version":"2026.03.20-03"}`, browser verified `/project_smoke_mvp_stale/artifacts` current badges plus chat response badge `Claude Sonnet 4.6`, Playwright captured a viewport screenshot of the verified state, and console showed no app errors. Next=`/validate`.
20260320-1537 — validation: reran the required check suite with shared interpreter `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` because this worktree has no local `.venv`: `make test-unit` passed (`603 passed, 139 deselected`), Ruff passed, targeted provenance tests passed (`12 passed`), `pnpm --dir ui run lint` passed with 5 pre-existing `react-refresh/only-export-components` warnings in unrelated files, `npx tsc -b` passed, and `pnpm --dir ui run build` passed. Browser validation confirmed the intended Story 127 flow on `/project_smoke_mvp_stale/artifacts`: artifact badges still read `Current`, persisted and newly streamed assistant messages show the model badge, and the console stayed clean. Extra stale-project regression check on `/the-mariner-36/artifacts` surfaced unrelated pre-existing console noise from missing historical run-state polling (`/api/runs/{id}/state`), which appears orthogonal to the chat-provenance diff and should be tracked separately. Recommended next step=`/mark-story-done`.
20260320-1607 — follow-up capture: user requested the stale-project historical run polling bug be attached to Story 127 as an explicit side requirement instead of a loose recommendation. Created [Story 139](story-139-historical-run-progress-cards-stop-polling-missing-runs.md) to track the fix and marked the capture task complete here. Next=`/mark-story-done`.
20260320-1642 — re-validation after follow-up capture: reran the required suite on the same implementation with the updated story text and follow-up linkage in place. Evidence: `make test-unit` passed again (`603 passed, 139 deselected, 1 pre-existing acceptance-mark warning`), Ruff passed, targeted provenance tests passed (`12 passed`), `pnpm --dir ui run lint` passed with the same 5 unrelated fast-refresh warnings, `npx tsc -b` passed, and `pnpm --dir ui run build` passed with the existing chunk-size warning only. Fresh browser verification on `/project_smoke_mvp_stale/artifacts` confirmed `Current` health badges still render, a newly sent assistant response still shows `Claude Sonnet 4.6`, Playwright captured `tmp/story-127-validate-20260320.png`, and console error count remained `0`. Recommended next step=`/mark-story-done`.
20260320-1654 — close-out: Story 127 marked done after validation confirmed the shipped slice is complete and the only unrelated stale-project browser issue is explicitly tracked in [Story 139](story-139-historical-run-progress-cards-stop-polling-missing-runs.md). Evidence remains the green backend/UI suite, targeted provenance tests, and clean browser verification on `/project_smoke_mvp_stale/artifacts` recorded above. Next step: `/check-in-diff`.
