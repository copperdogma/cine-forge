# Story 024: Direction Convergence and Review

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 12.5 (Direction Convergence), 8.6 (Disagreement Protocol), 8.1 (Director — review authority)
**Depends On**: Story 020 (editorial direction), Story 021 (visual direction), Story 022 (sound direction), Story 023 (performance direction), Story 015 (Director)

---

## Goal

Before shot planning begins for a scene, all four direction artifacts (editorial, visual, sound, performance) must exist and be internally consistent. The **Director** reviews the set for alignment, resolves conflicts, and produces a converged direction set that becomes the input to shot planning.

---

## Acceptance Criteria

### Convergence Review
- [ ] All four direction types must exist for a scene before convergence review.
- [ ] Director reviews the direction set for internal consistency:
  - [ ] Does the editorial intent align with the visual approach?
  - [ ] Does the sound design support or conflict with the pacing plan?
  - [ ] Do the performance notes fit the visual framing?
  - [ ] Are there timing conflicts between editorial pacing and sound transitions?
- [ ] Conflicts identified and flagged with:
  - [ ] Which direction artifacts conflict.
  - [ ] Nature of the conflict.
  - [ ] Director's recommended resolution.

### Conflict Resolution
- [ ] Conflicts resolved through the standard disagreement protocol (spec 8.6, Story 018).
- [ ] Resolved conflicts produce updated direction artifacts (new versions).
- [ ] Resolution decisions recorded as decision artifacts (Story 017).
- [ ] Unresolved conflicts escalated to human in checkpoint/advisory modes.

### Converged Direction Set
- [ ] The converged direction set is a single artifact referencing:
  - [ ] The specific versions of all four direction artifacts that are internally consistent.
  - [ ] Any conflict resolutions applied.
  - [ ] Director's overall creative notes for the scene.
  - [ ] Readiness status: ready for shot planning or needs further work.
- [ ] The converged set is what shot planning (Story 025) consumes.

### Convergence Module
- [ ] Module directory: `src/cine_forge/modules/creative_direction/direction_convergence_v1/`
- [ ] Reads all four direction artifact types for a scene.
- [ ] Invokes Director role for review.
- [ ] Outputs converged direction set artifact.

### Schema
- [ ] `ConvergedDirection` Pydantic schema:
  ```python
  class DirectionConflict(BaseModel):
      direction_a_type: str
      direction_b_type: str
      conflict_description: str
      resolution: str
      resolution_rationale: str

  class ConvergedDirection(BaseModel):
      scene_id: str
      editorial_ref: ArtifactRef
      visual_ref: ArtifactRef
      sound_ref: ArtifactRef
      performance_refs: list[ArtifactRef]  # One per character
      conflicts_found: list[DirectionConflict]
      director_notes: str
      readiness: Literal["ready", "needs_revision"]
      confidence: float
  ```
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for convergence review logic (mocked AI Director).
- [ ] Unit tests for conflict detection across direction types.
- [ ] Unit tests for conflict resolution flow.
- [ ] Integration test: four direction artifacts → convergence module → converged set.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Why Convergence Matters
Without convergence review, the four creative directions might pull in different directions — the Sound Designer wants silence, the Editorial Architect wants a fast-cutting montage, the Visual Architect wants a static long take, and the Actor Agent wants explosive energy. The Director must reconcile these into a coherent creative vision before shot planning begins.

### Iterative Convergence
Convergence may require multiple rounds. The Director might ask the Visual Architect to adjust lighting to match the Sound Designer's mood, then re-review. The module should support iterative convergence with a configurable max iteration count.

---

## Tasks

- [ ] Design and implement `ConvergedDirection`, `DirectionConflict` schemas.
- [ ] Register schemas in schema registry.
- [ ] Create `direction_convergence_v1` module.
- [ ] Implement convergence review logic (Director invocation).
- [ ] Implement conflict detection across direction types.
- [ ] Implement iterative convergence with conflict resolution.
- [ ] Implement readiness assessment.
- [ ] Update creative direction recipe to include convergence stage.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
