# Story 095: Intent / Mood Layer

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Synthesis §6 (Final Recommendation)
**Spec Refs**: 12.1 (Intent / Mood Layer)
**Ideal Refs**: R5 (full spectrum of involvement), R7 (iterative refinement), R11 (production readiness)
**Depends On**: Story 094 (concern group schemas), Story 014 (role system)

---

## Goal

Implement the **Intent / Mood layer** — the primary interaction surface where users describe what they want through emotion, references, and style presets. Changes in this layer auto-propagate suggested defaults to all five concern groups.

## Why (Ideal Alignment)

The Ideal says CineForge should feel like a creative conversation, not operating a pipeline. The Intent/Mood layer is how users enter that conversation. Non-filmmakers describe intent through emotion first ("tense," "dreamy"), references second ("like Blade Runner"), and sensory terms third ("dark," "grainy"). This layer speaks their language.

It also replaces the eliminated convergence step (Story 024). Cross-group coherence comes from the mood layer propagating consistent intent across all concern groups — not from a Director reviewing four separate artifacts.

Templates beat parameters (ADR-003 research finding). Style presets / "vibe" packages are the primary interaction pattern.

## Acceptance Criteria

- [ ] Mood/tone selector: emotional descriptors that propagate to concern group defaults
- [ ] Reference input: films, directors, aesthetic subcultures accepted as style references
- [ ] Style presets / "vibe" packages: named starting points that set coherent defaults across all five concern groups
- [ ] Natural language input: "make this scene darker and tenser" parsed and routed to appropriate concern groups
- [ ] Auto-propagation: changing mood shows proposed adjustments in each concern group
- [ ] Per-scene overrides of project-wide intent
- [ ] Works as the ONLY layer a user needs to touch for the 90/10 case

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
