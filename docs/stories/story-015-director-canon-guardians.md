# Story 015: Director and Canon Guardians

**Status**: Done
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
- [x] Director role definition with:
  - [x] System prompt embodying creative leadership, taste, and tradeoff reasoning.
  - [x] Style pack slot (accepts creative personality packs).
  - [x] Authority to override any lower-tier role with explicit justification.
  - [x] Authority to negotiate artifact locks (within user policy).
  - [x] Capability: `text` minimum, `image` preferred for visual review.
- [x] Director behaviors:
  - [x] Reviews artifacts at completion of each pipeline stage.
  - [x] Resolves disagreements between roles (per spec 8.6).
  - [x] Coordinates which roles are included in creative decisions.
  - [x] In autonomous mode, makes progression decisions. In checkpoint mode, presents decisions to user for approval.

### Script Supervisor Role
- [x] Script Supervisor role definition with:
  - [x] System prompt focused on narrative logic, motivation, and knowledge consistency.
  - [x] No style pack slot (Canon Guardians don't accept style packs).
  - [x] Authority to block progression pending narrative review.
  - [x] Capability: `text`.
- [x] Script Supervisor behaviors:
  - [x] Reviews scene artifacts for narrative consistency.
  - [x] Flags plot holes, motivation gaps, knowledge inconsistencies.
  - [x] Reviews character bibles for internal consistency.
  - [x] Reviews entity graph for relationship plausibility.

### Continuity Supervisor Role
- [x] Continuity Supervisor role definition with:
  - [x] System prompt focused on physical and temporal state consistency.
  - [x] No style pack slot.
  - [x] Authority to block progression pending continuity review.
  - [x] Capability: `text`, `image` (for visual continuity checks when available).
- [x] Continuity Supervisor behaviors:
  - [x] Reviews continuity states (from Story 011) for consistency.
  - [x] Flags continuity breaks (costume errors, prop inconsistencies, timeline paradoxes).
  - [x] Reviews shot plans for visual continuity before generation.

### Stage Completion Gating
- [x] Canon Guardians must sign off (or be overridden by Director) before a scene's artifacts at a stage are considered ready (spec 3.1).
- [x] Sign-off produces an immutable review artifact recording the guardian's assessment.
- [x] In checkpoint mode, user must also approve after guardian sign-off.
- [x] Override mechanism: Director can override a guardian's block with explicit justification — both positions are recorded.

### Disagreement Protocol (Spec 8.6)
- [x] Director-Guardian disagreement rules defined:
  - [x] Director can override Canon Guardian blocks with explicit justification.
  - [x] Both positions (objection + override rationale) preserved permanently and linked to affected artifacts.
  - [x] Script Supervisor and Continuity Supervisor may both flag the same scene for different reasons (narrative vs. physical) — both are recorded independently.
- [x] Note: The general conversation recording infrastructure and transcript retention is implemented in Story 018. This story defines the *rules* for Director/Guardian disagreements; Story 018 provides the *communication infrastructure* to record them.

### Testing
- [x] Unit tests for Director review and progression decisions (mocked AI).
- [x] Unit tests for Script Supervisor narrative consistency checks (mocked AI).
- [x] Unit tests for Continuity Supervisor state consistency checks (mocked AI).
- [x] Unit tests for stage completion gating (sign-off, override, checkpoint).
- [x] Unit tests for disagreement protocol (objection recording, override with justification).
- [x] Integration test: artifact review → guardian sign-off → Director approval → progression.
- [x] Schema validation on review artifacts.

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

- [x] Create Director role definition in `src/cine_forge/roles/director/`.
- [x] Create Script Supervisor role definition in `src/cine_forge/roles/script_supervisor/`.
- [x] Create Continuity Supervisor role definition in `src/cine_forge/roles/continuity_supervisor/`.
- [x] Write system prompts for all three roles.
- [x] Implement stage completion gating logic.
- [x] Implement review artifact schema and generation.
- [x] Implement disagreement protocol (objection recording, override).
- [x] Implement Director override with dual-position preservation.
- [x] Write unit tests for all roles and gating logic.
- [x] Write integration test for review → sign-off → progression flow.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Central Tenets Check

- [x] **Tenet 0 — Preserve user data / capture-first**: Stage reviews are immutable artifacts (`stage_review`) with lineage links to reviewed artifacts; overrides and objections are append-only.
- [x] **Tenet 1 — AI-friendly architecture**: Canon gating is explicit (`CanonGate`) with typed schemas and test fixtures that preserve execution context and decision rationale.
- [x] **Tenet 2 — Avoid over-engineering**: Implemented a focused canon-gating workflow for Director + guardians only; deferred generalized transcript infrastructure to Story 018 as scoped.
- [x] **Tenet 3 — Keep files manageable / types centralized**: Added role/canon review types in `src/cine_forge/schemas/role.py`; isolated orchestration logic in `src/cine_forge/roles/canon.py`.
- [x] **Tenet 4 — Verbose handoff log**: Work log entries include decisions, evidence paths, and verification outputs.
- [x] **Tenet 5 — Simplify toward ideal**: Reused existing `RoleContext` + `ArtifactStore` instead of creating a parallel persistence/runtime stack.

---

## Work Log

*(append-only)*

20260220-0938 — scope + baseline audit: confirmed Story 015 status/sections are actionable and audited Story 014 runtime constraints plus spec refs 3.1/8.6; found existing role YAML stubs but no canon-stage readiness gate, no immutable review artifact schema, and no dual-position disagreement persistence; evidence=`docs/stories/story-015-director-canon-guardians.md`, `docs/spec.md`, `src/cine_forge/roles/runtime.py`, `src/cine_forge/roles/*/role.yaml`; next=implement canon gate + schema + tests.

20260220-0957 — canon review model and runtime implemented: expanded role schemas with review artifacts and disagreement records (`ReviewDecision`, `GuardianReview`, `DirectorReview`, `DisagreementRecord`, `StageReviewArtifact`) and added `CanonGate` orchestration that invokes both guardians + Director, enforces explicit override justification, computes readiness by control mode (autonomous/checkpoint/advisory), and persists immutable `stage_review` artifacts with lineage and annotations; evidence=`src/cine_forge/schemas/role.py`, `src/cine_forge/roles/canon.py`, `src/cine_forge/driver/engine.py`, `src/cine_forge/roles/__init__.py`; next=align role prompts/capabilities and add tests.

20260220-1014 — role definitions upgraded for canon authority/guardian behavior: updated Director prompt to include stage review, disagreement resolution, role inclusion coordination, and lock negotiation language; enabled Director/Continuity Supervisor image capability declarations; tightened Script Supervisor/Continuity Supervisor guardian prompts with explicit `sign_off`/`block` review semantics and narrative/continuity scope; evidence=`src/cine_forge/roles/director/role.yaml`, `src/cine_forge/roles/script_supervisor/role.yaml`, `src/cine_forge/roles/continuity_supervisor/role.yaml`; next=validate with unit+integration tests.

20260220-1031 — verification complete and story closed: added new canon-gating unit/integration coverage for guardian block behavior, override disagreement persistence, explicit-justification enforcement, checkpoint approval gating, immutable version increments, and schema validation; updated existing role-system tests for Director/Guardian capability updates; checks passed: `.venv/bin/python -m pytest tests/unit/test_role_system.py tests/unit/test_canon_gate.py tests/integration/test_role_system_integration.py tests/integration/test_canon_gate_integration.py` (16 passed), `make test-unit PYTHON=.venv/bin/python` (239 passed), `.venv/bin/python -m ruff check src/ tests/` (pass), `make lint PYTHON=.venv/bin/python` (pass); evidence=`tests/unit/test_canon_gate.py`, `tests/integration/test_canon_gate_integration.py`, `tests/unit/test_role_system.py`; next=Story 016 style-pack infrastructure.
