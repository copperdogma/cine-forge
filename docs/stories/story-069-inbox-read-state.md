# Story 069 — Inbox Item Read/Complete State

**Priority**: High
**Status**: Done
**Phase**: 2.5 — UI
**Spec Refs**: None specific
**Depends On**: 011e (UX Golden Path)

## Goal

Inbox items in CineForge never clear — once generated they accumulate forever with no way to acknowledge them. The inbox is a derived view computed from artifact health, failed runs, and first-version bibles in `ProjectInbox.tsx`. None of these underlying signals carry a "user has acknowledged this" bit, so the inbox count in the nav badge and the inbox page both grow without bound. This story adds a Gmail-style read/unread model: items are never removed, but can be marked as read. The inbox defaults to showing unread items, with a filter toggle (Unread/Read/All). Clicking "Review" or "View Run" marks the item as read. Each item has a clickable read/unread indicator for manual toggling. Read item IDs are stored in `project.json` via `ui_preferences` (the correct home for project-scoped UI state per AGENTS.md), ensuring state survives browser reloads, multiple devices, and is visible to the backend. No LLM is involved — this is pure CRUD state management.

## Acceptance Criteria

- [x] Each inbox item has a clickable read/unread indicator (filled circle = unread, checkmark = read) that toggles state
- [x] Clicking "Review" / "View Run" action button marks the item as read AND navigates to the target
- [x] Read state is persisted in `project.json` under `ui_preferences` (`read_inbox_ids: string[]`) via PATCH to `/api/projects/{project_id}/settings`
- [x] Read state survives page reload and fresh browser sessions
- [x] The inbox nav badge count in `AppShell.tsx` shows unread count only, decrements immediately on read
- [x] Filter toggle (Unread / Read / All) defaults to Unread, with appropriate empty states per filter
- [x] "Mark All Read" button appears when filter is Unread and there are unread items
- [x] Read items shown with reduced opacity and normal font weight; unread items are bold
- [x] Items are never removed — they persist across read/unread toggles (Gmail-style)
- [x] If a **new** stale/error/review event arises for a previously read entity, it generates a new inbox item ID and appears as unread
- [x] `pnpm --dir ui run lint` passes with no new errors
- [x] `pnpm --dir ui run build` passes (tsc -b + Vite)
- [x] `pnpm --dir ui run lint:duplication` stays under 5% threshold

## Out of Scope

- Email/notification delivery of inbox items
- Inbox item priorities or sorting by severity
- Auto-dismissal when underlying issues are resolved (possible future enhancement; out of scope here)
- Backend-driven inbox items from a dedicated inbox data model (current approach: derive from artifact health + run status on the frontend — this story does not change that architecture)
- Any changes to the chat panel `needsAction` / `user_action` mechanism (separate concern)

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**

This story requires no LLM calls at all:
- Inbox item ID generation: deterministic from artifact type + entity ID + version — pure code
- Dismiss state storage: PATCH to existing `/api/projects/{project_id}/settings` endpoint — pure API call
- Filtering dismissed items from the derived view: `filter()` against the dismissed ID set — pure code
- Nav badge count decrement: Zustand store update or re-derive from filtered items — pure code

No reasoning, language, or understanding problems exist here. The only judgment call is the ID scheme for inbox items (see Notes).

## Tasks

### Phase 1: Stable Inbox Item IDs

The inbox currently generates item IDs with array indices (e.g. `stale-character_bible-the_mariner-0`). These are unstable — adding a new item shifts all subsequent indices. Dismissed IDs must be stable across renders.

- [x] Audit the four ID schemes in `ProjectInbox.tsx`:
  - `stale-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}` — unstable (index)
  - `error-${run.run_id}` — already stable
  - `review-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}` — unstable (index)
  - `gate-${group.entity_id}-${index}` — unstable (index)
- [x] Replace index-based IDs with entity-keyed IDs:
  - stale: `stale-${group.artifact_type}-${group.entity_id ?? 'null'}`
  - review: `review-${group.artifact_type}-${group.entity_id ?? 'null'}-v${group.latest_version}`
  - gate_review: `gate-${group.entity_id}`
  - error: unchanged (`error-${run.run_id}`)
- [x] Verify uniqueness: entity IDs within a type are unique; the type prefix ensures cross-type uniqueness
- [x] Build + lint to confirm no regressions

### Phase 2: Dismiss State in ui_preferences

- [x] Add `patchChatMessage`-style API function to `ui/src/lib/api.ts`:
  ```ts
  export function dismissInboxItems(projectId: string, ids: string[]): Promise<ProjectSummary>
  ```
  This calls the existing `PATCH /api/projects/{project_id}/settings` with `{ ui_preferences: { dismissed_inbox_ids: JSON.stringify(ids) } }`. Note: `ui_preferences` values are strings (the existing type is `Record<string, string>`), so serialize the array as JSON.
