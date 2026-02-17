# Story 043 — Entity-First Navigation

**Phase**: 2.5 — UI
**Priority**: High
**Status**: Draft
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
- **Detail pages**: Scene detail (entity roster + script link), Character detail (bible + appearances + relationships + continuity), Location detail (bible + appearances + relationships), Prop detail (bible + appearances)
- **Bidirectional linking**: Scene ↔ Script anchors, Entity detail → Scene appearances, Scene detail → Entity details
- Project status indicator (bar or sidebar element)
- Collapse Runs/Artifacts into Advanced section
- Keyboard shortcuts updated for new nav items

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

- [ ] Sidebar shows: Script, Scenes, Characters, Locations, Props, Inbox, Advanced (Runs/Artifacts/Settings)
- [ ] Each entity type has a list page showing all entities with name, key metadata, and artifact count/version
- [ ] Each entity type has a detail page showing bible content + cross-references
- [ ] Scene detail shows character/location/prop roster for that scene
- [ ] Character/Location detail shows scene appearances (which scenes they appear in)
- [ ] Character detail shows relationships (from entity_graph data)
- [ ] Clicking an entity in a scene → navigates to that entity's detail page
- [ ] Clicking a scene reference on an entity page → navigates to that scene's detail (or script anchor)
- [ ] Runs and Artifacts are accessible under a collapsed Advanced section
- [ ] Project status is visible on the Script/Home page
- [ ] Keyboard shortcuts updated and working
- [ ] All pages verified with screenshots against running backend with real data

## Tasks

- [x] Phase 1: Sidebar redesign + new routes + list pages
- [x] Phase 2: Entity detail pages (scene, character, location, prop)
- [ ] Phase 3: Script ↔ Scene bidirectional linking
- [ ] Phase 4: Polish, empty states, screenshot verification

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
