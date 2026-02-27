# Story 096: "Chat About This" Interaction Pattern

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Decision #4
**Spec Refs**: 12.8 (Prompt Compilation Model — "Chat about this" affordance)
**Ideal Refs**: R4 (creative conversation), R7 (iterative refinement), R12 (transparency)
**Depends On**: Story 011f (conversational AI chat), Story 082 (creative direction UX)

---

## Goal

Implement the **"Chat about this"** interaction pattern: user highlights any part of any artifact (bible entry, concern group field, compiled prompt, generated output) → drops it into chat with the appropriate AI role pre-tagged. This is the bridge between viewing artifacts and conversing about them.

## Why (Ideal Alignment)

The Ideal says interaction should feel like collaborating with creative people, not operating software. When a user reads a compiled prompt and thinks "that lighting description isn't right," the natural next step is to discuss it — not to navigate to a form and change a field. "Chat about this" makes every artifact a conversation starter.

This also supports the read-only prompt model (Decision #4). Users can't edit prompts directly, but they can instantly discuss any part of one and ask the AI to change the upstream artifact.

## Acceptance Criteria

- [ ] Any selectable text in any artifact view can be highlighted
- [ ] Highlight shows a "Chat about this" affordance (button, tooltip, or context menu)
- [ ] Clicking drops the selected text into the chat panel as a quoted reference
- [ ] The appropriate AI role is pre-tagged based on context (e.g., Look & Feel text → @visual_architect)
- [ ] User can change the pre-tagged role before sending
- [ ] Works on: bible entries, concern group artifacts, compiled prompts, generated output metadata

---

## Design Notes

Story 082 already implemented a basic version of this for editorial direction annotations ("Chat about this" button on DirectionAnnotation component, dispatches `cineforge:ask` event). This story generalizes it to all artifact types.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation. Extends the pattern established in Story 082's DirectionAnnotation component.
