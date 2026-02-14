# Story 015: Director and Canon Guardians

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.1 (Role Hierarchy — Director, Script Supervisor, Continuity Supervisor), 8.6 (Disagreement Protocol), 3.1 (Stage Progression — completion criteria)
**Depends On**: Story 014 (role system foundation), Story 011 (continuity tracking — data for Continuity Supervisor)

---

## Goal

Implement the three canon-level roles: **Director** (canon authority), **Script Supervisor** (canon guardian — narrative logic), and **Continuity Supervisor** (canon guardian — physical/temporal consistency). These roles gate pipeline progression and resolve creative disputes.

The Director is the most important AI role in CineForge — it oversees taste, intent, and tradeoffs. The Canon Guardians enforce consistency and can block progression until issues are addressed.

---

## Acceptance Criteria

### Director Role
- [ ] Director role definition with:
  - [ ] System prompt embodying creative leadership, taste, and tradeoff reasoning.
  - [ ] Style pack slot (accepts creative personality packs).
  - [ ] Authority to override any lower-tier role with explicit justification.
  - [ ] Authority to negotiate artifact locks (within user policy).
  - [ ] Capability: `text` minimum, `image` preferred for visual review.
- [ ] Director behaviors:
  - [ ] Reviews artifacts at completion of each pipeline stage.
  - [ ] Resolves disagreements between roles (per spec 8.6).
  - [ ] Coordinates which roles are included in creative decisions.
  - [ ] In autonomous mode, makes progression decisions. In checkpoint mode, presents decisions to user for approval.

### Script Supervisor Role
- [ ] Script Supervisor role definition with:
  - [ ] System prompt focused on narrative logic, motivation, and knowledge consistency.
  - [ ] No style pack slot (Canon Guardians don't accept style packs).
  - [ ] Authority to block progression pending narrative review.
  - [ ] Capability: `text`.
- [ ] Script Supervisor behaviors:
  - [ ] Reviews scene artifacts for narrative consistency.
  - [ ] Flags plot holes, motivation gaps, knowledge inconsistencies.
  - [ ] Reviews character bibles for internal consistency.
  - [ ] Reviews entity graph for relationship plausibility.

### Continuity Supervisor Role
- [ ] Continuity Supervisor role definition with:
  - [ ] System prompt focused on physical and temporal state consistency.
  - [ ] No style pack slot.
  - [ ] Authority to block progression pending continuity review.
  - [ ] Capability: `text`, `image` (for visual continuity checks when available).
- [ ] Continuity Supervisor behaviors:
  - [ ] Reviews continuity states (from Story 011) for consistency.
  - [ ] Flags continuity breaks (costume errors, prop inconsistencies, timeline paradoxes).
  - [ ] Reviews shot plans for visual continuity before generation.

### Stage Completion Gating
- [ ] Canon Guardians must sign off (or be overridden by Director) before a scene's artifacts at a stage are considered ready (spec 3.1).
- [ ] Sign-off produces an immutable review artifact recording the guardian's assessment.
- [ ] In checkpoint mode, user must also approve after guardian sign-off.
- [ ] Override mechanism: Director can override a guardian's block with explicit justification — both positions are recorded.

### Disagreement Protocol (Spec 8.6)
- [ ] Director-Guardian disagreement rules defined:
  - [ ] Director can override Canon Guardian blocks with explicit justification.
  - [ ] Both positions (objection + override rationale) preserved permanently and linked to affected artifacts.
  - [ ] Script Supervisor and Continuity Supervisor may both flag the same scene for different reasons (narrative vs. physical) — both are recorded independently.
- [ ] Note: The general conversation recording infrastructure and transcript retention is implemented in Story 018. This story defines the *rules* for Director/Guardian disagreements; Story 018 provides the *communication infrastructure* to record them.

### Testing
- [ ] Unit tests for Director review and progression decisions (mocked AI).
- [ ] Unit tests for Script Supervisor narrative consistency checks (mocked AI).
- [ ] Unit tests for Continuity Supervisor state consistency checks (mocked AI).
- [ ] Unit tests for stage completion gating (sign-off, override, checkpoint).
- [ ] Unit tests for disagreement protocol (objection recording, override with justification).
- [ ] Integration test: artifact review → guardian sign-off → Director approval → progression.
- [ ] Schema validation on review artifacts.

---

## Design Notes

### Director Intelligence
The Director is the hardest role to implement well. It needs to:
- Understand creative intent at a high level (what makes this scene work?).
- Balance competing concerns (the Visual Architect wants one thing, the Sound Designer wants another).
- Know when to delegate and when to decide.
- Respect the user's vision while adding creative value.

The system prompt and style pack are critical. Start simple and iterate.

### Guardian Scope
Script Supervisor looks at *story logic*: does this make sense narratively? Continuity Supervisor looks at *physical state*: do the details match? They don't overlap — a costume change can be narratively motivated (Script Supervisor approves) but visually inconsistent with the previous scene (Continuity Supervisor flags).

---

## Tasks

- [ ] Create Director role definition in `src/cine_forge/roles/director/`.
- [ ] Create Script Supervisor role definition in `src/cine_forge/roles/script_supervisor/`.
- [ ] Create Continuity Supervisor role definition in `src/cine_forge/roles/continuity_supervisor/`.
- [ ] Write system prompts for all three roles.
- [ ] Implement stage completion gating logic.
- [ ] Implement review artifact schema and generation.
- [ ] Implement disagreement protocol (objection recording, override).
- [ ] Implement Director override with dual-position preservation.
- [ ] Write unit tests for all roles and gating logic.
- [ ] Write integration test for review → sign-off → progression flow.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
