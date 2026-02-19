# Story NNN — TITLE

**Priority**: PRIORITY
**Status**: Pending
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

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- What parts of this story are reasoning/language/understanding problems? → LLM call
- What parts are orchestration/storage/UI? → Code
- Have you checked current SOTA capabilities? Your training data may be stale.
- See AGENTS.md "AI-First Problem Solving" for full guidance.

## Tasks

- [ ] {Implementation task 1}
- [ ] {Implementation task 2}
- [ ] {Implementation task 3}
- [ ] Run `pnpm typecheck && pnpm test && pnpm lint` — all pass
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

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
