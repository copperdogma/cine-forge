---
id: "204"
title: "Gemini 3.5 Flash Model-Slot Eval Refresh"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:3"
  - "spec:4"
  - "spec:6"
  - "spec:7"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
  - "119"
  - "202"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:4"
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
  - "C4"
  - "C5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
  - "generation_and_visualization"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "gemini-3.5-flash"
  - "google"
legacy_system: "Cross-Cutting"
---

# Story 204 - Gemini 3.5 Flash Model-Slot Eval Refresh

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:3, spec:4, spec:6, spec:7, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (model upgrades should reduce scaffolding only when evidence supports it)
**Depends On**: Story 035, Story 119, Story 202

## Goal

Evaluate Google `gemini-3.5-flash` as a CineForge text and multimodal reasoning challenger, using existing model-slot benchmark surfaces rather than public benchmark assumptions. Measure whether it improves scene/script understanding, entity discovery for downstream design-study backfill, QA judgment, generated-output video/frame reasoning, and the C3/C5 compromise signals. Do not touch render-video defaults or Gemini Omni until the API exposes a callable model ID and repo eval evidence exists.

## Source

- Inbox item dated 2026-05-19 from Conductor Scout 035: `/Users/cam/.codex/worktrees/dfe1/conductor/docs/scout/scout-035-google-gemini-35-flash-api-eval-opportunities.md`
- Live discovery on 2026-05-20 found `gemini-3.5-flash` as callable and `[NEW]` through the Google Gemini API.
- Official Google Gemini API pricing page lists `gemini-3.5-flash` standard paid pricing at `$1.50` input / `$9.00` output per 1M tokens, with output price including thinking tokens.

## Eval Ladder Context

- **Root / parent need**: `spec:8` requires evidence-backed model-slot decisions; `spec:2` and `spec:3` require robust screenplay and world-model understanding; `spec:4`, `spec:6`, and `spec:7` need honest multimodal/director-facing QA before role-modality scaffolding can shrink.
- **Parent evals**: maintained promptfoo tasks for `scene-extraction`, `scene-enrichment`, `entity-discovery`, `script-bible`, `qa-pass`, and `video-understanding`.
- **Measured trigger**: `scripts/discover-models.py --check-new` confirmed the account can call `gemini-3.5-flash`; the registry has no rows for it yet.
- **Child eval / baseline**: add one Gemini 3.5 Flash lane to the existing task configs, run only that provider, save raw result JSON, and compare quality/latency/cost against current registry leaders and runtime defaults.
- **Design-study prompt compiler note**: Story 202 proved default design-study prompt compilation through fixture and service evidence, not a promptfoo model-slot eval. This story probes the adjacent model-slot surfaces that feed or judge that path (`entity-discovery`, `script-bible`, `video-understanding`) and records the absence of a dedicated prompt-compiler eval instead of inventing one inline.

## Acceptance Criteria

- [x] Live model discovery and pricing evidence for `gemini-3.5-flash` are recorded before running paid evals.
- [x] Gemini 3.5 Flash is wired into the narrow maintained promptfoo configs covering scene/script understanding, entity discovery, QA verification, and video/frame reasoning.
- [x] Raw promptfoo results are saved under `benchmarks/results/`.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification for each new result.
- [x] C3 and C5 compromise implications are explicitly stated; defaults stay unchanged unless the measured quality, latency, and cost justify a change.
- [x] The completed inbox item is removed from `docs/inbox.md` only after registry evidence is complete.
- [x] Required tests, lint, methodology compile/check, YAML load, and `git diff --check` pass or blockers are recorded with evidence.

## Out of Scope

- Running final-render provider-floor, Veo, Imagen, Lyria, or Gemini Omni evals.
- Changing production model defaults from discovery or public benchmark claims alone.
- Re-tuning prompts, scorers, or goldens to help Gemini 3.5 Flash pass.
- Creating a new design-study prompt-compiler promptfoo eval in this story.
- Committing or pushing changes.

## Approach Evaluation

- **Simplification baseline**: if one fast Gemini model clears the maintained quality/latency/cost bars, tiered routing and role-modality pressure could drop. The benchmark suite is the source of truth; discovery alone is insufficient.
- **AI-only**: the benchmarked work is already AI reasoning. Directly run Gemini 3.5 Flash against the existing promptfoo tasks.
- **Hybrid**: provider plumbing and cost estimation stay in code; quality remains measured by deterministic Python scorers plus Opus rubric judgment.
- **Pure code**: appropriate only for provider-list additions, pricing/cost helpers, discovery classification, raw-result extraction, and registry bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment rather than assumed quality. ADR-003 says model improvements should remove workaround complexity only when measured evidence supports it. The inbox explicitly keeps render-video defaults and Gemini Omni out of scope.
- **Existing patterns to reuse**: Stories 189 and 200 model-refresh workflow, `scripts/discover-models.py`, `src/cine_forge/ai/llm.py`, `scripts/extract-eval-metrics.py`, `benchmarks/providers/video_understanding_provider.py`, promptfoo task provider blocks, and `docs/evals/registry.yaml`.
- **Eval**: existing tasks distinguish the relevant model-slot behavior. No new scorer/golden is expected unless a run exposes a harness bug rather than model behavior.

