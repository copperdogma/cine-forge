# Story 108 — Continuity UI Page

**Priority**: High
**Status**: Draft
**Ideal Refs**: R3 (perfect continuity tracking across narrative)
**Spec Refs**: Spec 6.4 (Asset States / Continuity)
**Depends On**: 092 (Continuity AI Detection — backend module)

## Goal

Story 092 built the backend continuity engine — extracting entity state (costume, injuries, emotional state, props, position) per scene and detecting changes between scenes. The artifacts exist (`continuity_state`, `continuity_index`) but there's no way to see them in the UI. This story adds a Continuity page under the "World" nav section that visualizes entity state timelines, change events, and continuity gaps.

The Ideal (R3) demands perfect continuity — the UI should make it trivially easy to spot gaps and verify that state flows correctly through the narrative. Think script supervisor's notes: "Mariner has blood on his knuckles from Scene 5 onward — check."

## Acceptance Criteria

- [ ] New route `/:projectId/world/continuity` accessible from the "World" tab in the pipeline bar
- [ ] Continuity overview page shows: overall continuity score, total gaps, entity timeline count
- [ ] Entity timeline list: each tracked entity (characters, locations, props) with state count, gap count, and a visual indicator of coverage across scenes
- [ ] Clicking an entity opens a timeline detail view showing per-scene state snapshots with: properties (costume, emotional_state, position, etc.), change events (what changed, from/to, evidence quote), confidence scores, and gap warnings
- [ ] Change events are visually distinct from stable state (e.g., highlighted diff-style or colored badges)
- [ ] Gap scenes are flagged with a warning indicator and explanation of what's missing
- [ ] Continuity data loads from the existing API artifact endpoints (no new backend endpoints needed)
- [ ] Page handles empty state gracefully (no continuity data yet → prompt to run world-building)
- [ ] Mobile-responsive (stacks vertically on narrow viewports)

## Out of Scope

- Editing or overriding continuity states (read-only visualization)
- Continuity error auto-fix suggestions (future story)
- Comparing continuity across script versions (requires versioning infrastructure)
- "World" landing page (this story only adds the continuity sub-page; other World pages like entity graph visualization are separate stories)

## Approach Evaluation

- **Pure code**: This is a UI story — no LLM calls needed. All data comes from existing `continuity_state` and `continuity_index` artifacts via the artifact API.
- **Eval**: N/A — no AI behavior to evaluate.

The main design question is **information density**: continuity data is rich (18 entities × 13 scenes × multiple properties each). The UI must avoid overwhelming the user while still surfacing problems (gaps, low confidence) prominently.

## Tasks

- [ ] Add "World" section to sidebar nav with "Continuity" sub-item
- [ ] Create route `/:projectId/world/continuity` in `App.tsx`
- [ ] Build `ContinuityPage` component: loads `continuity_index` artifact, displays overview stats and entity list
- [ ] Build `EntityTimeline` component: loads `continuity_state` artifacts for a selected entity, renders per-scene state cards with properties and change events
- [ ] Add visual gap/warning indicators for scenes with missing state or low confidence
- [ ] Add empty state handling (no continuity artifacts → "Run World Building" prompt)
- [ ] Wire "World" tab in pipeline bar to the continuity page
- [ ] Add `continuity_state` and `continuity_index` to artifact-meta.ts with appropriate icons
- [ ] Run required checks for touched scope:
  - [ ] UI lint: `pnpm --dir ui run lint`
  - [ ] UI typecheck: `cd ui && npx tsc -b`
  - [ ] UI build: `pnpm --dir ui run build`
  - [ ] Visual verification via Chrome MCP
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `ui/src/App.tsx` — Add `/world/continuity` route
- `ui/src/components/AppShell.tsx` — Add "World" section to sidebar nav
- `ui/src/pages/ContinuityPage.tsx` — NEW: Overview + entity timeline list
- `ui/src/components/EntityTimelineView.tsx` — NEW: Per-entity scene-by-scene state visualization
- `ui/src/lib/artifact-meta.ts` — Already has continuity entries, may need icon updates
- `ui/src/lib/constants.ts` — May need pipeline bar "World" tab wiring

## Notes

### Data Shape

The continuity module produces:

- **`continuity_index`** (1 per project): Master index with `timelines` dict (keyed by `entity_type:entity_id`), each containing state artifact paths and gap scene IDs. Also has `overall_continuity_score` and `total_gaps`.

- **`continuity_state`** (1 per entity-scene pair, e.g., `character_mariner_scene_006`): Contains `properties` (key/value/confidence), `change_events` (property_key, previous_value, new_value, reason, evidence, is_explicit, confidence), `overall_confidence`.

Example from The Mariner (13 scenes): 18 entities tracked, 43 state snapshots, 23 gaps, overall score 0.874.

### Design Direction

- Timeline view could use a horizontal scene axis (columns = scenes, rows = entities) for quick scanning, or a vertical entity-focused view (select entity, see scene-by-scene cards)
- Change events should show quoted evidence from the script — this is what makes continuity useful ("torn at the left sleeve" → costume damage)
- Low-confidence properties should be visually dimmed or flagged
- Gaps should be prominent — these are the actionable items a script supervisor would care about

## Plan

{Written by build-story Phase 2}

## Work Log

{Entries added during implementation}
