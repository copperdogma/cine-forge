# Story 012: Timeline Data Artifact

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 7.1 (Timeline Artifact), 7.3 (Always-Playable Rule), 3.1 (Stage Progression — scene/story ordering), 2.1 (Immutability)
**Depends On**: Story 005 (scene extraction — scene ordering), Story 011 (continuity tracking — story-time positions)

---

## Goal

Create the `timeline` artifact — a first-class data structure that represents the temporal organization of the film. The timeline supports scene order (edit order), story order (chronology), shot subdivision, and stacked tracks. It exists independently of final video and is the structural backbone for all downstream visualization and generation.

This story builds the data model and basic operations. Story 013 adds the track system and always-playable rule on top of this foundation.

---

## Acceptance Criteria

### Timeline Data Model
- [ ] `timeline_vN` artifact exists as an immutable, versioned artifact.
- [ ] Timeline contains:
  - [ ] **Scene order** (edit order): the sequence scenes appear in the film.
  - [ ] **Story order** (chronology): the chronological sequence of events.
  - [ ] Both orderings are explicit and independently navigable.
  - [ ] **Scene entries**: each scene has a position in both orderings, duration estimate, and references to scene artifacts.
  - [ ] **Shot subdivision**: scenes can be subdivided into shots (populated later by Story 025).
  - [ ] **Track slots**: placeholder structure for stacked tracks (populated by Story 013).
- [ ] Timeline supports reordering: creating a new timeline version with scenes in a different edit order while preserving story order.

### Timeline Operations
- [ ] Create timeline from scene index (initial construction).
- [ ] Reorder scenes (new version with different edit order).
- [ ] Add/remove scenes (new version).
- [ ] Query: "what scene is at position N in edit order?" / "what's the story-time position of scene X?"
- [ ] Duration tracking: estimated total runtime based on scene durations.

### Timeline-Scene Linkage
- [ ] Each timeline entry references a specific scene artifact version.
- [ ] Timeline depends on scene artifacts in the dependency graph.
- [ ] When a scene is updated, the timeline is marked stale.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/timeline/timeline_build_v1/`
- [ ] Reads scene index + continuity index to construct initial timeline.
- [ ] Outputs `timeline_v1` artifact.

### Schema
- [ ] `TimelineEntry` Pydantic schema:
  ```python
  class TimelineEntry(BaseModel):
      scene_id: str
      scene_ref: ArtifactRef
      edit_position: int          # Position in edit order (1-indexed)
      story_position: int         # Position in chronological order
      estimated_duration_seconds: float
      shot_count: int             # 0 until shot planning
      notes: str | None
  ```
- [ ] `Timeline` Pydantic schema:
  ```python
  class Timeline(BaseModel):
      entries: list[TimelineEntry]
      total_scenes: int
      estimated_runtime_seconds: float
      edit_order_locked: bool     # Whether edit order has been explicitly set
      story_order_locked: bool
      track_slots: list[str]      # Track names (populated by Story 013)
  ```
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for timeline construction from scene index.
- [ ] Unit tests for reordering operations (edit order changes).
- [ ] Unit tests for duration calculations.
- [ ] Unit tests for timeline-scene dependency tracking.
- [ ] Integration test: scene index → timeline module → timeline artifact.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Edit Order vs. Story Order
Most films are told in chronological order, so edit order and story order are the same. But some (Memento, Pulp Fiction, nonlinear narratives) have different orderings. The timeline must support both from day one because a style pack (e.g., Tarantino) might request nonlinear editing.

Initial timeline construction assumes edit order = story order. The user or Director can reorder to create a nonlinear edit.

### Shot Subdivision
Shots are not created in this story — they're created in Story 025 (Shot Planning). But the timeline data model must have slots for them so that shots can be placed into the timeline when they're created. For now, `shot_count` is 0 and the subdivision structure is empty.

### Always-Playable Rule (Foundation)
The always-playable rule (spec 7.3) says the timeline should be scrubbable at all times, showing the best available representation. This story builds the data model; Story 013 implements the playback logic with tracks and fallback representations.

---

## Tasks

- [ ] Design and implement `TimelineEntry`, `Timeline` schemas.
- [ ] Register schemas in schema registry.
- [ ] Create `timeline_build_v1` module (directory, manifest, main.py).
- [ ] Implement timeline construction from scene index.
- [ ] Implement reordering operations.
- [ ] Implement duration tracking.
- [ ] Wire timeline into dependency graph (scene dependencies).
- [ ] Create recipe: `configs/recipes/recipe-timeline.yaml`.
- [ ] Write unit tests for construction, reordering, queries.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
