# Story 011: Asset State Tracking (Continuity)

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 6.4 (Asset States / Continuity), 8.1 (Continuity Supervisor role — future), 2.1 (Immutability)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 010 (entity graph), Story 005 (scene extraction — scene ordering)

---

## Goal

Track how assets (characters, locations, props) change state across scenes. A character's costume, injuries, emotional state; a location's time-of-day appearance, weather, damage; a prop's position, condition — all evolve through the story. State snapshots are immutable artifacts stored within each entity's bible folder.

This completes the Phase 2 artifact model. Shots (Phase 6) consume state snapshots, not master definitions — ensuring continuity is maintained.

---

## Acceptance Criteria

### State Snapshot Model
- [ ] State snapshots are immutable artifacts within bible folders.
- [ ] Each state snapshot records:
  - [ ] Entity reference (type + id).
  - [ ] Scene reference (which scene this state applies to).
  - [ ] Story-time position (chronological order, not just scene order).
  - [ ] State properties (key-value pairs relevant to the entity type).
  - [ ] Change event: what changed from the previous state and why.
  - [ ] Evidence: script reference supporting the state.
  - [ ] Confidence score.
- [ ] State changes occur via explicit continuity events, not implicit inference.

### Entity-Type State Properties

**Character states** (examples):
- Costume / wardrobe.
- Physical condition (injuries, aging, appearance changes).
- Emotional state entering the scene.
- Props carried / possessions.
- Location.

**Location states** (examples):
- Time of day / lighting.
- Weather.
- Damage / destruction / modification.
- Occupants present.

**Prop states** (examples):
- Position / location.
- Condition (intact, damaged, destroyed).
- Ownership / who possesses it.

### Continuity Event Detection
- [ ] Extraction module reads scene artifacts and bibles to detect continuity events.
- [ ] Events detected:
  - [ ] Costume changes (explicit or inferred from scene context).
  - [ ] Injuries / physical changes.
  - [ ] Location transitions.
  - [ ] Prop state changes (picked up, broken, given away).
  - [ ] Time-of-day changes affecting appearance.
- [ ] Each event is flagged as explicit (stated in script) or inferred (with confidence).

### Continuity Timeline
- [ ] For each entity, produce a continuity timeline: ordered sequence of state snapshots across all scenes.
- [ ] Timeline supports both scene order (edit order) and story order (chronology) — matching spec 7.1.
- [ ] Continuity gaps detected: scenes where an entity's state is unknown or ambiguous.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/world_building/continuity_tracking_v1/`
- [ ] Reads scene artifacts, scene index, and all bible entries.
- [ ] Outputs state snapshots stored within bible folders + a continuity index artifact.

### Schema
- [ ] `ContinuityState` Pydantic schema:
  ```python
  class StateProperty(BaseModel):
      key: str
      value: str
      confidence: float

  class ContinuityEvent(BaseModel):
      property_key: str
      previous_value: str | None
      new_value: str
      reason: str
      evidence: str
      is_explicit: bool
      confidence: float

  class ContinuityState(BaseModel):
      entity_type: Literal["character", "location", "prop"]
      entity_id: str
      scene_id: str
      story_time_position: int
      properties: list[StateProperty]
      change_events: list[ContinuityEvent]
      overall_confidence: float
  ```
- [ ] `ContinuityIndex` schema: summary of all entities' state timelines with gap detection.
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for state snapshot creation and storage within bible folders.
- [ ] Unit tests for continuity event detection (mocked AI).
- [ ] Unit tests for timeline construction and gap detection.
- [ ] Integration test: bibles + scenes → continuity tracking → state snapshots in bible folders + continuity index.
- [ ] Schema validation on all outputs.

---

## Design Notes

### State vs. Master
The master definition (from Story 008/009) describes what an entity *is*. The state snapshot describes what an entity *is at this moment in the story*. A character's master says they have brown hair; their state in scene 15 says they have a black eye and are wearing a red dress.

Shots consume state snapshots, not masters. This is the key architectural decision from spec 6.4.

### Story Time vs. Scene Order
A film's edit order may differ from chronological story time. The continuity tracking must support both orderings so that:
- Edit-order continuity catches visual mismatches (if scene 5 is cut next to scene 12, do costumes match?).
- Story-order continuity catches narrative logic (the character can't have the knife in scene 3 if they dropped it in scene 2).

### Continuity Supervisor (Future)
Story 011 builds the data model. The Continuity Supervisor *role* (Story 015) will use this data to flag breaks and enforce consistency. This story just extracts and stores states — it doesn't enforce rules.

---

## Tasks

- [ ] Design and implement `ContinuityState`, `ContinuityEvent`, `StateProperty` schemas.
- [ ] Design and implement `ContinuityIndex` schema.
- [ ] Register schemas in schema registry.
- [ ] Extend bible folder structure to store state snapshots.
- [ ] Create `continuity_tracking_v1` module (directory, manifest, main.py).
- [ ] Implement continuity event detection from scene artifacts.
- [ ] Implement state snapshot generation per entity per scene.
- [ ] Implement continuity timeline construction.
- [ ] Implement gap detection.
- [ ] Update `recipe-world-building.yaml` to include continuity stage.
- [ ] Write unit tests for state snapshots, events, and timelines.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
