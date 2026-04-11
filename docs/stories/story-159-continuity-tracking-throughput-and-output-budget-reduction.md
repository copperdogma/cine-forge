---
id: "159"
title: "Continuity Tracking Throughput and Output Budget Reduction"
status: "Done"
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
**Status**: Done
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Radical transparency
**Spec Refs**: spec:3, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane outputs remain usable working artifacts). No throughput-specific ADR was found after search.
**Depends On**: Story 011, Story 032, Story 155

## Goal

Reduce the heaviest successful story-lane bottleneck surfaced by Story 155 without degrading continuity usefulness. The first honest screenplay-throughput detector shows `continuity_tracking` is the top successful-stage runtime and output-volume hotspot across the current short/medium baseline, landing at roughly `41.4s -> 72.3s / 1k words` and `6.5k -> 9.5k output tokens / 1k words` while also producing the largest byte/line payloads in the measured successful cases. This story should turn that detector result into a focused optimization line instead of leaving continuity as an anecdotal "the pipeline feels slow" complaint.

## Acceptance Criteria

- [x] A rerun of the Story 155 detector shows `world_building.continuity_tracking` no longer dominates normalized runtime on the successful short/medium cases, or the remaining dominance is explained with evidence and a tighter output budget.
- [x] Continuity output volume is reduced materially on the same detector cases without losing required state-change usefulness for downstream world/story inspection.
- [x] The chosen implementation makes continuity throughput tradeoffs inspectable in artifacts or detector output rather than hiding them behind one aggregate runtime number.
- [x] Focused regression coverage exists for any new continuity compaction, batching, or pruning logic before another paid rerun.
- [x] `docs/evals/registry.yaml`, Story 155, and this story classify the remaining result as runtime-blocking or non-runtime-blocking with explicit evidence.
- [x] If `big_fish_long` still fails inside `continuity_tracking`, the story reproduces the blocker and either fixes the continuity-side prompt/schema issue inline or records the remaining blocker truth explicitly in `docs/evals/registry.yaml`.

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

- [x] Inspect `continuity_tracking_v1` prompt/input shape and identify whether the dominant cost is prompt size, output verbosity, or call count.
- [x] Test the smallest candidate fixes first: prompt/output-budget tightening, input-pruning, or deterministic pre-aggregation before larger refactors.
- [x] Reproduce the current long-form `continuity_tracking` blocker and, if it is the same continuity-side prompt/schema/runtime path, absorb the smallest fix into this story before the final eval update.
- [x] Add focused regression coverage for any continuity payload-pruning or batching logic.
- [x] Rerun the Story 155 detector on the short/medium cases and record the before/after continuity row deltas.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI static checks: `pnpm --dir ui run lint` (warnings only, outside touched file), `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals are rerun: classify all significant mismatches and update `docs/evals/registry.yaml`
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
- `tests/integration/test_continuity_ai_integration.py` only if a real-model regression is needed for the long-form blocker
- `src/cine_forge/schemas/continuity.py` only if reproduction proves the continuity-side blocker is a prompt/schema mismatch (for example `new_value = null`)
- `benchmarks/scripts/full_script_throughput_support.py` only if the existing detector cannot expose the before/after continuity deltas cleanly
- `ui/src/components/EntityTimelineView.tsx` because the nullable `new_value` continuity fix crosses the backend/UI schema boundary
- `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.json` (read-only evidence)
- `docs/evals/registry.yaml`
- `docs/stories/story-155-end-to-end-throughput-detector-and-stage-efficiency-budgets.md`
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

## Plan

### Exploration Notes

- **Story status / buildability**: Story 159 is still `Draft`, but it is detailed enough and substrate-verified. The worktree is clean, `continuity_tracking_v1` has not changed since Story 092, and Story 155 / Story 160 provide the current benchmark truth, so the story should promote when implementation starts rather than stay draft.
- **Files that will likely change**: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`, a new narrow continuity-throughput unit test file under `tests/unit/`, `docs/evals/registry.yaml`, and this story file. `src/cine_forge/schemas/continuity.py`, `tests/integration/test_continuity_ai_integration.py`, and `benchmarks/scripts/full_script_throughput_support.py` are conditional follow-ons if reproduction proves they are needed.
- **Files at risk of breaking**: `src/cine_forge/modules/timeline/timeline_build_v1/main.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `ui/src/pages/ContinuityPage.tsx`, and `ui/src/components/EntityTimelineView.tsx` consume persisted continuity artifacts directly if the schema moves.
- **Decision context consulted**: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/build-map.md`, `docs/spec.md` (`spec:3`, `spec:8.1`, `spec:8.3`), ADR-003, Stories 011 / 032 / 040 / 092 / 112 / 129 / 155 / 160, `docs/evals/registry.yaml`, and live `scripts/discover-models.py --summary` output from `2026-04-11`.
- **Patterns to follow**: prompt-first before model escalation; detector-backed throughput work rather than anecdotal tuning; and the repo's newer `fail_on_truncation=True` pattern from `scene_analysis_v1`, `character_bible_v1`, and `location_bible_v1`.
- **Potential cleanup / redundancy**: over-verbose per-entity prompt sections, unconditional carry-forward state dumps, continuity-specific test growth inside the existing 717-line unit file, and detector-side continuity notes that do not explain prompt-vs-output pressure.
- **Surprises / risks found**:
  - The hotspot is clearly prompt/output volume, not missing stage reuse: Story 155 records `8379 -> 7535` tokens on the short case and `55060 -> 24560` tokens on the medium case for this stage alone.
  - `continuity_tracking_v1` makes one LLM call per scene, but the current detector only exposes stage totals, so the internal per-scene shape is still opaque.
  - The latest long-form rerun logged a `new_value = null` schema validation issue against the current non-null `ContinuityEvent.new_value`, so the long-case blocker may be partly schema/prompt mismatch, not only raw volume.
  - `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` and `_build_continuity_prompt()` already violate the repo's size guidance, so adding logic inline would be a plan bug.

