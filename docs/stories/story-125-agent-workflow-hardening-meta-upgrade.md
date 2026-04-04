---
id: "125"
title: "Agent Workflow Hardening Meta Upgrade"
status: "Done"
priority: "High"
ideal_refs:
  - "Vision-level preference: easy, fun, and engaging"
  - "R12 (decisions explainable and overridable)"
  - "R14 (process traceability)"
spec_refs:
  - "spec:11.1"
  - "spec:11.3"
  - "spec:11.4"
adr_refs: []
depends_on: []
category_refs:
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 125 — Agent Workflow Hardening Meta Upgrade

**Priority**: High
**Status**: Done
**Ideal Refs**: Vision-level preference: easy, fun, and engaging; R12 (decisions explainable and overridable); R14 (process traceability)
**Spec Refs**: spec:11.1 (Story Lifecycle and Handoff Chain), spec:11.3 (Verification, Eval Classification, and Registry Discipline), spec:11.4 (Agent Instructions, Skills, and Runbooks)
**ADR Refs**: None found after search
**Depends On**: 053

## Goal

Harden the repo's agent workflow so story execution, validation, check-in, and recurring repo-hygiene work are explicit, consistent, and safe. This bundle is meta-infrastructure: it reduces silent protocol drift, prevents agents from closing work prematurely, and keeps git landing predictable when parallel worktrees are in use.

## Acceptance Criteria

- [x] Agent-facing docs and reusable skills consistently require ADR lookup for architecture, workflow, schema, and UX questions, or an explicit statement that no ADR applies.
- [x] Story lifecycle skills enforce the intended handoff chain: implementation summary -> `/validate` -> `/mark-story-done`, with workflow gates in new stories.
- [x] `/check-in-diff` supports task-branch landing and `main` fallback without pushing unvalidated `main`, and any cross-worktree landing exception is explicit and git-only.
- [x] `codebase-improvement-scout` exists as a report-first skill with research backing, safe autofix limits, and a runbook.
- [x] This story records validation evidence and leaves a clear next step for closure.

## Out of Scope

- Scheduling the repo-hygiene scout as an automation
- Rolling these process changes out to other repos
- Fully reducing `AGENTS.md` to Story 103's target length

## Approach Evaluation

- **AI-only**: Rely on prompt wording and ad hoc reminders. This is too weak; the whole problem is that agents drift when the rules are not encoded in durable artifacts.
- **Hybrid**: Encode the rules in `AGENTS.md`, canonical skills, story templates, and runbooks, then verify with repo-native checks and manual review. This is the right fit for this repo because Story 053 already made `.agents/skills/` the canonical control surface.
- **Pure code**: Build hard automation around story state and git landing. Too brittle for now; it would fight the user's preference for flexible human checkpoints and occasional direct work on `main`.
- **Repo constraints / ADRs**: No dedicated ADR governs agent workflow. The solution must still respect the Ideal, `AGENTS.md` story execution protocol, the worktree strategy, and Story 053's cross-CLI skill architecture.
- **Existing patterns to reuse**: `.agents/skills/` as the canonical skill root, `scripts/sync-agent-skills.sh`, runbooks under `docs/runbooks/`, scout entries under `docs/scout/`, and the story template's new workflow-gate structure.
- **Eval**: Validate by repo-native checks (`pytest`, `ruff`, UI lint, `tsc -b`), skill sync verification, and manual consistency review of the git/worktree instructions.

## Tasks

