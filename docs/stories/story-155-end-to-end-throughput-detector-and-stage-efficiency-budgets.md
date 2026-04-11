---
id: "155"
title: "End-to-End Throughput Detector and Stage Efficiency Budgets"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "vision-level preference: Easy, fun, and engaging"
  - "vision-level preference: Radical transparency"
spec_refs:
  - "spec:2"
  - "spec:2.5"
  - "spec:2.6"
  - "spec:2.7"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "032"
  - "150"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "driver_and_runtime"
  - "ingest_and_world_building"
roadmap_tags:
  - "throughput"
  - "latency"
  - "runtime"
  - "output-budget"
legacy_system: ""
---

# Story 155 — End-to-End Throughput Detector and Stage Efficiency Budgets

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Easy, fun, and engaging, vision-level preference: Radical transparency
**Spec Refs**: spec:2, spec:2.5, spec:2.6, spec:2.7, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane / film-lane boundary). No dedicated throughput ADR was found after search.
**Depends On**: Story 032 (cost tracking substrate), Story 150 (custom runtime detector pattern)

## Goal

Establish an honest throughput requirement for CineForge's currently shipped screenplay-understanding path. The repo already tracks stage durations, token counts, and run cost, but it still lacks a checked-in detector for the question we actually care about: how long does a real screenplay take to become usable, which stages dominate that runtime, and where are we over-spending on output volume or model choice without quality justification? This story creates the detector, the first stage-efficiency budgets, and the measurement discipline so future requests like "optimize total pipeline time" route into a concrete benchmark-and-follow-up workflow instead of vague anecdotal tuning.

## Acceptance Criteria

- [x] A custom runtime detector exists for the current honest screenplay-understanding boundary, using representative checked-in fixtures and including at least one long-screenplay case.
- [x] The detector records total wall-clock runtime plus per-stage duration, input tokens, output tokens, estimated cost, and output-volume evidence so verbosity waste is visible instead of speculative.
- [x] The measured boundary is honest about scope: it distinguishes the currently shipped story-lane path from unfinished film-lane work instead of pretending CineForge's entire ideal pipeline is already benchmarkable end to end.
- [x] Stage-efficiency budgets or target ranges are recorded for the measured boundary, and they are labeled clearly as current budget versus climb goal rather than stop-ship requirements.
- [x] Focused local tests cover manifest parsing, recipe-chain aggregation, and output-volume / budget summary math so harness regressions fail before another paid benchmark run.
- [x] `docs/evals/registry.yaml`, Story 155, and `docs/methodology/state.yaml` all agree on ownership so future optimization work can split into measured follow-up stories instead of one undifferentiated "performance" bucket.

## Out of Scope

- Benchmarking every HTTP endpoint or non-AI CRUD path
- Pretending unfinished film-lane generation/export work is already a stable end-to-end throughput boundary
- Speculative caching, prompt-shortening, or model swaps before the detector proves a bottleneck
- Large UI/dashboard work beyond the minimum needed to inspect the detector output

## Approach Evaluation

- **Simplification baseline**: Existing run artifacts and `cost_tracking.py` already expose stage durations, token counts, and run costs. Reuse that substrate first instead of inventing a parallel telemetry system. The missing piece is a checked-in detector and budget discipline at the full-script boundary.
- **AI-only**: Rejected. This is a measurement/orchestration problem with deterministic source data available. An LLM can summarize results later, but it should not be the source of truth for runtime evidence.
- **Hybrid**: Possible only as a thin layer: deterministic runtime capture plus optional AI-assisted bottleneck summaries. Any recommendation layer must stay downstream of the measured facts.
- **Pure code**: Best fit. A benchmark harness can drive the honest recipe boundary, read `run_state.json` and cost summaries, and emit reproducible reports without changing product behavior.
- **Repo constraints / ADRs**: No dedicated throughput ADR exists yet. ADR-003 matters because the first honest detector boundary should be the story lane that actually ships on import, not a pretend "whole pipeline" finish line that includes unfinished film-lane behavior.
- **Existing patterns to reuse**: Reuse Story 150's runtime-detector pattern, `benchmarks/scripts/runtime_media_validation_eval.py`, existing `run_state.json` timing data, and `src/cine_forge/services/cost_tracking.py` rather than inventing new measurement plumbing by default.
- **Eval**: This story should create a registry-backed custom runtime detector for screenplay throughput. The discriminator is whether the harness can produce repeatable total/runtime/cost/token/output-volume reports and isolate the stages that dominate them.

