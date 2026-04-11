---
id: "160"
title: "Long-Form Character and Location Bible Output Budget Recovery"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "vision-level preference: Radical transparency"
spec_refs:
  - "spec:3"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "008"
  - "009"
  - "129"
  - "155"
category_refs:
  - "spec:3"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
roadmap_tags:
  - "throughput"
  - "output-budget"
  - "long-form"
  - "follow-up-from-155"
legacy_system: ""
---

# Story 160 — Long-Form Character and Location Bible Output Budget Recovery

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Radical transparency
**Spec Refs**: spec:3, spec:8.1, spec:8.3
**ADR Refs**: ADR-003. No dedicated bible-throughput ADR was found after search.
**Depends On**: Story 008, Story 009, Story 129, Story 155

## Goal

Recover honest long-form story-lane reachability for character and location bible generation. Story 155's first full-script throughput baseline shows the long `Big Fish` case reaches `world_building` successfully through `analyze_scenes`, `refresh_project_config`, `entity_discovery`, and `prop_bible`, then fails both `character_bible` and `location_bible` with `LLM output truncated due to max token limit`. This is a real product blocker for full-length screenplay understanding: the current long-form story lane does not finish, and the failure sits in output-budget / candidate-volume territory rather than in the benchmark harness.

## Acceptance Criteria

- [ ] The long screenplay case in the Story 155 detector completes `character_bible` and `location_bible` without truncation failures.
- [ ] The chosen fix explains whether the root cause was prompt/output budgeting, candidate over-selection, or model routing, and records that evidence in the story work log.
- [ ] Long-form entity candidate volume is made honest enough that bible generation does not depend on silent truncation or arbitrary manual fixture shrinking.
- [ ] Focused regression coverage exists for the recovered long-form path before another paid rerun.
- [ ] `docs/evals/registry.yaml` and Story 155 classify the previous truncation failure as runtime-blocking and record the corrected result or remaining blocker truth.

## Out of Scope

- General continuity or scene-analysis optimization not directly tied to the long-form bible failure
- Replacing character/location bibles with a different artifact concept
- UI work beyond surfacing the resulting throughput truth if another story needs it
- Pretending the detector failure is solved by removing the long fixture

## Approach Evaluation

- **Simplification baseline**: First test whether explicit `max_tokens` / response-budget adjustments or narrower prompt payloads solve the truncation without structural changes.
- **AI-only**: Possible if the problem is simply overlong prompts or over-verbose schema guidance. Measure prompt/output-budget tightening before wider code changes.
- **Hybrid**: Plausible if deterministic candidate pruning or excerpt selection reduces payload size while leaving final bible synthesis to the model.
- **Pure code**: Appropriate only for deterministic candidate caps, excerpt selection, or chunk orchestration. Do not replace bible reasoning with brittle heuristics.
- **Repo constraints / ADRs**: ADR-003 keeps these bibles as core story-lane artifacts, so the fix must preserve usefulness instead of reducing long-form support to a shallow placeholder.
- **Existing patterns to reuse**: `character_bible_v1`, `location_bible_v1`, `entity_discovery_v1`, Story 129 taxonomy tightening, Story 155 baseline artifacts, and prompt/output-budget lessons from Story 030's truncation recovery.
- **Eval**: The distinguishing eval is the long-form Story 155 detector rerun plus focused regression tests for the recovered bible path.

## Tasks

- [ ] Reproduce the long-form truncation failure directly in `character_bible_v1` and `location_bible_v1` with the `Big Fish` fixture and inspect prompt/candidate volume before choosing a fix.
- [ ] Test the smallest viable fixes first: explicit output budget, candidate pruning, narrower context windows, or chunked bible extraction.
- [ ] Add focused regression coverage for the recovered long-form bible path.
- [ ] Rerun the Story 155 detector on the long case, then the full pack if the long case clears.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals are rerun: classify all significant mismatches and update `docs/evals/registry.yaml`
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

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/world_building/character_bible_v1/main.py` and `src/cine_forge/modules/world_building/location_bible_v1/main.py` are the primary owners, with `entity_discovery_v1` as an upstream candidate-volume input if the detector proves over-selection is driving truncation.
- **Data contracts**: Preserve current bible artifact contracts. If chunked output or intermediate manifests are needed, keep the final bible outputs compatible with the existing story-lane consumers.
- **Decision context**: Story 155's `big_fish_long` case completed `analyze_scenes` and `entity_discovery`, then both bible stages failed with `LLM output truncated due to max token limit`. That is runtime-blocking and likely output-budget-sensitive, but the exact root cause is still unresolved.

## Files to Modify

- `src/cine_forge/modules/world_building/character_bible_v1/main.py`
- `src/cine_forge/modules/world_building/location_bible_v1/main.py`
- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` only if candidate-volume evidence proves it is part of the blocker
- new or existing focused unit/integration tests covering long-form bible generation
- `docs/evals/registry.yaml`
- `docs/stories/story-160-long-form-character-and-location-bible-output-budget-recovery.md`

## Redundancy / Removal Targets

- Implicit reliance on provider-default output caps for large structured bible responses
- Over-selected candidate lists that inflate bible prompts without improving story-lane usefulness
- Detector notes that conflate truncation with generic runtime slowness

## Notes

- Story 155 baseline evidence:
  - `big_fish_long.world_building.analyze_scenes` succeeded at `888.476s` / `$0.9336`
  - `big_fish_long.world_building.character_bible` failed after `57.044s` with `LLM output truncated due to max token limit`
  - `big_fish_long.world_building.location_bible` failed after `56.826s` with the same truncation error
- `entity_discovery` also surfaced unusually large upstream candidate sets (`184` locations, `242` props, with prop truncation to `25`), so this story may need to decide whether the bible failure is downstream-only or partly driven by discovery volume.

## Work Log

- 20260410-2232 — story-created: split Story 155's long-form bible truncation blocker into its own follow-up line so it does not get mixed with successful-stage runtime reduction work. Evidence: `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}` and `output/runs/big_fish_long-world_building-12d0/pipeline_events.jsonl` show `character_bible` and `location_bible` both failing with `LLM output truncated due to max token limit` after the long case already spent `888s` in `analyze_scenes`. Next step: run `/build-story 160` when the repo is ready to turn this runtime-blocking detector failure into a targeted recovery slice.
