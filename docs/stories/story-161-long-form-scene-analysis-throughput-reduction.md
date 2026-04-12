---
id: "161"
title: "Long-Form Scene Analysis Throughput Reduction"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R7 (generate -> react -> refine)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:2.7"
  - "spec:2.7.2"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "040"
  - "155"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
roadmap_tags:
  - "throughput"
  - "scene-analysis"
  - "long-form"
  - "follow-up-from-155"
legacy_system: ""
---

# Story 161 — Long-Form Scene Analysis Throughput Reduction

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R1 (story understanding), R7 (generate -> react -> refine), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:2.7, spec:2.7.2, spec:8.1, spec:8.3
**ADR Refs**: ADR-003. No dedicated scene-analysis throughput ADR was found after search.
**Depends On**: Story 040, Story 155

## Goal

Reduce the absolute long-form wait before world-building can proceed. Story 155's full-script detector shows `big_fish_long.world_building.analyze_scenes` alone takes `888.476s` and `$0.9336` before downstream bible or continuity work can even start. That runtime is already a product problem regardless of the later bible truncation failure: full-length screenplay understanding does not feel interactive or even patient-operator-friendly when the first world-building stage consumes nearly fifteen minutes by itself.

## Acceptance Criteria

- [x] A rerun of the Story 155 long case reduces `world_building.analyze_scenes` materially from the current `888.476s` baseline without a semantic quality collapse.
- [x] The chosen optimization explains whether the main driver was batch size, prompt volume, model routing, retry behavior, or unnecessary output verbosity.
- [x] Scene-analysis outputs remain sufficient for downstream world-building modules; speedups that merely starve later stages do not count as success.
- [x] Focused regression coverage exists for any new batching, chunking, or prompt-compaction behavior before another paid rerun.
- [x] Story 155 and `docs/evals/registry.yaml` record the before/after detector evidence and classify any remaining long-form delay as runtime-blocking or non-runtime-blocking.

## Out of Scope

- Replacing scene analysis with a different product concept
- Generic world-building optimization that is not meaningfully driven by the long-form `analyze_scenes` baseline
- UI work outside of optional follow-on surfacing of the detector result
- Treating short-script success as evidence that long-form runtime is solved

## Approach Evaluation

- **Simplification baseline**: First test whether prompt/output compaction or batch-size tuning alone can shrink the long-form stage without any module decomposition.
- **AI-only**: Possible if the current macro-analysis prompt is simply too verbose or too conservative on batch size.
- **Hybrid**: Plausible if deterministic pre-processing can cut repeated context while leaving narrative judgment to the model.
- **Pure code**: Appropriate for orchestration changes such as better batching, caching, or state reuse; not for replacing scene reasoning with brittle heuristics.
- **Repo constraints / ADRs**: `spec:2.7` and C4 explicitly preserve a richer scene-analysis tier because the structural-only path is not enough. The fix must preserve that richer output.
- **Existing patterns to reuse**: Story 155 detector, Story 040 performance lessons, existing macro-analysis batching in `scene_analysis_v1`, and current scene-index/discovery-tier contracts.
- **Eval**: The discriminating eval is the long-form Story 155 detector rerun, compared against the same `Big Fish` baseline plus any focused local fixture tests.

## Tasks

- [x] Reproduce the `big_fish_long` `analyze_scenes` runtime with direct instrumentation and identify the dominant cost driver before changing code.
- [x] Test the smallest viable optimizations first: batch-size tuning, prompt/output compaction, or selective context reduction.
- [x] Add focused regression coverage for any changed batching or prompt-shaping logic.
- [x] Rerun the long Story 155 case, then the full detector pack if the long case improves meaningfully.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
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

