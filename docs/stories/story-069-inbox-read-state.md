# Story 069 — Inbox Item Read/Complete State

**Priority**: High
**Status**: Pending
**Phase**: 2.5 — UI
**Spec Refs**: None specific
**Depends On**: 011e (UX Golden Path)

## Goal

Inbox items in CineForge never clear — once generated they accumulate forever with no way to dismiss or mark them done. The inbox is a derived view computed from artifact health, failed runs, and first-version bibles in `ProjectInbox.tsx`. None of these underlying signals carry a "user has acknowledged this" bit, so the inbox count in the nav badge and the inbox page both grow without bound. This story adds a dismiss/complete mechanism: the user can mark any inbox item as acknowledged, removing it from the active inbox view. Dismissed item IDs are stored in `project.json` via `ui_preferences` (the correct home for project-scoped UI state per AGENTS.md), ensuring state survives browser reloads, multiple devices, and is visible to the backend. No LLM is involved — this is pure CRUD state management.

## Acceptance Criteria

- [ ] Each inbox item row has a "Dismiss" button (or equivalent affordance such as a checkmark icon) that removes the item from the inbox view
- [ ] Dismissed items are persisted in `project.json` under `ui_preferences` (e.g. `dismissed_inbox_ids: string[]`) via a PATCH to `/api/projects/{project_id}/settings`
- [ ] After dismissal, the item does not reappear on page reload or in a fresh browser session
- [ ] The inbox nav badge count in `AppShell.tsx` decrements immediately on dismiss and does not show dismissed items
- [ ] A "Clear All" button on the inbox page dismisses all currently visible items in one action
- [ ] If a dismissed item's underlying cause is resolved (e.g. stale artifact re-run, failed run retried successfully), the item stays gone — its dismissed ID remains in the set even if the artifact health changes (dismissed = acknowledged, not auto-reopened)
- [ ] If a **new** stale/error/review event arises for a previously dismissed entity, it generates a new inbox item ID and appears again (dismissed IDs are entity-version-specific, not entity-permanent silences)
- [ ] `pnpm --dir ui run lint` passes with no new errors
- [ ] `pnpm --dir ui run build` passes (tsc -b + Vite)
- [ ] `pnpm --dir ui run lint:duplication` stays under 5% threshold

## Out of Scope

- Re-opening or un-dismissing individual items (no undo — dismissed is acknowledged)
- A separate "Dismissed" archive view or history
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

- [ ] Audit the four ID schemes in `ProjectInbox.tsx`:
  - `stale-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}` — unstable (index)
  - `error-${run.run_id}` — already stable
  - `review-${group.artifact_type}-${group.entity_id ?? 'null'}-${index}` — unstable (index)
  - `gate-${group.entity_id}-${index}` — unstable (index)
- [ ] Replace index-based IDs with entity-keyed IDs:
  - stale: `stale-${group.artifact_type}-${group.entity_id ?? 'null'}`
  - review: `review-${group.artifact_type}-${group.entity_id ?? 'null'}-v${group.latest_version}`
  - gate_review: `gate-${group.entity_id}`
  - error: unchanged (`error-${run.run_id}`)
- [ ] Verify uniqueness: entity IDs within a type are unique; the type prefix ensures cross-type uniqueness
- [ ] Build + lint to confirm no regressions

### Phase 2: Dismiss State in ui_preferences

- [ ] Add `patchChatMessage`-style API function to `ui/src/lib/api.ts`:
  ```ts
  export function dismissInboxItems(projectId: string, ids: string[]): Promise<ProjectSummary>
  ```
  This calls the existing `PATCH /api/projects/{project_id}/settings` with `{ ui_preferences: { dismissed_inbox_ids: JSON.stringify(ids) } }`. Note: `ui_preferences` values are strings (the existing type is `Record<string, string>`), so serialize the array as JSON.
- [ ] Add a `dismissedInboxIds` derived value to the hook or inline in `ProjectInbox.tsx`:
  - Read from `project.ui_preferences.dismissed_inbox_ids` (parse JSON, default to `[]`)
  - Filter `allItems` to exclude any item whose ID is in the dismissed set
- [ ] Add a `dismissItem(id: string)` handler in `ProjectInbox.tsx` that:
  1. Optimistically updates local state (instant UI feedback)
  2. Calls `dismissInboxItems` with the updated ID set (fire-and-forget, same pattern as `postChatMessage`)
  3. Invalidates the `useProject` query so `ui_preferences` refreshes from backend

### Phase 3: Dismiss UI

- [ ] Add a dismiss button to each inbox item row in `ProjectInbox.tsx`. Use an `X` icon (`lucide-react` `X`) or a checkmark (`CheckCircle2`). Position it as a small icon button at the right edge, before the existing action button (View/Review/View Run/Review Stage).
  - Use `Button variant="ghost" size="icon"` to keep it unobtrusive
  - Tooltip: "Dismiss — mark as acknowledged"
  - `aria-label="Dismiss inbox item"`
- [ ] Add a "Clear All" button in the summary badges row (top of inbox page, right-aligned). Show only when `allItems.length > 0` (after filtering dismissed items). Clicking it calls `dismissItem` for all currently visible item IDs at once.
- [ ] Confirm the empty state message ("All clear") shows when all items are dismissed

### Phase 4: Nav Badge Count

- [ ] Update the inbox count derivation in `AppShell.tsx` (lines ~159-175) to subtract dismissed items:
  - Read `dismissedInboxIds` from `project.data?.ui_preferences`
  - Parse the JSON string (default `[]`)
  - Subtract dismissed IDs from the `staleCount + errorCount + reviewCount` total using the same stable ID scheme
  - The ID scheme must be consistent with `ProjectInbox.tsx` — consider extracting a shared `buildInboxItemId(type, artifactType, entityId, version)` helper to `ui/src/lib/inbox-utils.ts` to avoid drift

### Phase 5: Checks and Verification

- [ ] Run required checks for touched scope:
  - [ ] Backend: no backend code changes needed — `PATCH /settings` already handles `ui_preferences`
  - [ ] UI lint: `pnpm --dir ui run lint`
  - [ ] UI build: `pnpm --dir ui run build`
  - [ ] Duplication: `pnpm --dir ui run lint:duplication`
- [ ] Manual verification:
  - [ ] Dismiss a stale item — confirm it disappears from inbox page and nav badge decrements
  - [ ] Reload browser — confirm dismissed item does not reappear
  - [ ] Open a second tab to the same project — confirm dismissed state is consistent (both tabs reload from backend)
  - [ ] "Clear All" dismisses all visible items and shows "All clear" empty state
  - [ ] Nav badge correctly shows 0 when all items dismissed
- [ ] Search docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved? (dismissed IDs are additive — no data deleted)
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
