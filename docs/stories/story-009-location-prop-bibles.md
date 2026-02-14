# Story 009: Location and Prop Bibles

**Status**: Done
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
- [x] Location extraction module reads scene artifacts and canonical script.
- [x] Each location bible includes:
  - [x] **Name**: canonical location name (normalized from scene headings).
  - [x] **Aliases**: alternative references to the same location.
  - [x] **Description**: physical description, atmosphere, time-of-day variants.
  - [x] **Explicit evidence**: direct quotes establishing the location.
  - [x] **Inferred traits**: AI-inferred characteristics (mood, size, era) with confidence.
  - [x] **Scene presence**: scenes where this location appears.
  - [x] **Interior/Exterior**: INT, EXT, or both (from scene headings).
  - [x] **Spatial relationships**: containment (bedroom is inside the house) and adjacency (alley is behind the bar) — stubs for Story 010 entity graph.
  - [x] **Time-of-day usage**: which times of day this location is used (DAY, NIGHT, etc.).
- [x] Location deduplication: normalize variants (`SARAH'S KITCHEN`, `KITCHEN`, `THE KITCHEN` → single location with aliases).

### Prop Bible Extraction
- [x] Prop extraction module reads scene artifacts and canonical script.
- [x] Each prop bible includes:
  - [x] **Name**: canonical prop name.
  - [x] **Description**: physical description, significance.
  - [x] **Explicit evidence**: script references establishing the prop.
  - [x] **Inferred traits**: symbolic meaning, narrative function (with confidence).
  - [x] **Scene presence**: scenes where this prop appears or is referenced.
  - [x] **Owner/association**: which character(s) the prop is associated with — stub for Story 010.
  - [x] **Narrative significance**: Chekhov's gun detection — props introduced early that pay off later (with confidence).
- [x] Prop filtering: distinguish significant props from incidental scene dressing. Only create bible entries for props with narrative weight (mentioned multiple times, associated with a character, or flagged as significant by AI).

### Module Manifests
- [x] Module directory: `src/cine_forge/modules/world_building/location_bible_v1/`
- [x] Module directory: `src/cine_forge/modules/world_building/prop_bible_v1/`
- [x] Each with `module.yaml` and `main.py` following the Story 008 pattern.

### Schema
- [x] `LocationBible` Pydantic schema with location-specific fields.
- [x] `PropBible` Pydantic schema with prop-specific fields.
- [x] Schemas registered in schema registry.
- [x] Reuses `BibleManifest` from Story 008.

### Testing
- [x] Unit tests for location extraction (mocked AI).
- [x] Unit tests for prop extraction (mocked AI).
- [x] Integration test: scene artifacts + script → location and prop bible folders.
- [x] Schema validation on all outputs.

---

## Tasks

- [x] Design and implement `LocationBible` schema.
- [x] Design and implement `PropBible` schema.
- [x] Register schemas in schema registry.
- [x] Create `location_bible_v1` module (directory, manifest, main.py).
- [x] Implement location extraction with deduplication and normalization.
- [x] Implement spatial relationship stub extraction.
- [x] Create `prop_bible_v1` module (directory, manifest, main.py).
- [x] Implement prop extraction with significance filtering.
- [x] Implement owner/association and narrative significance detection.
- [x] Update `recipe-world-building.yaml` to include location and prop stages.
- [x] Write unit tests for location extraction.
- [x] Write unit tests for prop extraction.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

### 20260214-2000 — Implemented Location and Prop Bibles with Cross-Recipe Reuse
- **Result:** Success.
- **Evidence:**
  - Added `LocationBible` and `PropBible` schemas.
  - Implemented `location_bible_v1` and `prop_bible_v1` modules using the **Resilient Work Pattern**.
  - Implemented AI prop discovery pass.
  - Enabled **Cross-recipe artifact reuse** via `store_inputs` in `world_building` recipe.
  - Added unit tests in `tests/unit/test_location_bible_module.py` and `tests/unit/test_prop_bible_module.py`.
  - Updated integration test to verify character, location, and prop bible production in a single flow.
  - Verified UI "Explorer" mode for browsing bible data files (`master_v1.json`).
