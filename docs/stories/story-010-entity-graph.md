# Story 010: Entity Relationship Graph

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 6.2 (Entity Graph — full relationship model), 2.1 (Immutability), 2.6 (Explanation Mandatory)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 005 (scene extraction — co-occurrence data)

---

## Goal

Build a queryable graph of typed relationships between all entities (characters, locations, props). The entity graph is extracted from script content and bible entries, stored as explicit typed edges, and versioned alongside the bibles it connects.

The graph powers continuity checking (Story 011), narrative consistency, and shot planning (which assets must be present in frame). It replaces the relationship stubs created in Stories 008–009 with a proper graph structure.

---

## Acceptance Criteria

### Relationship Types (Spec 6.2)
- [x] Character ↔ Character:
  - [x] Familial: parent, sibling, spouse, child.
  - [x] Social: friend, rival, mentor, employer, colleague.
  - [x] Narrative: protagonist/antagonist, ally, foil, love interest.
- [x] Character ↔ Location:
  - [x] Home, workplace, associated location.
  - [x] Scene presence: which characters appear at which locations, when.
- [x] Character ↔ Prop:
  - [x] Ownership or association.
  - [x] Narrative significance (Chekhov's gun link).
- [x] Location ↔ Location:
  - [x] Spatial containment (bedroom inside house).
  - [x] Adjacency / proximity (alley behind bar).

### Graph Structure
- [x] Relationships stored as explicit typed edges, not buried in free text.
- [x] Each edge includes:
  - [x] Source entity (type + id).
  - [x] Target entity (type + id).
  - [x] Relationship type (from the taxonomy above).
  - [x] Direction (symmetric vs. asymmetric).
  - [x] Evidence: script reference or bible reference supporting the relationship.
  - [x] Confidence score.
  - [x] Scenes where the relationship is demonstrated.
- [x] Graph is versioned: `entity_graph_vN` as an immutable artifact.
- [x] When a bible entry gets a new version, affected relationship edges are flagged for update.

### Queryability
- [x] API to query the graph:
  - [x] "Which characters share scenes?" → co-occurrence matrix.
  - [x] "What props appear at this location?" → location inventory.
  - [x] "Who are character X's relationships?" → filtered edge list.
- [x] Query results include evidence and confidence.

### Extraction Module
- [x] Module directory: `src/cine_forge/modules/world_building/entity_graph_v1/`
- [x] Reads character, location, and prop bibles + scene artifacts.
- [x] AI extracts relationships not already captured in bible stubs.
- [x] Merges bible relationship stubs with newly extracted edges.
- [x] Deduplicates and resolves conflicting relationship claims.

### Schema
- [x] `EntityEdge` Pydantic schema.
- [x] `EntityGraph` Pydantic schema.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for graph construction from bible stubs.
- [x] Unit tests for AI edge extraction (mocked).
- [x] Unit tests for edge deduplication and conflict resolution.
- [x] Integration test: bibles → entity graph module → graph artifact in store.
- [x] Schema validation on all outputs.

---

## Design Notes

### Graph Storage
For MVP, the entity graph is a single JSON artifact. If graphs become large (many entities, many edges), consider a more efficient representation. The query API should abstract over storage so the format can evolve.

### Co-occurrence vs. Relationships
Scene co-occurrence (characters appearing in the same scene) is deterministic data from scene artifacts. Relationships (family, social, narrative) require AI interpretation. The graph contains both — co-occurrence edges are high-confidence, relationship edges have variable confidence.

### Incremental Updates
When a bible entry is updated (new version), the entity graph should be updatable incrementally — only re-extract edges involving the changed entity. For MVP, full re-extraction is acceptable, but the data model should support incremental updates.

---

## Tasks

- [x] Design and implement `EntityEdge`, `EntityGraph` schemas.
- [x] Register schemas in schema registry.
- [x] Implement graph query API (co-occurrence, filtered edges, path traversal).
- [x] Create `entity_graph_v1` module (directory, manifest, main.py).
- [x] Implement bible stub merge + AI edge extraction.
- [x] Implement deduplication and conflict resolution.
- [x] Implement co-occurrence edge generation from scene artifacts.
- [x] Update `recipe-world-building.yaml` to include entity graph stage.
- [x] Write unit tests for graph construction and queries.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

### 20260214-2350 — Implemented Entity Relationship Graph and needs_all
- **Result:** Success.
- **Evidence:**
  - Added `EntityEdge` and `EntityGraph` schemas.
  - Extended `RecipeStage` and `DriverEngine` with `needs_all` support.
  - Implemented `entity_graph_v1` module with bible stub merging and co-occurrence generation.
  - Updated bible modules to output dual artifacts (data + manifest).
  - Verified with 124 unit tests and updated world-building integration test.
- **Next Step:** Proceed to Story 011 (Continuity Tracking).