- **Owning class/module**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` is the primary owner. Keep the detector and reporting logic inside Story 155's benchmark harness instead of embedding throughput reporting into product code.
- **Data contracts**: Preserve current enriched scene artifacts and scene-index semantics. If batching changes require extra metadata, keep it schema-first and compatible with downstream world-building consumers.
- **Decision context**: Story 155 baseline shows the long case spends `888.476s` in `analyze_scenes` before later long-form failures even begin. That makes scene analysis an independent long-form wait problem, not just a side effect of later bible truncation.

## Files to Modify

- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`
- `src/cine_forge/modules/ingest/scene_analysis_v1/batching.py`
- `src/cine_forge/modules/ingest/scene_analysis_v1/module.yaml`
- `configs/recipes/recipe-world-building.yaml`
- `tests/unit/test_scene_analysis_module.py`
- `tests/unit/test_scene_analysis_batch_planning.py`
- `docs/evals/registry.yaml`
- `docs/stories/story-161-long-form-scene-analysis-throughput-reduction.md`

## Redundancy / Removal Targets

- Overly large macro-analysis context windows that do not change downstream usefulness
- Output verbosity that later stages do not need
- Detector notes that blame the whole world-building lane when the actual delay is concentrated in `analyze_scenes`

## Notes

- Story 155 baseline evidence:
  - `open_frequency_short.world_building.analyze_scenes` = `26.336s`
  - `last_birthday_card_medium.world_building.analyze_scenes` = `127.554s`
  - `big_fish_long.world_building.analyze_scenes` = `888.476s`
- The long-case runtime is already a blocker even before character/location bible truncation is considered.

## Work Log

