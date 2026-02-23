# Story 075 — Entity Detail Page Polish

**Priority**: High
**Status**: Done
**Spec Refs**: UI / Entity Navigation
**Depends On**: 045 (Entity Cross-Linking), 057 (Prev/Next Navigation)

## Goal

Polish the entity detail page (`EntityDetailPage.tsx`) on four fronts: (1) make every
cross-reference in the Relationships section a clickable link that navigates to that entity,
(2) break the flat Relationships list into typed sub-sections (Characters, Locations, Props),
(3) reorder the page sections so the entity's profile/bio content appears first, and
(4) reduce vertical density of relationship rows so more fit on-screen at once.

## Acceptance Criteria

- [x] Every entity referenced in the Relationships section is a working clickable link (same behaviour as Scene Appearances)
- [x] Relationships are split into sub-sections: Characters, Locations, Props (section hidden if empty); generic label "Other" used for any untyped edge
- [x] Page section order for character/location/prop pages: Profile first → Relationships → Scene Appearances
- [x] "Content" section header renamed to "Profile" for bibles, "Scene" for scene pages
- [x] Relationship rows are visually compact — noticeably less vertical space per item than current full-card rows
- [x] Relationship items use a 2-column grid layout within each sub-section so wide screens use horizontal space rather than just stacking
- [x] All existing links (Scene Appearances, SceneEntityRoster) still work correctly
- [x] `pnpm --dir ui run lint` passes; `cd ui && npx tsc -b` passes

## Out of Scope

- Changes to backend / pipeline logic
- Reordering scene-type pages (scene pages have a different layout already)
- Pagination or filtering of relationships
- Changes to the EntityListPage or other pages

## AI Considerations

Pure UI refactor — no LLM calls involved. All work is restructuring JSX and tweaking Tailwind classes.

## Tasks

- [x] **Linking**: `resolve(otherId, otherType)` confirmed working; replaced bare `<Link hover:underline>` with `RelationshipTile` which wraps the entire card in a `<Link>` — visually obvious and click target is the whole tile
- [x] **Relationships split**: Partitioned into charEdges/locEdges/propEdges/otherEdges; rendered under typed sub-section headers with icons; empty groups hidden
- [x] **Compact row layout**: New `RelationshipTile` component — icon + name + scene count suffix + rel-type subtitle; `grid grid-cols-2 gap-1.5`; py-2 vs old py-2.5+spacer; confidence badge dropped from rows
- [x] **Page reorder**: Profile card moved first; `section !== 'scenes'` branch: Profile → Relationships → Scene Appearances; `section === 'scenes'` branch: EntityRoster → Scene card
- [x] Run required checks:
  - [x] `pnpm --dir ui run lint` — 0 errors, 7 pre-existing warnings (shadcn/ui internals)
  - [x] `cd ui && npx tsc -b` — clean
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Read-only UI change, no data mutation
  - [x] **T1 — AI-Coded:** `RelationshipTile`, `RelGroup`, `EdgeItem` types clearly named; logic is linear
  - [x] **T2 — Architect for 100x:** Single small component, no over-engineering
  - [x] **T3 — Fewer Files:** All changes in one file; no new files
  - [x] **T4 — Verbose Artifacts:** Work log covers decisions
  - [x] **T5 — Ideal vs Today:** Simple 2-col grid is the right abstraction level

## Files to Modify

- `ui/src/pages/EntityDetailPage.tsx` — all changes live here; `RelationshipsSection`, section order, header rename

## Notes

- `resolve(id, type)` in `useEntityResolver` normalises via `norm(s)` = `s.toLowerCase().replace(/[^a-z0-9]/g, '')`. Graph edge IDs like `bandolier` should resolve fine. Verify the type-filtered branch hits `entityMap.get(normalized)` for IDs.
- Compact rows: keep icon + entity name (linked) + relationship type on one line. Drop the confidence badge from individual rows (or move it to a tooltip). Keep scene count only if > 0 as a small `·N scenes` suffix.
- For the 2-col grid, each cell is `min-w-0` so names truncate cleanly.

## Plan

*To be filled in by build-story Phase 2.*

## Work Log

20260223-1830 — story created from user feedback on entity detail page UX gaps.
20260223-1900 — implemented: all four changes landed in EntityDetailPage.tsx in one pass. Key decisions: (1) linking was already wired via resolve() but visually invisible (hover:underline only) — fixed by making the entire RelationshipTile a <Link> wrapper; (2) split into 4 groups (Characters/Locations/Props/Other) with a fixed display order; (3) new RelationshipTile component using grid grid-cols-2; (4) Profile card moved to top, section order swapped. Verified by navigating Mariner→Rose (char link) and Bandolier→Mariner (prop→char link) — both navigated correctly. lint: 0 errors, tsc -b: clean.
