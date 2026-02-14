# Story 022: Sound Designer and Sound Direction

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 11 (Sound Design), 12.3 (Sound Direction), 12.5 (Direction Convergence — sound input)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews sound direction), Story 005 (scene extraction)

---

## Goal

Implement the **Sound Designer** role and its primary output: **sound direction artifacts**. Sound design begins before shot planning (spec 11.1) — it's a creative input to visual and editorial decisions, not an afterthought.

Sound direction artifacts are produced per scene and consumed by shot planning (Story 025) and the track system (Story 013).

---

## Acceptance Criteria

### Sound Designer Role
- [ ] Role definition with:
  - [ ] System prompt embodying sonic storytelling: sound-driven storytelling, silence placement, offscreen cues, audio transitions.
  - [ ] Tier: structural_advisor.
  - [ ] Style pack slot (accepts sound personality packs — e.g., "David Lynch").
  - [ ] Capability: `text`, `audio+video` (when available for audio review).

### Sound Direction Artifacts (Spec 12.3)
- [ ] Per-scene sound direction including:
  - [ ] **Ambient environment**: baseline soundscape (city noise, wind, silence, machinery hum).
  - [ ] **Emotional soundscape**: how sound supports the scene's emotional arc.
  - [ ] **Silence placement**: intentional absence of sound and where it falls.
  - [ ] **Offscreen audio cues**: sounds from outside the frame that expand the world or foreshadow.
  - [ ] **Sound-driven transitions**: audio bridges, stingers, motifs connecting to adjacent scenes.
  - [ ] **Music intent**: score direction (tension, release, theme, absence of score).
  - [ ] **Diegetic vs. non-diegetic**: what sounds exist in the story world vs. for the audience only.
- [ ] All direction artifacts immutable, versioned, with audit metadata.
- [ ] Reviewed by Director.

### Sound Direction Module
- [ ] Module directory: `src/cine_forge/modules/creative_direction/sound_direction_v1/`
- [ ] Reads scene artifacts, scene index, and project configuration.
- [ ] Invokes Sound Designer role.
- [ ] Outputs one sound direction artifact per scene.

### Sound Asset List (Spec 11.2)
- [ ] Optional: generate IRL-ready sound asset lists for real-world production workflows.
- [ ] Sound intent annotations attached to scene artifacts.

### Schema
- [ ] `SoundDirection` Pydantic schema with all fields from spec 12.3.
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for Sound Designer role invocation (mocked AI).
- [ ] Unit tests for sound direction generation.
- [ ] Integration test: scenes → sound direction module → direction artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Sound Before Shots
The spec is explicit: sound design begins before shot planning. Sound can drive visual decisions — a scene that's meant to be driven by offscreen audio cues needs different coverage than a visually driven scene. The Sound Designer's direction feeds into the Editorial Architect's coverage priority and the Visual Architect's camera personality.

### Sound Transitions
Sound transitions (bridges, stingers) are inherently cross-scene. The Sound Designer needs to see adjacent scenes to propose audio transitions, similar to how the Editorial Architect thinks about transitions.

---

## Tasks

- [ ] Create Sound Designer role definition in `src/cine_forge/roles/sound_designer/`.
- [ ] Write system prompt for Sound Designer.
- [ ] Design and implement `SoundDirection` schema.
- [ ] Register schema in schema registry.
- [ ] Create `sound_direction_v1` module.
- [ ] Implement sound direction generation per scene.
- [ ] Implement cross-scene transition analysis.
- [ ] Implement optional sound asset list generation.
- [ ] Implement Director review integration.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