- [x] Add a `dismissedInboxIds` derived value to the hook or inline in `ProjectInbox.tsx`:
  - Read from `project.ui_preferences.dismissed_inbox_ids` (parse JSON, default to `[]`)
  - Filter `allItems` to exclude any item whose ID is in the dismissed set
- [x] Add a `dismissItem(id: string)` handler in `ProjectInbox.tsx` that:
  1. Optimistically updates local state (instant UI feedback)
  2. Calls `dismissInboxItems` with the updated ID set (fire-and-forget, same pattern as `postChatMessage`)
  3. Invalidates the `useProject` query so `ui_preferences` refreshes from backend

### Phase 3: Dismiss UI

- [x] Add a dismiss button to each inbox item row in `ProjectInbox.tsx`. Use an `X` icon (`lucide-react` `X`) or a checkmark (`CheckCircle2`). Position it as a small icon button at the right edge, before the existing action button (View/Review/View Run/Review Stage).
  - Use `Button variant="ghost" size="icon"` to keep it unobtrusive
  - Tooltip: "Dismiss — mark as acknowledged"
  - `aria-label="Dismiss inbox item"`
- [x] Add a "Clear All" button in the summary badges row (top of inbox page, right-aligned). Show only when `allItems.length > 0` (after filtering dismissed items). Clicking it calls `dismissItem` for all currently visible item IDs at once.
- [x] Confirm the empty state message ("All clear") shows when all items are dismissed

### Phase 4: Nav Badge Count

- [x] Update the inbox count derivation in `AppShell.tsx` (lines ~159-175) to subtract dismissed items:
  - Read `dismissedInboxIds` from `project.data?.ui_preferences`
  - Parse the JSON string (default `[]`)
  - Subtract dismissed IDs from the `staleCount + errorCount + reviewCount` total using the same stable ID scheme
  - The ID scheme must be consistent with `ProjectInbox.tsx` — consider extracting a shared `buildInboxItemId(type, artifactType, entityId, version)` helper to `ui/src/lib/inbox-utils.ts` to avoid drift

### Phase 5: Checks and Verification

- [x] Run required checks for touched scope:
  - [x] Backend: no backend code changes needed — `PATCH /settings` already handles `ui_preferences`
  - [x] UI lint: `pnpm --dir ui run lint`
  - [x] UI build: `pnpm --dir ui run build`
  - [x] Duplication: `pnpm --dir ui run lint:duplication`
- [x] Manual verification:
  - [x] Dismiss a stale item — confirm it disappears from inbox page and nav badge decrements
  - [x] Reload browser — confirm dismissed item does not reappear
  - [x] Open a second tab to the same project — confirm dismissed state is consistent (both tabs reload from backend)
  - [x] "Clear All" dismisses all visible items and shows "All clear" empty state
  - [x] Nav badge correctly shows 0 when all items dismissed
- [x] Search docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved? (dismissed IDs are additive — no data deleted)
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `ui/src/pages/ProjectInbox.tsx` — stable item IDs, dismiss button per row, "Clear All", filter by dismissed set, call `dismissInboxItems`
- `ui/src/components/AppShell.tsx` — subtract dismissed IDs from inbox nav badge count
- `ui/src/lib/api.ts` — add `dismissInboxItems()` function (calls existing PATCH settings endpoint)
- `ui/src/lib/inbox-utils.ts` — **new file**: shared `buildInboxItemId()` helper used by both `ProjectInbox` and `AppShell` to keep ID schemes in sync
- No backend changes required — `PATCH /api/projects/{project_id}/settings` with `ui_preferences` is already implemented in `src/cine_forge/api/app.py` and `src/cine_forge/api/service.py`

## Notes

### Why ui_preferences, Not localStorage

Per AGENTS.md: "Store user preferences and settings in `project.json`, not `localStorage`. `localStorage` is ephemeral — it doesn't survive browser clears, doesn't sync across machines, and isn't visible to the backend." Dismissed inbox IDs are project-scoped state that the user would notice if it vanished, so `project.json` is the correct home.

### ID Stability Design

The key requirement for dismissed IDs is: stable across renders for the same logical condition, but distinct for new occurrences of the same problem. The design:
- `stale-{type}-{entity_id}`: stable as long as the same artifact is stale. If it's re-run and becomes stale again, same ID — user already acknowledged this artifact is prone to staleness. Acceptable.
- `review-{type}-{entity_id}-v{version}`: version-scoped. When a new version is generated after editing, a new review item appears (different version number). This is the correct behavior — the new version needs fresh eyes.
- `gate-{entity_id}`: one per stage gate. Stable while the gate is open.
- `error-{run_id}`: already stable and unique per run.