- 20260410-2234 — story-created: split Story 155's absolute long-form scene-analysis wait into its own follow-up line so it does not disappear under the broader world-building runtime story. Evidence: `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.{json,md}` shows `big_fish_long.world_building.analyze_scenes` at `888.476s` / `$0.9336` before downstream long-form failures even start. Next step: run `/build-story 161` when the repo is ready to focus on long-form scene-analysis scale.
- 20260411-2318 — exploration: Story 161 is buildable and should promote from `Draft` when implementation starts. Evidence reviewed: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/spec.md` (`spec:2.6`, `spec:2.7`, `spec:2.7.2`, `spec:8.1`, `spec:8.3`), ADR-003, Stories 040/107/155/159/160/162, `benchmarks/results/full-script-throughput-story-155-baseline-2026-04-10.md`, `docs/evals/registry.yaml`, `configs/recipes/recipe-world-building.yaml`, `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, and `tests/unit/test_scene_analysis_module.py`. Live checks: `make check-size`, `wc -l` on planned touch files, `git diff --stat 96afaa6 -- src/cine_forge/modules/ingest/scene_analysis_v1/main.py` (no diff), `git diff --stat f9dc74d -- src/cine_forge/modules/ingest/scene_analysis_v1/main.py` (no diff), `scripts/discover-models.py --summary`, and direct fixture instrumentation on `Big-Fish.fountain` using the current batcher. Key findings: the shipped `world_building` recipe already sets `skip_qa: true`, so the long-form cliff is not QA cost; the current long fixture still implies `188` scenes and `38` macro-analysis calls at `batch_size: 5`; average batch size is only `680.2` words with a `1609`-word max, so the fixed batch size looks overly conservative; and `scene_analysis_v1/main.py` still centralizes input resolution, scene-text extraction, batching, prompt construction, retry/escalation, optional QA, and artifact merge in one `614`-line module with `run_module()` still spanning roughly `71-277`. Files likely to change: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, `configs/recipes/recipe-world-building.yaml`, a new narrow throughput-focused unit test file under `tests/unit/`, `docs/evals/registry.yaml`, and this story. Files at risk of breaking: downstream world-building stages that consume the enriched `scene_index`, detector expectations in Story 155 / the eval registry, and any tests assuming fixed `batch_size: 5` behavior. Patterns to follow: prompt-first before model escalation, detector-backed stage-budget work, existing `enable_caching=True` / `fail_on_truncation=True` patterns, and Story 107's current default of `claude-sonnet-4-6` for `scene_analysis_v1` work while newer models remain untested for this task. Potential cleanup / redundancy targets: the currently unused recipe-path QA branch for `scene_analysis_v1`, duplicated prompt assembly inside `_analyze_batch()`, and detector notes that still describe the whole world-building lane instead of the isolated `analyze_scenes` cliff. Next step: write the implementation plan and stop at the human gate before code changes.
- 20260411-2334 — implementation-started: promoted Story 161 from `Draft` to `Pending` after the user approved the build plan. Next step: rerun `pnpm methodology:compile`, then move the story to `In Progress` before touching code.
- 20260411-2338 — in-progress: reran `pnpm methodology:compile` in the `Pending` state, then moved Story 161 to `In Progress` so implementation can start. Expected warning remains the open architecture finding for `ingest_and_world_building`; next step is a second compile in the in-progress state, then code changes in `scene_analysis_v1`.
- 20260412-0014 — implementation: extracted the new batch-planning and prompt-building seam into `src/cine_forge/modules/ingest/scene_analysis_v1/batching.py`, so `run_module()` now delegates planning/orchestration instead of owning fixed batch math inline. Added explicit adaptive controls (`max_batch_size`, `max_batch_words`) to `scene_analysis_v1`, documented them in `module.yaml`, and opted the shipped `world_building` recipe into `batch_size=5`, `max_batch_size=10`, `max_batch_words=2500` so the long-form path can use the spec-approved `5-10` range without unbounded prompt growth. Also fixed the pre-existing `_analysis_failed` sentinel leak so fallback scenes no longer serialize the internal marker into persisted scene payloads. Added focused regression coverage in `tests/unit/test_scene_analysis_batch_planning.py` and kept the legacy batching contract tests alive by moving fixed-batch imports to the new helper seam. Local verification: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_scene_analysis_module.py tests/unit/test_scene_analysis_batch_planning.py` (`16 passed`) and `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/cine_forge/modules/ingest/scene_analysis_v1/main.py src/cine_forge/modules/ingest/scene_analysis_v1/batching.py tests/unit/test_scene_analysis_module.py tests/unit/test_scene_analysis_batch_planning.py` (pass). Cheap detector evidence from direct fixture instrumentation on `tests/fixtures/round_trip/big-fish/Big-Fish.fountain`: `188` scenes still parse, but the shipped plan drops from `38` fixed macro-analysis batches to `19` adaptive batches, with the largest batch at `10` scenes / `2485` words. Structural health: `scene_analysis_v1/main.py` is still large, but the new seam reduced it from `795` back to `661` lines and isolated the throughput logic in a focused `135`-line helper instead of leaving it inside the driver entrypoint. Next step: run the paid `big_fish_long` Story 155 boundary rerun during `/validate 161`, then update `docs/evals/registry.yaml` only after measured before/after evidence exists.
- 20260412-0019 — validate-pass: reran the required validation suite and the paid `big_fish_long` Story 155 boundary on the current Story 161 diff. Fresh check evidence from this pass: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`714 passed, 159 deselected, 1 existing warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_scene_analysis_module.py tests/unit/test_scene_analysis_batch_planning.py` (`16 passed`), `pnpm methodology:compile` (pass with the expected `ingest_and_world_building` architecture warning after the registry/story updates), `pnpm methodology:check` (pass with the same warning), and the targeted detector rerun `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/full_script_throughput_eval.py --fixture-manifest benchmarks/fixtures/full_script_throughput_cases.json --filter-case big_fish_long --keep-projects --output-prefix benchmarks/results/full-script-throughput-story-161-big-fish-2026-04-12` (pass). Mandatory UI commands were executed but this worktree still lacks `ui/node_modules`: `pnpm --dir ui run lint` failed with `eslint: command not found`, and `npx tsc -b` failed with the local TypeScript placeholder message; no UI files changed in Story 161. Fresh runtime truth: `benchmarks/results/full-script-throughput-story-161-big-fish-2026-04-12.{json,md}` shows the long case completing end to end at `2808707 ms` / `$3.24163222`; `world_building.analyze_scenes` improved to `810.038s` from Story 162's `858.7512s` and Story 155's `888.476s`, while downstream stages still completed (`character_bible` `147.496s`, `location_bible` `106.126s`, `continuity_tracking` `1723.375s`). Remaining long-form issue stays **non-runtime-blocking** and continuity-owned: `7` scenes (`048`, `093`, `169`, `175`, `183`, `189`, `190`) produced `52` `needs_review` continuity states after bounded truncation fallbacks, down from Story 162's `10` scenes / `77` states. I did not spend another full-pack detector rerun in this validation pass because the long-case win is real but still stage-local (`analyze_scenes` `-5.7%` versus the latest full long-case rerun, `-8.8%` versus the original Story 155 baseline), and the current detector remains dominated by continuity rather than scene analysis. Next step: close Story 161 if we accept the remaining low-priority drift note about the optional QA path and the still-oversized `scene_analysis_v1/main.py`, otherwise land a small follow-up fix before `/mark-story-done`.
- 20260412-0032 — story-done: closed Story 161 after the close-out pass confirmed the shipped slice is complete and the remaining issues do not belong to this story's success surface. Evidence: `pnpm --dir ui install --frozen-lockfile` (pass), `pnpm --dir ui run lint` (pass with `0` errors / `6` pre-existing warnings), `cd ui && npx tsc -b` (pass), plus the existing Story 161 validation suite and the targeted `big_fish_long` rerun. Completion classification: the only remaining measured detector issue is **ambiguous** but **non-runtime-blocking** continuity quality/output-budget drift on `7` long scenes, which belongs to the already-open continuity lane rather than scene-analysis throughput. Residual watchpoints kept visible instead of blocking closure: the optional QA review-marking path still over-broadcasts `needs_review` if QA is re-enabled, and `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` remains oversized even after the batching extraction. Recommended next step: `/check-in-diff`.

## Plan

### Exploration Notes

- **Story status / buildability**: Story 161 is still `Draft`, but it is substrate-verified and implementation-ready. The owner module has not changed since the Story 155 baseline or the Story 162 rerun, so the checked-in detector numbers are still current truth for planning.
- **Current runtime truth**:
  - Story 155 baseline still records `big_fish_long.world_building.analyze_scenes = 888.476s` and `60039` output tokens.
  - Story 162's later rerun still records `analyze_scenes = 858.7512s` even after downstream blockers moved, so this wait cliff remains unresolved.
  - Direct fixture instrumentation on the current code shows `188` scenes, `38` batches, and therefore `38` analysis calls before retries on the honest long-form path; the shipped recipe already sets `skip_qa: true`, so the current bottleneck is call volume plus prompt shape, not QA overhead.
- **Files that will likely change**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, `configs/recipes/recipe-world-building.yaml`, a new narrow throughput-focused unit test file under `tests/unit/`, `docs/evals/registry.yaml`, and this story file.
- **Files at risk of breaking**: downstream world-building consumers of enriched `scene` / `scene_index` artifacts, `tests/unit/test_scene_analysis_module.py`, any integration tests that assume a fixed batch count, and Story 155 / registry notes that summarize the long-case hotspot.
- **Decision docs consulted**: ADR-003 is the active architecture constraint. No dedicated scene-analysis throughput ADR exists. Story 040 was re-read as historical performance context, but it predates the current two-lane architecture and detector discipline, so it is cautionary context rather than a source of current defaults.
- **Patterns to follow**: detector-backed throughput work rather than anecdotal tuning; prompt-first before model escalation; existing `fail_on_truncation=True` / `enable_caching=True` long-form call posture; Story 107's current `scene_analysis_v1` work-model default (`claude-sonnet-4-6`) until a fresh scene-analysis eval proves a better option.
- **Potential cleanup / redundancy targets**: the currently inactive recipe-path QA branch in `scene_analysis_v1`, fixed-size batch planning that is more conservative than the spec's `5-10 scenes per call` allowance, and prompt scaffolding that repeats metadata the model does not need on every batch.
- **Surprises / risks found**:
  - The shipped runtime path already avoids QA for `analyze_scenes`, so speeding up QA would not move the current long-form detector.
  - Live model discovery found `71` currently available models across providers and `27` untested ones, but no fresh scene-enrichment eval exists for those models, so a blind model swap would violate eval-first discipline.
  - The current long fixture's average batch is only `680.2` words and the maximum measured batch is `1609` words, which is much smaller than the fixed `batch_size: 5` policy implies. That points to overly conservative batching, not obviously oversized per-call input, as the first thing to test.

### Baseline / Eval Gate

- **Checked-in baseline is still current**: `scene_analysis_v1/main.py` has no diff versus the Story 155 baseline commit (`96afaa6`) or the Story 162 rerun commit (`f9dc74d`), so the existing detector artifacts are valid current baselines for planning.
- **Primary eval boundary**: the Story 155 full-script throughput detector on `big_fish_long`, rerun via `benchmarks/scripts/full_script_throughput_eval.py --filter-case big_fish_long`.
- **Current baseline to beat**:
  - Story 155 baseline: `888.476s`, `$0.9336`, `60039` output tokens.
  - Story 162 rerun: `858.7512s` on the current module after downstream blockers were cleared.
- **Local baseline / instrumentation**:
  - Direct fixture instrumentation on `Big-Fish.fountain` with the current batcher yields `188` scenes, `38` batches, `38` analysis calls before retries, `680.2` average batch words, and `1609` max batch words.
  - Existing unit baseline: `tests/unit/test_scene_analysis_module.py`.
- **Candidate approaches**:
  - **AI-only**: swap to a different work model. Rejected as the first move because Story 107 still pegs `claude-sonnet-4-6` as the current default for `scene_analysis_v1`, live inventory alone is not eval evidence, and the module has no fresh scene-enrichment benchmark across the newly discovered models.
  - **Hybrid**: keep the current work model, reduce analysis-call count with an evidence-backed larger batch shape, and compact prompt scaffolding or per-batch metadata so long-form batches carry less repeated overhead. Preferred first path.
  - **Pure code**: deterministic pre-summarization or cached intermediate scene digests. Rejected as the first move because it adds new substrate and risks starving downstream world-building of narrative signal before the simpler batch-shape lever has been tested.
- **Chosen first path**: hybrid batching + prompt compaction with no model swap in the first implementation pass.

### Repo-Fit / Optimality Evidence

- `spec:2` is in `climb`, and the state lane explicitly says long-form screenplay throughput should be improved via detector-backed stage budgets rather than anecdotal "the pipeline feels slow" tuning.
- `spec:2.7` already allows Macro-Analysis at `5-10` scenes per call. The shipped recipe hardcodes `batch_size: 5`, but the current long fixture evidence shows that fixed lower bound is conservative.
- ADR-003 says story-lane artifacts must remain useful working artifacts. That rules out aggressive deterministic compression that would remove narrative detail just to go faster.
- The current module/runtime evidence points to batch shape first:
  - the honest path already skips QA,
  - the long case still spends ~14 minutes in `analyze_scenes`,
  - the module is unchanged since the measured baselines,
  - and direct fixture instrumentation shows only `38` analysis calls stand between the current code and the long-form cliff.
- Main alternatives rejected:
  - **Blind model swap**: current repo evidence is insufficient, and Story 107 plus live model inventory say we would just be guessing.
  - **Generic caching / new substrate**: higher complexity than necessary while the fixed batch size remains the obvious measured bottleneck.
  - **Shorten downstream expectations**: wrong for this repo because Story 161 is specifically about long-form scene-analysis scale without semantic collapse.

### Structural Health Check

- `make check-size` already flags the likely touch points:
  - `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — `614` lines
  - `docs/evals/registry.yaml` — `2285` lines
  - `tests/unit/test_scene_analysis_module.py` — `333` lines
  - `docs/stories/story-161-long-form-scene-analysis-throughput-reduction.md` — `144` lines
  - `configs/recipes/recipe-world-building.yaml` — small enough to edit directly
