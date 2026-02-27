# Story 100: Motif Tracking System

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Decision #3
**Spec Refs**: 12.6 (Story World — motif tracking)
**Ideal Refs**: R3 (continuity), R8 (production artifacts)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 011 (continuity), Story 094 (concern group schemas — motifs feed into Look & Feel and Sound & Music)

---

## Goal

Implement **motif tracking** — annotations at any scope (character, location, prop, scene, world-level) that record recurring visual or audio elements with thematic meaning. Motifs are inputs to concern group generation, ensuring thematic coherence across scenes.

## Why (Ideal Alignment)

Visual and audio motifs are among the three most commonly neglected elements in AI generation (ADR-003 research). Global style/mood creates consistency, but not motifs. A motif is a specific recurring element with thematic meaning: "every time John makes a choice, there's a mirror in frame" or "every time we see the sky, there's an alien ship looming." These need explicit tracking because they're intentional creative choices that AI won't spontaneously maintain.

Motifs are part of the Story World concern group (§12.6) — the persistent world that must remain coherent across the project.

## Acceptance Criteria

- [ ] Motif annotations can be attached to: characters, locations, props, scenes, or the project/world level
- [ ] Each motif has: description, type (visual/audio), scope, thematic meaning
- [ ] Motifs are inputs to Look & Feel and Sound & Music concern group generation
- [ ] AI scene planning receives motif annotations as context and follows them
- [ ] Users can create motifs manually or accept AI-suggested motifs
- [ ] Motif dashboard: view all motifs across the project, see which scenes use each

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation. Motifs elevated from "just consistency" to explicit thematic tracking per ADR-003 Discussion #3.
