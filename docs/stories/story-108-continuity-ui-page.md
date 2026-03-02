# Story 108 — Continuity UI Page

**Priority**: High
**Status**: Done
**Ideal Refs**: R3 (perfect continuity tracking across narrative)
**Spec Refs**: Spec 6.4 (Asset States / Continuity)
**Depends On**: 092 (Continuity AI Detection — backend module)

## Goal

Story 092 built the backend continuity engine — extracting entity state (costume, injuries, emotional state, props, position) per scene and detecting changes between scenes. The artifacts exist (`continuity_state`, `continuity_index`) but there's no way to see them in the UI. This story adds a Continuity page under the "World" nav section that visualizes entity state timelines, change events, and continuity gaps.

The Ideal (R3) demands perfect continuity — the UI should make it trivially easy to spot gaps and verify that state flows correctly through the narrative. Think script supervisor's notes: "Mariner has blood on his knuckles from Scene 5 onward — check."

## Acceptance Criteria

- [x] New route `/:projectId/world/continuity` accessible from the "World" tab in the pipeline bar
- [x] Continuity overview page shows: overall continuity score, total gaps, entity timeline count
- [x] Entity timeline list: each tracked entity (characters, locations, props) with state count, gap count, and a visual indicator of coverage across scenes
- [x] Clicking an entity opens a timeline detail view showing per-scene state snapshots with: properties (costume, emotional_state, position, etc.), change events (what changed, from/to, evidence quote), confidence scores, and gap warnings
- [x] Change events are visually distinct from stable state (e.g., highlighted diff-style or colored badges)
- [x] Gap scenes are flagged with a warning indicator and explanation of what's missing
- [x] Continuity data loads from the existing API artifact endpoints (no new backend endpoints needed)
- [x] Page handles empty state gracefully (no continuity data yet → prompt to run world-building)
- [x] Mobile-responsive (stacks vertically on narrow viewports)

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

- [x] Add "World" section to sidebar nav with "Continuity" sub-item
- [x] Create route `/:projectId/world/continuity` in `App.tsx`
- [x] Build `ContinuityPage` component: loads `continuity_index` artifact, displays overview stats and entity list
- [x] Build `EntityTimeline` component: loads `continuity_state` artifacts for a selected entity, renders per-scene state cards with properties and change events
- [x] Add visual gap/warning indicators for scenes with missing state or low confidence
- [x] Add empty state handling (no continuity artifacts → "Run World Building" prompt)
- [x] Wire "World" tab in pipeline bar to the continuity page
- [x] Add `continuity_state` and `continuity_index` to artifact-meta.ts with appropriate icons
- [x] Run required checks for touched scope:
  - [x] UI lint: `pnpm --dir ui run lint`
  - [x] UI typecheck: `cd ui && npx tsc -b`
  - [x] UI build: `pnpm --dir ui run build`
  - [x] Visual verification via Chrome MCP
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

Vertical entity-focused view (accordion list of entities, expand to see scene-by-scene cards). Chosen over horizontal matrix for information density reasons — a horizontal grid at 18 entities × 13 scenes is unreadable on most screens. The accordion approach lets users drill into one entity at a time, which matches how a script supervisor actually works.

Data loading:
1. `useArtifactGroups` → find `continuity_index` group → `useArtifact(projectId, 'continuity_index', 'project', version)` to get the master index
2. When entity expanded: `useQueries` across `timeline.states` list → look up each `continuity_state` artifact version from groups map → load in parallel

Two new files:
- `ui/src/pages/ContinuityPage.tsx` — overview stats + entity accordion
- `ui/src/components/EntityTimelineView.tsx` — per-entity scene cards with properties, changes, gap warnings

AppShell: Add World collapsible section (mirrors Advanced section pattern). Route: `world/continuity` under project-scoped routes in App.tsx.

## Work Log

20260302-1400 — Explored codebase: confirmed continuity_index and continuity_state already registered in artifact-meta.ts (with Globe icon). Data loading pattern confirmed by tracing IntentMoodPage + hooks.ts. EntityTimeline.states[] contains exact artifact entity_ids for continuity_state lookup; continuity_index singleton uses entity_id "project".

20260302-1430 — Implemented all tasks. New files: ContinuityPage.tsx (overview stats + entity accordion), EntityTimelineView.tsx (per-entity scene cards). Modified: App.tsx (route), AppShell.tsx (World collapsible nav section + breadcrumb), artifact-meta.ts (Globe → Activity icon for both continuity types).

20260302-1445 — Fixed two lint errors: (1) `entityKey` unused in EntityTimelineView — removed from interface and destructuring entirely since timeline.states contains the needed IDs; (2) unnecessary eslint-disable-next-line comment in ContinuityPage — removed. All checks pass: lint clean, tsc -b clean, build clean.

20260302-1500 — Visual verification via Chrome MCP: the-mariner-55 project loads correctly showing 87% score, 23 gaps, 18 entities — matches expected data exactly. Entity rows expand inline. Mariner's scene cards show properties (costume, emotional_state, etc.), diff-style change events with evidence quotes, amber gap warnings. Empty state untested (no project without continuity data available) but code path verified by inspection.

20260302-1600 — Post-review UI fixes: User testing revealed three UX problems. (1) Gap subtitle said "low confidence or contradictory state" even for 97%-confidence scenes — replaced with condition-specific message via gapMessage() that infers which backend gap condition triggered the flag. (2) Confidence badge had no label — added native tooltip "Extraction confidence — how precisely the AI read this scene's text" to all three badge variants. (3) Changes section showed first-mentions (previous_value="Not described in detail") with the same strikethrough+arrow format as real state changes — added isFirstMention() sentinel detection and a "first mention" sky badge instead. All three in EntityTimelineView.tsx. Lint clean, tsc -b clean. Story 112 created to track the backend redesign (gap_reason storage, stable vs. mutable property categories).

Tenet checks:
- T0: Read-only page. No user data touched. ✓
- T1: Both files have top-level JSDoc explaining purpose and dependencies. Explicit inline comments on data loading strategy. ✓
- T2: No over-engineering. Two focused components, each doing one thing. ✓
- T3: Types defined in EntityTimelineView.tsx (domain types close to use). ContinuityIndexData inline in ContinuityPage (only used there). ✓
- T4: This work log captures decisions, approach rationale, and evidence. ✓
- T5: Accordion pattern is the right level of complexity — matches how a script supervisor actually thinks (one entity at a time). Horizontal matrix considered and rejected for density reasons. ✓
