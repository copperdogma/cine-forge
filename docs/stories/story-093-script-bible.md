# Story 093: Script Bible Artifact

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Decisions #1/#11/#14 (story-lane always runs on import), #12 (script bible artifact)
**Spec Refs**: 4.5 (Script Bible), 4.6 (Two-Lane Architecture)
**Ideal Refs**: R1 (story understanding), R8 (production artifacts)
**Depends On**: Story 003 (story ingestion), Story 004 (script normalization)

---

## Goal

Add a **script bible** as the first artifact derived from the script, sitting between ingestion and entity extraction. The script bible captures the high-level story understanding: logline, synopsis, act structure, themes, and narrative arc. This is a story-lane artifact — cheap, always generated on import.

## Why (Ideal Alignment)

The Ideal says CineForge must understand the story completely (R1). Currently the pipeline jumps from raw script to scene extraction and entity extraction. The script bible fills the gap — it captures the macro-level story understanding that informs everything downstream. Every concern group, every role, every creative decision references "what is this story about?" The script bible is that answer.

The project IS the story (ADR-003 Decision #12). The script bible is the story's identity document.

## Acceptance Criteria

- [ ] Script bible generated automatically on script import (story-lane, always runs)
- [ ] Contains: logline, synopsis (1-3 paragraphs), act structure (acts and turning points), themes, narrative arc, genre/tone confirmation
- [ ] Stored as immutable versioned artifact
- [ ] Script revision triggers script bible re-generation with entity reconciliation (R15)
- [ ] All downstream roles and concern groups can reference the script bible
- [ ] Schema validated

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