## Tasks

- [x] Run live discovery and confirm `gemini-3.5-flash` is callable.
- [x] Read methodology/spec/ADR/story context and run `make check-size`.
- [x] Add Gemini 3.5 Flash pricing/cost support.
- [x] Add Gemini 3.5 Flash lanes to `scene-extraction`, `scene-enrichment`, `entity-discovery`, `script-bible`, `qa-pass`, and `video-understanding`.
- [x] Run the targeted Gemini 3.5 Flash eval set and save result JSON.
- [x] Update `docs/evals/registry.yaml` with measured rows and mismatch/runtime classifications.
- [x] Decide whether any default-changing recommendation is warranted.
- [x] Remove the completed inbox item.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint for touched Python files and generated registry helpers.
  - [x] UI not touched; UI checks are not applicable.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] UI not touched; browser verification is not applicable.
- [x] Search all docs and update any related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** No user project data mutated; benchmark artifacts are additive.
  - [x] **T1 - AI-Coded:** Provider lanes and registry notes are clear to future agents.
  - [x] **T2 - Architect for 100x:** No default or workaround changes without measured value evidence.
  - [x] **T3 - Fewer Files:** Reuse existing provider/runtime/cost seams instead of adding parallel infrastructure.
  - [x] **T4 - Verbose Artifacts:** Raw result files, registry rows, and work log preserve the evidence.
  - [x] **T5 - Ideal vs Today:** New model evidence is used to test whether scaffolding can shrink.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete
- [x] Story marked done

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: discovery stays in `scripts/discover-models.py`; shared runtime cost estimates stay in `src/cine_forge/ai/llm.py`; eval metric extraction stays in `scripts/extract-eval-metrics.py`; multimodal promptfoo support stays in `benchmarks/providers/video_understanding_provider.py`; eval truth stays in `docs/evals/registry.yaml`.
- **Data contracts**: no new application-layer contracts. Promptfoo providers return existing output, token usage, cost, latency, and metadata fields.
- **File sizes**: `make check-size` reported only existing large-file watchpoints. This story should keep edits to large Python files surgical: `src/cine_forge/ai/llm.py` is `979` lines before this story; `scripts/discover-models.py` and `scripts/extract-eval-metrics.py` receive only pricing/classification additions if needed. Benchmark YAML edits are provider-list additions.
- **Decision context**: Reviewed ADR-001, ADR-003, `docs/spec.md` model/compromise sections, `docs/methodology/state.yaml`, `docs/build-map.md`, Story 189, Story 200, and Story 202. No new ADR is needed because this is eval/provider measurement, not a new product architecture decision.

## Files to Modify

- `src/cine_forge/ai/llm.py` - add Gemini 3.5 Flash pricing for runtime/provider cost estimates if not already covered.
- `scripts/extract-eval-metrics.py` - add Gemini 3.5 Flash pricing for result-to-registry extraction.
- `src/cine_forge/env.py` - export stale `GOOGLE_API_KEY` from the canonical Gemini env value so promptfoo's native Google provider uses the same key as CineForge discovery.
- `tests/unit/test_env.py` - cover stale `GOOGLE_API_KEY` override behavior.
- `benchmarks/tasks/scene-extraction.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/tasks/scene-enrichment.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/tasks/entity-discovery.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/tasks/script-bible.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/tasks/qa-pass.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/tasks/video-understanding.yaml` - add Gemini 3.5 Flash lane.
- `benchmarks/results/*gemini35flash*.json` - raw promptfoo evidence.
- `docs/evals/registry.yaml` - measured score rows and classifications.
- `docs/evals/models-available.yaml` - refreshed live discovery cache if discovery cache is updated.
- `docs/inbox.md` - remove the completed item after evidence is recorded.
- `docs/stories/story-204-gemini-35-flash-model-slot-eval-refresh.md` - story truth and work log.

## Redundancy / Removal Targets

- None removed. This is a new measurable model lane. Existing Gemini 2.5/3.0/3.1 lanes remain valuable comparators because Gemini 3.5 Flash did not show a clear suite-wide replacement.

## Notes

- Gemini 3.5 Flash standard pricing is materially higher than the cheapest Flash-Lite lanes, so the eval must compare cost and latency alongside score. A quality tie is not enough for a default change.
- `gemini-flash-latest` and `gemini-pro-latest` were discovered but are aliases, not the stable target from the inbox item. This story tests the canonical `gemini-3.5-flash` ID.
- `lyria-*` and Gemini Omni are out of scope because this story is text/multimodal reasoning, not music/audio/video generation.

## Plan

1. **Wire the model lane and pricing**
   - Files: `src/cine_forge/ai/llm.py`, `scripts/extract-eval-metrics.py`, six promptfoo task YAML files.
   - Work: add standard Gemini 3.5 Flash cost estimates and one provider block per target task.
   - Done when: promptfoo can filter to `Gemini 3.5 Flash` and result extraction reports quality, latency, and cost.

