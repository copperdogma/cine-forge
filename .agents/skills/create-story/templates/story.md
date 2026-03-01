# Story NNN — TITLE

**Priority**: PRIORITY
**Status**: Draft
**Spec Refs**: {spec refs}
**Depends On**: {depends on}

## Goal

{One paragraph describing what this story accomplishes and why it matters.}

## Acceptance Criteria

- [ ] {Testable criterion 1}
- [ ] {Testable criterion 2}
- [ ] {Testable criterion 3}

## Out of Scope

- {Explicitly list what this story does NOT do}

## Approach Evaluation

{List candidate approaches — do NOT pre-decide. build-story's eval-first gate selects the winner with evidence.}
- **AI-only**: {Could an LLM call handle this? What would it cost per run?}
- **Hybrid**: {Cheap detection + AI judgment? Where's the split?}
- **Pure code**: {Only if this is strictly orchestration/plumbing with no reasoning.}
- **Eval**: {What test distinguishes the approaches? Does it exist yet?}

## Tasks

- [ ] {Implementation task 1}
- [ ] {Implementation task 2}
- [ ] {Implementation task 3}
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- {path/to/file} — {what changes}

## Notes

{Design notes, open questions, references}

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
