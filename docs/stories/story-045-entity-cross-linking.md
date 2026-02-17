# Story 045 — Entity Cross-Linking

**Phase**: Cross-Cutting (Pipeline + UI)
**Priority**: High
**Status**: To Do
**Depends on**: Story 043 (Entity-First Navigation — Done), Story 041 (Artifact Quality Improvements — To Do)

## Goal

Make every entity in the system richly cross-linked so that navigating between characters, locations, props, and scenes is seamless and complete. Currently, cross-references are sparse, inconsistent in format, and missing entire relationship categories (e.g., props have no links to characters or locations at all).

After this story: every entity detail page shows accurate, clickable links to all related entities. The data pipeline produces clean, structured cross-references rather than free-text descriptions that the UI must fuzzy-match.

## Context

### Problems Discovered (Story 043 testing)

During entity-first navigation testing, we found multiple layers of linking issues spanning both the pipeline (data quality) and the UI (resolution logic).

#### Upstream / Pipeline Issues

1. **Entity graph has zero prop edges.** The `entity_graph` extraction module only produces character-character and character-location edges. Props are completely absent from the relationship graph, so prop detail pages show no relationships at all.

2. **`scene_presence` contains free-text descriptions, not structured references.** Bible artifacts store scene references like `"EXT. CITY CENTRE - NIGHT: Establishing shot showing the post-apocalyptic urban wasteland with fires..."` instead of structured scene IDs like `"scene_002"`. This forces the UI to do fragile fuzzy/prefix matching against scene headings.

3. **Scenes have no `props_present` field.** The scene schema has `characters_present: list[str]` but no equivalent for props. Scene detail pages can't show which props appear in them.

4. **`characters_present` uses display names, not entity IDs.** Scene data has `"ROSE"` but the character artifact is `character_bible/rose`. The UI must fuzzy-match names to entity_ids, which breaks for edge cases (nicknames, aliases, compound names).

5. **No reverse index from entities to scenes by entity_id.** Bible artifacts track scene presence by heading text, not by scene entity_id. There's no clean way to join `character_bible/rose` to `scene/scene_004` without string matching.

#### UI Issues (workarounds in place, but fragile)

6. **`useEntityResolver` relies on fuzzy prefix matching.** Works for most cases but will break for scenes with similar headings (e.g., "INT. HALLWAY - DAY" and "INT. HALLWAY - NIGHT" could collide after normalization if scene_presence is truncated).

7. **Unresolvable links render as plain badges.** When the resolver can't match a reference, it falls back to a non-clickable badge. This is correct behavior but makes broken data invisible — users don't know if a badge is "no link available" vs "link broken."

### Ideal Data Model

The pipeline should produce structured cross-references so the UI doesn't need fuzzy matching at all:

```
# In scene artifacts:
characters_present: ["rose", "mariner"]      # entity_ids, not display names
locations: ["backyard"]                        # entity_id
props_present: ["bandolier", "flare_gun"]     # entity_id (new field)

# In bible artifacts:
scene_presence: ["scene_002", "scene_007"]    # entity_ids, not headings

# In entity_graph:
edges:
  - source_id: bandolier, source_type: prop,
    target_id: mariner, target_type: character,
    relationship_type: "wielded_by"
  - source_id: backyard, source_type: location,
    target_id: bandolier, target_type: prop,
    relationship_type: "contains_prop"
```

## Scope

### In Scope

- Pipeline: Add `props_present` field to scene schema and extraction
- Pipeline: Normalize `scene_presence` in bibles to use scene entity_ids instead of free-text headings
- Pipeline: Normalize `characters_present` in scenes to use entity_ids instead of display names
- Pipeline: Add prop edges to entity_graph extraction (prop↔character, prop↔location)
- UI: Scene-based inference as a fallback — if entities share scenes, show them as implicitly linked
- UI: Distinguish "no data" badges from "broken link" badges visually
- Schema updates for new fields (backward-compatible — new fields optional)

### Out of Scope

- Prop extraction quality improvements (that's Story 041 — classification, missing props, etc.)
- Entity graph visualization page (that's a separate UI story)
- Editing relationships through the UI (future interactive feature)

## Technical Approach

### Phase 1 — Schema & Pipeline Changes

- Add `props_present: list[str]` to Scene schema (optional, default empty)
- Update scene extraction module to populate `props_present` with entity_ids
- Update scene extraction to emit `characters_present` as entity_ids (add `characters_present_names` for display)
- Update bible extraction modules to emit `scene_presence` as scene entity_ids (add `scene_presence_display` for human-readable labels)
- Update entity_graph extraction to include prop edges
- Run pipeline on test screenplay, verify all new fields populated

### Phase 2 — UI: Scene-Based Inference

- Build `useSceneInference` hook: given an entity, find all scenes it appears in, then find all other entities in those scenes
- Show "Also in these scenes" section on prop/character/location detail pages
- This works even without perfect upstream data — it's a pure join on shared scene membership

### Phase 3 — UI: Clean Resolution

- Update `useEntityResolver` to prefer entity_id lookups over fuzzy heading matching
- Add visual distinction for unresolvable references (e.g., dimmed text with tooltip "Not yet linked")
- Remove fuzzy matching fallbacks once pipeline produces clean IDs (keep as graceful degradation)

### Phase 4 — Validation

- Run pipeline end-to-end on The Mariner screenplay
- Verify every entity detail page has working cross-links
- Verify scene detail pages show characters, locations, AND props
- Screenshot verification of all entity types

## Acceptance Criteria

- [ ] Scene artifacts include `props_present` field with entity_ids
- [ ] Scene `characters_present` uses entity_ids (with display name field for UI)
- [ ] Bible `scene_presence` uses scene entity_ids (with display label for UI)
- [ ] Entity graph includes prop↔character and prop↔location edges
- [ ] Prop detail pages show related characters and locations (from graph or scene inference)
- [ ] Scene detail pages show props roster alongside characters and location
- [ ] All cross-reference links on entity detail pages are clickable (no broken links with real data)
- [ ] Unresolvable references are visually distinct from working links
- [ ] Pipeline tested end-to-end with The Mariner screenplay

## Tasks

- [ ] Phase 1: Schema and pipeline changes (scene, bible, entity_graph modules)
- [ ] Phase 2: UI scene-based inference for implicit entity relationships
- [ ] Phase 3: UI clean resolution (prefer entity_ids, visual distinction for broken links)
- [ ] Phase 4: End-to-end validation and screenshot verification

## Notes

- Story 041 (Artifact Quality) should ideally land first or concurrently — fixing prop classification (removing costume items, adding missing props) before we link them makes the linking more useful.
- The fuzzy resolver in `useEntityResolver` (hooks.ts) is a solid temporary bridge. Phase 3 degrades it to a fallback rather than removing it, so older data still works.
- Scene-based inference (Phase 2) is valuable even after clean IDs land — it catches implicit relationships the explicit graph might miss.

## Work Log