## Tasks

- [x] Define the first honest throughput boundary for current CineForge product reality, likely `screenplay -> story-lane ready` / `workspace-ready`, and choose representative fixtures including one long screenplay.
- [x] Build the runtime harness and checked-in manifest, reusing existing run-state and cost-tracking substrate wherever possible.
- [x] Capture per-stage duration, token usage, cost, and output-volume evidence. If output-volume evidence is not currently available, land the smallest substrate change needed to expose it.
- [x] Add focused unit coverage for manifest parsing, recipe-chain aggregation, and output-volume / budget summary rendering so the detector can regress locally before paid reruns.
- [x] Register the detector in `docs/evals/registry.yaml` with a clear target, command, result artifact path, and runtime-blocking classification rules.
- [x] Run the baseline, inspect the report, and split the measured hotspots into concrete follow-up stories instead of absorbing multiple optimization bets into one diff.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched in this story; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` not required
- [x] If agent tooling or project instructions are touched: not touched; `make skills-check` not required
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: classified the long-form detector failure as ambiguous and runtime-blocking, then updated `docs/evals/registry.yaml`
- [x] If UI is touched: UI not touched; browser verification not required
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

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: This should live as a new benchmark/runtime harness under `benchmarks/scripts/`, not as more product logic inside the API or driver. Product runtime data should continue to come from the existing run artifacts and cost summaries.
- **Data contracts**: Prefer benchmark-local Pydantic models for manifest, per-recipe summary, stage-efficiency rows, and report output. Product schemas/services should change only if fresh `run_state.json` artifacts cannot expose the minimum token, artifact-ref, and output-volume evidence needed for this detector.
- **File sizes**: `src/cine_forge/services/cost_tracking.py` is already `789` lines, `docs/evals/registry.yaml` is `2149`, and `benchmarks/scripts/real_ai_previz_runtime_eval.py` is `484`. If implementation touches `cost_tracking.py`, keep the edit narrow or extract helpers instead of accreting more logic into an already large file.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, Story 040, Story 149, Story 150, and searched decision docs for a direct throughput ADR. No dedicated throughput ADR exists yet; ADR-003 is the relevant boundary constraint.

## Files to Modify

- `benchmarks/scripts/full_script_throughput_eval.py` — new detector runner for honest screenplay-throughput measurement (`new`)
- `benchmarks/scripts/full_script_throughput_support.py` — support module for manifest/report models, aggregation, and Markdown rendering so the eval runner stays thin (`new`)
- `benchmarks/fixtures/full_script_throughput_cases.json` — checked-in fixture manifest for representative screenplay cases (`new`)
- `tests/unit/test_full_script_throughput_support.py` — focused coverage for manifest parsing, recipe aggregation, and report math (`new`)
- `src/cine_forge/ai/fountain_validate.py` — absorbed fixture-driven substrate fix so representative medium/long screenplay title pages no longer crash normalization before the detector can measure them (`367`)
- `tests/unit/test_fountain_validate_v2.py` — regression coverage for blank metadata keys with indented continuation lines (`new coverage`)
- `docs/evals/registry.yaml` — register detector target, result paths, and latest measurements (`2149`)
- `src/cine_forge/services/cost_tracking.py` — only if existing run summaries lack output-volume evidence (`789`)
- `docs/stories/story-155-end-to-end-throughput-detector-and-stage-efficiency-budgets.md` — keep the plan, work log, and closure truth aligned (`this file`)

## Redundancy / Removal Targets

- Ad hoc "the pipeline feels slow" tuning without a reproducible detector
- One-off shell timing scripts that are not registered or fixture-backed
- Prompt/output verbosity expansions that survive only because nobody measured their cost against quality

## Notes

- This is deliberately not the repo's top active focus. It is a standing secondary requirement that should stay visible while the broader pipeline is still being built.
- The first measured boundary should start where CineForge already ships honest value today: the surfaced `Break Down Script` -> `Deep Breakdown` path (`mvp_ingest` followed by `world_building`) that turns a fresh screenplay into current story-lane readiness. Film-lane and final generation throughput can layer on later as those boundaries stabilize.
- The fixture pack should not anchor on one tiny script. Use a short control plus at least one medium and one long checked-in screenplay so stage budgets are not inferred from `open_frequency_short` alone.
- The detector should treat verbosity as a first-class performance input. If a stage produces materially more output than downstream consumers need, that is a quality/cost/runtime problem, not just a prompt-style preference.
- The first full baseline exposed one tightly coupled substrate bug and one real long-form blocker:
  - representative medium/long fixtures initially crashed in `script_normalize_v1` because `clean_fountain_metadata()` mishandled blank metadata keys like `Contact:` / `Notes:` when the value lived on indented continuation lines
  - after that fix, the long `Big Fish` case still failed honestly in `character_bible` and `location_bible` with `LLM output truncated due to max token limit`, which remains runtime-blocking and is now split into Story 160

## Plan

### Baseline / Eval Gate

- No registered screenplay-throughput detector exists yet. `docs/evals/registry.yaml` has no Story 155 entry today, so the current baseline is "missing eval substrate," not a stale score to preserve.
- Historical evidence exists but is not sufficient as the detector baseline. The Liberty Church production snapshot captures old `mvp_ingest` (`844.19s`) and `world_building` (`763.21s`) runs, but that snapshot predates current `run_state.json` fields like `stage_order` and token totals, so it is context only, not the benchmark source of truth.
- The honest product boundary to measure is the surfaced story-lane path a fresh operator takes today:
  - `mvp_ingest` (`Break Down Script`)
  - `world_building` (`Deep Breakdown`)
  - success = the project reaches current story-lane readiness for scene/world exploration, not unfinished film-lane generation
- Candidate approaches:
  - **AI-only**: rejected. This is deterministic runtime/cost/artifact measurement.
  - **Hybrid**: unnecessary except for optional future bottleneck narration after the detector exists.
  - **Pure code**: chosen. The repo already persists run timings, token counts, cost, and artifact refs; the missing piece is a checked-in harness and report shape.

### Repo-Fit / Optimality Evidence

- `spec:2` explicitly owns "quickly enough to start creative work," and `spec:8` says throughput/output-volume optimization must be driven by runtime detectors and measured stage budgets rather than anecdotal tuning.
- ADR-003 and the UI walkthrough runbook both reinforce the same boundary: CineForge currently surfaces a two-step story lane before film-lane work. Measuring only `mvp_ingest` would undercount the real operator path; measuring film-lane generation would overclaim shipped capability.
- Reuse the existing benchmark pattern from `benchmarks/scripts/runtime_media_validation_eval.py` and the extracted-support pattern from Story 150's `real_ai_previz_runtime_eval.py` / `real_ai_previz_runtime_support.py`. Start split rather than waiting for a new 500-line harness to justify extraction.
- Default to benchmark-local aggregation over product-code changes. Fresh runs already persist `duration_seconds`, `cost_usd`, `input_tokens`, `output_tokens`, and artifact refs per stage. The harness should derive output-volume evidence locally from stage tokens plus artifact counts / bytes before touching `src/cine_forge/services/cost_tracking.py`.

### Structural Health Check

- `make check-size` confirms the main risk files already exceed the repo thresholds:
  - `src/cine_forge/services/cost_tracking.py` — `789`
  - `docs/evals/registry.yaml` — `2149`
  - `benchmarks/scripts/real_ai_previz_runtime_eval.py` — `484`
- Plan consequence:
  - keep `full_script_throughput_eval.py` thin and push manifest/report math into `full_script_throughput_support.py`
  - avoid product-code edits unless fresh benchmark runs prove `run_state.json` is missing the needed evidence
  - keep registry edits surgical and evidence-backed
- No new inter-layer product contract or event type should be added unless the harness proves benchmark-local parsing is impossible.

### Recommended Scope Adjustment

- Small, tightly coupled scope expansion absorbed here:
  - add focused unit tests for the new benchmark support layer
  - include a medium-screenplay fixture alongside the short and long cases so stage budgets are not anchored to one tiny control and one pathological max-length script
- No UI work is planned. If implementation stays benchmark-only, browser verification is not part of this story's acceptance path.

### Implementation Order

1. **Lock the measured boundary and fixture pack**
   - Files: `benchmarks/fixtures/full_script_throughput_cases.json`, this story
   - Change: define cases for the current surfaced path (`mvp_ingest` then `world_building`) using checked-in screenplay fixtures:
     - short control: `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
     - medium screenplay: `tests/fixtures/round_trip/the-last-birthday-card/The-Last-Birthday-Card.fountain`
     - long screenplay: `tests/fixtures/round_trip/big-fish/Big-Fish.fountain`
   - Done looks like: the manifest documents which recipe chain runs for each case and why that boundary is the honest current product path.