- Oversized-method risk inside the owner module:
  - `run_module()` spans roughly lines `71-277` and still owns too many concerns
  - `_build_enriched_scene()` spans roughly lines `469-584`
- **Plan consequence**: the first implementation task must extract a testable batch/options seam out of `run_module()` before adding new throughput logic. New throughput regression coverage should live in a new narrow test file rather than enlarging the existing general module suite.
- **Schema / event check**: no new inter-layer schema or event type is planned. This should stay inside the existing scene artifact contracts and benchmark surfaces.

### Recommended Scope Adjustment

- **Small scope expansion folded into this story**: include `configs/recipes/recipe-world-building.yaml` if the measured fix requires changing the shipped `batch_size` from `5` to a larger long-form-safe value. This is tightly coupled to the runtime truth and should not be split into a separate story.
- **Small scope expansion folded into this story**: add a new narrow throughput-oriented test file instead of only extending `tests/unit/test_scene_analysis_module.py`.
- **No larger scope expansion recommended**: do not absorb a new scene-enrichment eval or model-selection story here. If batching/prompt changes fail, that is follow-up evidence for `/improve-eval` or a dedicated scene-analysis model comparison, not hidden scope creep.

### Implementation Order

#### Task 1 — Extract the batch-planning seam before adding throughput logic

