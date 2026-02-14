# Story 020: Editorial Architect and Editorial Direction

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 9.1 (Editorial Architect), 12.1 (Editorial Direction), 12.5 (Direction Convergence — editorial input)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews editorial direction), Story 005 (scene extraction)

---

## Goal

Implement the **Editorial Architect** role and its primary output: **editorial direction artifacts**. The Editorial Architect combines the traditional roles of editor and transitions designer — responsible for cut-ability prediction, coverage adequacy, pacing, and transition suggestions.

Editorial direction artifacts are produced per scene (or per act) and consumed by shot planning (Story 025).

---

## Acceptance Criteria

### Editorial Architect Role
- [ ] Role definition with:
  - [ ] System prompt embodying editorial thinking: rhythm, pacing, coverage, transitions.
  - [ ] Tier: structural_advisor.
  - [ ] Style pack slot (accepts editorial personality packs).
  - [ ] Capability: `text`.
- [ ] Role behaviors:
  - [ ] Analyzes scenes for editorial structure.
  - [ ] Proposes transition strategies between scenes.
  - [ ] Evaluates coverage requirements.
  - [ ] Identifies montage and parallel editing candidates.

### Editorial Direction Artifacts (Spec 12.1)
- [ ] Per-scene editorial direction including:
  - [ ] **Scene function**: role in the narrative arc (inciting incident, escalation, climax, resolution, transition).
  - [ ] **Pacing intent**: fast/slow, building/releasing tension, breathing room.
  - [ ] **Transition strategy**: how to enter and exit the scene (hard cut, dissolve, match cut, sound bridge, smash cut) and why.
  - [ ] **Coverage priority**: what the editor will need (e.g., "prioritize close-ups for emotional beats").
  - [ ] **Montage/parallel editing candidates**: if applicable.
- [ ] Per-act editorial direction (when scoped to an act):
  - [ ] Pacing arc across scenes.
  - [ ] Turning points.
  - [ ] Rhythm across scenes.
- [ ] All direction artifacts are immutable, versioned, and carry standard audit metadata.
- [ ] Reviewed by Director and Script Supervisor.

### Editorial Direction Module
- [ ] Module directory: `src/cine_forge/modules/creative_direction/editorial_direction_v1/`
- [ ] Reads scene artifacts, scene index, and project configuration.
- [ ] Invokes Editorial Architect role to produce direction artifacts.
- [ ] Outputs one editorial direction artifact per scene.

### Schema
- [ ] `EditorialDirection` Pydantic schema:
  ```python
  class EditorialDirection(BaseModel):
      scene_id: str
      scene_function: str
      pacing_intent: str
      transition_in: str
      transition_in_rationale: str
      transition_out: str
      transition_out_rationale: str
      coverage_priority: str
      montage_candidates: list[str] | None
      parallel_editing_notes: str | None
      act_level_notes: str | None
      confidence: float
  ```
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for Editorial Architect role invocation (mocked AI).
- [ ] Unit tests for editorial direction generation per scene.
- [ ] Unit tests for act-level direction generation.
- [ ] Integration test: scenes → editorial direction module → direction artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Editorial Thinking
The Editorial Architect thinks backwards from the edit: "how will this scene cut together?" This means it considers adjacent scenes (what comes before and after), not just the scene in isolation. The transition strategy for scene 5 depends on how scene 4 ends and how scene 6 begins.

### Coverage as a Pre-Requirement for Shot Planning
Coverage priority from editorial direction directly informs shot planning. If the editor says "I need close-ups for the emotional beats and a wide master for safety," the shot planner knows what types of shots to include. This is the primary data flow from editorial to shot planning.

---

## Tasks

- [ ] Create Editorial Architect role definition in `src/cine_forge/roles/editorial_architect/`.
- [ ] Write system prompt for Editorial Architect.
- [ ] Design and implement `EditorialDirection` schema.
- [ ] Register schema in schema registry.
- [ ] Create `editorial_direction_v1` module (directory, manifest, main.py).
- [ ] Implement editorial direction generation per scene.
- [ ] Implement act-level direction aggregation.
- [ ] Implement Director/Script Supervisor review integration.
- [ ] Create recipe: `configs/recipes/recipe-creative-direction.yaml`.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
