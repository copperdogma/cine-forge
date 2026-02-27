# Story 021: Look & Feel — Visual Direction

**Status**: To Do
**Created**: 2026-02-13
**Reshaped**: 2026-02-27 — ADR-003 reorganizes direction types into concern groups. Visual direction → Look & Feel concern group.
**Spec Refs**: 9.2 (Visual Architect), 12.2 (Look & Feel)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews direction), Story 008 (character bibles), Story 009 (location/prop bibles), Story 011 (continuity states)
**Ideal Refs**: R7 (iterative refinement), R11 (production readiness), R12 (transparency)

---

## Goal

Implement the **Look & Feel** concern group — everything that shapes what the audience sees. This is one of five concern groups in the ADR-003 three-layer architecture.

The Visual Architect role produces Look & Feel artifacts per scene, informed by the Intent/Mood layer (project-wide style/mood settings) and constrained by entity bibles and continuity states. Look & Feel is the visual world: lighting, color, composition, camera, costume, set design, and visual motifs.

---

## ADR-003 Context

**Before (old architecture):** Visual direction was one of four role-produced direction types (editorial, visual, sound, performance) that fed into a convergence step (Story 024) before shot planning.

**After (new architecture):** Look & Feel is one of five concern groups in the Creative Concerns layer. There is no convergence step — the Intent/Mood layer provides cross-group coherence. The Visual Architect role still produces this output, but it's organized by creative concern (what the audience sees) rather than by professional role (what the Visual Architect does).

**Key changes from the original story:**
- Spec ref 12.5 (convergence) removed — Story 024 is cancelled
- Output is a "Look & Feel" artifact, not a "Visual Direction" artifact
- The artifact is informed by project-wide Intent/Mood settings (from the Intent/Mood layer)
- Visual motifs are now annotations at any scope (character, location, world-level) — not just per-scene notes

---

## Acceptance Criteria

### Look & Feel Artifacts (per scene)
- [ ] Per-scene Look & Feel specification including:
  - [ ] **Lighting concept**: key light direction, quality (hard/soft), motivated vs. stylized, practical sources.
  - [ ] **Color palette**: dominant colors, temperature (warm/cool), saturation, contrast.
  - [ ] **Composition philosophy**: symmetry, negative space, depth of field intention, framing style.
  - [ ] **Camera personality**: static/controlled vs. handheld/chaotic, observational vs. intimate.
  - [ ] **Reference imagery**: visual references from style pack, user-injected (R17), or AI-suggested.
  - [ ] **Costume and production design notes**: what characters and environment look like, referencing bible states.
  - [ ] **Visual motifs**: recurring visual elements connecting to larger themes (may reference world-level, character-level, or scene-level motif annotations).
  - [ ] **Aspect ratio and format**: if scene-specific override of project-wide setting.
- [ ] Artifacts informed by project-wide Intent/Mood settings (style presets, mood descriptors, reference films).
- [ ] Artifacts reference continuity states from Story 011 for character/location appearance.
- [ ] All artifacts immutable, versioned, with audit metadata.
- [ ] Reviewed by Director.

### Visual Architect Role
- [ ] Role definition with system prompt embodying visual storytelling.
- [ ] Tier: structural_advisor.
- [ ] Style pack slot (accepts visual personality packs — e.g., "Roger Deakins").
- [ ] Capability: `text`, `image` (for reference image evaluation).

### Progressive Disclosure (ADR-003 Decision #2)
- [ ] AI generates Look & Feel for any scene on demand ("let AI fill this").
- [ ] User can specify any subset of fields; AI fills the rest.
- [ ] Readiness indicator: red (no specification), yellow (partial), green (fully specified and reviewed).

### Testing
- [ ] Unit tests for Look & Feel generation referencing bible states and Intent/Mood settings.
- [ ] Integration test: scenes + bibles + Intent/Mood → Look & Feel artifacts.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Global Coherence via Intent/Mood
The old architecture used a convergence step (Story 024) to ensure cross-direction consistency. The new architecture achieves this through the Intent/Mood layer — project-wide mood/style settings automatically propagate as constraints to all concern groups. Look & Feel generation should read and respect these settings.

### Bible State References
Look & Feel references continuity states, not master definitions. If a character has a black eye in scene 15 (from Story 011), the Look & Feel for that scene should note it.

---

## Tasks

_To be detailed during implementation planning. The future AI should research current codebase patterns (especially Story 020's editorial direction module) before writing implementation tasks._

---

## Work Log

*(append-only)*

20260227 — Story reshaped per ADR-003. Visual direction → Look & Feel concern group. Convergence dependency (024) removed. Intent/Mood layer replaces convergence for cross-group coherence. Visual motifs expanded to any-scope annotations.
