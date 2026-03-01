# Story 109 — Golden Build Runbook

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: Eval infrastructure reliability
**Spec Refs**: AGENTS.md Golden References, Definition of Done #5
**Depends On**: None

## Goal

Create `docs/runbooks/golden-build.md` documenting the CineForge golden fixture build process — how to create, validate, and maintain golden reference files used by promptfoo evals and acceptance tests. Include semantic review phases, failure pattern taxonomy, and enforcement cross-references showing how every lifecycle skill (`/build-story`, `/validate`, `/mark-story-done`, `/verify-eval`) connects to the golden build process.

## Acceptance Criteria

- [ ] `docs/runbooks/golden-build.md` exists with: Context, Prerequisites, Steps, Boundaries, Troubleshooting, Lessons Learned sections
- [ ] Steps cover: creating a new golden from scratch, semantic review phases (structural → semantic → cross-reference), failure patterns taxonomy
- [ ] "Eval-Driven Golden Improvement" section documents the fix protocol (identical to `/verify-eval` Phase 4 but as a standalone reference)
- [ ] "Enforcement across skills" section cross-references every lifecycle skill that enforces golden quality
- [ ] A corresponding `/setup-golden` skill exists or is updated to reference the runbook

## Out of Scope

- Changing the golden file format or schema
- Creating new golden files (this documents the process, doesn't execute it)
- Modifying the `/verify-eval` skill (already landed in Scout 005)

## Approach Evaluation

- **Pure code**: This is documentation — no code, no AI. Straightforward runbook authoring.
- **Eval**: N/A — documentation story.

## Tasks

- [ ] Draft `docs/runbooks/golden-build.md` using dossier's `golden-build.md` as template, adapted for CineForge's promptfoo-based eval structure
- [ ] Add enforcement cross-references to `/build-story`, `/validate`, `/mark-story-done`, `/verify-eval`
- [ ] Verify `/setup-golden` skill references the new runbook
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `docs/runbooks/golden-build.md` — new file
- `.agents/skills/setup-golden/SKILL.md` — add runbook reference

## Notes

Sourced from Scout 005 (item 11). Dossier's `docs/runbooks/golden-build.md` is the template — adapt for CineForge's golden file locations (`benchmarks/golden/`, `tests/fixtures/golden/`) and promptfoo-based eval structure.

## Plan

{Written by build-story Phase 2}

## Work Log

20260301-1200 — Created from Scout 005, item 11. Deferred from inline implementation due to scope (runbook + cross-skill wiring).
