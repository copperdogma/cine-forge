# Story 008: Bible Infrastructure and Character Bible

**Status**: To Do
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
- [ ] Folder-based bible artifact model implemented:
  - [ ] Each entity is a directory: `{project}/artifacts/bibles/{entity_type}_{entity_id}/`
  - [ ] Directory contains a `manifest_vN.json` tracking all files, versions, and provenance.
  - [ ] Individual files within the folder are immutable; "updating" means adding new files and producing a new manifest version.
  - [ ] Manifest schema defined and registered.
- [ ] Bible manifest tracks:
  - [ ] All files in the folder with their purpose (master definition, evidence, reference image, etc.).
  - [ ] Per-file version and provenance (AI-generated, user-injected, extracted).
  - [ ] Creation timestamp and producing module/role.
- [ ] Artifact store supports folder-based artifacts:
  - [ ] `save_bible_entry()` creates/updates a bible folder with a new manifest version.
  - [ ] `load_bible_entry()` loads the current manifest and any referenced files.
  - [ ] `list_bible_entries()` lists all entities of a given type.
- [ ] Bible entries integrate with the dependency graph:
  - [ ] Character bibles depend on scene artifacts (lineage tracked).
  - [ ] Downstream artifacts can depend on specific bible entries.

### Character Bible Extraction
- [ ] Character extraction module reads scene artifacts and canonical script to build character master definitions.
- [ ] Each character bible includes:
  - [ ] **Name**: canonical character name (normalized from scene extraction).
  - [ ] **Aliases**: alternative names, nicknames, V.O./O.S. variants.
  - [ ] **Description**: physical description, personality, role in story.
  - [ ] **Explicit evidence**: direct quotes from the script that establish traits (with source spans).
  - [ ] **Inferred traits**: AI-inferred characteristics flagged with confidence and rationale.
  - [ ] **Scene presence**: list of scenes where this character appears (from scene index).
  - [ ] **Dialogue summary**: approximate dialogue volume, speaking patterns, key lines.
  - [ ] **Narrative role**: protagonist, antagonist, supporting, minor (with confidence).
  - [ ] **Relationships**: typed edges to other characters (family, social, narrative) — stub for Story 010 entity graph.
- [ ] Confidence scores on all inferred fields.
- [ ] AI rationale for non-obvious inferences (spec 2.6).

### Character Ranking and Filtering
- [ ] Characters ranked by importance (dialogue count, scene presence, narrative role).
- [ ] Primary/supporting/minor classification with evidence.
- [ ] Noise filtering: pronouns, structural tokens, OCR artifacts removed before bible creation.
- [ ] Derivative name detection: merged names like `ROSESWALLOWS` filtered when `ROSE` exists separately.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/world_building/character_bible_v1/`
- [ ] `module.yaml`:
  ```yaml
  module_id: character_bible_v1
  stage: world_building
  description: "Extracts character master definitions from scene artifacts and canonical script."
  input_schemas: ["scene_index", "canonical_script"]
  output_schemas: ["character_bible", "bible_manifest"]
  parameters:
    model:
      type: string
      required: false
      default: "gpt-4o"
    min_scene_appearances:
      type: integer
      required: false
      default: 1
      description: "Minimum scene appearances to create a bible entry."
    skip_qa:
      type: boolean
      required: false
      default: false
  ```
- [ ] `main.py` implementing the standard module contract.

### Schema
- [ ] `BibleManifest` Pydantic schema:
  ```python
  class BibleFileEntry(BaseModel):
      filename: str
      purpose: Literal["master_definition", "evidence", "reference_image",
                        "continuity_state", "role_notes", "user_injected"]
      version: int
      provenance: Literal["ai_extracted", "ai_inferred", "user_injected", "system"]
      created_at: datetime

  class BibleManifest(BaseModel):
      entity_type: Literal["character", "location", "prop"]
      entity_id: str
      display_name: str
      files: list[BibleFileEntry]
      version: int
      created_at: datetime
  ```
- [ ] `CharacterBible` Pydantic schema:
  ```python
  class CharacterEvidence(BaseModel):
      trait: str
      quote: str
      source_scene: str
      source_span: SourceSpan

  class InferredTrait(BaseModel):
      trait: str
      value: str
      confidence: float
      rationale: str

  class CharacterRelationshipStub(BaseModel):
      target_character: str
      relationship_type: str
      evidence: str
      confidence: float

  class CharacterBible(BaseModel):
      character_id: str
      name: str
      aliases: list[str]
      description: str
      explicit_evidence: list[CharacterEvidence]
      inferred_traits: list[InferredTrait]
      scene_presence: list[str]
      dialogue_summary: str
      narrative_role: Literal["protagonist", "antagonist", "supporting", "minor"]
      narrative_role_confidence: float
      relationships: list[CharacterRelationshipStub]
      overall_confidence: float
  ```
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for bible infrastructure:
  - [ ] Folder creation, manifest versioning, file immutability.
  - [ ] Manifest schema validation.
  - [ ] Artifact store integration (save/load/list bible entries).
- [ ] Unit tests for character extraction (mocked AI):
  - [ ] Characters correctly identified from scene index.
  - [ ] Evidence extraction from canonical script.
  - [ ] Noise filtering (pronouns, structural tokens, derivative names).
  - [ ] Ranking and classification (primary/supporting/minor).
- [ ] Integration test: scene artifacts + canonical script → character bible module → bible folders in artifact store with valid manifests.
- [ ] Schema validation: all outputs validate against Pydantic schemas.

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

- [ ] Design and implement `BibleManifest`, `BibleFileEntry` schemas in `src/cine_forge/schemas/`.
- [ ] Design and implement `CharacterBible`, `CharacterEvidence`, `InferredTrait`, `CharacterRelationshipStub` schemas.
- [ ] Register all schemas in schema registry.
- [ ] Extend artifact store to support folder-based bible artifacts (save/load/list).
- [ ] Create module directory: `src/cine_forge/modules/world_building/character_bible_v1/`.
- [ ] Write `module.yaml` manifest.
- [ ] Implement character aggregation from scene index (names, counts, scene presence).
- [ ] Implement noise filtering (pronouns, structural tokens, derivative names).
- [ ] Implement character ranking and classification logic.
- [ ] Implement AI extraction prompt for character master definitions.
- [ ] Implement evidence extraction with source span references.
- [ ] Implement relationship stub extraction.
- [ ] Implement `main.py`: load scenes + script → aggregate → filter → rank → AI extract → save bible folders.
- [ ] Write unit tests for bible infrastructure.
- [ ] Write unit tests for character extraction (mocked AI).
- [ ] Write unit tests for noise filtering and ranking.
- [ ] Write integration test: full pipeline → character bible artifacts.
- [ ] Create recipe: `configs/recipes/recipe-world-building.yaml` (chains ingest → world building).
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
