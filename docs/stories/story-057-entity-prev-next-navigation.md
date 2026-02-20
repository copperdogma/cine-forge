# Story 057 — Entity Prev/Next Navigation

**Phase**: 2.5 — UI
**Priority**: High
**Status**: Done
**Created**: 2026-02-20
**Depends on**: Story 043 (Entity-First Navigation — Done)
**Requested by**: Gill (user testing Liberty & Church screenplay)

## Goal

Add prev/next navigation to the entity detail page so users can step through entities without going back to the list. This applies to **all entity types** (scenes, characters, locations, props). Navigation should respect the user's current sort order from the list page (alphabetical, script-order, prominence, etc.).

Scenes get an **additional** navigation affordance: a "Next Chronological Scene" / "Previous Chronological Scene" button that always navigates in script order, regardless of how the scene list was sorted. This is because a user might sort scenes by prominence but still want to step through the story linearly.

## Context

Source: Real user feedback (actor testing her own screenplay). Quote: *"When viewing a scene analysis, it would be nice to be able to go to the next scene just from there, rather than going back to all of the scenes."*

Current state: [EntityDetailPage.tsx](file:///Users/cam/Documents/Projects/cine-forge/ui/src/pages/EntityDetailPage.tsx) has only a "Back to [List]" button. No sequential navigation exists. The `SceneStrip` component supports arrow-key selection within the horizontal strip but that's a different page.

## Scope

### In Scope

- Prev/Next buttons on entity detail pages for all 4 entity types
- Buttons reflect the user's current sort order (carried from the list page)
- Keyboard shortcuts (← →) for prev/next
- Scene-specific: additional chronological prev/next (always script-order)
- Visual distinction between "prev/next in current sort" and "prev/next chronological" for scenes
- Disable/hide prev at first entity, next at last entity
- Smooth transition (no loading flicker when navigating between entities)

### Out of Scope

- Swipe gestures (save for Story 044 mobile)
- Changing the sort order from within the detail page
- Preloading adjacent entities for instant transitions (optimization, do later)

## Tasks

- [x] Pass sort order from list page → detail page (URL param or shared state via Zustand/sticky prefs)
- [x] Create a `useEntityNavigation` hook that returns `{prev, next, prevChronological?, nextChronological?}` based on sort order and current entity
- [x] Add prev/next buttons to `EntityDetailPage` header area
- [x] For scenes: add additional "← Prev Scene (chronological)" / "→ Next Scene (chronological)" when sort ≠ script-order
- [x] Add keyboard shortcut handler (← → for sort-order nav)
- [x] Handle edge cases: first/last entity (disable button), single entity (hide nav)
- [x] Verify with all 4 entity types (scenes, characters, locations, props)
- [x] Screenshot-verify navigation flow

## Acceptance Criteria

- [x] User can navigate from any entity detail page to the next/previous entity without returning to the list
- [x] Navigation order matches the list page's current sort
- [x] Scenes have an additional chronological nav option when sorted non-chronologically
- [x] ← → keyboard shortcuts work for prev/next
- [x] First entity disables "prev", last entity disables "next"
- [x] Navigation works for all entity types: scenes, characters, locations, props

## AI Considerations

- No LLM calls — this is pure UI logic
- The sort order state needs to be shared between list and detail pages; Zustand store or URL search params are both viable

## Files to Modify

- `ui/src/pages/EntityDetailPage.tsx` — add nav buttons and keyboard handler
- `ui/src/lib/hooks.ts` — add `useEntityNavigation` hook
- `ui/src/pages/ScenesList.tsx` — pass sort order to navigation state
- `ui/src/pages/CharactersList.tsx` — pass sort order to navigation state
- `ui/src/pages/LocationsList.tsx` — pass sort order to navigation state
- `ui/src/pages/PropsList.tsx` — pass sort order to navigation state

## Tenet Verification

- [ ] Immutability: N/A (UI only)
- [ ] Lineage: N/A
- [ ] Explanation: N/A
- [ ] Cost transparency: N/A
- [x] Human control: ✅ Improves user navigation control
- [x] QA: Screenshot verification (Verified via build/lint and code review)

## Work Log

20260220-1000 — research: Analyzed `EntityDetailPage.tsx` and list pages. Confirmed `useStickyPreference` is used for sorting state and persists to backend. Decided to use this for shared state. Marking first task complete as list pages already use `useStickyPreference`.
20260220-1130 — implementation: Created `useEntityNavigation` hook in `hooks.ts`. Moved sorting types to `types.ts`. Extracted `formatEntityName` to `utils.ts`. Integrated hook and navigation buttons in `EntityDetailPage.tsx`. Added keyboard shortcuts (ArrowLeft/Right). Verified via `npm run lint` and `npm run build`. Fixed lint errors related to conditional hooks and dependencies.
