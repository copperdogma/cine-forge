# Story 097: AI Artifact Editing

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Decision #4
**Spec Refs**: 12.8 (Prompt Compilation Model — upstream editing mechanism)
**Ideal Refs**: R4 (creative conversation), R5 (full spectrum of involvement), R12 (transparency)
**Depends On**: Story 014 (role system), Story 089 (interaction mode / autonomy settings)

---

## Goal

Give AI roles the capability to **propose and execute artifact edits** with user permission. When the user says "give the Mariner a moustache," the AI updates the character bible upstream, change propagation (R15) fires, and any downstream compiled prompts recompile with the moustache.

## Why (Ideal Alignment)

The Ideal describes conversational iteration: "No, darker." "Give John slicked-back hair." "Drop the fedora." Each of these is an instruction to change an upstream artifact. Today, the AI can suggest changes but the user must navigate to the artifact and make the edit manually. This story closes that gap — the AI becomes the editing agent.

This is also essential for the read-only prompt model. Users can't edit prompts directly; instead, they tell the AI what to change, and the AI changes the right upstream artifact. Without this capability, the read-only prompt decision creates friction.

Per-edit permission is governed by the autonomy settings from Story 089 (interaction mode selection).

## Acceptance Criteria

- [ ] AI roles can propose artifact edits (show diff/preview to user)
- [ ] User can approve, reject, or modify proposed edits
- [ ] Approved edits create new artifact versions (immutability preserved)
- [ ] Change propagation (R15) fires automatically on edit
- [ ] Autonomy levels: "ask before every edit" / "auto-edit with notification" / "auto-edit silently" (per Story 089 settings)
- [ ] Edit provenance: every AI-edited artifact records which role made the change, why, and which conversation prompted it
- [ ] Works for: character bibles, location bibles, prop bibles, concern group artifacts, script bible

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
