# Story 109 — Golden Build Runbook

**Priority**: Medium
**Status**: Done
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

- [x] Draft `docs/runbooks/golden-build.md` using dossier's `golden-build.md` as template, adapted for CineForge's promptfoo-based eval structure
- [x] Add enforcement cross-references to `/build-story`, `/validate`, `/mark-story-done`, `/verify-eval`
- [x] Verify `/setup-golden` skill references the new runbook
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** N/A — docs only, no user data
  - [x] **T1 — AI-Coded:** Yes — runbook is structured for AI consumption with tagged steps
  - [x] **T2 — Architect for 100x:** No over-engineering — straightforward runbook
  - [x] **T3 — Fewer Files:** One new file, appropriate size (~250 lines)
  - [x] **T4 — Verbose Artifacts:** Work log is detailed
  - [x] **T5 — Ideal vs Today:** Runbook supports accurate eval measurement, which supports the Ideal

## Files to Modify

- `docs/runbooks/golden-build.md` — new file
- `.agents/skills/setup-golden/SKILL.md` — add runbook reference

## Notes

Sourced from Scout 005 (item 11). Dossier's `docs/runbooks/golden-build.md` is the template — adapt for CineForge's golden file locations (`benchmarks/golden/`, `tests/fixtures/golden/`) and promptfoo-based eval structure.

## Plan

### Task 1: Draft `docs/runbooks/golden-build.md`
- **Source**: Dossier's `docs/runbooks/golden-build.md` as structural template
- **Adaptations**: CineForge uses `benchmarks/golden/` (promptfoo evals) + `tests/fixtures/golden/` (unit tests), not Dossier's EntityGraph-specific structure. Remove Dossier-specific references (evidence offsets, mention types, `find_offsets.py`, `validate_golden.py`). Replace with CineForge's dual evaluation pattern (Python scorer + LLM rubric), promptfoo workflow, and golden file locations from AGENTS.md.
- **Sections**: Context, Prerequisites, Build Phases (adapted), Boundaries, Common Failure Patterns (adapted), Eval-Driven Golden Improvement, Periodic Golden Audit, Enforcement Across Skills, Troubleshooting, Lessons Learned
- **Done when**: File exists, all runbook conventions met (Context, Prerequisites, Steps tagged [script]/[judgment], Boundaries, Troubleshooting, Lessons Learned)

### Task 2: Add enforcement cross-references
- The runbook's "Enforcement across skills" section will reference `/build-story` 11b, `/validate` 5b, `/mark-story-done` checklist, `/verify-eval`, and AGENTS.md DoD #5
- These skills already reference `/verify-eval` — the runbook completes the circle by documenting the golden-side of the protocol

### Task 3: Verify `/setup-golden` references
- `/setup-golden` already has a forward reference to `docs/runbooks/golden-build.md` (lines 136-144). Verify it's accurate after the runbook is created. No changes expected.

### Task 4: Doc updates + tenets
- Check AGENTS.md "Golden References" section — may need a link to the runbook
- Tenet verification

### Impact
- No code changes. No tests affected. Pure documentation.
- No human-approval blockers (no deps, no schema changes).

## Work Log

20260301-1200 — Created from Scout 005, item 11. Deferred from inline implementation due to scope (runbook + cross-skill wiring).

20260301-1430 — Implementation complete. Created `docs/runbooks/golden-build.md` (~250 lines) adapted from Dossier's EntityGraph-specific runbook. Key adaptations: replaced evidence offset/mention type detail with CineForge's dual scoring (Python structural + LLM rubric) via promptfoo; replaced Dossier-specific tooling refs with CineForge's `benchmarks/` workflow; replaced failure patterns (truncated quotes, wrong-scene evidence) with CineForge-relevant patterns (missing aliases, shallow descriptions, phantom entries, wrong relationship types, convention inconsistencies). Added AGENTS.md link to Golden References section. All ACs verified met.

20260301-1400 — Phase 1 exploration complete. Key findings:
- Dossier runbook is EntityGraph-specific (evidence offsets, mention types, fact→evidence mappings). CineForge golden files are simpler: JSON reference files for promptfoo evals (character/location/prop/scene/config/relationship extraction) and one unit test fixture (scene entities). Need to strip Dossier-specific detail and replace with CineForge's dual eval pattern.
- `/setup-golden` already forward-references `docs/runbooks/golden-build.md` at lines 136-144. No changes needed there.
- CineForge has 11 golden files across 2 locations: `benchmarks/golden/` (10 files for promptfoo) and `tests/fixtures/golden/` (1 file for unit tests).
- AGENTS.md "Golden References" table lists 7 golden files with source/purpose. May need a link to the runbook.

20260301-1500 — Story marked Done. Validation grade: A (after fixing `/setup-golden` Operational Playbook bullets to match actual runbook content). All 5 ACs met. CHANGELOG entry added.