2. **Build the support-first throughput harness**
   - Files: `benchmarks/scripts/full_script_throughput_support.py`, `benchmarks/scripts/full_script_throughput_eval.py`
   - Change: seed a fresh project per case, run the recipe chain, read fresh `run_state.json` outputs, and emit JSON/Markdown with:
     - per-recipe and total wall-clock runtime
     - per-stage duration, input tokens, output tokens, and cost
     - output-volume evidence from artifact counts plus artifact byte sizes/line counts where meaningful
     - stage-efficiency budget labels (`current observed`, `climb target`)
   - Repo-fit choice: use raw run-state + artifact refs as the source of truth first; only fall back to `CostTrackingService` or product-code edits if fresh runs prove the benchmark cannot derive the needed evidence cleanly.
   - Done looks like: one filtered case can run end-to-end and write stable `.json` / `.md` reports.

3. **Add focused local regression coverage**
   - Files: `tests/unit/test_full_script_throughput_support.py`
   - Change: cover manifest parsing, recipe-chain aggregation, output-volume calculations, and budget/report summary math using the same direct-import benchmark-test pattern already used by `tests/unit/test_previz_usefulness_report.py` and `tests/unit/test_real_ai_previz_runtime_support.py`.
   - Done looks like: harness math regresses locally without paid model calls.

