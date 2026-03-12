# Story NNN — TITLE

**Priority**: PRIORITY
**Status**: Draft
**Ideal Refs**: {ideal refs}
**Spec Refs**: {spec refs}
**ADR Refs**: {adr refs or "None found after search"}
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
- **Repo constraints / ADRs**: {What existing decisions, patterns, or constraints shape the choice?}
- **Existing patterns to reuse**: {Which components, helpers, modules, or prior stories should this extend instead of duplicating?}
- **Eval**: {What test distinguishes the approaches? Does it exist yet?}

## Tasks

- [ ] {Implementation task 1}
- [ ] {Implementation task 2}
- [ ] {Implementation task 3}
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: {What existing class or module owns this feature? If none, propose a new focused class — not an existing large one.}
- **Data contracts**: {What typed interfaces (Pydantic models) define the data contracts for this feature? If new data crosses a layer boundary, a schema must be defined first.}
- **File sizes**: {Current line count of each file to be modified. Run `make check-size` to check. Flag any file >500 lines per Architecture Rules in AGENTS.md.}
- **Decision context**: {Which ADRs / decision docs were reviewed? If none apply, say why.}

## Files to Modify

- {path/to/file} — {what changes} ({current line count})

## Redundancy / Removal Targets

- {old path, helper, abstraction, or docs likely to become redundant if this lands}

## Notes

{Design notes, open questions, references}

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