### Baseline / Eval Gate

- **Checked-in baseline is still current**: the continuity module, continuity schema, and continuity unit suite have not changed since Story 092; the worktree is clean; Story 155 remains the honest current detector.
- **Detector baseline to beat**:
  - `open_frequency_short`: `61988 ms`, `8379` input tokens, `7535` output tokens, `185101` output bytes
  - `last_birthday_card_medium`: `157010 ms`, `55060` input tokens, `24560` output tokens, `1183030` output bytes
  - Normalized hotspot from Story 155: `72295.372 ms / 1k words` and `9510.535 output tokens / 1k words`
- **Local baseline**: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_continuity_tracking_module.py -q` currently passes `14/14`.
- **Candidate approaches**:
  - **AI-only**: tighten the prompt/output contract, shrink carry-forward state summaries, and enforce truncation visibly.
  - **Hybrid**: deterministically pre-aggregate or bucket previous state so the LLM sees only the continuity-relevant delta rather than the full carried-forward state.
  - **Pure code**: prune emitted artifacts or skip continuity reasoning. Rejected as the first move because it risks silent quality loss.
- **Chosen first path**: AI-only prompt/output tightening plus explicit truncation enforcement. The repo already uses a cheap tested work model (`claude-haiku-4-5-20251001`), AGENTS says prompt-first before model escalation, and live model discovery on `2026-04-11` showed many untested models but no continuity-specific evidence that a model swap would beat slimming the current hot path.
- **Success measures**:
  - Primary: rerun the Story 155 detector on `open_frequency_short` and `last_birthday_card_medium`
  - Secondary: targeted `big_fish_long` rerun only if the continuity-side blocker remains relevant after the short/medium change
  - Local: new narrow regression tests for prompt compaction, carry-forward summarization, and any null-event hardening

### Repo-Fit / Optimality Evidence

- `docs/methodology/state.yaml` explicitly says throughput and output-volume optimization should be driven by runtime detectors and measured stage budgets, which is exactly the Story 155 harness.
- ADR-003 keeps continuity as a story-lane working artifact. Any optimization that wins by emitting shallow placeholders or erasing useful state-change evidence is wrong for this repo.
- Story 040 and Story 160 point in the same direction: fix batch shape, prompt volume, and budget handling before swapping providers.
- `continuity_tracking_v1` currently differs from the repo's newer long-form AI modules: it sets `max_tokens=4096` but does not set `fail_on_truncation=True`, while `scene_analysis_v1`, `character_bible_v1`, and `location_bible_v1` do.
- **Rejected alternatives**:
  - **Model-routing first**: no continuity-specific eval evidence justifies it yet, and it papers over an oversized prompt/output path.
  - **Story 112 redesign first**: wrong scope for a measured throughput/output-budget story.
  - **Detector-only work first**: the 812-line throughput support file is not the root cause, and growing it before slimming the module would be backwards.

### Structural Health Check

- `make check-size` flags the expected large files:
  - `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` — `569` lines
  - `tests/unit/test_continuity_tracking_module.py` — `717` lines
  - `benchmarks/scripts/full_script_throughput_support.py` — `812` lines
  - `docs/evals/registry.yaml` — `2234` lines
- Oversized methods:
  - `run_module()` — `211` lines
  - `_build_continuity_prompt()` — `120` lines
- **Plan consequence**: the first implementation task must extract a small helper seam from `run_module()` and/or `_build_continuity_prompt()` before adding new logic. New throughput-specific unit coverage should go in a new narrow test file instead of enlarging the existing 717-line suite.
- **Schema / event check**: no new event type is expected. No new inter-layer contract is planned unless reproducing the `new_value = null` failure proves the persisted continuity schema is wrong; if that happens, schema-first changes must land before module/output changes.

### Recommended Scope Adjustment

- **Small scope expansion folded into this story**: reproduce the current `big_fish_long` continuity-owned blocker and absorb the smallest continuity-side prompt/schema hardening if it is the same output-budget path. Splitting that out again would hide the current blocker behind an obsolete short/medium-only reading of the story.
- **Small test-scope expansion folded into this story**: add a new narrow continuity-throughput test file instead of growing `tests/unit/test_continuity_tracking_module.py`.
- **No larger scope expansion recommended**: a first-principles continuity redesign remains Story 112 territory and should stay separate unless the throughput work proves the concept itself is the blocker.

### Implementation Order

#### Task 1 — Extract continuity-throughput seams before adding logic

- **Files**: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`, new narrow unit test file under `tests/unit/`
- **Changes**:
  - extract prompt-context assembly and/or per-scene extraction bookkeeping out of `run_module()` / `_build_continuity_prompt()`
  - create a small seam for testing prompt/state compaction without mocking the entire module end-to-end
