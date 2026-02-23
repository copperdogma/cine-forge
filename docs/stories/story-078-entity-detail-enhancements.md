# Story 078 — Entity Detail: Scroll-to-Top, Cross-Ref Ordering & Props Metadata

**Priority**: Medium
**Status**: Done
**Spec Refs**: UI / Entity Navigation
**Depends On**: 076 (Entity Detail Cross-Ref Layout)

## Goal

Three small UX improvements to the entity detail page following Story 076: (1) navigating to an
entity link should scroll to the top of the page — currently the page content loads in place and
the user may land mid-scroll; (2) the characters/locations/props panels in `CrossReferencesGrid`
have no ordering, making the most important co-stars hard to find — sort by scene co-occurrence
count descending so the most connected entities appear first; (3) the Props panel should visually
distinguish props that belong to a character (`signature_prop_of` edges) from props they merely
encountered (`co-occurrence` edges) — show an ownership indicator on signature items.

## Acceptance Criteria

- [x] Clicking any `EntityLink` (linked or unlinked) navigates to the target entity page and the
  page scrolls to the top — the user sees the entity header, not mid-page content
- [x] In the Characters, Locations, and Props panels of `CrossReferencesGrid`, items are sorted by
  scene co-occurrence count (number of shared scenes with the current entity) descending; ties
  broken alphabetically
- [x] Props panel items with `relType === 'signature_prop_of'` render with a visual ownership
  indicator (amber filled star icon) and are sorted to the top within the Props panel
- [x] Unresolvable entity entries (dimmed chips) follow the same sort logic — not pinned
- [x] `pnpm --dir ui run lint` passes; `cd ui && npx tsc -b` passes

## Out of Scope

- Ordering within Scene Appearances panel (scenes use their heading label naturally)
- Scene-count badges or numbers shown on the chips themselves (just ordering for now)
- Changing signature prop logic in the backend pipeline
- Prominence tiers on the ordering (that's Story 077)
- Pagination of panels

## AI Considerations

Pure UI/code — no LLM call needed. The ordering and metadata are already present in edge data.

## Tasks

- [x] **Scroll-to-top**: Added `mainScrollRef` on a wrapper `<div>` around the main content
  `<ScrollArea>` in `AppShell.tsx`. `useEffect` on `location.pathname` queries
  `[data-radix-scroll-area-viewport]` inside the ref and calls `.scrollTo({ top: 0 })`.
- [x] **Track scene co-occurrence count in `CrossReferencesGrid`**: Extended `RawEdge` with
  `sceneRefs: string[]` populated from `e.scene_refs`. Dedup logic now merges refs across
  duplicate edges (union) so count is maximally accurate. Sort by `sceneRefs.length` desc,
  then alphabetically within ties.
- [x] **Props ownership indicator**: `CrossRefPanel` items now carry `sceneCount` and `relType`.
  Props panel splits into signature-first (amber star icon `fill-amber-400`) then co-occurrence,
  each sorted by scene count. Star rendered via `suffix` prop added to `EntityLink`.
- [x] Run required checks:
  - [x] `pnpm --dir ui run lint` — 0 errors, 7 pre-existing warnings
  - [x] `cd ui && npx tsc -b` — clean
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Read-only UI change — no data at risk
  - [x] **T1 — AI-Coded:** Clear, self-documenting changes
  - [x] **T2 — Architect for 100x:** No over-engineering; sort logic is trivial
  - [x] **T3 — Fewer Files:** Changes in 2 files only (AppShell + EntityDetailPage)
  - [x] **T4 — Verbose Artifacts:** Work log covers decisions
  - [x] **T5 — Ideal vs Today:** Right level of complexity for current need

## Files to Modify

- `ui/src/app/AppShell.tsx` (or similar layout wrapper) — add scroll-to-top on route change
- `ui/src/pages/EntityDetailPage.tsx` — extend `RawEdge` with `sceneRefs`; sort panels; add
  ownership indicator for Props

## Notes

- The scroll container is a Radix `<ScrollArea>` inside `AppShell.tsx`, NOT `window`. Targeting
  `window.scrollTo(0, 0)` will not work.
- Graph edge data includes `scene_refs` (array of scene IDs) — this is the co-occurrence count
  source. It is currently discarded during `RawEdge` mapping and needs to be preserved.
- `relationship_type: "signature_prop_of"` is already in the raw edge data; it survives
  deduplication in `relType` — just needs to be threaded through to the render layer.
- Ownership indicator: use Lucide `Star` with `fill-amber-400` to distinguish from the outline
  style. Keep it subtle — small icon after the label, no tooltip needed.

## Work Log

20260223-1945 — story created. Three UX polish items from user review of Story 076 output:
scroll-to-top on entity navigation; sort cross-ref panels by shared scene count; distinguish
signature props from co-occurrence props in the Props panel.

20260223-2000 — implemented. Scroll-to-top: added wrapper `div` ref on the main `<ScrollArea>`
in AppShell; `useEffect` on pathname queries `[data-radix-scroll-area-viewport]` and scrolls to
top. Verified by navigating from Mariner→Rose while scrolled mid-page — Rose opens at header.
Cross-ref ordering: extended `RawEdge` with `sceneRefs: string[]` from graph `scene_refs` field;
dedup now merges refs across duplicate edges (union set). Sort: `b.sceneCount - a.sceneCount ||
a.label.localeCompare(b.label)`. Characters panel now shows Rose, Salvatori, Dad first. Props
ownership: `CrossRefPanel` items carry `relType`; Props panel splits signature (amber star) /
co-occurrence; both halves sorted by scene count. Mariner's Props panel shows Gun, Bosun Oar,
Airtag etc. with stars at top; Purse, Desk, Bookshelves without star below. No new files.
lint: 0 errors; tsc -b: clean.

20260223-2030 — follow-on work (post-story, included in same CHANGELOG entry): (1) Removed
duplicate "Scene Presence" collapsible from `ProfileViewer` in `ArtifactViewers.tsx` — same
`scene_presence` data was already shown as linked Scene Appearances chips in `CrossReferencesGrid`,
old version was plain unlinked text. Removed `Film` icon and `scenePresence` var. (2) Scene
Appearances now sorted in script order — added `useSceneIndex` to `EntityDetailPage`, build
`headingToNumber` map from `scene_index` artifact entries, sort `sceneRefs` by `scene_number`
ascending; unknown headings go to end (9999). Mariner's appearances: EXT Ruddy Rear → Elevator →
11th Floor → Stairwells → 13th/15th Floor → Backyard flashback — correct chronological order.
(3) "Owned by" row in prop detail Profile card — extracts `signature_prop_of` source edges where
`source_id === entityId`, renders linked `EntityLink` chips with `Users` icon below the profile
content, separated by border-t. Bandolier shows "Owned by · Mariner"; Desk shows nothing.
(4) Owner pills on Props list page — `useEntityGraph` loaded for `section === 'props'` only;
`propOwners: Record<string, string[]>` built from `signature_prop_of` edges; `OwnerPills`
component renders linked pills with `e.stopPropagation()` in all three density variants.
Screenshot confirmed: Airtag→Mariner, Beer→Mariner+Dad, Blockchain→Rose. All checks: 284 unit
tests pass, ruff clean, lint 0 errors, tsc -b clean.