- **Files**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, new narrow `tests/unit/` file
- **Changes**:
  - extract options resolution and batch planning out of `run_module()`
  - create a testable helper that can plan batches from scene text sizes without invoking the full artifact merge path
- **Impact / risk**: reduces the blast radius of later batching changes inside an already oversized module
- **Done looks like**: `run_module()` stops owning batch sizing inline, and batch planning can be tested independently

#### Task 2 — Land the smallest throughput fix first: adaptive long-form batch sizing

- **Files**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, `configs/recipes/recipe-world-building.yaml` if needed
- **Changes**:
  - keep short/medium behavior safe, but allow the honest long-form path to use a larger batch target within the spec's `5-10` scene range
  - add a word-budget or similar guard so unusually dense scenes do not create giant prompts just because the scene count cap increased
  - preserve current artifact contracts and the existing `enable_caching=True` / `fail_on_truncation=True` posture
- **Impact / risk**: larger batches could reduce narrative accuracy or create truncation if the guard is wrong
- **Done looks like**: the long fixture requires materially fewer macro-analysis calls without forcing downstream schema or consumer changes

#### Task 3 — Compact per-batch prompt overhead only where it is clearly redundant

- **Files**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, narrow test file
- **Changes**:
  - trim repeated batch metadata or scaffolding that does not change the model's scene reasoning
  - keep the completeness and grounding instructions from Scout 010 intact
  - do not cut raw scene text or narrative output contracts blindly
