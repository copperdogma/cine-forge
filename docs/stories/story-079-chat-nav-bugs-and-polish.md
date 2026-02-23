# Story 079 — Chat & Nav Bugs + Polish Bundle

**Priority**: Medium
**Status**: Done
**Spec Refs**: 2.5 — UI
**Depends On**: none

## Goal

Fix five small but noticeable bugs and polish items across the chat panel and navigation layer. These are bundled because they're all independent, low-risk, and fast to ship — no reason to give each a full story file.

## Acceptance Criteria

- [x] Clicking an entity (character, location, prop, scene) shows the entity as a persistent context chip above the chat input (icon + name, updates on navigation, clears on list pages). Originally spec'd as a chat message injection; redesigned to context chip during implementation with user approval.
- [x] Slash-search (CommandPalette `/` trigger) navigates to the entity detail page (`/characters/:id`, `/locations/:id`, `/props/:id`, `/scenes/:id`) — not the raw artifact URL. Confirmed in browser: searching MARINER → `/characters/mariner`.
- [x] Chat panel auto-scrolls to the bottom when new messages arrive **only if** the user is already at/near the bottom. Pre-existing — `shouldAutoScrollRef` + `ResizeObserver` already implemented in `ChatPanel.tsx:452-489`. No-op.
- [x] `ChatMessagePayload` backend model includes `route` field — `route: str | None = None` added to `models.py`. Persists via `model_dump(exclude_none=False)` for non-None values.
- [x] Ghost params `skip_enrichment` and `perform_deep_analysis` — grep across `src/` and `configs/` returned empty. Already clean from Story 062 refactor. No-op.

## Out of Scope

- Redesigning the entity-click-to-chat UX (just restore the regression)
- Changing how search results are ranked or scored
- Full chat scroll UX overhaul (sticky scroll indicator, jump-to-bottom button, etc.)
- Any changes to `ChatMessagePayload` beyond adding the `route` field

## AI Considerations

All five items are code, not LLM calls. No AI judgment required — just fix, test, verify.

## Tasks

- [x] **Entity context chip** (redesigned from "inject into chat"): Entity navigation now sets a persistent context chip above the chat input via `setEntityContext` in the store. Chip shows section icon + entity name, updates on navigation, clears when leaving an entity detail page. The `addActivity` findIndex fix remains as a robustness improvement for non-entity navigation callers.
- [x] **Slash-search routing fix**: Updated all 4 `onSelect` handlers in `CommandPalette.tsx` to navigate to entity detail URLs.
- [x] **Chat auto-scroll**: No-op — already correctly implemented in `ChatPanel.tsx` (ResizeObserver + `shouldAutoScrollRef` pattern, 120px threshold).
- [x] **`ChatMessagePayload` route field**: Added `route: str | None = None` to `models.py`.
- [x] **Ghost param audit**: No-op — grep returned empty across all of `src/` and `configs/`.
- [x] Run required checks:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 284 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — all checks passed
  - [x] UI: lint — 0 errors (7 pre-existing warnings, not ours); `tsc -b` — clean; vite build — clean
- [x] Search docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk. Activity messages are ephemeral context.
  - [x] **T1 — AI-Coded:** Comment in `addActivity` explains the idempotency fix clearly.
  - [x] **T2 — Architect for 100x:** All changes are minimal — no over-engineering.
  - [x] **T3 — Fewer Files:** 3 files touched, no new files created.
  - [x] **T4 — Verbose Artifacts:** Work log captures root cause and evidence.
  - [x] **T5 — Ideal vs Today:** Fixes are as simple as possible.

## Files to Modify

- `ui/src/components/CommandPalette.tsx` — fix entity search `onSelect` to navigate to detail pages
- `ui/src/components/ChatPanel.tsx` — add auto-scroll-if-at-bottom logic
- `ui/src/pages/EntityDetailPage.tsx` — restore entity → chat reference injection (or wherever this lived before)
- `ui/src/lib/chat-store.ts` — may need an `addEntityContext` / replace-last-nav-message helper
- `src/cine_forge/api/models.py` — add `route` field to `ChatMessagePayload`
- `src/cine_forge/api/app.py` — confirm route field flows through to JSONL write (likely automatic)

## Notes

- The ghost param audit is a "confirm then close" task — it may be a no-op if the cleanup already happened as part of the 3-stage refactor (Story 062). Check before spending time on it.
- For the entity → chat injection regression: the previous implementation likely lived in a `useEffect` keyed on the current URL or entity ID, calling `addMessage` with a `type: "activity"` or `type: "navigation"` message. Look at git log for the last commit that touched `EntityDetailPage` or `chat-store` to find when it broke.
- CommandPalette entity routing: characters → `/${projectId}/characters/:id`, locations → `/${projectId}/locations/:id`, props → `/${projectId}/props/:id`, scenes → may stay at artifact path if no dedicated scene detail page exists yet.

## Plan

### Exploration Summary

