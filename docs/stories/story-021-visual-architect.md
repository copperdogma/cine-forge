# Story 021: Visual Architect and Visual Direction

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 9.2 (Visual Architect), 12.2 (Visual Direction), 12.5 (Direction Convergence — visual input)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews visual direction), Story 008 (character bibles), Story 009 (location/prop bibles), Story 011 (continuity states)

---

## Goal

Implement the **Visual Architect** role and its primary output: **visual direction artifacts**. The Visual Architect combines production design, costume, lighting philosophy, locations, and visual motifs — ensuring global visual cohesion across the film.

Visual direction artifacts are produced per scene and consumed by shot planning (Story 025).

---

## Acceptance Criteria

### Visual Architect Role
- [ ] Role definition with:
  - [ ] System prompt embodying visual storytelling: lighting, color, composition, camera, visual motifs.
  - [ ] Tier: structural_advisor.
  - [ ] Style pack slot (accepts visual personality packs — e.g., "Roger Deakins").
  - [ ] Capability: `text`, `image` (for reference image evaluation).

### Visual Direction Artifacts (Spec 12.2)
- [ ] Per-scene visual direction including:
  - [ ] **Lighting concept**: key light direction, quality (hard/soft), motivated vs. stylized, practical sources.
  - [ ] **Color palette**: dominant colors, temperature (warm/cool), saturation, contrast.
  - [ ] **Composition philosophy**: symmetry, negative space, depth of field intention, framing style.
  - [ ] **Camera personality**: static/controlled vs. handheld/chaotic, observational vs. intimate.
  - [ ] **Reference imagery**: visual references from style pack, user-injected, or AI-suggested.
  - [ ] **Costume and production design notes**: what characters and environment look like, referencing bible states.
  - [ ] **Visual motifs**: recurring visual elements connecting to larger themes.
- [ ] Direction references continuity states from Story 011 for character/location appearance.
- [ ] All direction artifacts are immutable, versioned, with audit metadata.
- [ ] Reviewed by Director.

### Visual Direction Module
- [ ] Module directory: `src/cine_forge/modules/creative_direction/visual_direction_v1/`
- [ ] Reads scene artifacts, character/location/prop bibles, continuity states, and project configuration.
- [ ] Invokes Visual Architect role to produce direction artifacts.
- [ ] Outputs one visual direction artifact per scene.

### Schema
- [ ] `VisualDirection` Pydantic schema with all fields from spec 12.2.
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for Visual Architect role invocation (mocked AI).
- [ ] Unit tests for visual direction generation referencing bible states.
- [ ] Integration test: scenes + bibles → visual direction module → direction artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Visual Cohesion
The Visual Architect's key responsibility is global visual cohesion. Scene-level direction must be consistent with the overall visual language. If the style pack says "muted, desaturated palette," every scene's color palette should reflect that — not just the first one.

### Bible State References
Visual direction references continuity states, not master definitions. If a character has a black eye in scene 15 (from Story 011), the visual direction for that scene should note it.

---

## Tasks

- [ ] Create Visual Architect role definition in `src/cine_forge/roles/visual_architect/`.
- [ ] Write system prompt for Visual Architect.
- [ ] Design and implement `VisualDirection` schema.
- [ ] Register schema in schema registry.
- [ ] Create `visual_direction_v1` module.
- [ ] Implement visual direction generation per scene.
- [ ] Implement bible state referencing for character/location appearance.
- [ ] Implement Director review integration.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
