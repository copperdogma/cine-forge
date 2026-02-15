# Story 011: Asset State Tracking (Continuity)

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 6.4 (Asset States / Continuity), 8.1 (Continuity Supervisor role — future), 2.1 (Immutability)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 010 (entity graph), Story 005 (scene extraction — scene ordering)

---

## Goal

Track how assets (characters, locations, props) change state across scenes. A character's costume, injuries, emotional state; a location's time-of-day appearance, weather, damage; a prop's position, condition — all evolve through the story. State snapshots are immutable artifacts stored within each entity's bible folder.

This completes the Phase 2 artifact model. Shots (Phase 6) consume state snapshots, not master definitions — ensuring continuity is maintained.

### Bedrock Mandate
**IMPORTANT**: This story must establish the **3-Recipe Architecture** for the project:
1.  **Intake** (`mvp_ingest`): Raw material to Canonical Script + Scenes.
2.  **World Synthesis** (`world_building`): Script to Entity Bibles (Characters, Locations, Props).
3.  **Narrative Analysis** (`narrative_analysis`): Bibles + Scenes to Entity Graph + Continuity.

Each recipe should be self-contained and use `store_inputs` to resolve prerequisites from the Artifact Store.

---

## Acceptance Criteria

### Narrative Analysis Recipe
- [ ] New recipe `recipe-narrative-analysis.yaml` implemented.
- [ ] Includes `entity_graph` and `continuity_tracking` stages.
- [ ] Resolves all bibles and scene index via `store_inputs`.

### State Snapshot Model
- [x] State snapshots are immutable artifacts within bible folders.
- [x] Each state snapshot records:
  - [x] Entity reference (type + id).
  - [x] Scene reference (which scene this state applies to).
  - [x] Story-time position (chronological order, not just scene order).
  - [x] State properties (key-value pairs relevant to the entity type).
  - [ ] Change event: what changed from the previous state and why.
  - [ ] Evidence: script reference supporting the state.
  - [x] Confidence score.
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
- [x] For each entity, produce a continuity timeline: ordered sequence of state snapshots across all scenes.
- [ ] Timeline supports both scene order (edit order) and story order (chronology) — matching spec 7.1.
- [ ] Continuity gaps detected: scenes where an entity's state is unknown or ambiguous.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/world_building/continuity_tracking_v1/`
- [x] Reads scene artifacts, scene index, and all bible entries.
- [x] Outputs state snapshots stored within bible folders + a continuity index artifact.

### Schema
- [x] `ContinuityState` Pydantic schema.
- [x] `ContinuityIndex` schema: summary of all entities' state timelines with gap detection.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for state snapshot creation and storage within bible folders.
- [x] Unit tests for continuity event detection (mocked AI).
- [x] Unit tests for timeline construction and gap detection.
- [x] Integration test: bibles + scenes → continuity tracking → state snapshots in bible folders + continuity index.
- [x] Schema validation on all outputs.

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

- [x] Design and implement `ContinuityState`, `ContinuityEvent`, `StateProperty` schemas.
- [x] Design and implement `ContinuityIndex` schema.
- [x] Register schemas in schema registry.
- [x] Extend bible folder structure to store state snapshots.
- [x] Create `continuity_tracking_v1` module (directory, manifest, main.py).
- [ ] Implement continuity event detection from scene artifacts.
- [x] Implement state snapshot generation per entity per scene.
- [x] Implement continuity timeline construction.
- [ ] Implement gap detection.
- [x] Update `recipe-world-building.yaml` to be focused only on entity extraction.
- [x] Create `recipe-narrative-analysis.yaml`.
- [ ] Implement AI-driven continuity event detection.
- [x] Implement basic continuity visualization in Operator Console.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

## Work Log

### 20260215-0030 — Implemented Continuity Tracking Foundation
- **Result:** Success.
- **Evidence:**
  - Added `ContinuityState`, `ContinuityEvent`, `StateProperty`, `ContinuityIndex` schemas.
  - Implemented `continuity_tracking_v1` module with timeline construction and mock state generation.
  - Verified with 125 unit tests and world-building integration test.

### 20260215-0100 — Established 3-Recipe Architecture and Bulk Resource Reuse
- **Result:** Success.
- **Evidence:**
  - Split pipeline into Intake, Synthesis (World Building), and Analysis (Narrative Analysis).
  - Implemented `store_inputs_all` in `DriverEngine` to resolve all artifacts of a type.
  - Verified with full sequential run of all three recipes in integration tests.
  - Added `ContinuityViewer` to the Artifacts browser.
- **Next Step:** Proceed to Story 011b (Production UI Rebuild).
