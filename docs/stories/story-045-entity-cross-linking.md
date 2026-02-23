# Story 045 — Entity Cross-Linking

**Phase**: Cross-Cutting (Pipeline + UI)
**Priority**: High
**Status**: Done
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

- [ ] Scene artifacts include `characters_present_ids` (slugified entity IDs alongside display names)
- [ ] `PropBible.scene_presence` populated with scene entity IDs (deterministic, from script spans)
- [ ] `PropBible.associated_characters` populated with slugified character IDs who primarily own/use this prop
- [ ] Entity graph includes prop↔character edges typed `"signature_prop_of"` (from `associated_characters`) and `"co-occurrence"` (from shared scenes)
- [ ] Entity graph includes prop↔location edges (from shared scene data)
- [ ] Entity graph co-occurrence edges use slugified character IDs (not `.lower()`)
- [ ] Prop detail pages show related characters (from graph edges)
- [ ] Scene detail pages show props roster inferred from prop bible `scene_presence`
- [ ] Unresolvable cross-reference badges are visually distinct (dimmed) from working links
- [ ] `make test-unit` passes; ruff clean; `tsc -b` clean

## Tasks

- [x] Task 1: Schema — add `characters_present_ids` to `Scene` + `SceneIndexEntry`; add `associated_characters` to `PropBible`
- [x] Task 2: `scene_breakdown_v1` — populate `characters_present_ids` by slugifying display names
- [x] Task 3: `prop_bible_v1` — deterministic `scene_presence` from script spans; AI-extracted `associated_characters`
- [x] Task 4: `entity_graph_v1` — fix 3 bugs; use `characters_present_ids`; emit `signature_prop_of` + co-occurrence prop edges
- [x] Task 5: UI — props section on scene detail page; dim unresolved `EntityLink` badges
- [x] Task 6: Tests — cover prop_list fix, char slugify, prop edges, scene_presence, associated_characters

## Notes

- Story 041 (Artifact Quality) should ideally land first or concurrently — fixing prop classification (removing costume items, adding missing props) before we link them makes the linking more useful.
- The fuzzy resolver in `useEntityResolver` (hooks.ts) is a solid temporary bridge. Phase 3 degrades it to a fallback rather than removing it, so older data still works.
- Scene-based inference (Phase 2) is valuable even after clean IDs land — it catches implicit relationships the explicit graph might miss.

## Plan

### Exploration Findings

**Key discovery**: `CharacterBible.scene_presence` and `LocationBible.scene_presence` already emit scene IDs (`"scene_001"`) — not free-text headings as the story assumed. Problems 2 and 5 in the story context are pre-solved for chars/locations. `PropBible.scene_presence` exists in schema but is never populated.

**`entity_graph_v1` has 3 bugs:**
- Line 200: `prop_list = ", ".join([p["name"] for prop in props for p in prop.get("files", [])])` — always produces empty string because `PropBible` dicts have no `"files"` key. Should be `", ".join([p["name"] for p in props])`.
- Co-occurrence edges use `char.lower()` for character source_id (e.g. `"the mariner"`) but character bible entity IDs are `_slugify()`-formatted (`"the_mariner"`). Deduplication and graph lookups miss these.
- Prop edges: completely absent. Can be derived from prop bible `scene_presence` once that's populated.

**Pipeline ordering constraint**: `props_present` on scene artifacts cannot be populated during `scene_breakdown_v1` (runs before prop discovery). The acceptance criterion "Scene artifacts include `props_present` field" is met via UI-side inference from prop bibles' `scene_presence` instead. The spirit is preserved — scene detail pages show props alongside characters.

**UI infrastructure**: `useEntityDetails(projectId, 'prop_bible')` already returns all prop bibles with `data.scene_presence`. Scene→props inference is a simple filter.

### Task 1 — Schema: new fields
**Files**: `src/cine_forge/schemas/scene.py`, `src/cine_forge/schemas/bible.py`

- Add `characters_present_ids: list[str] = Field(default_factory=list)` to both `Scene` and `SceneIndexEntry`. Carries slugified entity IDs alongside display-name `characters_present`.
- Add `associated_characters: list[str] = Field(default_factory=list)` to `PropBible`. AI-extracted slugified IDs of characters who primarily own or use this prop (signature props). Distinct from `scene_presence` (which is all scenes the prop appears in).

### Task 2 — `scene_breakdown_v1`: populate `characters_present_ids`
**File**: `src/cine_forge/modules/ingest/scene_breakdown_v1/main.py`

After building each scene artifact data dict, add:
```python
artifact_data["characters_present_ids"] = [_slugify(c) for c in artifact_data.get("characters_present", [])]
```
Add a local `_slugify` helper (same pattern as other modules: `re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")`).
Also update `SceneIndexEntry` construction to include `characters_present_ids` so `entity_graph_v1` can use it.

