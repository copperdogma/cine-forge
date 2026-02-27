# Story 022: Sound & Music — Sound Direction

**Status**: To Do
**Created**: 2026-02-13
**Reshaped**: 2026-02-27 — ADR-003 reorganizes direction types into concern groups. Sound direction → Sound & Music concern group.
**Spec Refs**: 11 (Sound Design), 12.3 (Sound & Music)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews direction), Story 005 (scene extraction)
**Ideal Refs**: R7 (iterative refinement), R11 (production readiness), R12 (transparency)

---

## Goal

Implement the **Sound & Music** concern group — everything that shapes what the audience hears. This is one of five concern groups in the ADR-003 three-layer architecture.

The Sound Designer role produces Sound & Music artifacts per scene, informed by the Intent/Mood layer. Sound design begins before shot planning (spec 11.1) — it's a creative input to visual and editorial decisions, not an afterthought.

---

## ADR-003 Context

**Before:** Sound direction was one of four role-produced direction types feeding into convergence (Story 024).

**After:** Sound & Music is a concern group. No convergence step. The Intent/Mood layer provides cross-group coherence. The Sound Designer role still produces this, but organized by creative concern (what the audience hears).

**Key changes:**
- Convergence dependency removed (024 cancelled)
- Output is a "Sound & Music" artifact
- **Silence** is a first-class element (ADR-003 Decision #3): Sound roles must actively recommend silence as a creative tool, countering AI video gen's tendency toward constant output. This is a compromise — model limitations may prevent silence from being respected in generated video, but the artifact should specify it correctly.
- Sound & Music includes: ambient/room tone, diegetic SFX, music, Foley, silence (deliberate), mixing balance, audio motifs/leitmotifs

---

## Acceptance Criteria

### Sound & Music Artifacts (per scene)
- [ ] Per-scene Sound & Music specification including:
  - [ ] **Ambient environment**: baseline soundscape (city noise, wind, silence, machinery hum).
  - [ ] **Emotional soundscape**: how sound supports the scene's emotional arc.
  - [ ] **Silence placement**: intentional absence of sound and where it falls. The Sound Designer should actively consider and recommend silence — AI video gen defaults to constant noise.
  - [ ] **Offscreen audio cues**: sounds from outside the frame that expand the world or foreshadow.
  - [ ] **Sound-driven transitions**: audio bridges, stingers, motifs connecting to adjacent scenes.
  - [ ] **Music intent**: score direction (tension, release, theme, absence of score).
  - [ ] **Diegetic vs. non-diegetic**: what sounds exist in the story world vs. for the audience only.
  - [ ] **Audio motifs/leitmotifs**: recurring sound elements with thematic meaning (may reference world-level annotations).
- [ ] Artifacts informed by project-wide Intent/Mood settings.
- [ ] All artifacts immutable, versioned, with audit metadata.
- [ ] Reviewed by Director.

### Sound Designer Role
- [ ] Role definition with system prompt embodying sonic storytelling.
- [ ] Tier: structural_advisor.
- [ ] Style pack slot (accepts sound personality packs — e.g., "David Lynch").
- [ ] Capability: `text`, `audio+video` (when available for audio review).

### Cross-Scene Awareness
- [ ] Sound transitions (bridges, stingers) require adjacent scene context.
- [ ] Sound Designer sees adjacent scenes when proposing audio transitions.

### Progressive Disclosure (ADR-003 Decision #2)
- [ ] AI generates Sound & Music for any scene on demand.
- [ ] User can specify any subset; AI fills the rest.
- [ ] Readiness indicator: red/yellow/green.

### Sound Asset List (Spec 11.2)
- [ ] Optional: generate IRL-ready sound asset lists for real-world production workflows (R17).

### Testing
- [ ] Unit tests for Sound & Music generation.
- [ ] Integration test: scenes + Intent/Mood → Sound & Music artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Sound Before Shots
Sound design begins before shot planning. A scene driven by offscreen audio cues needs different coverage than a visually driven scene.

### Silence as Compromise (ADR-003 Decision #3)
Silence is specified correctly in artifacts. Whether video gen models respect it is a model capability compromise. Engine packs (Story 028) handle model-specific workarounds.

---

## Tasks

_To be detailed during implementation planning._

---

## Work Log

*(append-only)*

20260227 — Story reshaped per ADR-003. Sound direction → Sound & Music concern group. Convergence dependency (024) removed. Silence elevated as first-class element per ADR-003 Decision #3. Audio motifs added.