- **Impact / risk**: avoids making a 569-line module and 211-line entrypoint worse
- **Done looks like**: prompt-shaping and continuity-scene metrics can be tested in isolation

#### Task 2 — Reproduce and classify the long-form continuity-owned blocker

- **Files**: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`, `src/cine_forge/schemas/continuity.py` only if reproduction proves a schema mismatch
- **Changes**:
  - reproduce the `big_fish_long` continuity failure enough to confirm whether `new_value = null`, silent truncation, or sheer prompt/output volume is the actual continuity-side blocker
  - if the blocker is a continuity prompt/schema mismatch, absorb the smallest safe fix here instead of creating another shell
- **Impact / risk**: any persisted schema change must preserve timeline, UI, and consumer compatibility
- **Done looks like**: the long-case blocker is no longer ambiguous on the continuity side

#### Task 3 — Apply the smallest prompt/output-budget fix first

- **Files**: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`
- **Changes**:
  - tighten the continuity prompt to downstream-needed fields only
  - reduce repeated carry-forward state text where it does not change the continuity judgment
  - explicitly enable truncation surfacing/retry behavior so output-budget failures are visible and recoverable
  - keep model choice unchanged unless the simplified path still fails on verified measurements
- **Impact / risk**: changing prompt shape must not erase required injury / prop / location change signal
- **Done looks like**: the stage produces materially less input/output volume on the short/medium detector cases without losing useful continuity evidence

#### Task 4 — Add focused regression and inspectability coverage

- **Files**: new narrow `tests/unit/` file, `tests/integration/test_continuity_ai_integration.py` only if a real-model regression is needed, `benchmarks/scripts/full_script_throughput_support.py` only if existing run-state surfaces cannot show the before/after continuity deltas cleanly
- **Changes**:
  - add unit tests for prompt compaction, carry-forward summarization, and null change-event handling
  - add the smallest inspectability surface that makes prompt-vs-output tradeoffs visible, preferring module-local or existing run-state data over large benchmark-support churn
