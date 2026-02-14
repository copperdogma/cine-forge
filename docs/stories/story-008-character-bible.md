# Story 008: Bible Infrastructure and Character Bible

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 6.1 (Asset Masters), 6.2 (Entity Graph — character edges), 6.3 (Bible Artifact Structure), 2.1 (Immutability), 2.6 (Explanation Mandatory), 2.7 (Cost Transparency)
**Depends On**: Story 005 (scene extraction — provides per-scene character lists), Story 002 (artifact store — folder-based artifact support)

---

## Goal

Build the bible infrastructure (folder-based artifacts with manifests) and create the first bible type: **character bibles**. Each character identified during scene extraction gets a master definition extracted from the canonical script, with explicit evidence, inferred traits, relationships, and confidence markers.

This story establishes the bible artifact pattern that Stories 009 (locations/props) and 011 (continuity states) will reuse. Get the infrastructure right here — the pattern should be copy-paste for other entity types.

---

## Acceptance Criteria

### Bible Infrastructure (Shared by 008/009/011)
... (existing items) ...
- [x] Bible entries integrate with the dependency graph:
  - [x] Character bibles depend on scene artifacts (lineage tracked).
  - [x] Downstream artifacts can depend on specific bible entries.

### Subsumption Model Strategy (Infra)
- [ ] `ModelStrategy` schema implemented and integrated into `ProjectConfig`.
- [ ] Driver supports hierarchical model resolution (Module > Recipe > Project).
- [ ] UI supports "Model Profiles" (Mock, Drafting, Production) that map to tiered slots.
- [ ] `RunState` persists `runtime_params` for full execution traceability.

### Character Bible Extraction (Resilient Pattern)
- [ ] Character extraction module implements the "Resilient Work" pattern:
  - [ ] Attempt extraction with `work` model.
  - [ ] Validate with `verify` model.
  - [ ] Automatically escalate to `escalate` model on validation failure.
... (existing character items) ...
- [x] Character extraction module reads scene artifacts and canonical script to build character master definitions.
- [x] Each character bible includes:
  - [x] **Name**: canonical character name (normalized from scene extraction).
  - [x] **Aliases**: alternative names, nicknames, V.O./O.S. variants.
  - [x] **Description**: physical description, personality, role in story.
  - [x] **Explicit evidence**: direct quotes from the script that establish traits (with source spans).
  - [x] **Inferred traits**: AI-inferred characteristics flagged with confidence and rationale.
  - [x] **Scene presence**: list of scenes where this character appears (from scene index).
  - [x] **Dialogue summary**: approximate dialogue volume, speaking patterns, key lines.
  - [x] **Narrative role**: protagonist, antagonist, supporting, minor (with confidence).
  - [x] **Relationships**: typed edges to other characters (family, social, narrative) — stub for Story 010 entity graph.
- [x] Confidence scores on all inferred fields.
- [x] AI rationale for non-obvious inferences (spec 2.6).

### Character Ranking and Filtering
- [x] Characters ranked by importance (dialogue count, scene presence, narrative role).
- [x] Primary/supporting/minor classification with evidence.
- [x] Noise filtering: pronouns, structural tokens, OCR artifacts removed before bible creation.
- [x] Derivative name detection: merged names like `ROSESWALLOWS` filtered when `ROSE` exists separately.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/world_building/character_bible_v1/`
- [x] `module.yaml`
- [x] `main.py` implementing the standard module contract.

### Schema
- [x] `BibleManifest` Pydantic schema
- [x] `CharacterBible` Pydantic schema
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for bible infrastructure
- [x] Unit tests for character extraction (mocked AI)
- [x] Integration test: full pipeline → character bible artifacts.
- [x] Schema validation: all outputs validate against Pydantic schemas.

---

## Design Notes

### Folder-Based Bibles
The spec (6.3) is explicit: bibles are folder-based, not single files. This is because a character bible may eventually contain reference images, sketches, user-injected photos, continuity state snapshots, and role decision notes — not just a JSON definition. The manifest tracks everything.

For MVP, most bible entries will only contain `master_v1.json`. The infrastructure must support the full model even if early content is simple.

### Extraction Strategy
Character extraction is a two-phase process:
1. **Aggregate from scenes**: collect all character names from scene artifacts, count appearances, identify dialogue volume.
2. **AI enrichment**: for each significant character, send relevant script excerpts to AI to extract description, traits, evidence, and relationships.

This keeps AI calls proportional to character count, not script length.

### Relationship Stubs
This story creates relationship *stubs* (basic edges with confidence). Story 010 (Entity Graph) will build the full typed relationship graph. The stubs here ensure character bibles capture obvious relationships without waiting for the graph infrastructure.

### What This Story Does NOT Include
- **Location/prop bibles** — Story 009, same infrastructure, different extraction logic.
- **Entity relationship graph** — Story 010, builds on relationship stubs from this story.
- **Continuity state tracking** — Story 011, adds per-scene state snapshots to bible folders.
- **Reference image injection** — Story 029 (User Asset Injection), but the manifest supports it now.

---

## Tasks

- [x] Design and implement `BibleManifest`, `BibleFileEntry` schemas in `src/cine_forge/schemas/`.
- [x] Design and implement `CharacterBible`, `CharacterEvidence`, `InferredTrait`, `CharacterRelationshipStub` schemas.
- [x] Register all schemas in schema registry.
- [x] Extend artifact store to support folder-based bible artifacts (save/load/list).
- [x] Create module directory: `src/cine_forge/modules/world_building/character_bible_v1/`.
- [x] Write `module.yaml` manifest.
- [x] Implement character aggregation from scene index (names, counts, scene presence).
- [x] Implement noise filtering (pronouns, structural tokens, derivative names).
- [x] Implement character ranking and classification logic.
- [x] Implement AI extraction prompt for character master definitions.
- [x] Implement evidence extraction with source span references.
- [x] Implement relationship stub extraction.
- [x] Implement `main.py`: load scenes + script → aggregate → filter → rank → AI extract → save bible folders.
- [x] Write unit tests for bible infrastructure.
- [x] Write unit tests for character extraction (mocked AI).
- [x] Write unit tests for noise filtering and ranking.
- [x] Write integration test: full pipeline → character bible artifacts.
- [x] Create recipe: `configs/recipes/recipe-world-building.yaml` (chains ingest → world building).
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

### 20260213-1130 — Implemented Bible Infrastructure and Character Bible Module
- **Result:** Success.
- **Evidence:**
  - Added `src/cine_forge/schemas/bible.py` with `BibleManifest` and `CharacterBible` schemas.
  - Extended `ArtifactStore` in `src/cine_forge/artifacts/store.py` with `save_bible_entry`, `load_bible_entry`, and `list_bible_entries`.
  - Updated `DriverEngine` in `src/cine_forge/driver/engine.py` to handle `bible_manifest` artifacts.
  - Implemented `character_bible_v1` module.
  - Added `configs/recipes/recipe-world-building.yaml`.
  - Added unit tests in `tests/unit/test_bible_infrastructure.py` and `tests/unit/test_character_bible_module.py`.
  - Added integration test in `tests/integration/test_world_building_integration.py`.
  - All tests passed, lint clean.
- **Next:** Proceed to Story 009 (Location and Prop Bibles).
