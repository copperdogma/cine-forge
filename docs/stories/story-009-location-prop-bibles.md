# Story 009: Location and Prop Bibles

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 6.1 (Asset Masters — locations, props), 6.3 (Bible Artifact Structure), 6.4 (Asset States — state tracking hooks), 2.6 (Explanation Mandatory)
**Depends On**: Story 008 (bible infrastructure + character bible pattern), Story 005 (scene extraction — location/prop data)

---

## Goal

Apply the bible infrastructure from Story 008 to create **location bibles** and **prop bibles**. Each location and significant prop identified during scene extraction gets a master definition with evidence, inferred traits, spatial relationships, and confidence markers.

This story reuses the folder-based bible pattern established in Story 008. The extraction logic differs (locations care about spatial relationships, props care about narrative significance) but the artifact structure is identical.

---

## Acceptance Criteria

### Location Bible Extraction
- [ ] Location extraction module reads scene artifacts and canonical script.
- [ ] Each location bible includes:
  - [ ] **Name**: canonical location name (normalized from scene headings).
  - [ ] **Aliases**: alternative references to the same location.
  - [ ] **Description**: physical description, atmosphere, time-of-day variants.
  - [ ] **Explicit evidence**: direct quotes establishing the location.
  - [ ] **Inferred traits**: AI-inferred characteristics (mood, size, era) with confidence.
  - [ ] **Scene presence**: scenes where this location appears.
  - [ ] **Interior/Exterior**: INT, EXT, or both (from scene headings).
  - [ ] **Spatial relationships**: containment (bedroom is inside the house) and adjacency (alley is behind the bar) — stubs for Story 010 entity graph.
  - [ ] **Time-of-day usage**: which times of day this location is used (DAY, NIGHT, etc.).
- [ ] Location deduplication: normalize variants (`SARAH'S KITCHEN`, `KITCHEN`, `THE KITCHEN` → single location with aliases).

### Prop Bible Extraction
- [ ] Prop extraction module reads scene artifacts and canonical script.
- [ ] Each prop bible includes:
  - [ ] **Name**: canonical prop name.
  - [ ] **Description**: physical description, significance.
  - [ ] **Explicit evidence**: script references establishing the prop.
  - [ ] **Inferred traits**: symbolic meaning, narrative function (with confidence).
  - [ ] **Scene presence**: scenes where this prop appears or is referenced.
  - [ ] **Owner/association**: which character(s) the prop is associated with — stub for Story 010.
  - [ ] **Narrative significance**: Chekhov's gun detection — props introduced early that pay off later (with confidence).
- [ ] Prop filtering: distinguish significant props from incidental scene dressing. Only create bible entries for props with narrative weight (mentioned multiple times, associated with a character, or flagged as significant by AI).

### Module Manifests
- [ ] Module directory: `src/cine_forge/modules/world_building/location_bible_v1/`
- [ ] Module directory: `src/cine_forge/modules/world_building/prop_bible_v1/`
- [ ] Each with `module.yaml` and `main.py` following the Story 008 pattern.

### Schema
- [ ] `LocationBible` Pydantic schema with location-specific fields.
- [ ] `PropBible` Pydantic schema with prop-specific fields.
- [ ] Schemas registered in schema registry.
- [ ] Reuses `BibleManifest` from Story 008.

### Testing
- [ ] Unit tests for location extraction (mocked AI):
  - [ ] Location deduplication and normalization.
  - [ ] Spatial relationship stub extraction.
  - [ ] Scene presence aggregation.
- [ ] Unit tests for prop extraction (mocked AI):
  - [ ] Significance filtering (narrative props vs. scene dressing).
  - [ ] Owner/association detection.
  - [ ] Chekhov's gun detection.
- [ ] Integration test: scene artifacts + script → location and prop bible folders.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Location Deduplication
Scene headings often refer to the same location with different names. The extraction should normalize aggressively and create a single location bible with aliases. When uncertain, err on the side of splitting (two separate locations are easier to merge later than one incorrectly merged location is to split).

### Prop Significance Threshold
Not every object mentioned in a script deserves a bible entry. A "glass of water" in one scene is not a prop — it's scene dressing. A "glass of water" that appears in three scenes and is thrown at someone is a prop. The AI should evaluate narrative significance, and the module should have a configurable threshold.

### What This Story Does NOT Include
- **Entity relationship graph** — Story 010 turns relationship stubs into a full typed graph.
- **Continuity state tracking** — Story 011 adds state snapshots to bible folders.
- **Reference images** — Story 029 (User Asset Injection).

---

## Tasks

- [ ] Design and implement `LocationBible` schema.
- [ ] Design and implement `PropBible` schema.
- [ ] Register schemas in schema registry.
- [ ] Create `location_bible_v1` module (directory, manifest, main.py).
- [ ] Implement location extraction with deduplication and normalization.
- [ ] Implement spatial relationship stub extraction.
- [ ] Create `prop_bible_v1` module (directory, manifest, main.py).
- [ ] Implement prop extraction with significance filtering.
- [ ] Implement owner/association and narrative significance detection.
- [ ] Update `recipe-world-building.yaml` to include location and prop stages.
- [ ] Write unit tests for location extraction.
- [ ] Write unit tests for prop extraction.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