- **Impact / risk**: keep `full_script_throughput_support.py` edits surgical if detector output truly needs them
- **Done looks like**: future regressions fail locally and the throughput story no longer hides continuity behind one opaque stage total

#### Task 5 — Re-measure and record the new truth

- **Files**: `docs/evals/registry.yaml`, this story, Story 155 if the follow-up note changes materially
- **Checks / evidence**:
  - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_continuity_tracking_module.py -q`
  - new narrow continuity-throughput unit tests
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `PYTHONPATH=src .venv/bin/python benchmarks/scripts/full_script_throughput_eval.py --fixture-manifest benchmarks/fixtures/full_script_throughput_cases.json --filter-case open_frequency_short --filter-case last_birthday_card_medium --output-prefix benchmarks/results/full-script-throughput-story-159`
  - optional targeted `--filter-case big_fish_long` rerun if Task 2 touched the long-case blocker
- **Mismatch handling**:
  - classify the rerun result as runtime-blocking or non-runtime-blocking with explicit evidence
  - update `docs/evals/registry.yaml` with verified new measurements, date, and git SHA
- **Done looks like**: Story 159 owns a fresh detector-backed before/after result rather than anecdotal speed claims

### Impact Analysis

- **Likely consumers at risk only if the persisted continuity schema changes**: `src/cine_forge/modules/timeline/timeline_build_v1/main.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `ui/src/pages/ContinuityPage.tsx`, and `ui/src/components/EntityTimelineView.tsx`
- **UI verification plan**: scope expanded into `EntityTimelineView.tsx` because the nullable `new_value` fix crosses into the continuity timeline. Static UI checks passed (`pnpm --dir ui run lint`, `pnpm --dir ui run build`), but browser runtime verification was blocked when the Playwright MCP transport stayed closed after `python3 scripts/reset_playwright_mcp.py`; the fallback local Playwright path also was not available because the package is not installed in this worktree.
- **Redundancy plan**: remove any obsolete prompt text, duplicate carry-forward summaries, or ad hoc continuity-throughput notes that survive only because the detector did not explain the hotspot clearly.
- **Human-approval blockers**: none for the planned prompt/output-budget path. The only conditional risk is a persisted schema change if the `new_value = null` issue reproduces; if that becomes necessary, it stays in-bounds but must remain schema-first and compatibility-checked.

## Work Log

- 20260410-2230 — story-created: split Story 155's top successful-stage hotspot into its own follow-up line so continuity optimization does not get buried under unrelated long-form failures. Evidence: `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}` shows `world_building.continuity_tracking` as the top normalized runtime/output hotspot across successful cases. Next step: run `/build-story 159` once the current active focus allows this secondary throughput line to move.
- 20260411-1131 — exploration: Story 159 is buildable and should promote from `Draft` when implementation starts.
  - Evidence: the worktree is clean, `continuity_tracking_v1` has not changed since Story 092, Story 155 still provides the current short/medium baseline, and Story 160 moved the active long-form blocker into `continuity_tracking`.
  - Files likely to change: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`, a new narrow continuity-throughput unit test file, `docs/evals/registry.yaml`, and this story; `src/cine_forge/schemas/continuity.py`, `tests/integration/test_continuity_ai_integration.py`, and `benchmarks/scripts/full_script_throughput_support.py` are conditional depending on reproduction.
  - Files at risk: `timeline_build_v1`, `track_system_v1`, `ContinuityPage.tsx`, and `EntityTimelineView.tsx` consume persisted continuity artifacts directly if the schema moves.
  - Decision docs consulted: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/build-map.md`, `docs/spec.md` (`spec:3`, `spec:8.1`, `spec:8.3`), ADR-003, Stories 011 / 032 / 040 / 092 / 112 / 129 / 155 / 160, and `docs/evals/registry.yaml`.
  - Patterns to follow: prompt-first before model escalation, detector-backed throughput changes, and the repo's newer `fail_on_truncation=True` pattern in `scene_analysis_v1`, `character_bible_v1`, and `location_bible_v1`.
  - Risks / surprises: the hotspot is prompt/output volume, not missing stage reuse; `run_module()` and `_build_continuity_prompt()` are already oversized; the current detector hides internal per-scene continuity call shape; and the latest long-form rerun logged a `new_value = null` schema mismatch against the current non-null `ContinuityEvent.new_value`.