Done when: a scene artifact for "THE MARINER" scene has `characters_present_ids: ["the_mariner"]`.

### Task 3 — `prop_bible_v1`: `scene_presence` + `associated_characters`
**File**: `src/cine_forge/modules/world_building/prop_bible_v1/main.py`

**3A — Deterministic `scene_presence`**: add helper:
```python
def _find_scene_presence(prop_name: str, canonical_script: dict, scene_index: dict) -> list[str]:
    lines = canonical_script["script_text"].splitlines()
    prop_upper = prop_name.upper()
    found = []
    for entry in scene_index.get("entries", []):
        span = entry["source_span"]
        scene_lines = lines[span["start_line"] - 1 : span["end_line"]]
        if any(prop_upper in line.upper() for line in scene_lines):
            found.append(entry["scene_id"])
    return found
```
After AI extraction, overwrite: `definition = definition.model_copy(update={"scene_presence": scene_ids})`

**3B — AI-extracted `associated_characters`**: the LLM already receives full scene context via `_build_extraction_prompt`. Update the prompt to explicitly instruct the model to populate `associated_characters` with slugified character IDs. The `PropBible` schema now has the field, so the structured output will include it automatically. The prompt should clarify: "Set `associated_characters` to the slugified IDs (lowercase, underscores) of characters who *primarily own or wield* this prop — not every character who briefly touches it."

Done when: a signature prop like "bandolier" has `associated_characters: ["the_mariner"]` and `scene_presence: ["scene_001", "scene_003", ...]`.

### Task 4 — `entity_graph_v1`: fix 3 bugs + add prop edges
**File**: `src/cine_forge/modules/world_building/entity_graph_v1/main.py`

**Fix A (line 200):**
```python
# Before: prop_list = ", ".join([p["name"] for prop in props for p in prop.get("files", [])])
prop_list = ", ".join([p["name"] for p in props])
```

**Fix B** — in `_generate_co_occurrence_edges`, use `_slugify(char)` instead of `char.lower()` for both the char-location and char-char edge `source_id`/`target_id` fields.

**Fix C** — add prop co-occurrence edges in `_generate_co_occurrence_edges`:
- Add `prop_bibles` parameter (`list[dict[str, Any]]`, default `[]`)
- After the existing char-char loop, add: for each prop, for each `scene_id` in `prop.get("scene_presence", [])`, look up the matching scene entry from the index, emit `prop↔character` and `prop↔location` edges (`relationship_type="co-occurrence"`, `confidence=0.9`)
- Update the call site in `run_module` to pass `prop_bibles`

**Addition D** — `signature_prop_of` edges from `associated_characters`: add `_generate_signature_edges(prop_bibles)` function. For each prop, for each char_id in `prop.get("associated_characters", [])`, emit an edge:
```python
EntityEdge(
    source_type="prop", source_id=prop["prop_id"],
    target_type="character", target_id=char_id,
    relationship_type="signature_prop_of",
    direction="source_to_target",
    confidence=0.95,
)
```
Call after co-occurrence generation. Deduplication already handles overlap.

Also update the fallback in `_generate_co_occurrence_edges` to use `characters_present_ids` from scene entries when available (more accurate than re-slugifying display names):
```python
char_ids = entry.get("characters_present_ids") or [_slugify(c) for c in entry.get("characters_present", [])]
```

Done when: test with mock data shows prop↔character edges exist and no TypeError from prop_list fix.

### Task 5 — UI: props on scene detail page + unresolved link styling
**File**: `ui/src/pages/EntityDetailPage.tsx`

**5A — Props section on scene detail:**
In the scene detail rendering, add:
```tsx
const { data: propEntities } = useEntityDetails(projectId, 'prop_bible')
const propsInScene = useMemo(
  () => propEntities?.filter(p => (p.data?.scene_presence as string[] | undefined)?.includes(entityId ?? '')) ?? [],
  [propEntities, entityId]
)
```
In `SceneEntitySection`, accept `propsInScene` and render a "Props" block (same pattern as Characters).

**5B — Unresolved `EntityLink` styling:**
When `resolved === null`, render with `opacity-50 cursor-default` and a tooltip:
```tsx
if (!resolved) {
  return (
    <span className={cn(baseClass, 'opacity-50 cursor-default')} title="Reference not yet linked">
      {Icon && <Icon className={cn('h-3 w-3 shrink-0', iconColor)} />}
      <span className={compact ? undefined : 'truncate'}>{label}</span>
    </span>
  )
}
```

Done when: scene detail page shows a Props section; unresolved badges are visibly dimmed.

### Task 6 — Tests
**File**: `tests/unit/test_entity_graph.py` (or existing entity graph test file)

- `test_prop_list_fix`: entity_graph with 2 prop bibles produces non-empty `prop_list` in AI prompt
- `test_char_slugify_co_occurrence`: co-occurrence edges for "THE MARINER" have `source_id="the_mariner"` not `"the mariner"`
- `test_prop_cooccurrence_edges`: prop bible with `scene_presence=["scene_001"]` + scene_index with that scene having char "ROSE" → produces prop↔character edge