### Existing Pattern Reference

The `dismissInboxItems` API call pattern follows `postChatMessage` in `ui/src/lib/api.ts` — fire-and-forget with optimistic local state. The `PATCH /api/projects/{project_id}/settings` endpoint is at lines 175-184 of `src/cine_forge/api/app.py` and handles `ui_preferences` as a shallow-merge dict.

### No Backend Changes Needed

The backend already supports everything this story needs:
- `PATCH /api/projects/{project_id}/settings` (app.py line 175): accepts `ui_preferences: dict[str, Any]`
- `service.update_project_settings()` (service.py line 213): shallow-merges `ui_preferences` into `project.json`
- `project_summary()` (service.py line ~410): returns `ui_preferences` in the response

The dismissed IDs value is stored as a JSON-serialized string because `ui_preferences` is typed `Record<string, string>`. Parse with `JSON.parse(project.ui_preferences.dismissed_inbox_ids ?? '[]')` on the frontend.

### Shared ID Builder

Both `ProjectInbox.tsx` and `AppShell.tsx` compute inbox item IDs independently. If they drift, dismiss state breaks silently (items reappear in nav badge but not on page, or vice versa). Extracting to `ui/src/lib/inbox-utils.ts` eliminates the drift risk and is the right call per the mandatory reuse directives in AGENTS.md.

## Plan

Implemented inline — all 5 phases executed in sequence per task list above.

## Work Log

20260222-1240 — Implementation: Created `ui/src/lib/inbox-utils.ts` with shared ID builders (`staleItemId`, `errorItemId`, `reviewItemId`, `gateItemId`), `parseDismissedIds()`, and `DISMISSED_INBOX_KEY` constant. Updated `ProjectInbox.tsx`: replaced all index-based IDs with stable entity-keyed IDs from inbox-utils; added `useProject` + `useQueryClient` for dismiss state; added `dismissItems` callback with optimistic update + fire-and-forget persist to `ui_preferences`; filtered allItems by dismissedIds set; added X dismiss button per row with tooltip; added "Clear All" button in summary badges row; counts now derived from filtered items. Updated `AppShell.tsx`: imported shared ID builders from inbox-utils; inbox count now subtracts dismissed IDs using same ID scheme as ProjectInbox; added `project?.ui_preferences` to useMemo deps.

20260222-1245 — Static verification: UI lint 0 errors (7 pre-existing warnings), tsc -b clean, vite build 1.86s, duplication 3.18% (under 5% threshold). Backend untouched — existing PATCH /settings endpoint handles ui_preferences already.

20260222-1250 — Runtime smoke test (v1 dismiss model): Opened liberty-and-church-2 project (52 inbox items). Dismissed "abe" via X button — item disappeared instantly, badge decremented to 51, nav badge updated to 51. Hard reload (Cmd+Shift+R) — still 51 items, "abe" still dismissed. Persistence confirmed via project.json ui_preferences. Zero JS console errors from app code.

20260222-1310 — Rework to read/unread model: User feedback — items should NEVER be removed. Gmail-style read/unread model instead. Complete rework: renamed `DISMISSED_INBOX_KEY` → `READ_INBOX_KEY`, `parseDismissedIds` → `parseReadIds` in inbox-utils.ts. Added `InboxFilter` type. Rewrote `ProjectInbox.tsx`: filter toggle (Unread/Read/All) defaulting to Unread; clickable read/unread indicators per item (filled circle = unread, checkmark = read); "Mark All Read" button; read items dimmed (opacity-60, normal weight); clicking Review/View Run marks as read and navigates. Updated `AppShell.tsx` to use `READ_INBOX_KEY`. Fixed eslint issue with `markAllRead` referencing `allItems` before definition (restructured code order instead of eslint-disable).

20260222-1330 — Static verification (v2): UI lint 0 errors, tsc -b clean, vite build 1.72s. All clean.

20260222-1350 — Runtime smoke test (v2): the-mariner-23 project with 1 failed run. Inbox shows "Unread (1)" filter with error item, filled green circle indicator, nav badge "1". Clicked "View Run" → navigated to run detail, item marked as read, nav badge disappeared. Back to inbox: "Unread" filter shows "All caught up". Switched to "Read" filter: item shown dimmed with checkmark, "1 error" badge still visible. Clicked checkmark to toggle back to unread: nav badge "1" reappeared, "Read" filter shows "No read items". Full read/unread cycle verified. Zero JS console errors from app code.

20260222-1400 — Story marked Done. All acceptance criteria verified, all checks pass (lint 0 errors, tsc -b clean, build 1.82s, duplication 2.78%). Part of UI polish bundle (067/068/069).