2. **Run targeted evals**
   - Files: `benchmarks/results/`.
   - Work: run only Gemini 3.5 Flash on `scene-extraction`, `scene-enrichment`, `entity-discovery`, `script-bible`, `qa-pass`, and `video-understanding`, using project env wrapper and Node 24.
   - Done when: raw JSON exists for every task and failures are separable as model behavior vs harness/runtime failure.

3. **Record registry truth and inbox disposition**
   - Files: `docs/evals/registry.yaml`, `docs/inbox.md`, story file.
   - Work: add measured rows with mismatch classifications and runtime/default implications, update C3/C5 notes if needed, then remove the inbox note only if the evidence is complete.
   - Done when: future `/triage` can see whether Gemini 3.5 Flash changes any model-slot or compromise pressure.

4. **Verify**
   - Files: validation outputs and generated methodology surfaces.
   - Work: run focused lint/tests for touched Python, YAML loading/metric extraction, `make test-unit` through the canonical venv, methodology compile/check, and `git diff --check`.
   - Done when: checks pass or blockers are documented in the work log with exact commands.

## Work Log

20260520-0839 - discovery-and-plan: live discovery with `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/discover-models.py --check-new` found `gemini-3.5-flash` as a callable Google model marked `[NEW]`, with all provider keys present. Official Google pricing page lists standard paid pricing at `$1.50` input / `$9.00` output per 1M tokens, output including thinking tokens. Reviewed `docs/inbox.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/spec.md`, ADR-001, ADR-003, Stories 189/200/202, and ran `make check-size`; the story will reuse the existing model-refresh pattern and keep render-video/Gemini Omni out of scope. Next step: add pricing and promptfoo lanes, then run the targeted evals.

20260520-0901 - provider-lanes-and-env-fix: added Gemini 3.5 Flash standard pricing to runtime and eval-metric cost maps, then added one `Gemini 3.5 Flash` lane to `scene-extraction`, `scene-enrichment`, `entity-discovery`, `script-bible`, `qa-pass`, and `video-understanding`. The first promptfoo smoke failed because promptfoo's native Google provider preferred a stale `GOOGLE_API_KEY` even though CineForge discovery used the current `CINE_FORGE_GEMINI_API_KEY` / `GEMINI_API_KEY`; patched `src/cine_forge/env.py` so legacy provider export overwrites stale `GOOGLE_API_KEY` from the resolved Gemini key, and added unit coverage in `tests/unit/test_env.py`. Evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_env.py -q` passed, and the focused Gemini 3.5 Flash scene-enrichment smoke then passed.

20260520-0948 - targeted-eval-results: ran the targeted Gemini 3.5 Flash eval set with Node 24 and `scripts/with_cine_forge_provider_env.py`, saving raw results under `benchmarks/results/`. Results: `scene-enrichment` 0.8842, 2/2 pass, 9.982s, `$0.0052`; `qa-pass` 0.6250, 1/2 pass, 8.320s, `$0.0044`; `entity-discovery` 0.9200, 1/1 pass, 14.305s, `$0.0099`; `script-bible` 0.9100, 1/1 pass, 20.739s, `$0.0215`; `scene-extraction` 0.8108, 1/1 harness pass but below quality target, 38.265s, `$0.0247`; `video-understanding` 0.5562, 1/6 pass, 11.037s, `$0.0120`. Classification: scene-extraction, scene-enrichment, entity-discovery, script-bible, and video-understanding are model-wrong/non-runtime-blocking for current defaults; `qa-pass` is model-wrong and runtime-blocking if used as a QA default because it false-negatived the known-good scene. No model default changes are warranted, and C3/C5 compromise pressure does not shrink.

20260520-0959 - registry-and-inbox: recorded all six measured rows in `docs/evals/registry.yaml` with score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification. Refreshed `docs/evals/models-available.yaml` with `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/discover-models.py --cache` after the registry rows existed, and removed only the processed Gemini 3.5 Flash inbox item from `docs/inbox.md`. The refreshed provider cache now marks Google at 16 discovered models including `gemini-3.5-flash`; it also reflects the current xAI catalog shrink returned by discovery.

20260520-1015 - validation-and-closeout: verification passed for the touched scope. Evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/cine_forge/ai/llm.py src/cine_forge/env.py scripts/extract-eval-metrics.py tests/unit/test_env.py` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_env.py -q` passed; YAML/JSON loading passed for `docs/evals/registry.yaml`, `docs/evals/models-available.yaml`, and all six `*gemini35flash-2026-05-20.json` result files; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/check-compromises.py` still reports C3 and C5 as `not yet`; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `911 passed, 185 deselected, 1 warning`; `pnpm methodology:compile` and `pnpm methodology:check` passed and regenerated `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`; `git diff --check` passed. Methodology warnings were pre-existing process reminders: architecture audit domains due and UI scout freshness due.
