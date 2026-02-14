# Story 025: Shot Planning

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 13 (Shot Planning — full section), 13.1 (Coverage Strategy), 13.2 (Individual Shot Definition), 13.3 (Coverage Patterns), 13.4 (Export Compatibility)
**Depends On**: Story 024 (direction convergence — converged direction set), Story 013 (track system — shots track), Story 012 (timeline — shot subdivision slots), Story 011 (continuity — asset state snapshots)

---

## Goal

Implement **shot planning** — where all upstream creative decisions converge into concrete, shot-by-shot instructions. Shot planning translates "what happens in this scene" into "what the audience sees and hears." The output mirrors a real-world shot list but is richer — every shot records the reasoning behind each choice and references to upstream artifacts.

---

## Acceptance Criteria

### Scene Coverage Strategy (Spec 13.1)
- [ ] One coverage strategy per scene, produced before individual shots:
  - [ ] **Coverage approach**: what types of shots are needed and why.
  - [ ] **Editorial intent**: from editorial direction (how this scene should cut together).
  - [ ] **Visual intent**: from visual direction (lighting, color, mood, composition).
  - [ ] **Sound intent**: from sound direction (ambient, silence, offscreen cues).
  - [ ] **Performance notes**: from performance direction (emotional beats, subtext).
  - [ ] **Coverage adequacy check**: does planned coverage give the editor enough angles?

### Individual Shot Definition (Spec 13.2)
- [ ] Each shot includes:
  - **Framing and Camera**:
    - [ ] Shot size (Extreme Wide through Extreme Close-Up, Insert).
    - [ ] Camera angle (Eye level, Low, High, Dutch, Bird's eye, Worm's eye).
    - [ ] Camera movement (Static, Pan, Tilt, Dolly, Crane, Steadicam, Handheld, Drone).
    - [ ] Lens / focal length (Wide 18-35mm, Normal 40-60mm, Telephoto 85mm+).
  - **Content**:
    - [ ] Scene reference and shot ID (e.g., scene 7, shot C).
    - [ ] Characters in frame (and whose POV if applicable).
    - [ ] Blocking: character positions and movement during the shot.
    - [ ] Action / description: what happens visually.
    - [ ] Dialogue: lines delivered during this shot.
    - [ ] Duration estimate.
  - **Editorial and Coverage**:
    - [ ] Coverage role (Master, Single, Two-shot, OTS, Reaction, Insert, Cutaway).
    - [ ] Edit intent: why this shot exists from an editing perspective.
  - **Continuity and References**:
    - [ ] Asset state snapshots consumed (not masters — per spec 6.4).
    - [ ] References to upstream artifacts (scene, bibles, direction artifacts).
  - **Audit**:
    - [ ] Standard CineForge metadata (intent, rationale, alternatives considered, confidence, source).

### Coverage Patterns (Spec 13.3)
- [ ] System understands standard coverage patterns:
  - [ ] Master, Singles/Close-ups, Over-the-Shoulder, Two-shot, Reaction shots, Inserts/Cutaways.
- [ ] Editorial Architect verifies planned coverage is sufficient for scene assembly.

### Export Compatibility (Spec 13.4)
- [ ] Shot plan contains all fields of an industry-standard shot list.
- [ ] Export capability: formatted shot list documents (PDF/CSV).
- [ ] Optional: overhead/blocking diagrams.

### Shot Plan Module
- [ ] Module directory: `src/cine_forge/modules/shot_planning/shot_plan_v1/`
- [ ] Reads converged direction set, scene artifacts, continuity states.
- [ ] Produces coverage strategy + individual shot definitions per scene.
- [ ] Integrates shots into timeline (Story 012) shot subdivision and places them on the shots track (Story 013).

### Schema
- [ ] `CoverageStrategy` Pydantic schema.
- [ ] `ShotDefinition` Pydantic schema with all spec 13.2 fields.
- [ ] `ShotPlan` schema (per-scene collection of shots + coverage strategy).
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for coverage strategy generation (mocked AI).
- [ ] Unit tests for individual shot definition (all field categories).
- [ ] Unit tests for coverage adequacy checking.
- [ ] Unit tests for export formatting.
- [ ] Integration test: converged direction → shot planning → shot plan artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Shot Planning Is the Culmination
This is where everything comes together. Every upstream artifact (scene extraction, bibles, continuity states, editorial/visual/sound/performance direction) feeds into shot planning. The shot plan is the most information-dense artifact in the system.

### Asset State Snapshots, Not Masters
Shots consume continuity state snapshots (Story 011), not master definitions. If a character has changed costume by scene 15, the shot plan for scene 15 references the state snapshot showing the new costume, not the master definition showing the original costume.

### Coverage as Creative Decision
Coverage patterns are not formulaic. The Editorial Architect's coverage priority drives which patterns are used. A dialogue-heavy emotional scene might get tight singles and close-ups. An action scene might get wide masters and handheld. The shot planner must respect the creative direction, not apply generic templates.

---

## Tasks

- [ ] Design and implement `CoverageStrategy`, `ShotDefinition`, `ShotPlan` schemas.
- [ ] Register schemas in schema registry.
- [ ] Create `shot_plan_v1` module.
- [ ] Implement coverage strategy generation.
- [ ] Implement individual shot definition generation.
- [ ] Implement coverage adequacy verification (Editorial Architect review).
- [ ] Implement continuity state reference linking.
- [ ] Implement shot integration into timeline.
- [ ] Implement export formatting (shot list documents).
- [ ] Create recipe: `configs/recipes/recipe-shot-planning.yaml`.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
