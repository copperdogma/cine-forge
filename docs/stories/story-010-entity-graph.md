# Story 010: Entity Relationship Graph

**Status**: To Do
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
- [ ] Character ↔ Character:
  - [ ] Familial: parent, sibling, spouse, child.
  - [ ] Social: friend, rival, mentor, employer, colleague.
  - [ ] Narrative: protagonist/antagonist, ally, foil, love interest.
- [ ] Character ↔ Location:
  - [ ] Home, workplace, associated location.
  - [ ] Scene presence: which characters appear at which locations, when.
- [ ] Character ↔ Prop:
  - [ ] Ownership or association.
  - [ ] Narrative significance (Chekhov's gun link).
- [ ] Location ↔ Location:
  - [ ] Spatial containment (bedroom inside house).
  - [ ] Adjacency / proximity (alley behind bar).

### Graph Structure
- [ ] Relationships stored as explicit typed edges, not buried in free text.
- [ ] Each edge includes:
  - [ ] Source entity (type + id).
  - [ ] Target entity (type + id).
  - [ ] Relationship type (from the taxonomy above).
  - [ ] Direction (symmetric vs. asymmetric).
  - [ ] Evidence: script reference or bible reference supporting the relationship.
  - [ ] Confidence score.
  - [ ] Scenes where the relationship is demonstrated.
- [ ] Graph is versioned: `entity_graph_vN` as an immutable artifact.
- [ ] When a bible entry gets a new version, affected relationship edges are flagged for update.

### Queryability
- [ ] API to query the graph:
  - [ ] "Which characters share scenes?" → co-occurrence matrix.
  - [ ] "What props appear at this location?" → location inventory.
  - [ ] "Who are character X's relationships?" → filtered edge list.
  - [ ] "What is the shortest path between entity A and entity B?" → graph traversal.
- [ ] Query results include evidence and confidence.

### Extraction Module
- [ ] Module directory: `src/cine_forge/modules/world_building/entity_graph_v1/`
- [ ] Reads character, location, and prop bibles + scene artifacts.
- [ ] AI extracts relationships not already captured in bible stubs.
- [ ] Merges bible relationship stubs with newly extracted edges.
- [ ] Deduplicates and resolves conflicting relationship claims.

### Schema
- [ ] `EntityEdge` Pydantic schema:
  ```python
  class EntityEdge(BaseModel):
      source_type: Literal["character", "location", "prop"]
      source_id: str
      target_type: Literal["character", "location", "prop"]
      target_id: str
      relationship_type: str
      direction: Literal["symmetric", "source_to_target", "target_to_source"]
      evidence: list[str]
      scene_refs: list[str]
      confidence: float
  ```
- [ ] `EntityGraph` Pydantic schema:
  ```python
  class EntityGraph(BaseModel):
      edges: list[EntityEdge]
      entity_count: dict[str, int]  # {"character": 5, "location": 8, "prop": 3}
      edge_count: int
      extraction_confidence: float
  ```
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for graph construction from bible stubs.
- [ ] Unit tests for AI edge extraction (mocked).
- [ ] Unit tests for query API (co-occurrence, filtered edges, path traversal).
- [ ] Unit tests for edge deduplication and conflict resolution.
- [ ] Integration test: bibles → entity graph module → graph artifact in store.
- [ ] Schema validation on all outputs.

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

- [ ] Design and implement `EntityEdge`, `EntityGraph` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement graph query API (co-occurrence, filtered edges, path traversal).
- [ ] Create `entity_graph_v1` module (directory, manifest, main.py).
- [ ] Implement bible stub merge + AI edge extraction.
- [ ] Implement deduplication and conflict resolution.
- [ ] Implement co-occurrence edge generation from scene artifacts.
- [ ] Update `recipe-world-building.yaml` to include entity graph stage.
- [ ] Write unit tests for graph construction and queries.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
