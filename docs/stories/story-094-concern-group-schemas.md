# Story 094: Concern Group Artifact Schemas

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003
**Spec Refs**: 12.1-12.7 (Creative Direction — Concern Groups)
**Ideal Refs**: R8 (production artifacts), R11 (production readiness), R12 (transparency)
**Depends On**: Story 002 (artifact store)

---

## Goal

Define and implement the **concern group artifact schemas** — the data model that replaces the four direction type schemas (EditorialDirection, VisualDirection, SoundDirection, PerformanceDirection) with five concern group schemas plus an Intent/Mood schema.

## Why (Ideal Alignment)

ADR-003 reorganizes creative direction from professional roles to creative concerns. The existing EditorialDirection schema (Story 020, Done) needs a migration path. The new schemas must support:
- Progressive disclosure (all fields optional, AI fills what user doesn't specify)
- Red/yellow/green readiness computation per concern group per scene
- Scope layering (project-wide defaults with per-scene and per-shot overrides)
- Prompt compilation (schemas are the source of truth from which generation prompts are compiled)

## Acceptance Criteria

- [ ] `IntentMood` schema — mood descriptors, reference films/directors, style preset ID, natural language intent
- [ ] `LookAndFeel` schema — lighting, color, composition, camera, costume, set design, visual motifs, aspect ratio
- [ ] `SoundAndMusic` schema — ambient, emotional soundscape, silence, music intent, transitions, diegetic/non-diegetic, audio motifs
- [ ] `RhythmAndFlow` schema — scene function, pacing, transitions, coverage, camera movement dynamics, montage
- [ ] `CharacterAndPerformance` schema — emotional state, arc, motivation, subtext, physical notes, blocking, delivery (contingent on Story 023 decision)
- [ ] `StoryWorld` schema — entity design baselines, continuity references, motif annotations
- [ ] All schemas registered in schema registry
- [ ] Readiness computation: given a scene and its concern group artifacts, compute red/yellow/green per group
- [ ] Migration path from existing EditorialDirection artifacts (Story 020 output)

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