- 20260411-1203 — implementation: extracted continuity-throughput helper seams, tightened the scene prompt/output contract, hardened nullable change-event handling, and kept persisted continuity snapshots usable instead of collapsing them into sparse diffs. Evidence: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` now resolves inputs/model/entity catalogs through helper seams, clips previous-state prompt context, instructs sparse scene-local properties, enables `fail_on_truncation=True`, lowers `max_tokens` to `2400`, and records `throughput` counters on the `continuity_index` metadata; `src/cine_forge/schemas/continuity.py` now allows `ContinuityEvent.new_value = null`; `ui/src/components/EntityTimelineView.tsx` renders nullable change events as `cleared`; `tests/unit/test_continuity_tracking_throughput.py` covers carried-forward state merging, prompt compaction, property clearing, and the new throughput metadata surface. Next step: run the full required check stack and re-measure the detector truth.
- 20260411-1229 — validation-pass: required code checks passed for the touched backend/UI slice, but browser runtime evidence is blocked by tooling rather than product behavior. Evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_continuity_tracking_throughput.py tests/unit/test_continuity_tracking_module.py -q` (pass: `17 passed`), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (pass: `707 passed, 159 deselected, 1 existing warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with 6 pre-existing warnings outside the touched file), and `pnpm --dir ui run build` (pass). Browser status: Playwright MCP failed with `Browser is already in use...`, `python3 scripts/reset_playwright_mcp.py` cleared the stale processes, then the transport stayed closed for the rest of the session; the fallback local Playwright route was unavailable because `playwright` is not installed in this worktree. Next step: record the measured detector deltas and blocker truth in the story + registry.
- 20260411-1255 — detector-reruns: Story 159 now owns fresh short/medium and long-case truth rather than inheriting Story 155/160 notes. Evidence:
  - Short/medium rerun: `benchmarks/results/full-script-throughput-story-159-short-medium-2026-04-11.{json,md}`. Successful-case continuity remains the top normalized hotspot, but the model-facing budget improved from `72295.372 -> 65442.187 ms / 1k words` (`-9.5%`) and `9510.535 -> 8428.378 output tok / 1k words` (`-11.4%`). Per-case continuity deltas: `open_frequency_short` `61.988s -> 54.800s` and `7535 -> 6784` output tokens; `last_birthday_card_medium` `157.010s -> 150.395s` and `24560 -> 21095` output tokens. Persisted artifact bytes increased (`185101 -> 208566` short, `1183030 -> 1321249` medium) because the module now stores merged carried-forward state snapshots; that tradeoff is now explicit instead of hidden.
  - Inspectability surface: `tests/unit/test_continuity_tracking_throughput.py::test_sparse_scene_response_carries_forward_previous_state` asserts `continuity_index["metadata"]["throughput"]` exposes `scene_calls`, `observed_properties`, `carried_forward_properties`, and `change_event_count`, so continuity cost shape is inspectable in produced artifacts rather than only as one stage-total line.
  - Long-case rerun: targeted `big_fish_long` rerun (`output/runs/big_fish_long-world_building-06d8/run_state.json`, `output/runs/big_fish_long-world_building-06d8/pipeline_events.jsonl`, kept project `output/eval-full-script-throughput-big_fish_long-a05f35/`). `analyze_scenes` completed in `847.0068s`, `character_bible` in `144.4212s`, `location_bible` in `102.0051s`, `prop_bible` in `29.2672s`, and `entity_graph` in `11.2613s`, re-confirming the old bible truncation blocker is cleared. `continuity_tracking` then ran with no new `run_state.json`, `pipeline_events.jsonl`, or continuity artifacts for about `14.9` minutes while the process held an open provider HTTPS connection, so the operator terminated the rerun. The prior `new_value = null` schema validation failure did not reappear before termination.
  - Classification: successful-case continuity optimization is **non-runtime-blocking** but not converged; the remaining `big_fish_long` blocker is still **ambiguous** and **runtime-blocking** in `continuity_tracking`, now narrowed to a renewed long-stage stall rather than the old nullable-schema crash.
  - Next step: `/validate` should review whether the new carried-forward-state byte growth is acceptable for Story 159 closure or whether a follow-up state-storage compaction line is needed beside the long-stage stall work.
- 20260411-1436 — validate: reran the required backend/UI/methodology checks in this validation pass and recovered browser evidence via a local Playwright fallback after the MCP transport closed. Evidence:
  - Code checks rerun fresh: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_continuity_tracking_throughput.py tests/unit/test_continuity_tracking_module.py -q` (`17 passed`), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`707 passed, 159 deselected, 1 existing warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with 6 pre-existing warnings outside the touched file), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass with only the existing large-chunk warning), and `pnpm methodology:check` (pass).
  - Browser evidence rerun fresh: `scripts/reset_playwright_mcp.py` cleared the stale Playwright processes, but the MCP transport closed immediately afterward, so validation used a local temporary Playwright harness instead. Representative state came from a normal driver-generated project at `output/story159-ui-validate/`, built from `tests/fixtures/ingest_inputs/open_frequency_short.fountain` through `recipe-mvp-ingest` + `recipe-world-building`; the continuity page loaded cleanly at `http://127.0.0.1:5174/story159-ui-validate/world/continuity` in both desktop and mobile views with no browser console/page errors. Screenshot artifacts: `tmp/validate-browser/story159-continuity-desktop.png` and `tmp/validate-browser/story159-continuity-mobile.png`.
  - Fresh runtime note: the validation-only short project completed `continuity_tracking` in `123.6032s`, which is slower than the Story 159 detector short case and shows that continuity throughput remains sensitive even after the recorded detector win; this run was a browser-enabling acceptance project, not a registry-tracked eval rerun.
  - Structural note: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` is now `741` lines and `run_module()` still spans `159` lines without an approved oversized-method exemption, so the story remains implementation-strong but structurally unfinished in the same module.
  - Next step: keep Story 159 open long enough to either extract the remaining orchestration out of `run_module()` or explicitly approve/document the oversize exception before `/mark-story-done`.
- 20260411-1605 — structure-refactor-revalidate: extracted continuity runtime/prompting helpers into module-local support files so the touched continuity files now respect the repo size rules, then reran the full validation boundary on the current code. Evidence:
  - Structural extraction: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` now only owns the driver entrypoint and public re-exports (`84` lines, `run_module()` = `38` lines). New helper files: `support.py` (`574` lines) for runtime/state bookkeeping and `prompting.py` (`204` lines) for prompt/extraction helpers. A post-refactor size scan found no touched continuity method over `100` lines and no touched continuity file over `600` lines.
  - Fresh checks after the extraction: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`707 passed, 159 deselected, 1 existing warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_continuity_tracking_throughput.py tests/unit/test_continuity_tracking_module.py -q` (`17 passed`), `pnpm --dir ui run lint` (same 6 pre-existing warnings outside touched files), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass with the existing chunk-size warning), and `pnpm methodology:check` (pass).
  - Fresh browser evidence after the extraction: local API + Vite rerun, then desktop/mobile continuity-page verification at `http://127.0.0.1:5174/story159-ui-validate/world/continuity` via a temporary local Playwright harness. Both passed with no console/page errors on the current code. Screenshot artifacts: `tmp/validate-browser/story159-continuity-desktop-rerun.png` and `tmp/validate-browser/story159-continuity-mobile-rerun.png`.
  - Eval note: no registry-tracked detector or promptfoo eval was rerun after this extraction because the change was behavior-preserving refactoring only; the latest measured Story 159 detector truth remains the `2026-04-11` entries already recorded in `docs/evals/registry.yaml`.
  - Next step: `/mark-story-done`.
- 20260411-1645 — marked-done: closed Story 159 after the structural refactor cleared the last validation finding and the story met the close-now boundary. Evidence:
  - Story gates: build complete, validation complete, tasks checked, acceptance criteria satisfied, tenet/doc update checks complete, and eval truth already recorded in `docs/evals/registry.yaml`.
  - Final validation basis: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`707 passed, 159 deselected`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), targeted continuity pytest (`17 passed`), `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:check`, and representative desktop/mobile continuity-page browser verification on `http://127.0.0.1:5174/story159-ui-validate/world/continuity`.
  - Closure note: the remaining long-form continuity stall is explicitly tracked as runtime-blocking follow-up truth, not hidden inside this story's closure.
  - Next step: `/check-in-diff`.
