# Story 067 — chat-duplicate-nav-dedup

**Priority**: High
**Status**: Done
**Spec Refs**: None
**Depends On**: 011e (UX Golden Path), 051 (Chat UX Polish)

## Goal

Navigation context messages ("Viewing run: X", "Reviewing Run History", etc.) accumulate in the chat history as duplicates instead of replacing each other. The root cause is a mismatch between in-memory deduplication and backend persistence: `addActivity` in `chat-store.ts` correctly replaces the last in-memory activity message, but it always writes the new message to the backend JSONL without deleting the old one. Because each call generates a fresh ID (`activity_${Date.now()}_...`), the backend idempotency check (keyed on message ID) never fires. On the next cold load or `syncMessages`, all accumulated activity lines are replayed and the chat fills with duplicate navigation entries. This story fixes the persistence layer so that at most one activity message ever appears at the tail of the chat history, both in-memory and in the stored JSONL.

## Acceptance Criteria

- [x] Clicking through Runs, Run Detail, Characters, Scenes, etc. in sequence produces exactly one activity message visible at the bottom of the chat at all times — never a stack of duplicates.
- [x] After a hard page reload, the chat history contains at most one trailing activity message per navigation session (no JSONL-replayed duplicates).
- [x] Non-activity messages (AI responses, user messages, pipeline status) are never affected — they remain untouched by the deduplication logic.
- [x] Rapid navigation (clicking 3-4 pages in quick succession) does not leave orphan activity entries — the final visible state shows only the last destination.
- [x] The fix is purely in-memory and backend-persistence logic; no visible UI or UX change is introduced.

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

- [x] In `ui/src/lib/chat-store.ts` — `addActivity`: change the generated message ID from `activity_${Date.now()}_${random}` to a stable per-project key `activity_nav_${projectId}`. This ensures the backend idempotency guard fires correctly after the upsert is added.
- [x] In `src/cine_forge/api/service.py` — `append_chat_message`: add upsert logic for `activity`-typed messages. When the incoming message type is `activity`, scan the JSONL for any line with the same ID and replace it in place (rewrite the file), or scan for any existing `activity` message at the tail and overwrite. Fall back to normal append for all other types.
- [x] In `ui/src/lib/chat-store.ts` — `migrateMessages`: add client-side dedup safety net — keep only the last activity message on cold load.
- [x] Verify end-to-end: start the backend, open the UI, navigate to Scenes → Characters → Locations → Props → Inbox — confirm only one activity message appears and survives a hard page reload.
- [x] Run required checks for touched scope:
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — All checks passed
  - [x] Backend unit tests: `.venv/bin/python -m pytest -m unit` — All 252 passed
  - [x] UI lint: `pnpm --dir ui run lint` — 0 errors (7 pre-existing warnings)
  - [x] UI typecheck: `cd ui && npx tsc -b` — Clean
  - [x] UI build: `pnpm --dir ui run build` — Built in 2.02s
- [x] Search docs and update any related story or AGENTS.md if a new pitfall pattern emerges — Added ChatMessagePayload missing `route` field to docs/inbox.md
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Activity messages are ephemeral UI context — no user-authored data at risk. JSONL rewrite is strictly scoped to `type == "activity"`.
  - [x] **T1 — AI-Coded:** Upsert branch clearly commented with story reference. migrateMessages dedup documented.
  - [x] **T2 — Architect for 100x:** Minimal change — stable ID + targeted upsert. No over-engineering.
  - [x] **T3 — Fewer Files:** Zero new files. Changes in 2 existing files only.
  - [x] **T4 — Verbose Artifacts:** Work log captures all evidence.
  - [x] **T5 — Ideal vs Today:** This is the ideal fix — backend upsert ensures JSONL correctness, client dedup provides safety net.

## Files to Modify

- `ui/src/lib/chat-store.ts` — change `addActivity` to use a stable per-project message ID (`activity_nav_${projectId}`) instead of a random timestamp-based ID, so backend upsert can locate and replace the existing record by ID.
- `src/cine_forge/api/service.py` — update `append_chat_message` to perform an in-place upsert when `message["type"] == "activity"`: find any existing line with the same ID (or any `activity`-type line at the tail), replace it, and rewrite the JSONL. All other message types use the existing append-with-idempotency logic unchanged.

## Notes

**Root cause summary**: `addActivity` (chat-store.ts:98-124) correctly replaces the last in-memory activity. But the `postChatMessage` call on line 120 always writes a new record to the backend JSONL because the ID is unique every time (`activity_${Date.now()}_...`). The backend `append_chat_message` in service.py:909-930 is ID-keyed for idempotency — since the ID is always new, it always appends. On `syncMessages` (cold load), all stored activity lines replay into the in-memory store, producing the duplicate stack.

**Why the in-memory dedup doesn't help on reload**: `migrateMessages` in chat-store.ts:13-19 only converts `ai_status` → `ai_status_done`. It does not deduplicate activity messages. So all N JSONL activity lines load directly into the messages array.