4. **Register the detector and capture the first real baseline**
   - Files: `docs/evals/registry.yaml`, this story, optionally `docs/methodology/state.yaml` only if ownership wording proves insufficient
   - Change:
     - add the new custom eval entry and command
     - run a short pilot first, then the full fixture pack if the harness shape is sound
     - record measured scores with `git_sha`, date, result paths, and runtime-blocking notes
     - classify the first hotspot follow-ups instead of burying optimization ideas inside Story 155
   - Risk: this step requires a working project Python environment and provider credentials. In the current worktree, `.venv` is absent and bare `python3` is missing repo dependencies (`yaml`, `dotenv`, `pydantic`, `rapidfuzz`), so environment bootstrap is a prerequisite before the paid baseline run.

5. **Redundancy and docs pass**
   - Files: this story plus any touched docs
   - Change: remove or explicitly deprecate ad hoc timing commands/notes if the detector replaces them, keep the story/work log aligned with the measured hotspot follow-ups, and rerun `pnpm methodology:compile` only if canonical planning inputs change.
   - Done looks like: Story 155 owns the throughput detector cleanly and future optimization work has concrete measured homes.

## Work Log

- 20260410-1036 — setup: Created the throughput/efficiency requirement as Story 155 and anchored it to `spec:2` + `spec:8` instead of a generic performance bucket. Evidence: `spec:2` already owns "quickly enough to start creative work," `spec:8` already owns cost/speed/model tradeoffs, Story 150 already proves the custom runtime-detector pattern, and the repo already tracks stage durations plus token counts in `cost_tracking.py`. Next step: when this line is promoted, run `/build-story 155` to lock the first honest screenplay-throughput boundary and fixture set.
- 20260410-1829 — exploration: confirmed Story 155 is buildable and narrowed the honest boundary to the surfaced story-lane path, not just `mvp_ingest` in isolation. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, ADR-003, Story 032, Story 150, `configs/recipes/recipe-mvp-ingest.yaml`, `configs/recipes/recipe-world-building.yaml`, `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, `ui/src/lib/chat-action-state.ts`, `src/cine_forge/api/run_orchestrator.py`, the current benchmark scripts, and `make check-size`. Files likely to change: new benchmark eval/support scripts, a fixture manifest, a focused benchmark-unit test file, `docs/evals/registry.yaml`, and this story; `src/cine_forge/services/cost_tracking.py` is only a fallback if fresh run-state artifacts prove insufficient. Files at risk if touched: `src/cine_forge/services/cost_tracking.py` (`789`) and `docs/evals/registry.yaml` (`2149`). Patterns to follow: Story 150's extracted benchmark harness shape and direct-import benchmark unit tests. Surprise/risk: the current worktree has no `.venv`, and bare `python3` is missing repo dependencies (`yaml`, `dotenv`, `pydantic`, `rapidfuzz`), so environment bootstrap is a prerequisite before running the first paid baseline. Next step: human review of the plan before implementation.
- 20260410-1925 — harness-implementation: bootstrapped `.venv`, added the new screenplay-throughput manifest/support/eval runner, and locked benchmark-local output-volume math before any paid baseline run. Evidence: new `benchmarks/scripts/full_script_throughput_eval.py`, `benchmarks/scripts/full_script_throughput_support.py`, `benchmarks/fixtures/full_script_throughput_cases.json`, and `tests/unit/test_full_script_throughput_support.py`; `.venv/bin/python -m py_compile benchmarks/scripts/full_script_throughput_eval.py benchmarks/scripts/full_script_throughput_support.py tests/unit/test_full_script_throughput_support.py` (pass); `.venv/bin/python -m ruff check benchmarks/scripts/full_script_throughput_eval.py benchmarks/scripts/full_script_throughput_support.py tests/unit/test_full_script_throughput_support.py` (pass); `.venv/bin/python -m pytest tests/unit/test_full_script_throughput_support.py -q` (3 passed). Next step: run a short paid pilot to verify the boundary and report shape before the full pack.
- 20260410-2054 — substrate-fix: the first full-pack attempt exposed a deterministic normalization bug on representative medium/long fixtures, so Story 155 absorbed the smallest honest fix instead of downgrading the fixture pack. Evidence: `last_birthday_card_medium` and `big_fish_long` both failed in `script_normalize_v1` before any model call with `IndexError: list index out of range`; traceback pinned the error to `clean_fountain_metadata()` in `src/cine_forge/ai/fountain_validate.py`, where indented title-page continuation lines after blank `Contact:` / `Notes:` keys were misclassified as screenplay body. Fix landed in `src/cine_forge/ai/fountain_validate.py` with regression coverage in `tests/unit/test_fountain_validate_v2.py`; `.venv/bin/python -m ruff check src/cine_forge/ai/fountain_validate.py tests/unit/test_fountain_validate_v2.py` (pass); `.venv/bin/python -m pytest tests/unit/test_fountain_validate.py tests/unit/test_fountain_validate_v2.py tests/unit/test_full_script_throughput_support.py -q` (17 passed). Next step: rerun the full throughput baseline on the intended short/medium/long pack.
- 20260410-2225 — baseline-and-split: completed the first honest short/medium/long story-lane baseline, registered the detector, and split the resulting hotspots into concrete follow-up stories instead of hiding them inside Story 155. Evidence: pilot artifact `benchmarks/results/full-script-throughput-story-155-pilot-2026-04-10.{json,md}` plus full baseline `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}`. Result: `open_frequency_short` succeeded at `142628 ms` / `$0.1741`; `last_birthday_card_medium` succeeded at `368853 ms` / `$0.5481`; `big_fish_long` reached `world_building.analyze_scenes` at `888.476s` / `$0.9336`, then `character_bible` and `location_bible` failed with `LLM output truncated due to max token limit`, making the long-form path **runtime-blocking**. Successful-case hotspot truth: `continuity_tracking` is the top normalized runtime/output hotspot, `analyze_scenes` is the long-form absolute wait cliff, and long-form bible generation remains blocked by output-budget ambiguity. Follow-up stories created: Story 159 (`continuity_tracking` throughput/output budgets), Story 160 (long-form character/location bible truncation recovery), and Story 161 (long-form scene-analysis throughput reduction). Next step: run the full project validation suite and regenerate methodology surfaces before handing off to `/validate`.
- 20260410-2241 — validation-and-handoff: finished the build-phase validation and repaired the detector's methodology lineage so the generated planning surfaces reflect the new eval honestly. Evidence: `make test-unit PYTHON=.venv/bin/python` (pass: `699 passed, 159 deselected, 1 warning` from an existing unknown `acceptance` pytest mark), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts` (pass), `pnpm methodology:compile` (pass), and `pnpm methodology:check` (pass). Registry alignment fix: `full-script-throughput` now declares `spec:2`, `spec:3`, and `spec:8`, matching Story 155 plus follow-up Stories 159/160/161. Remaining blocker truth: the long `Big Fish` detector result is still **ambiguous** and **runtime-blocking** because `analyze_scenes` spends `888.476s` before `character_bible` and `location_bible` both truncate on output limits. Next step: `/validate` to review the detector outcome and decide whether Story 159, 160, or 161 should move first.
- 20260410-2312 — validate-pass: reran the validation suite from scratch against the local delta and confirmed the implementation is complete enough to close. Evidence rerun in this pass: `make test-unit PYTHON=.venv/bin/python` (pass: `699 passed, 159 deselected, 1 existing warning`), `.venv/bin/python -m ruff check src/ tests/` (pass), `.venv/bin/python -m pytest tests/unit/test_full_script_throughput_support.py tests/unit/test_fountain_validate.py tests/unit/test_fountain_validate_v2.py -q` (pass: `17 passed`), `pnpm methodology:compile` (pass), and `pnpm methodology:check` (pass). Validation caveat: mandatory UI commands were executed but the local environment lacks `ui/node_modules`, so `pnpm --dir ui run lint` failed with `eslint: command not found` and `npx tsc -b` failed because local TypeScript is not installed; no UI files changed in Story 155. Review outcome: acceptance criteria still hold, no remaining implementation gaps were found, and the prior long-form detector failure remains correctly classified as **ambiguous** + **runtime-blocking** follow-up work already split into Stories 159/160/161. Next step: `/mark-story-done`.
- 20260410-2321 — story-done: closed Story 155 after build + validation confirmed the shipped slice is complete and the remaining runtime-blocking long-form issues already have explicit follow-up homes. Evidence: Story status moved to `Done`; workflow gates are all checked; detector artifacts live in `benchmarks/scripts/full_script_throughput_{eval,support}.py`, `benchmarks/fixtures/full_script_throughput_cases.json`, and `benchmarks/results/full-script-throughput-story-155-*.{json,md}`; methodology surfaces were regenerated after closure so generated views match story reality. Recommended next step: `/check-in-diff`.
- 20260411-0039 — Story-160-follow-up-truth: Story 160 reran the detector on `big_fish_long` and cleared the original bible truncation blocker without changing the detector boundary. Evidence: `output/runs/big_fish_long-world_building-1a9d/run_state.json` and `output/runs/big_fish_long-world_building-1a9d/pipeline_events.jsonl` show `character_bible` completing in `149.6905s` and `location_bible` in `103.0185s` after logging that discovery-backed second-pass adjudication was skipped; the prior `LLM output truncated due to max token limit` failure no longer occurs. Remaining blocker truth moved downstream: `continuity_tracking` logged a schema validation issue (`entity_states.*.change_events.*.new_value = null`) and then hung with no run-state/event updates for roughly 26 minutes before the operator stopped the stuck rerun. Next step: keep Story 160 scoped as resolved bible recovery and route the remaining long-case runtime-blocking truth to Story 159.
- 20260411-1255 — Story-159-follow-up-truth: Story 159 reran the short/medium detector subset and then re-probed `big_fish_long` on the current continuity code. Evidence: `benchmarks/results/full-script-throughput-story-159-short-medium-2026-04-11.{json,md}` shows the successful-case continuity hotspot tightening from `72295.372 -> 65442.187 ms / 1k words` and `9510.535 -> 8428.378 output tok / 1k words`, while continuity still remains the top normalized runtime hotspot. Long-case evidence: `output/runs/big_fish_long-world_building-06d8/run_state.json` and `output/runs/big_fish_long-world_building-06d8/pipeline_events.jsonl` show `analyze_scenes` completing in `847.0068s`, `character_bible` in `144.4212s`, and `location_bible` in `102.0051s`; `continuity_tracking` then produced no new run-state/event writes or continuity artifacts for about `14.9` minutes before the operator terminated the rerun. The old nullable-schema error did not recur, so Story 159 now owns a narrower but still **ambiguous** + **runtime-blocking** long-case continuity stall, while the successful-case optimization remains **non-runtime-blocking** and detector-backed.
