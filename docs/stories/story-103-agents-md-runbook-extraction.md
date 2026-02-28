# Story 103 — AGENTS.md Runbook Extraction (300-Line Cap)

**Priority**: Medium
**Status**: Draft
**Spec Refs**: —
**Depends On**: —

## Goal

Move detailed reference material out of AGENTS.md into dedicated docs/runbooks, keeping AGENTS.md as a compact summary with pointers. AGENTS.md is currently 545+ lines. Long AGENTS.md causes agents to skim rather than internalize key principles. Target: AGENTS.md under 300 lines, with detailed material in runbooks that agents consult on-demand.

## Notes

- Sourced from Scout 003 (Storybook's AGENTS.md 300-line cap)
- Candidates for extraction:
  - Promptfoo section (prerequisites, workspace structure, running benchmarks, judge model, scorer interface, dual eval, pitfalls, adding evals, eval catalog) → `docs/runbooks/promptfoo.md`
  - UI Development Workflow (project setup, visual identity, build loop, checkpoints, mandatory reuse, component registry, feedback contract) → `docs/runbooks/ui-development.md`
  - Deep Research section → `docs/runbooks/deep-research.md` (partially exists)
  - Worktree Strategy → `docs/runbooks/worktree-strategy.md`
  - Golden References table → leave in AGENTS.md (short, frequently referenced)
- Keep AGENTS.md pointers: "See `docs/runbooks/promptfoo.md` for full reference"
- Agent Memory log stays in AGENTS.md (most valuable section per Storybook's finding)
- Was previously skipped in Scout 001 — reconsidering now that AGENTS.md has grown further

## Work Log

20260228 — Created as Draft from Scout 003 finding #7.
