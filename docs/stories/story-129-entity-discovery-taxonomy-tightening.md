# Story 129 — Entity Discovery Taxonomy Tightening

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: Story Understanding quality bar
**Spec Refs**: 6 (Bibles & Entity Graph)
**ADR Refs**: None found after search; bounded prompt-quality follow-up on Story 124
**Depends On**: Story 081 (Scene Index as Canonical Character Source), Story 124 (Recall Verification Loop)

## Goal

Reduce obvious entity noise before it pollutes downstream bibles. The current character taxonomy still allows generic roles such as `WAITER`, `GUARD`, and `CROWD`, and the prop taxonomy is not explicit enough about excluding generic environmental objects. This story tightens the prompt contract for `entity_discovery_v1`, then re-runs the existing eval path so we verify the noise reduction does not cost real recall.

## Acceptance Criteria

- [ ] Character discovery instructions explicitly exclude unnamed background characters, crowd labels, and generic service/security roles unless they have plot impact and a specific narrative identity.
- [ ] Prop discovery instructions explicitly exclude costumes, set dressing, and generic environmental objects unless they are handled by actors or materially matter to the story.
- [ ] Unit tests verify the tightened prompt language so future edits do not silently relax the exclusions.
- [ ] Entity-discovery eval is re-run after the prompt change, all significant mismatches are classified via `/verify-eval`, and `docs/evals/registry.yaml` is updated if scores move.
- [ ] Noise reduction does not regress required recall on the existing golden fixture.

## Out of Scope

- New entity-discovery architecture such as multi-pass orchestration or post-hoc rule filters
- Changes to downstream bible extraction prompts
- Character alias resolution beyond the current normalization path
- Retaxonomizing locations or introducing new entity types

## Approach Evaluation

- **AI-only**: A prompt-only change may be enough because the problem is taxonomy ambiguity, not missing data.
- **Hybrid**: Prompt tightening plus a small deterministic post-filter is possible if eval shows prompt-only is insufficient.
- **Pure code**: A pure post-filter is risky because generic names can sometimes be real plot entities. It should be a fallback, not the default assumption.
- **Repo constraints / ADRs**: AGENTS requires prompt-first before model escalation. Story 124 already gave us a stable eval harness and verification loop, so this story should prove the smaller prompt fix before reaching for extra heuristics.
- **Existing patterns to reuse**: `entity_discovery_v1/main.py`, Story 124 eval assets (`benchmarks/tasks/entity-discovery.yaml`, scorer, golden), `/verify-eval` workflow, `tests/unit/test_module_entity_discovery_v1.py`.
- **Eval**: Existing entity-discovery promptfoo eval plus targeted unit tests distinguish prompt-only vs prompt+filter approaches. This capability already has a benchmark and registry entry.

## Tasks

- [ ] Tighten the character and prop taxonomy strings in `entity_discovery_v1`.
- [ ] Add prompt-text regression tests so the exclusions remain explicit.
- [ ] Run the entity-discovery eval after the prompt change.
- [ ] Run `/verify-eval` if mismatches appear; classify all meaningful diffs as model-wrong, golden-wrong, or ambiguous.
- [ ] Update `docs/evals/registry.yaml` with the post-change score, date, and git SHA if the eval is rerun.
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

- **Owning class/module**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` owns the taxonomy text and discovery loop. This should remain a focused prompt-quality change unless eval evidence proves a larger intervention is necessary.
- **Data contracts**: Existing `EntityDiscoveryResults` schema remains the contract. No new inter-layer models should be needed unless the implementation adds new verification metadata.
- **File sizes**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` (362), `tests/unit/test_module_entity_discovery_v1.py` (359), `benchmarks/tasks/entity-discovery.yaml` (107), `benchmarks/scorers/entity_discovery_scorer.py` (171), `docs/evals/registry.yaml` (1152, large). `make check-size` flags `registry.yaml` as an especially easy place to create noisy churn.
- **Decision context**: Reviewed Story 065 work log (where this was deferred), Story 124, the current module prompt, and the eval requirements in AGENTS. No ADR governs this exact prompt wording.

## Files to Modify

- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — tighten taxonomy language (362)
- `tests/unit/test_module_entity_discovery_v1.py` — prompt-text regression tests (359)
- `benchmarks/tasks/entity-discovery.yaml` — rerun existing eval harness if needed (107)
- `docs/evals/registry.yaml` — update verified score metadata if eval reruns (1152)

## Redundancy / Removal Targets

- Any later one-off prompt comments that try to restate the taxonomy outside the single source in `entity_discovery_v1`

## Notes

This is intentionally small-scope. If a prompt edit fixes the noise, adding post-filters or a multi-pass controller would be worse than what already exists.

## Plan

To be written by `/build-story` after implementation planning and eval planning.

## Work Log

20260313-1658 — triage: created from inbox item "Tighten entity_discovery character/prop taxonomy prompts". Existing homes checked: Story 065 explicitly deferred this, Story 124 covers recall verification but not taxonomy noise. Next=`/build-story` when ready.
