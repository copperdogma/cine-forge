---
id: "208"
title: "Gemini 3.6 Flash and 3.5 Flash-Lite Model-Slot Eval Refresh"
status: "In Progress"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:3"
  - "spec:7"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
  - "204"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
  - "C5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
  - "generation_and_visualization"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "gemini-3.6-flash"
  - "gemini-3.5-flash-lite"
  - "google"
legacy_system: "Cross-Cutting"
---

# Story 208 - Gemini 3.6 Flash and 3.5 Flash-Lite Model-Slot Eval Refresh

**Priority**: High
**Status**: In Progress
**Ideal Refs**: R1 (story understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:3, spec:7, spec:8
**ADR Refs**: ADR-001 (Shared Entity Extraction Library; eval-first model assignment), ADR-003 (Film Elements; model improvements reduce scaffolding)
**Depends On**: Story 035, Story 204

## Goal

Evaluate Google `gemini-3.6-flash` and `gemini-3.5-flash-lite` as CineForge text and multimodal reasoning challengers on the maintained Gemini model-slot surfaces. Measure whether either model improves screenplay understanding, entity discovery, script-bible synthesis, QA safety, or director-facing frame reasoning at compelling latency and cost. Do not change defaults from launch claims alone.

## Eval Ladder Context

- **Root / parent need**: `spec:8` requires evidence-backed model-slot decisions; C2 tests whether QA can shrink; C3 tests whether one model can replace tiered routing; C5 tests whether role/modality specialization can shrink.
- **Parent evals**: maintained Promptfoo tasks for `config-detection`, `scene-extraction`, `scene-enrichment`, `entity-discovery`, `script-bible`, `qa-pass`, and `video-understanding`. The latter six were most recently used for Gemini 3.5 Flash in Story 204; config detection is included because Gemini Flash currently owns that production slot.
- **Measured trigger**: live discovery on 2026-07-21 confirmed both exact API IDs are callable. `gemini-3.6-flash` is untested; `gemini-3.5-flash-lite` was falsely labeled tested because fuzzy registry matching confused it with `gemini-3.5-flash`.
- **Child eval / baseline**: add both models to the existing task configs, run only those providers with no cache, save raw evidence, and compare quality, latency, and cost with current registry leaders and runtime defaults.

## Acceptance Criteria

- [x] Live discovery and official pricing/model-contract evidence are recorded before the full paid runs.
- [x] Discovery matching distinguishes Flash from Flash-Lite within the same Gemini version and has regression coverage.
- [x] Both exact model IDs run on the seven maintained, default-driving Gemini comparison surfaces without changing prompts, scorers, goldens, or production defaults.
- [x] Raw Promptfoo results are saved under `benchmarks/results/`.
- [x] Every significant mismatch is classified as model-wrong, golden-wrong, or ambiguous, with runtime/default implications.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, and result file for every run.
- [x] After explicit user approval, `script_bible_v1` adopts Gemini 3.5 Flash-Lite in both its manifest and direct-call runtime fallback, with regression coverage preventing drift.
- [x] Focused checks, full unit tests, lint, YAML/JSON loads, methodology checks, compromise checks, and `git diff --check` pass.

## Out of Scope

- Changing production defaults without a clear maintained quality, latency, and cost win plus explicit user approval.
- Retuning prompts, scorers, or hand-curated goldens to help either model.
- Running image/video generation models or creating a new eval surface.
- Running the full 20-clip video suite before a model clears the six-anchor pilot floor.
- Committing or pushing changes.

## Approach Evaluation

- **Simplification baseline**: direct single-model calls are the baseline. If one subject clears all maintained bars, C2/C3/C5 pressure may shrink; otherwise existing specialization remains justified.
- **AI-only**: run the exact subjects on existing reasoning tasks; this directly measures the requested capability.
- **Hybrid**: deterministic Python scorers plus the maintained Opus rubric judge verify structure and semantics while pricing extraction provides value evidence.
- **Pure code**: limited to provider configuration, official pricing tables, discovery matching, regression tests, result extraction, and registry bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment. ADR-003 allows model improvements to remove scaffolding only after measured evidence. C2, C3, and C5 remain `hold` until their detectors pass.
- **Existing patterns to reuse**: Stories 204 and 207, `scripts/discover-models.py`, existing Gemini pricing maps, the seven Promptfoo task configs, and `docs/evals/registry.yaml`.
- **Eval**: the seven maintained tasks already distinguish the relevant behavior; no scorer or golden changes are expected. Character extraction is a conditional follow-up only if the core suite shows an adoption-quality win.

## Tasks

- [x] Run live discovery, inspect prior Gemini evaluation evidence, relevant methodology state, ADR-001, ADR-003, and structural-size baseline.
- [x] Record official model/pricing facts and add any required pricing support.
- [x] Fix same-family Flash versus Flash-Lite discovery matching with regression coverage.
- [x] Add both model lanes to the seven maintained Promptfoo configs.
- [x] Run the targeted no-cache eval suite and save raw result JSON.
- [x] Extract metrics, inspect outputs, classify mismatches, and update `docs/evals/registry.yaml` and the story work log.
- [x] Refresh `docs/evals/models-available.yaml` after registry evidence exists and decide whether any default change is warranted.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint for touched Python files.
  - [x] UI not touched; UI lint and TypeScript checks still passed, while browser verification is not applicable.
- [x] If story metadata changes: `pnpm methodology:compile` and `pnpm methodology:check`.
- [x] Run `/improve-eval` equivalent mismatch investigation; classify all mismatches and update `docs/evals/registry.yaml`.
- [x] Search all docs and update any related to what was touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Benchmark work is additive and does not mutate user project data.
  - [x] **T1 - AI-Coded:** Provider labels, result names, registry notes, and work log are explicit.
  - [x] **T2 - Architect for 100x:** No workaround or default is added from launch claims alone.
  - [x] **T3 - Fewer Files:** Existing provider, pricing, benchmark, and registry seams are reused.
  - [x] **T4 - Verbose Artifacts:** Raw results and classification notes preserve the decision evidence.
  - [x] **T5 - Ideal vs Today:** The new subjects explicitly test whether current model scaffolding can shrink.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: discovery stays in `scripts/discover-models.py`; runtime/eval cost estimates stay in existing pricing tables; Promptfoo task YAML owns subject lanes; the registry owns measured truth.
- **Data contracts**: no application-layer contract changes. Both subjects use the existing Google provider and current Promptfoo result shapes.
- **File sizes**: `src/cine_forge/ai/llm.py` is an existing 987-line large file and receives only pricing rows; `scripts/discover-models.py` is 856 lines and receives a narrow matcher fix. No method is expanded past the architectural limit and no new responsibility is added.
- **Decision context**: reviewed ADR-001, ADR-003, Story 204, Story 207, current registry targets, methodology state, and build map. No new ADR is needed because this is measurement within established provider/eval seams.

## Files to Modify

- `scripts/discover-models.py` (856 lines) and `tests/unit/test_discover_models_xai.py` (141 lines) - correct and cover same-family tier-name matching.
- `src/cine_forge/ai/llm.py` (987 lines) and `scripts/extract-eval-metrics.py` (365 lines) - add official pricing if absent.
- `benchmarks/tasks/{config-detection,scene-extraction,scene-enrichment,entity-discovery,script-bible,qa-pass,video-understanding}.yaml` (147-306 lines) - add two filtered subject lanes.
- `benchmarks/results/*gemini36flash*2026-07-21.json` and `*gemini35flashlite*2026-07-21.json` - raw scored evidence.
- `docs/evals/registry.yaml` (3432 lines) and `docs/evals/models-available.yaml` (601 lines) - durable measured/discovery truth.
- `docs/stories/story-208-gemini-36-flash-and-35-flash-lite-model-slot-eval-refresh.md` - scope, evidence, and decision.

## Redundancy / Removal Targets

- No runtime path should become redundant from benchmark-only evidence. If discovery's substring matcher cannot remain safely generic, replace the faulty comparison rather than adding a compatibility shim.

## Notes

- UI is untouched, so browser verification is not applicable.
- Full-project/root Ideal evals are deferred because this is a model-slot refresh; the maintained parent tasks are the comparable decision surfaces.

## Result and Recommendation

| Eval | Gemini 3.6 Flash | Gemini 3.5 Flash-Lite | Decision |
|---|---:|---:|---|
| Config detection | 0.6799 / 14.4s / $0.0149 | 0.8195 / 2.8s / $0.0036 | Keep Gemini 3 Flash (0.953). |
| Scene extraction | 0.7675 / 35.5s / $0.0217 | 0.8142 / 5.5s / $0.0070 | Keep GPT-5.2 (0.925). |
| Scene enrichment | 0.8792 / 7.9s / $0.0043 | 0.8717 / 1.4s / $0.0011 | Keep Sonnet 4.6 (0.959 verified). |
| Entity discovery | 0.9200 / 11.4s / $0.0098 | 0.9200 / 1.3s / $0.0023 | Both trail the 0.93 target and cheaper/current lanes. |
| Script bible | 0.8850 / 21.2s / $0.0195 | 0.9100 / 6.1s / $0.0049 | 3.5 Flash-Lite cleared every target twice and is adopted for `script_bible_v1`. |
| QA pass | 0.5813 / 5.7s / $0.0038 | 0.5950 / 1.6s / $0.0014 | Invalid comparison: the supposed good golden is materially wrong. |
| Video understanding | 0.5884 / 8.4s / $0.0115 | 0.5095 / 2.2s / $0.0027 | Invalid for adoption: mixed model misses plus materially wrong symbolic-frame targets. |

The script-bible adoption is based on two no-cache 3.5 Flash-Lite runs: `0.95165` at `5650 ms` / `$0.0054`, then `0.9100` at `6074 ms` / `$0.0049`; both independently clear the `0.90`, `30s`, and `$0.01` gates. The mean is `0.930825`, `5862 ms`, and `$0.00515`. Compared with the previous Gemini 2.5 Flash-Lite registry lane (`0.885`, `8047 ms`, `$0.0012`), it buys a meaningful quality and latency improvement for about $0.004 more on a once-per-project call. The user explicitly approved adopting it on 2026-07-21; both the module manifest and direct-call runtime fallback now select `gemini-3.5-flash-lite`.

Gemini 3.6 Flash does not win any measured slot. Its apparently poor QA result is actually favorable but uncalibrated evidence: both new Gemini models correctly rejected a fixture that the current golden incorrectly labels good. The fixture changes the AirTag location and discovery timing and omits the three thugs and gunfight. The neon and muzak video cases likewise use byte-identical symbolic frames while their targets demand absent motion and objects. Correcting these maintained truth surfaces is a separate, coherent follow-up requiring approval; this story preserves the raw results and excludes those contaminated scores from adoption decisions.

Official GA contract recorded for both exact model IDs: text/image/video/audio/PDF input, text output, `1,048,576` input tokens, `65,536` output tokens, and minimal/low/medium/high thinking. Standard paid prices are `$1.50` input / `$7.50` output per million tokens for 3.6 Flash and `$0.30` / `$2.50` for 3.5 Flash-Lite. Promptfoo `0.121.1` did not yet carry these prices, so the task configs and local estimator use explicit official rates.

## Plan

1. **Make discovery and pricing trustworthy**: fix the Flash/Flash-Lite false match, add focused regression coverage, and record official prices in the existing cost maps.
2. **Wire the bounded comparison**: add both exact IDs to the seven maintained task configs without changing prompts, scorers, goldens, or judge settings.
3. **Measure and classify**: run each subject only, no-cache; extract score/latency/cost; manually inspect every failing output and classify runtime impact.
4. **Record and verify**: update registry/cache/story, run focused and full checks, regenerate methodology surfaces, and report an explicit adopt/skip decision.

## Work Log

20260721-1706 - discovery-and-plan: the canonical checkout was one commit behind `origin/main` and contained an unrelated `docs/deploy-log.md` edit, so work moved to a clean `codex/gemini-36-35-eval-20260721` worktree based on `f5a3ffb`. Live discovery found both exact Google IDs with all provider keys available. It correctly marked `gemini-3.6-flash` new but falsely marked `gemini-3.5-flash-lite` tested because the registry contains Gemini 3.5 Flash. Reviewed the Ideal/spec methodology lane, C2/C3/C5 hold state, ADR-001, ADR-003, Stories 204/207, current benchmark configs, and `make check-size`. The approved bounded plan is to reuse seven maintained Gemini lanes, leave prompts/scorers/goldens/defaults unchanged, and decide from quality, latency, cost, and mismatch evidence.

20260721-2329 - implementation-and-measurement: added exact variant-aware discovery matching plus regression coverage, official GA pricing in the existing runtime/result estimators, and both subjects to seven maintained task configs. The live API accepted both exact IDs. All targeted runs completed and raw JSON was retained, including a second no-cache confirmation of the only potential win, 3.5 Flash-Lite script bible. No prompts, scorers, goldens, or runtime defaults changed. An initial combined provider-filter attempt matched zero providers and was discarded. Login-shell key reloading then caused rejected authentication attempts; those artifacts were overwritten by valid runs after using the repository key wrapper without a login shell. A delegated video run accidentally started 20 cases and was stopped at 19/20 without producing an artifact; the valid retained result is the intended six-anchor run. These calls are wasted spend, not benchmark evidence.

20260721-2340 - classification-and-decision: registry rows now preserve score, latency, estimated cost, base SHA, raw artifact, classification, and runtime implication for all 14 model/eval combinations. Gemini 3.6 Flash is rejected for every slot. Gemini 3.5 Flash-Lite is rejected for six measured slots and recommended only for `script_bible_v1`, where two runs independently cleared all gates. Manual evidence review reclassified both QA false negatives as golden-wrong and found material golden/rubric contamination in the symbolic video fixtures; those scores are not used as capability evidence. Refreshed the live model cache after registry evidence existed. No existing runtime path became redundant; a future QA/video truth-surface repair is recommended but intentionally not absorbed into this model-refresh story.

20260721-2350 - validation: no material implementation defect was found in the local diff. Fresh gates passed: `916` unit tests (`186` deselected; one pre-existing unknown-mark warning), Ruff across `src/` and `tests/`, UI lint and TypeScript build after installing the clean worktree's locked UI dependencies, all touched YAML and Gemini result JSON loads, compromise checks, methodology compile/check, and `git diff --check`. UI/browser verification is not applicable because no UI source changed. `codex review --uncommitted` was attempted but unavailable because installed Codex `0.143.0` cannot call configured `gpt-5.6-sol`; the main-thread review plus two independent result-review packets found no code defect. Existing methodology warnings remain for due architecture audits and a stale UI scout; neither was introduced here. `/learning-review` was considered because of the command retries and surprising golden failures, but no generic candidate is warranted: the existing artifact-first and mismatch-classification rules caught both, while the needed corrections are project-specific QA/video fixture work. Validation grade: A for the implemented evaluation slice. Closure recommendation: Keep open under `/mark-story-done`'s guardrail until the golden-wrong QA and symbolic-video findings are corrected and rerun, or until the user approves a rescope that closes this model-refresh slice separately.

20260721-2405 - approved-adoption: the user approved Gemini 3.5 Flash-Lite for `script_bible_v1` and authorized check-in and push. Updated both model-default owners (`module.yaml` and the Python fallback), added a focused regression that exercises the actual no-override call path and asserts manifest/runtime alignment, updated deployment guidance and the changelog, and corrected the story's ADR labels to their actual repository titles. The contaminated QA/video comparisons remain explicitly deferred to the next user-approved task; they do not weaken the two clean script-bible adoption runs.

20260721-2415 - adoption-validation: the post-adoption full suite passed with `917` unit tests (`186` deselected; one pre-existing unknown acceptance-mark warning), Ruff across `src/` and `tests/`, UI lint and TypeScript build, focused script-bible/discovery tests, methodology compile/check, compromise checks, YAML/JSON artifact loads, and `git diff --check`. The first lint pass found only import ordering in the new test; Ruff applied the mechanical fix and the full lint/focused tests then passed. No UI behavior changed, so browser verification remains not applicable. Ready for the user-authorized `/check-in-diff` branch push, integration validation, fast-forward landing, and remote SHA verification.
