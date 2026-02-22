# Story 067 — chat-duplicate-nav-dedup

**Priority**: High
**Status**: Pending
**Spec Refs**: None
**Depends On**: 011e (UX Golden Path), 051 (Chat UX Polish)

## Goal

Navigation context messages ("Viewing run: X", "Reviewing Run History", etc.) accumulate in the chat history as duplicates instead of replacing each other. The root cause is a mismatch between in-memory deduplication and backend persistence: `addActivity` in `chat-store.ts` correctly replaces the last in-memory activity message, but it always writes the new message to the backend JSONL without deleting the old one. Because each call generates a fresh ID (`activity_${Date.now()}_...`), the backend idempotency check (keyed on message ID) never fires. On the next cold load or `syncMessages`, all accumulated activity lines are replayed and the chat fills with duplicate navigation entries. This story fixes the persistence layer so that at most one activity message ever appears at the tail of the chat history, both in-memory and in the stored JSONL.

## Acceptance Criteria

- [ ] Clicking through Runs, Run Detail, Characters, Scenes, etc. in sequence produces exactly one activity message visible at the bottom of the chat at all times — never a stack of duplicates.
- [ ] After a hard page reload, the chat history contains at most one trailing activity message per navigation session (no JSONL-replayed duplicates).
- [ ] Non-activity messages (AI responses, user messages, pipeline status) are never affected — they remain untouched by the deduplication logic.
- [ ] Rapid navigation (clicking 3-4 pages in quick succession) does not leave orphan activity entries — the final visible state shows only the last destination.
- [ ] The fix is purely in-memory and backend-persistence logic; no visible UI or UX change is introduced.

## Out of Scope

- Backfilling or cleaning up existing chat.jsonl files that already contain duplicate activity lines — those are test/dev artifacts and this is a greenfield project.
- General chat history pruning, pagination, or archiving.
- Changing any other message type's persistence behaviour.
- Backend API changes beyond the existing `append_chat_message` / `list_chat_messages` surface.

## AI Considerations

This is a pure code fix — no LLM call is involved or useful. The problem is a structural state management bug: in-memory deduplication works but the persistence write is unconditional and always uses a unique ID, so the idempotency guard in `append_chat_message` never fires. The fix options are:

1. **Option A — Stable activity ID (simplest)**: Give activity messages a deterministic, project-scoped ID (e.g., `activity_nav_<projectId>`) instead of `activity_${Date.now()}_...`. The backend idempotency check will then detect the existing record and skip the append. On replace, the in-memory update still happens; the backend eventually converges (at most one nav message per reload).
   - Downside: Old and new message content diverges — the JSONL always has the *first* activity for that ID, not the *latest*, until the session is long enough that the ID rotates.
   - This makes cold-load replays show the first nav action, not the most recent.

2. **Option B — Overwrite / upsert on backend (correct)**: Add a `PUT /api/projects/{project_id}/chat/{message_id}` endpoint (or an `upsert` flag on the POST) so that when `addActivity` replaces a message in-memory, it also replaces it on the backend. The JSONL entry for the old ID gets updated in place (rewrite the file) or the old line is tombstoned and the new line appended.
   - More correct, but requires a new API endpoint and file rewrite logic on the backend.

3. **Option C — Single reserved activity slot in JSONL (pragmatic)**: Keep the stable-ID approach but make `append_chat_message` perform an **upsert** when the incoming message type is `activity`. Scan for any existing `activity`-typed message at the tail, remove it, then append the new one. No new endpoint needed.
   - This is the recommended path: minimal backend change, correct semantics, no new API surface.

Recommendation: **Option C**. Implement a backend upsert for `activity` type messages in `service.py`, and change `addActivity` in `chat-store.ts` to use a stable project-scoped ID (e.g., `activity_nav_<projectId>`) so the upsert can find and replace it by ID.

## Tasks

- [ ] In `ui/src/lib/chat-store.ts` — `addActivity`: change the generated message ID from `activity_${Date.now()}_${random}` to a stable per-project key `activity_nav_${projectId}`. This ensures the backend idempotency guard fires correctly after the upsert is added.
- [ ] In `src/cine_forge/api/service.py` — `append_chat_message`: add upsert logic for `activity`-typed messages. When the incoming message type is `activity`, scan the JSONL for any line with the same ID and replace it in place (rewrite the file), or scan for any existing `activity` message at the tail and overwrite. Fall back to normal append for all other types.
- [ ] Verify end-to-end: start the backend, open the UI, navigate to Runs, a Run Detail, back to Characters — confirm only one activity message appears and survives a page reload.
- [ ] Run required checks for touched scope:
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] Backend unit tests: `.venv/bin/python -m pytest -m unit`
  - [ ] UI lint: `pnpm --dir ui run lint`
  - [ ] UI build/typecheck: `pnpm --dir ui run build` (or tsc -b equivalent)
- [ ] Search docs and update any related story or AGENTS.md if a new pitfall pattern emerges
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved? (Activity messages are ephemeral UI context — no user-authored data at risk.)
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `ui/src/lib/chat-store.ts` — change `addActivity` to use a stable per-project message ID (`activity_nav_${projectId}`) instead of a random timestamp-based ID, so backend upsert can locate and replace the existing record by ID.
- `src/cine_forge/api/service.py` — update `append_chat_message` to perform an in-place upsert when `message["type"] == "activity"`: find any existing line with the same ID (or any `activity`-type line at the tail), replace it, and rewrite the JSONL. All other message types use the existing append-with-idempotency logic unchanged.

## Notes

**Root cause summary**: `addActivity` (chat-store.ts:98-124) correctly replaces the last in-memory activity. But the `postChatMessage` call on line 120 always writes a new record to the backend JSONL because the ID is unique every time (`activity_${Date.now()}_...`). The backend `append_chat_message` in service.py:909-930 is ID-keyed for idempotency — since the ID is always new, it always appends. On `syncMessages` (cold load), all stored activity lines replay into the in-memory store, producing the duplicate stack.

**Why the in-memory dedup doesn't help on reload**: `migrateMessages` in chat-store.ts:13-19 only converts `ai_status` → `ai_status_done`. It does not deduplicate activity messages. So all N JSONL activity lines load directly into the messages array.

**JSONL rewrite is safe here**: Activity messages have no user-authored content. The only risk of a JSONL rewrite is data loss of other message types, which can be guarded by limiting the upsert/replace logic strictly to `type == "activity"`.

**Alternative simpler fix if backend upsert is too invasive**: Add a `migrateMessages` deduplication pass in `chat-store.ts:loadMessages` that drops all but the last `activity` message in the loaded array. This is a client-side-only fix, requires zero backend change, and stops the visual duplication immediately. The JSONL will still accumulate activity lines over time (minor disk waste), but the UI will always be correct. This is a viable fallback if the backend upsert is deferred.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