All five items investigated. Two are no-ops:
- **Auto-scroll (AC3)**: Already implemented in `ChatPanel.tsx` lines 452-489 via `shouldAutoScrollRef` + `ResizeObserver`. No changes needed.
- **Ghost params (AC5)**: `grep` across all of `src/` and `configs/` returns empty. Already clean from the Story 062 refactor.

**Three items need changes:**

---

### Task A — Fix `addActivity` idempotency bug (`ui/src/lib/chat-store.ts`)

**Root cause**: `addActivity` only replaces the activity message when it's the *last* message. Once an AI response arrives after a navigation event, the activity message is no longer last. Subsequent calls fall through to `addMessage`, which has a stable-ID idempotency guard (`activity_nav_${projectId}`) that blocks the update silently.

**Fix**: In `addActivity`, replace the `lastMsg?.type === 'activity'` check with `existing.findIndex(m => m.id === stableId)`. If the activity message exists anywhere in the list, update it in-place via `set()`. If it doesn't exist, fall through to `addMessage` (which will succeed since the ID is absent).

```
chat-store.ts addActivity():
  OLD: if (lastMsg?.type === 'activity') { replace last; } else { addMessage() }
  NEW: const existingIdx = existing.findIndex(m => m.id === `activity_nav_${projectId}`)
       if (existingIdx !== -1) { replace in-place via set(); postChatMessage(); }
       else { addMessage() }
```

**Files**: `ui/src/lib/chat-store.ts` only.
**Risk**: Low. The idempotency in `addMessage` still works for non-activity paths. Replacing in-place keeps temporal position (which is correct — the activity note should stay where the user navigated, not jump to the bottom).

---

### Task B — Fix search routing in `CommandPalette.tsx`

**Change**: 4 `navigate()` calls, one per entity type.

| Type | Before | After |
|------|--------|-------|
| Scenes | `/${projectId}/artifacts/scene/${scene.scene_id}/1` | `/${projectId}/scenes/${scene.scene_id}` |
| Characters | `/${projectId}/artifacts/${char.artifact_type}/${char.entity_id}/1` | `/${projectId}/characters/${char.entity_id}` |
| Locations | `/${projectId}/artifacts/${loc.artifact_type}/${loc.entity_id}/1` | `/${projectId}/locations/${loc.entity_id}` |
| Props | `/${projectId}/artifacts/${prop.artifact_type}/${prop.entity_id}/1` | `/${projectId}/props/${prop.entity_id}` |

**Files**: `ui/src/components/CommandPalette.tsx` only.
**Risk**: Very low. Routes confirmed in `App.tsx`.

---

### Task C — Add `route` field to `ChatMessagePayload` (`src/cine_forge/api/models.py`)

Add `route: str | None = None` to the Pydantic model. The `exclude_none=True` serialization means non-None routes persist; None routes are omitted (matching existing behavior for optional fields).

**Files**: `src/cine_forge/api/models.py` only.
**Risk**: Zero. Additive-only schema change. No existing code breaks.

---

### Approval blockers
None — all three changes are contained, additive-or-corrective, no new deps.

### Definition of done
- `addActivity` updates the activity message regardless of its position in the list
- Slash-search for a character navigates to `/characters/:id`
- `ChatMessagePayload` serializes `route` when non-None
- `make test-unit` passes, ruff clean, UI lint clean, `tsc -b` clean

## Work Log

20260223-1600 — explore: traced all 5 items. auto-scroll already implemented (ChatPanel.tsx:452-489 ResizeObserver pattern). ghost params already clean (grep empty). entity→chat bug root-caused to addActivity idempotency gap in chat-store.ts. slash-search routing bug confirmed in CommandPalette.tsx:308/340/364/385. route field missing from ChatMessagePayload (models.py:205). Plan written, awaiting approval.

20260223-1630 — implement: 3 changes landed. (1) chat-store.ts addActivity: replaced lastMsg?.type==='activity' check with findIndex(stableId) so activity message is updated regardless of position in list. (2) CommandPalette.tsx: 4 onSelect handlers updated — scenes→/scenes/:id, characters→/characters/:id, locations→/locations/:id, props→/props/:id. (3) models.py ChatMessagePayload: added route field. All checks clean: 284 unit tests pass, ruff clean, tsc -b clean, vite build clean. Runtime smoke: clicked "12 Gauge Shells" → chat showed "Viewing Prop: 12 Gauge Shells"; clicked "Airtag" → replaced with "Viewing Prop: Airtag"; slash-searched MARINER → navigated to /characters/mariner (not raw artifact). All ACs confirmed.

20260223-1700 — redesign (post-story): entity-click-to-chat activity message replaced with a persistent context chip above the chat input. New `entityContext` state in chat-store (setEntityContext / clearEntityContext). AppShell entity detail navigation calls setEntityContext instead of addActivity; all non-entity navigations call clearEntityContext. ChatPanel renders chip with section icon + clickable entity name. Validated via browser: chip shows "Mariner" on character detail, clears on list pages. Story marked Done. Validate: A — all checks pass.
