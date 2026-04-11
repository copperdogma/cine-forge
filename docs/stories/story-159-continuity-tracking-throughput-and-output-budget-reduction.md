---
id: "159"
title: "Continuity Tracking Throughput and Output Budget Reduction"
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
  - "011"
  - "032"
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
  - "continuity"
  - "output-budget"
  - "follow-up-from-155"
legacy_system: ""
---

# Story 159 — Continuity Tracking Throughput and Output Budget Reduction

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Radical transparency
**Spec Refs**: spec:3, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane outputs remain usable working artifacts). No throughput-specific ADR was found after search.
**Depends On**: Story 011, Story 032, Story 155

## Goal

Reduce the heaviest successful story-lane bottleneck surfaced by Story 155 without degrading continuity usefulness. The first honest screenplay-throughput detector shows `continuity_tracking` is the top successful-stage runtime and output-volume hotspot across the current short/medium baseline, landing at roughly `41.4s -> 72.3s / 1k words` and `6.5k -> 9.5k output tokens / 1k words` while also producing the largest byte/line payloads in the measured successful cases. This story should turn that detector result into a focused optimization line instead of leaving continuity as an anecdotal "the pipeline feels slow" complaint.

## Acceptance Criteria

- [ ] A rerun of the Story 155 detector shows `world_building.continuity_tracking` no longer dominates normalized runtime on the successful short/medium cases, or the remaining dominance is explained with evidence and a tighter output budget.
- [ ] Continuity output volume is reduced materially on the same detector cases without losing required state-change usefulness for downstream world/story inspection.
- [ ] The chosen implementation makes continuity throughput tradeoffs inspectable in artifacts or detector output rather than hiding them behind one aggregate runtime number.
- [ ] Focused regression coverage exists for any new continuity compaction, batching, or pruning logic before another paid rerun.
- [ ] `docs/evals/registry.yaml`, Story 155, and this story classify the remaining result as runtime-blocking or non-runtime-blocking with explicit evidence.

## Out of Scope

- Replacing continuity tracking with a different product concept
- General world-building optimization that is not meaningfully driven by the Story 155 detector
- UI dashboard work beyond what is needed to inspect runtime and output-budget changes
- Silent quality regressions that merely make the continuity payload smaller

## Approach Evaluation

- **Simplification baseline**: First measure whether prompt tightening alone can cut continuity output without code changes. If a single prompt/config change is enough, prefer that over new orchestration.
- **AI-only**: Possible if the continuity prompt is simply over-verbose. Measure whether a stricter completeness contract plus terser schema guidance fixes the budget.
- **Hybrid**: Plausible if deterministic change-detection or event bucketing can narrow what the LLM has to summarize while keeping AI judgment for the final continuity read.
- **Pure code**: Only right for deterministic payload pruning, batching, or artifact-shape cleanup. Do not hard-code narrative reasoning that the model should own.
- **Repo constraints / ADRs**: ADR-003 keeps story-lane artifacts as useful planning surfaces. Any optimization that strips away continuity signal to chase speed is wrong for this repo.
- **Existing patterns to reuse**: Story 155's detector output, `continuity_tracking_v1`, existing cost/token tracking, and the Story 040 lesson that output budgets and batch shape can matter more than raw provider swaps.
- **Eval**: The distinguishing eval is the Story 155 custom detector, rerun on the same short/medium baseline with continuity-specific before/after evidence.

## Tasks

- [ ] Inspect `continuity_tracking_v1` prompt/input shape and identify whether the dominant cost is prompt size, output verbosity, or call count.
- [ ] Test the smallest candidate fixes first: prompt/output-budget tightening, input-pruning, or deterministic pre-aggregation before larger refactors.
- [ ] Add focused regression coverage for any continuity payload-pruning or batching logic.
- [ ] Rerun the Story 155 detector on the short/medium cases and record the before/after continuity row deltas.
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

- **Owning class/module**: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` is the primary owner. Keep detector/report code in the Story 155 benchmark harness rather than adding product-specific throughput logic to the driver.
- **Data contracts**: Prefer existing continuity artifact contracts. If the optimization needs a new compact representation, keep it schema-first and preserve downstream readability.
- **Decision context**: Story 155 baseline (`benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}`) shows `continuity_tracking` is the top successful-stage hotspot on both runtime and output-volume for the short/medium successful cases.

## Files to Modify

- `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`
- `tests/unit/` continuity-tracking coverage files, or a new narrow test file if no focused seam exists
- `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.json` (read-only evidence)
- `docs/evals/registry.yaml`
- `docs/stories/story-159-continuity-tracking-throughput-and-output-budget-reduction.md`

## Redundancy / Removal Targets

- Verbose continuity payload sections that downstream consumers do not actually need
- Duplicate continuity summarization passes if one prompt already subsumes them
- Detector-free "continuity feels expensive" tuning notes

## Notes

- Baseline evidence from Story 155:
  - `open_frequency_short`: `continuity_tracking` = `61.988s`, `7535` output tokens
  - `last_birthday_card_medium`: `continuity_tracking` = `157.010s`, `24560` output tokens
- This story is about the successful hotspot, not the separate long-form truncation failure in character/location bible generation.

## Work Log

- 20260410-2230 — story-created: split Story 155's top successful-stage hotspot into its own follow-up line so continuity optimization does not get buried under unrelated long-form failures. Evidence: `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}` shows `world_building.continuity_tracking` as the top normalized runtime/output hotspot across successful cases. Next step: run `/build-story 159` once the current active focus allows this secondary throughput line to move.