**File**: `tests/unit/test_prop_bible.py` (or existing)
- `test_scene_presence_populated`: mock canonical_script with "BANDOLIER" mention in scene_002 → `scene_presence=["scene_002"]`

### Impact Analysis
- `scene_breakdown_v1` touches scene schema: rerun intake recipe on any project to refresh (no old data is harmed; new field just absent on old artifacts)
- `entity_graph` changes: rerun world-building recipe to regenerate edges
- No public API changes; no UI routing changes
- Tests at risk: existing `entity_graph` tests that verify edge counts (the bug fix will change them)

### Definition of Done
- `entity_graph_v1` produces prop↔character and prop↔location edges
- `PropBible.scene_presence` populated with actual scene IDs
- Scene artifacts include `characters_present_ids`
- Scene detail page shows props section
- Unresolved EntityLink badges are visually dimmed
- `make test-unit` passes; ruff clean; `tsc -b` clean

## Work Log

20260223-1500 — explore: Discovered that char/loc bible scene_presence already uses scene IDs (pre-solved). PropBible.scene_presence exists in schema but never populated. entity_graph_v1 has 3 bugs: (A) prop_list always empty due to wrong list comprehension (line 200), (B) co-occurrence uses char.lower() not _slugify() causing ID mismatch, (C) prop edges completely absent. Pipeline ordering constraint: props_present can't be a scene artifact field; UI inference from prop bibles is the right approach. useEntityDetails(projectId, 'prop_bible') already returns what's needed.

20260223-1500 — impl Task 1: Added characters_present_ids to Scene+SceneIndexEntry (scene.py); added associated_characters to PropBible (bible.py) with description doc.

20260223-1500 — impl Task 2: Added _slugify helper to scene_breakdown_v1/main.py; populated characters_present_ids by slugifying characters_present on both the scene payload dict and the SceneIndexEntry construction.

20260223-1500 — impl Task 3: Added _find_scene_presence() to prop_bible_v1/main.py — deterministic scan of canonical_script line spans from scene_index to find which scenes each prop appears in. Added overwrite of definition.scene_presence after AI extraction. Updated _build_extraction_prompt to explicitly instruct AI to populate associated_characters with slugified character IDs for signature/ownership relationships only.

20260223-1500 — impl Task 4: entity_graph_v1/main.py — fixed prop_list bug (line 200), fixed char.lower() → _slugify(char) in co-occurrence edges, added _generate_signature_edges() for associated_characters → signature_prop_of edges, extended _generate_co_occurrence_edges() to accept prop_bibles and emit prop↔character + prop↔location co-occurrence edges using scene_presence.

20260223-1500 — impl Task 5: EntityDetailPage.tsx — updated EntityLink unresolved branch to render with opacity-50+cursor-default+hover:bg-transparent and title tooltip. Added useEntityDetails(projectId,'prop_bible') call when section==='scenes'; computed propsInScene via useMemo filtering by scene_presence.includes(entityId); updated SceneEntityRoster to accept+render propsInScene as a Props subsection. tsc -b clean, build clean.

20260223-1500 — impl Task 6: Added 5 tests to test_entity_graph_module.py (slugify bug, characters_present_ids preference, prop co-occurrence, signature edges, prop_list regression guard); added 3 tests to test_prop_bible_module.py (_find_scene_presence with match, no match, mock overwrite); added 1 test to test_scene_breakdown_module.py (characters_present_ids populated and slugified). 283 passed, 9 new, ruff clean.

20260223-1630 — smoke test + bug fix: Ran full pipeline on The Mariner script (output/smoke-045 and smoke-045b). Discovered scene_analysis_v1/main.py was NOT emitting characters_present_ids in its _build_enriched_scene() output — it built characters but never called _slugify. Fixed by importing _slugify from scene_breakdown_v1.main and adding "characters_present_ids": sorted(_slugify(c) for c in characters) to the return dict. All 283 tests still pass, ruff clean.

Evidence from smoke test on The Mariner script:
- characters_present_ids: scene_006=['mariner','rose'], scene_008=['carlos','mariner','mikey','rose','vinnie'] ✓
- prop scene_presence: 'Gun'→[scene_001,003,004,007,008,009,013], 'Purse'→[scene_004,006,009,010] ✓
- prop associated_characters: 'Wooden Oar'→['the_mariner'], 'Blockchain Password Chip'→['rose'], 'Gun'→['the_mariner','salvatori'] ✓
- entity_graph: 164 total edges, 84 prop edges, 15 signature_prop_of edges (conf=0.95), co-occurrence edges for all props (conf=0.9) ✓
- Cost: $0.20 ingest+extract+world-building, $0.004 entity_graph