- [x] Add ADR lookup guidance across agent docs and reusable skills
- [x] Encode workflow gates and handoff ownership across story lifecycle skills and templates
- [x] Create the research-backed `codebase-improvement-scout` skill and runbook
- [x] Fix `/check-in-diff`, its runbook, and `AGENTS.md` so the `main` fallback never pushes before validation and the worktree landing exception is explicit
- [x] Add a tracking story for this bundle, update the story index, and record validation evidence
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` (lint + `tsc -b` run; build not required because no UI files changed)
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker (not applicable here; no UI files changed)
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: This is process infrastructure owned by `AGENTS.md`, canonical skills under `.agents/skills/`, and runbooks under `docs/runbooks/`. No runtime service or schema is involved.
- **Data contracts**: None. This story changes documentation, prompts, and git workflow instructions rather than runtime data crossing a layer boundary.
- **File sizes**: `AGENTS.md` (619), `.agents/skills/check-in-diff/SKILL.md` (151), `.agents/skills/build-story/SKILL.md` (159), `.agents/skills/validate/SKILL.md` (129), `.agents/skills/create-story/SKILL.md` (88), `.agents/skills/create-story/templates/story.md` (86), `.agents/skills/mark-story-done/SKILL.md` (83), `.agents/skills/codebase-improvement-scout/SKILL.md` (179), `docs/runbooks/check-in-worktree-landing.md` (97), `docs/runbooks/codebase-improvement-scout.md` (86), `docs/scout/scout-011-codebase-improvement-skill.md` (69), `docs/stories.md` (277).
- **Decision context**: Reviewed `docs/ideal.md` and `docs/design/decisions.md`. No dedicated ADR was found for agent git/worktree workflow, so this story records the process explicitly instead of pretending a missing ADR exists.

## Files to Modify

- `AGENTS.md` — story execution protocol and worktree strategy cleanup (619)
- `.agents/skills/check-in-diff/SKILL.md` — safe landing order and `main` fallback rules (151)
- `docs/runbooks/check-in-worktree-landing.md` — operational steps aligned with the skill (97)
- `docs/stories.md` — track the meta-process story in the story index (277)
- `docs/stories/story-125-agent-workflow-hardening-meta-upgrade.md` — acceptance criteria, tasks, gates, and work log for this bundle (86 at scaffold creation)

## Redundancy / Removal Targets

- Contradictory worktree landing guidance between `AGENTS.md`, `/check-in-diff`, and the runbook
- Ambiguous branch naming guidance where the benchmark sidequest uses an older user-managed branch name
- Untracked process bundles that never get a story, work log, or closure gate

## Notes

- This story was created retroactively after `/validate` flagged that the process-upgrade bundle had no matching story file.
- Research for the repo-hygiene scout lives in `docs/research/codebase-improvement-skill/` and Scout 011.
- Story 103 still owns the larger `AGENTS.md` shrink-down goal; that work is related but not a blocking dependency for this story.

## Plan

Retroactive finish-up only:
- fix the remaining `/check-in-diff` landing-order and worktree-policy inconsistencies
- add this tracking story and index row
- rerun validation checks and record the outcome here
- stop at a validated handoff; do not mark the story Done inline

## Work Log

20260312-1545 — story-created: Added a retroactive tracking story after `/validate` found the process-upgrade bundle had no matching story. Evidence=`docs/stories.md`, validation report in session. Next=fix the remaining check-in/worktree inconsistencies and rerun validation.
20260312-1605 — workflow-hardened-and-validated: Fixed `/check-in-diff` so `main` fallback chooses the execution branch before any push, made the cross-worktree landing exception git-only in both `AGENTS.md` and `docs/runbooks/check-in-worktree-landing.md`, clarified the legacy benchmark sidequest branch naming, synced skill wrappers, and reran checks. Evidence=`scripts/sync-agent-skills.sh`, `scripts/sync-agent-skills.sh --check`, `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 warning), `.venv/bin/python -m ruff check src/ tests/` (clean), `pnpm --dir ui run lint` (0 errors, 5 existing warnings), `cd ui && npx tsc -b` (clean). Next=`/mark-story-done` if the user wants to close Story 125, otherwise `/check-in-diff`.
20260312-1615 — story-closed: Re-ran the required close-out checks, confirmed all acceptance criteria, tasks, and workflow gates, narrowed dependencies to the actual completed prerequisite, and marked Story 125 Done. Evidence=`make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 warning), `.venv/bin/python -m ruff check src/ tests/` (clean), `pnpm --dir ui run lint` (0 errors, 5 pre-existing warnings), `cd ui && npx tsc -b` (clean), `CHANGELOG.md`. Next=`/check-in-diff`.
