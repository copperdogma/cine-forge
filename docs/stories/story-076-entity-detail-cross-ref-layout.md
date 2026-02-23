# Story 076 — Entity Detail: Cross-Reference Layout & Narrative Role Polish

**Priority**: High
**Status**: Done
**Spec Refs**: UI / Entity Navigation
**Depends On**: 075 (Entity Detail Page Polish)

## Goal

Three follow-up polish items on the entity detail page: (1) unify ALL cross-reference groups
(Characters, Locations, Props, Scene Appearances) into a single 2-column panel grid so they
sit visually at the same level — no more separate "Relationships" card plus "Scene Appearances"
card, just one coherent grid of type panels; (2) note that some entities in co-occurrence edges
have no bible artifact and therefore cannot be linked — pipeline coverage gap, tracked below;
(3) move the narrative role tag out of its own collapsible section and inline it into the
character profile header where it takes up much less space.

## Acceptance Criteria

- [x] All cross-reference groups (Characters, Locations, Props, Scene Appearances) are rendered
  as individual panel cards in a single `grid grid-cols-2` container — no separate "Relationships"
  wrapper, no separate "Scene Appearances" card outside the grid
- [x] Within each panel, items are a flat vertical list (same style as the current Scene
  Appearances list uses) — not 2-columns within the panel
- [x] Each entity in a panel is a clickable `EntityLink` chip; unresolvable entities (no bible)
  are shown dimmed/disabled
- [x] Narrative role badge is displayed inline in the character profile header (right after the
  name/aliases line), not in a separate collapsible section
- [x] The separate "Narrative Role" CollapsibleSection and its Separator are removed from ProfileViewer
- [x] All existing navigation and links continue to work
- [x] `pnpm --dir ui run lint` passes; `cd ui && npx tsc -b` passes

## Out of Scope

- Fixing missing character bibles (Thug 1/2/3 pipeline coverage gap) — tracked separately below
- Changes to pipeline, adjudicator, or backend code
- Pagination or filtering within panels
- Changes to scene pages (SceneEntityRoster already handles scenes correctly)

## Pipeline Coverage Note

Entities like "Thug 1", "Thug 2", "Thug 3" appear in co-occurrence relationship edges (derived
from scene breakdowns) but have no `character_bible` artifact. The entity adjudicator filters
them out as minor/unnamed characters. The dimmed display in the Characters panel is correct UI
behaviour — there is no profile page to navigate to. The root fix is a separate pipeline story:
lower the adjudicator threshold OR extract minimal bibles for all discovered entities. Needs
investigation before building.

## Tasks

- [x] **CrossReferencesGrid component**: Replaced `RelationshipsSection` + `SceneAppearances`
  with a single `CrossReferencesGrid`. Renders groups in `grid grid-cols-2 gap-4`.
  Groups: Characters, Locations, Props, Scene Appearances, Other (only non-empty groups shown).
- [x] **Panel contents**: Each panel is a `Card` with header (icon + label + count) and flat
  `space-y-1.5` list of `EntityLink` chips. Deduplication by entity ID with preference for
  named relationships over co-occurrence.
- [x] **Removed old components**: Deleted `RelationshipsSection`, `SceneAppearances`,
  `RelationshipTile`, and `typeIconAndColor` from `EntityDetailPage.tsx`.
- [x] **Narrative role inline**: Added `narrativeRole` badge in ProfileViewer header; removed
  the separate CollapsibleSection and its Separator.
- [x] Run required checks:
  - [x] `pnpm --dir ui run lint` — 0 errors
  - [x] `cd ui && npx tsc -b` — clean (fixed EntityType union type mismatch)
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Read-only UI change
  - [x] **T1 — AI-Coded:** Clear component names, linear logic
  - [x] **T2 — Architect for 100x:** No over-engineering
  - [x] **T3 — Fewer Files:** Changes in two files
  - [x] **T4 — Verbose Artifacts:** Work log covers decisions
  - [x] **T5 — Ideal vs Today:** Simple grid is the right level

## Files to Modify

- `ui/src/pages/EntityDetailPage.tsx` — replace RelationshipsSection + SceneAppearances with CrossReferencesGrid
- `ui/src/components/ArtifactViewers.tsx` — move narrative role badge to header in ProfileViewer

## Notes

- Deduplication: build a `Map<entity_id, edge>` — keep first non-co-occurrence edge, fall back
  to co-occurrence. Gives the most meaningful relationship label.
- Group order in grid: Characters → Locations → Props → Scene Appearances → Other. They flow
  naturally into 2 columns with no explicit row control needed.
- For scene refs in CrossReferencesGrid, call `resolve(ref, 'scene')` as before.
- The `EntityLink` non-compact variant already handles full-width display with truncation.

## Work Log

20260223-1910 — story created from follow-up UX feedback after Story 075.
20260223-1930 — implemented. CrossReferencesGrid replaces two separate components; panels flow naturally into 2-col grid; deduplication prefers named rel over co-occurrence. Narrative role badge moved into ProfileViewer header — no separate section. TypeScript catch: CrossReferencesGrid resolve prop typed as `string` but hooks.ts resolve expects `EntityType` union — fixed by using the explicit union type. Verified visually: Mariner page shows Characters(10)+Locations(9) side by side, then Props+Scene Appearances. Bandolier shows Mariner/Rose linked, Thug 1/2/3 dimmed correctly. lint: clean, tsc -b: clean.