**JSONL rewrite is safe here**: Activity messages have no user-authored content. The only risk of a JSONL rewrite is data loss of other message types, which can be guarded by limiting the upsert/replace logic strictly to `type == "activity"`.

**Alternative simpler fix if backend upsert is too invasive**: Add a `migrateMessages` deduplication pass in `chat-store.ts:loadMessages` that drops all but the last `activity` message in the loaded array. This is a client-side-only fix, requires zero backend change, and stops the visual duplication immediately. The JSONL will still accumulate activity lines over time (minor disk waste), but the UI will always be correct. This is a viable fallback if the backend upsert is deferred.

## Bundle

Stories 067, 068, and 069 form a **UI polish bundle** and should be implemented together in one session. They are independent of each other (no inter-dependencies) but share the same scope (UI state management and navigation). Completing all three clears the pending UI backlog before Phase 5 creative work begins.

## Plan

**Approach: Option C (pragmatic backend upsert + stable ID) with client-side safety net.**

### Task 1: Stable activity ID (frontend)

**File:** `ui/src/lib/chat-store.ts`
**Change:** In `addActivity` (line 104), replace:
```ts
id: `activity_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
```
with:
```ts
id: `activity_nav_${projectId}`
```
This makes all navigation activity messages for a project share one stable ID, so the backend idempotency/upsert can locate and replace the previous one.

### Task 2: Backend upsert for activity messages

**File:** `src/cine_forge/api/service.py`
**Change:** In `append_chat_message` (lines 909-930), add an upsert branch before the normal append:
- When `message.get("type") == "activity"` and `msg_id` is set:
  - Read all JSONL lines
  - If a line with the same ID exists, replace it with the new message and rewrite the file
  - If no match, append normally (fall through to existing logic)
- All non-activity messages use the existing idempotency-and-append path unchanged

### Task 3: Client-side dedup safety net (belt-and-suspenders)

**File:** `ui/src/lib/chat-store.ts`
**Change:** In `migrateMessages` (lines 13-19), add a final pass after the existing `ai_status` migration:
- Walk the message array and keep only the last `activity`-typed message, dropping earlier ones
- This handles any pre-existing JSONL files that already contain duplicate activity lines

### Impact Analysis

- **No new API endpoints** — reuses existing POST `/api/projects/{project_id}/chat`
- **No schema changes** — `ChatMessagePayload` model unchanged
- **No risk to non-activity messages** — upsert branch is strictly `type == "activity"`; all other types follow the existing append path
- **No backend tests exist** for chat persistence (confirmed via grep) — verified manually via smoke test per acceptance criteria
- **Pre-existing issue noted**: `ChatMessagePayload` model (models.py:205) is missing the `route` field, so activity message routes are stripped on backend persistence. Out of scope for this story.

### Approval Blockers

None — no new dependencies, no schema changes, no public API changes. Pure behavioral fix.

### Definition of Done

- Navigate through 4+ pages → only one activity message visible in chat
- Hard reload → no duplicates replayed from JSONL
- Non-activity messages (AI responses, user messages, pipeline status) unaffected
- Rapid navigation (3-4 pages quickly) → only last destination shown
- Backend lint + unit tests pass
- UI lint + typecheck pass

## Work Log

20260222-1210 — Exploration: Traced full call graph. 14 callers of addActivity across AppShell.tsx, ChatPanel.tsx, ProjectRun.tsx. Confirmed root cause: unique timestamp-based IDs bypass backend idempotency. migrateMessages only handles ai_status, not activity dedup. ChatMessagePayload model missing `route` field (pre-existing, logged to inbox.md). No existing tests for chat persistence.

20260222-1215 — Implementation: Applied Option C (stable ID + backend upsert + client dedup safety net).
- chat-store.ts: Changed addActivity ID to `activity_nav_${projectId}` (stable per-project).
- chat-store.ts: Added migrateMessages dedup pass — keeps only last activity message on cold load. Used manual reverse loop instead of `findLastIndex` (ES2023 not in tsconfig lib target).
- service.py: Added upsert branch in append_chat_message — when type=="activity" and ID matches existing JSONL line, replace in-place and rewrite file. Non-activity messages use existing append path unchanged.

20260222-1220 — Static verification: ruff clean, 252 unit tests pass, UI lint 0 errors, tsc -b clean, vite build success (2.02s).

20260222-1225 — Runtime smoke test: Started backend (port 8155) + UI dev server (port 5199). Opened Liberty and Church project. Navigated Scenes → Characters → Locations → Props → Inbox in quick succession. Chat panel showed exactly one activity message ("Reviewing Inbox") throughout. Hard reload (Cmd+Shift+R) — still one activity message, no JSONL-replayed duplicates. Console errors: only Chrome extension noise, zero app errors. All 5 acceptance criteria met.

20260222-1400 — Story marked Done. All acceptance criteria verified, all checks pass (252 unit tests, ruff clean, lint 0 errors, tsc -b clean, build 1.82s, duplication 2.78%). Part of UI polish bundle (067/068/069).