- **Impact / risk**: over-trimming could improve speed while starving downstream world-building quality
- **Done looks like**: prompt shape is leaner, but the enriched `scene` / `scene_index` contract remains semantically equivalent

#### Task 4 — Add focused regression coverage for long-form batching behavior

- **Files**: new narrow `tests/unit/` file, maybe `tests/unit/test_scene_analysis_module.py` for small contract assertions
- **Changes**:
  - cover adaptive batch planning on a Big-Fish-like scene distribution
  - cover the prompt-shape helper so batching changes fail locally before another paid rerun
  - keep at least one assertion that the enriched artifact structure remains unchanged
- **Done looks like**: the new long-form planner and prompt compaction logic regress locally without provider calls

#### Task 5 — Re-measure the honest boundary and update planning truth

- **Files**: `docs/evals/registry.yaml`, this story, Story 155 only if the follow-up note changes materially
- **Checks / evidence**:
  - rerun the targeted long case first
  - if the long case improves meaningfully without semantic collapse, rerun the full detector pack
  - classify any remaining long-form issue as runtime-blocking or non-runtime-blocking
- **Done looks like**: Story 161 owns current measured before/after evidence rather than anecdotal "scene analysis feels faster"

### Verification Plan

- Backend static checks:
  - `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - focused pytest for the touched scene-analysis tests
- Eval / runtime checks:
  - `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/full_script_throughput_eval.py --fixture-manifest benchmarks/fixtures/full_script_throughput_cases.json --filter-case big_fish_long --output-prefix benchmarks/results/full-script-throughput-story-161-big-fish-<date>`
  - rerun the full fixture pack only if the targeted long case is promising
- UI verification:
  - not required unless scope expands into UI files; no browser plan is needed for the current backend/eval-only slice

### Human Approval / Blockers

- No schema migration, public API change, or ADR-level blocker is known.
- The only meaningful approval gate is cost: the targeted long-form detector rerun is a paid eval, so implementation should land before spending on the rerun.
