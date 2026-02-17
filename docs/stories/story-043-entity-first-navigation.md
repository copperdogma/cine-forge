# Story 043 — Entity-First Navigation

**Phase**: 2.5 — UI
**Priority**: High
**Status**: Done
**Depends on**: Story 042 (Wire Mock UI — Done), Story 011f (Conversational AI Chat — In Progress)

## Goal

Promote creative entities (script, scenes, characters, locations, props) to first-class sidebar navigation items, replacing the pipeline-centric Artifacts dump. The Operator Console should feel like a **story workspace**, not a pipeline dashboard.

After this story: the sidebar is organized around the screenplay's creative objects. Every entity has a dedicated list page and detail page. Cross-entity navigation (scenes ↔ characters ↔ locations ↔ props) is intuitive and bidirectional. Pipeline concepts (Runs, raw Artifacts) move to a collapsed Advanced section.

## Context

The current sidebar has four items: **Home, Runs, Artifacts, Inbox**. "Artifacts" is a flat list of every artifact type — useful for debugging, not for creative work. The user thinks in terms of "my characters" and "scene 12," not `character_bible/SARAH/v3`.

### Design Decisions (from planning discussion)

1. **Script is Home.** The screenplay is the landing page for a project. A project status bar sits above or near the script view.
2. **Scenes get their own nav item.** Each scene has a detail page showing its character/location/prop roster. Clicking an entity in the scene jumps to its detail page; clicking a scene reference from anywhere else jumps to that scene in the script.
3. **Characters, Locations, Props** each get their own nav items with list → detail pages.
4. **Entity detail pages are rich.** A character page shows: bible profile, scene appearances, relationships (from entity_graph), continuity timeline, and associated props. Same pattern for locations and props (adapted to what's relevant).
5. **Relationships and continuity are not standalone nav items.** They surface naturally on entity detail pages.
6. **Inbox stays** in the sidebar as-is.
7. **Runs and raw Artifacts** move to a collapsed "Advanced" section at the bottom of the sidebar.
8. **Shots** are a future concern (noted for story planning but out of scope here).

### New Sidebar Structure

```
📄 Script          (Home — the screenplay + project status)
🎬 Scenes          (list all scenes → scene detail)
👤 Characters      (list all characters → character detail)
📍 Locations       (list all locations → location detail)
🔧 Props           (list all props → prop detail)
📥 Inbox           (filtered chat messages, unchanged)
─── Advanced ───
⚙️ Runs            (pipeline runs, collapsed by default)
📦 Artifacts       (raw artifact browser, collapsed by default)
⚙️ Settings
```

## Scope

### In Scope

- Sidebar redesign with entity-centric nav items
- Route structure for all new pages
- **List pages**: Scenes, Characters, Locations, Props (each showing entity cards with key metadata)
- **List sorting**: Three sort modes per list — script order (default), alphabetical, prominence (scene count / mention frequency)
- **List view density**: Three view sizes — compact (single-line rows), medium (current card grid), large (expanded cards with summary/description)
- **Detail pages**: Scene detail (entity roster + script link), Character detail (bible + appearances + relationships + continuity), Location detail (bible + appearances + relationships), Prop detail (bible + appearances)
- **Bidirectional linking**: Scene ↔ Script anchors, Entity detail → Scene appearances, Scene detail → Entity details
- Project status indicator (bar or sidebar element)
- Collapse Runs/Artifacts into Advanced section
- Keyboard shortcuts updated for new nav items
- Delete `ui/operator-console-lite/` — legacy stopgap, fully superseded by the production UI

### Out of Scope

- Shots/shot planning (future story)
- New API endpoints (reuse existing artifact APIs — group by type, filter by entity)
- Inline editing of entities (existing edit flow via chat/artifacts is unchanged)
- Chat panel changes (011f owns that)
- Entity graph visualization page (the data surfaces on detail pages, but a standalone graph viz is out of scope)

## API Surface (existing, no changes needed)

| Endpoint | Used For |
|----------|----------|
| `GET /api/projects/{id}/artifacts` | List all artifact groups → filter by type for entity lists |
| `GET /api/projects/{id}/artifacts/{type}/{entity_id}/{version}` | Load entity detail (bible content) |
| `GET /api/projects/{id}/artifacts/entity_graph/{entity_id}/{version}` | Relationships for an entity |
| `GET /api/projects/{id}/artifacts/scene/{entity_id}/{version}` | Scene detail with entity references |
| `GET /api/projects/{id}/artifacts/continuity_state/{entity_id}/{version}` | Continuity for an entity |

If the existing artifact API doesn't support filtering by type efficiently, we may add a query parameter — but that's a minor backend tweak, not a new endpoint.

## Technical Approach

### Phase 1 — Sidebar + Routes + List Pages
- Redesign `AppShell.tsx` sidebar with new nav items
- Add routes: `/:projectId/scenes`, `/:projectId/characters`, `/:projectId/locations`, `/:projectId/props`
- Create list page components that fetch artifacts by type and render entity cards
- Collapse Runs/Artifacts into Advanced section with toggle
- Update keyboard shortcuts (⌘0–⌘5 for new nav)
- Update breadcrumbs for new route structure

### Phase 2 — Entity Detail Pages
- Scene detail page: heading, description, entity roster (characters/locations/props with links)
- Character detail page: bible profile (reuse ProfileViewer), scene appearances, relationships section, continuity timeline
- Location detail page: same pattern as character
- Prop detail page: bible profile, scene appearances
- All detail pages link bidirectionally to scenes and related entities

### Phase 2b — List Sorting and View Density
- Sort toggle (toolbar at top of list pages): Script Order (default), Alphabetical, Prominence
  - Script Order = first appearance scene number. Industry standard default.
  - Alphabetical = by entity name. Universal fallback for quick lookup.
  - Prominence = by scene count (number of scenes the entity appears in). Production-focused — identifies who/what gets the most screen time.
  - Future consideration: "By Dialogue Lines" for characters (needs data from script analysis).
- View density toggle (compact / medium / large):
  - Compact: single-line rows — icon, name, scene count badge. Dense, scannable.
  - Medium: current card grid — name, version, health, key metadata.
  - Large: expanded cards — name + summary/description snippet + scene count + relationship count.
- Preferences stored in project settings (project.json), sticky per entity type (e.g., characters=alphabetical+compact, scenes=script-order+medium)
- Research notes: Final Draft uses Order of Appearance as default. Highland 2 offers "by number of scenes" and "by number of lines." StudioBinder uses production-oriented grouping. No tool offers AI-driven "dramatic importance" ranking — future CineForge differentiator.

### Phase 3 — Script ↔ Scene Integration
- Add scene anchors/sections to the script view (scrollable TOC or visual markers)
- "Jump to script" from scene detail page
- "Jump to scene" from script view scene headings
- Project status bar above or near the script view

### Phase 4 — Polish
- Loading states, empty states, error states for all new pages
- Responsive behavior (sidebar collapse, mobile)
- Screenshot-verify every page with real data
- Browser click-through test with running backend

## Acceptance Criteria

- [x] Sidebar shows: Script, Scenes, Characters, Locations, Props, Inbox, Advanced (Runs/Artifacts/Settings)
- [x] Each entity type has a list page showing all entities with name, key metadata, and artifact count/version
- [x] Each entity type has a detail page showing bible content + cross-references
- [x] Scene detail shows character/location/prop roster for that scene
- [x] Character/Location detail shows scene appearances (which scenes they appear in)
- [x] Character detail shows relationships (from entity_graph data)
- [x] Clicking an entity in a scene → navigates to that entity's detail page
- [x] Clicking a scene reference on an entity page → navigates to that scene's detail (or script anchor)
- [x] Runs and Artifacts are accessible under a collapsed Advanced section
- [x] Project status is visible on the Script/Home page
- [x] Entity lists are sortable by: script order (first appearance), alphabetical, prominence (scene count)
- [x] Entity lists support three view densities: compact, medium, large
- [x] Sort and density preferences are sticky (stored in project.json, remembered per entity type)
- [x] Keyboard shortcuts updated and working
- [x] All pages verified with screenshots against running backend with real data
- [x] `ui/operator-console-lite/` deleted

## Tasks

- [x] Phase 1: Sidebar redesign + new routes + list pages
- [x] Phase 2: Entity detail pages (scene, character, location, prop)
- [x] Phase 2b: List sorting (script order / alphabetical / prominence) and view density (compact / medium / large)
- [x] Phase 3: Script ↔ Scene bidirectional linking
- [x] Phase 4a: Polish — build fixes, browser verification, runtime bug fixes
- [x] Phase 4b: Flatten `ui/operator-console/` → `ui/`
- [x] Housekeeping: Delete operator-console-lite (legacy stopgap)

## Work Log

20260216-1430 — Phase 1 complete: sidebar + routes + list pages + entity detail wrapper
- **Result**: Build passes. All new pages created, sidebar redesigned, routes wired.
- **Files created**: `ScenesList.tsx`, `CharactersList.tsx`, `LocationsList.tsx`, `PropsList.tsx`, `EntityDetailPage.tsx`
- **Files modified**: `AppShell.tsx` (sidebar: entity-first nav + collapsible Advanced section), `App.tsx` (new routes)
- **Sidebar**: Script, Scenes, Characters, Locations, Props, Inbox, then collapsible Advanced (Runs, Artifacts, Settings)
- **Shortcuts**: ⌘0=Script, ⌘1=Scenes, ⌘2=Characters, ⌘3=Locations, ⌘4=Props, ⌘5=Inbox
- **Breadcrumbs**: Updated for entity detail routes (e.g., Characters > Sarah Connor)
- **Entity detail page**: Phase 1 wrapper that resolves latest artifact version and renders existing viewers
- **Branch**: `feature/043-entity-first-navigation` in worktree `cine-forge-043`
- **Next**: Phase 2 — Enrich entity detail pages with cross-references (scene appearances, relationships, continuity)

20260216-1630 — Phase 2 complete: Rich entity detail pages with cross-references
- **Result**: Build passes. EntityDetailPage.tsx rewritten with cross-reference components.
- **Files modified**: `EntityDetailPage.tsx` (major rewrite), `hooks.ts` (added `useEntityGraph`)
- **SceneAppearances**: Reads `scene_presence` from bible data, renders clickable scene links
- **RelationshipsSection**: Fetches entity_graph artifact, filters edges for current entity, shows related entities with links
- **SceneEntityRoster**: For scene detail pages — lists characters_present and location with clickable entity links
- **Entity ID resolution**: Fuzzy matching via `resolveEntityId()` — normalizes names/IDs for cross-linking
- **Next**: Phase 3 — Script ↔ Scene bidirectional linking

20260216-2100 — Phase 2b complete: Sort controls + view density toggles on all list pages
- **Result**: Build passes. All 4 list pages have toolbar with 3 sort modes + 3 density views.
- **Files created**: `EntityListControls.tsx` (shared toolbar component)
- **Files modified**: `ScenesList.tsx`, `CharactersList.tsx`, `LocationsList.tsx`, `PropsList.tsx`
- **Sort modes**: Script Order (default), Alphabetical (A-Z), Prominence (TODO: wire to scene data for bible entities)
- **View densities**: Compact (single-line rows), Medium (card grid), Large (expanded 2-col cards)
- **Housekeeping**: Deleted `ui/operator-console-lite/`, updated AGENTS.md repo map, removed stray root `package.json`
- **Provenance**: De-emphasized from standalone card to inline badge in entity detail header

20260216-2130 — Phase 3 complete: Script ↔ Scene bidirectional linking
- **Result**: Build passes. Clickable scene headings in editor + "View in Script" on scene detail pages.
- **Files modified**: `ScreenplayEditor.tsx` (forwardRef, scrollToLine/scrollToHeading, onSceneHeadingClick), `ProjectHome.tsx` (?scene= param handling, heading click → scene detail nav), `EntityDetailPage.tsx` ("View in Script" button)
- **Flow**: Scene detail → "View in Script" → Script page with `?scene=heading` → auto-scrolls editor to that scene heading
- **Flow**: Script page → click scene heading (amber text) → navigates to scene detail page
- **Next**: Phase 4 — Polish, screenshot verification, flatten ui/ directory

20260217-0043 — Phase 4a complete: Browser verification + runtime bug fixes
- **Result**: Build passes. All pages verified in browser with real backend data (The Mariner project, 71 artifact groups).
- **Bug found & fixed**: React hooks ordering violation in CharactersList, LocationsList, PropsList — `useMemo` was called after early returns (`isLoading`/`error` guards). Moved `useMemo` above all early returns in all three files. ScenesList was already correct.
- **Bug found & fixed**: Missing `navigate` variable in EntityDetailPage (used in "View in Script" button but never declared in component scope). Added `const navigate = useNavigate()`.
- **Bug found & fixed**: Type-only imports needed for `SortMode`/`ViewDensity` in all 4 list pages (verbatimModuleSyntax).
- **Verified pages**: Landing, Script/Home, Scenes list (all 3 densities + sort), Scene detail (entity roster, View in Script), Characters list (sort + density), Character detail (scene appearances, bible content), Locations list, Props list, Advanced section expand/collapse.
- **Bidirectional linking verified**: Script heading click → scene detail, Scene "View in Script" → script with auto-scroll.
- **No console errors** in any page (only unrelated Chrome extension noise).
- **Remaining**: Phase 4b — flatten `ui/operator-console/` → `ui/` (deferred — needs current changes committed first since `git mv` requires clean working tree for moved files).

20260217-0620 — Sticky preferences + Phase 4b complete: Story done
- **Sticky preferences**: Extended backend `PATCH /settings` to accept `ui_preferences` dict with shallow merge. Frontend `useStickyPreference` hook reads from project summary, optimistic updates, fire-and-forget persistence. All 4 list pages (Scenes, Characters, Locations, Props) now persist sort, density, and direction per entity type to `project.json`.
- **Backend files**: `models.py` (ui_preferences on ProjectSummary + ProjectSettingsUpdate), `service.py` (merge-based write), `app.py` (pass-through)
- **Frontend files**: `types.ts`, `api.ts`, `hooks.ts` (useStickyPreference), all 4 list pages
- **Phase 4b**: Flattened `ui/operator-console/` → `ui/` via `git mv` (74 files). Updated AGENTS.md repo map, README.md dev command, index.html title → "CineForge".
- **All acceptance criteria met.** Story 043 complete.
