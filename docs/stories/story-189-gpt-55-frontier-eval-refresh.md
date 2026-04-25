---
id: "189"
title: "GPT-5.5 Frontier Eval Refresh"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "gpt-5.5"
legacy_system: "Cross-Cutting"
---

# Story 189 - GPT-5.5 Frontier Eval Refresh

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:3, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (models improve as design principle and prompt compilation handles model upgrades)
**Depends On**: Story 035 (model benchmarking system)

## Goal

Run the newly available OpenAI `gpt-5.5` and `gpt-5.5-pro` models through the maintained CineForge text promptfoo eval suite, preserve the raw evidence, update the eval registry, and classify whether the new models change any value defaults or compromise signals.

## Eval Ladder Context

- **Root / parent need**: `spec:8` requires current, evidence-backed model selection; `spec:2` and `spec:3` depend on extraction and understanding quality; compromises C2, C3, and C4 stay only while eval evidence justifies QA gates, tiered model routing, and split scene understanding.
- **Parent evals**: the maintained text promptfoo evals for character, location, prop, relationship, config, scene extraction, normalization, scene enrichment, QA, continuity, entity discovery, and script bible.
- **Measured trigger**: live model discovery showed `gpt-5.5` and `gpt-5.5-pro` are now available, so the dormant `new-subject-model` trigger is real.
- **Child eval / baseline**: run the two new OpenAI models against the existing promptfoo tasks and compare quality, latency, and cost against current registry leaders.

## Acceptance Criteria

- [x] Live model discovery confirms the current OpenAI model IDs before adding providers.
- [x] `gpt-5.5` and `gpt-5.5-pro` are wired into the maintained promptfoo text eval configs without changing existing provider lanes.
- [x] All target text evals are run with raw results saved under `benchmarks/results/`.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification for each new result.
- [x] Required backend/static/methodology checks pass after the registry and benchmark wiring changes.
- [x] Any default-changing recommendation is evidence-backed; no model default is changed unless quality, latency, and cost support it.

## Out of Scope

- Running image, video, storyboard, live-smoke, or full-script-throughput paid evals.
- Promoting a new model default in pipeline code from this refresh alone.
- Tuning prompts or scorers to help GPT-5.5 pass; this story measures current behavior.
- Committing or pushing the changes.

## Approach Evaluation

- **Simplification baseline**: The right baseline is direct single-call use of the new frontier models on existing tasks. If one model dominates quality, latency, and cost, model-tier scaffolding could shrink. The measured results do not show that.
- **AI-only**: All benchmarked tasks are AI calls already. GPT-5.5 and Pro can be measured directly through promptfoo; Pro required a Responses API provider because the stock promptfoo Chat/Completions providers could not call it correctly.
- **Hybrid**: Keep existing deterministic Python scorers plus LLM rubric scoring. Use custom plumbing only for transport, not quality shaping.
- **Pure code**: Appropriate only for provider integration, cost estimation, and registry bookkeeping. Do not encode model-specific success heuristics.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment rather than assumed model quality. ADR-003 says model upgrades should reduce workaround complexity only when measured evidence supports it.
- **Existing patterns to reuse**: Story 035/047 promptfoo config layout, `docs/evals/registry.yaml`, `scripts/discover-models.py`, `scripts/extract-eval-metrics.py`, and `cine_forge.ai.llm.estimate_cost_usd`.
- **Eval**: Existing promptfoo task configs and registry targets distinguish whether GPT-5.5 should become a value default or only frontier evidence.

## Tasks

- [x] Run live model discovery and verify `gpt-5.5` / `gpt-5.5-pro` IDs and current pricing.
- [x] Add GPT-5.5 provider blocks to text promptfoo task configs.
- [x] Add a minimal Responses API promptfoo provider for GPT-5.5 Pro.
- [x] Run the maintained text eval matrix for both new models and save result JSON.
- [x] Rerun the scene-extraction Pro case with a larger output budget to distinguish truncation from quality failure.
- [x] Update local cost-estimation tables for GPT-5.5 and GPT-5.5 Pro.
- [x] Update `docs/evals/registry.yaml` with measured rows and mismatch classifications.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; no existing provider path is redundant because only Pro needs Responses API transport.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched; UI checks are not applicable.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] UI not touched; browser verification is not applicable.
- [x] Search all docs and update any related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** No user data mutation; benchmark results are additive.
  - [x] **T1 - AI-Coded:** Provider plumbing is isolated and registry notes explain the result.
  - [x] **T2 - Architect for 100x:** No default or prompt workaround was added without value evidence.
  - [x] **T3 - Fewer Files:** One focused provider file was added because promptfoo lacked working Pro transport.
  - [x] **T4 - Verbose Artifacts:** Raw result files, registry notes, and work log record what happened.
  - [x] **T5 - Ideal vs Today:** New frontier evidence is used to test whether scaffolding can shrink; it cannot yet.

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

- **Owning class/module**: benchmark provider/config ownership stays under `benchmarks/`; cost estimation stays in `src/cine_forge/ai/llm.py` and `scripts/extract-eval-metrics.py`; registry truth stays in `docs/evals/registry.yaml`.
- **Data contracts**: No new application layer contract. Promptfoo provider returns the existing provider result shape (`output`, `tokenUsage`, `cost`, `latencyMs`, `metadata`).
- **File sizes**: `src/cine_forge/ai/llm.py` is already large at `907` lines; this story only adds two pricing entries. `scripts/extract-eval-metrics.py` is `348` lines, the new provider is `166` lines, and task config changes are provider-list additions. `make check-size` still reports existing large-file baseline noise, including `llm.py`.
- **Decision context**: Reviewed ADR-001 for eval-first model assignment and ADR-003 for the model-upgrade principle. No new ADR is needed because this is provider/eval measurement, not a product architecture decision.

## Files to Modify

- `benchmarks/tasks/*-extraction.yaml`, `benchmarks/tasks/config-detection.yaml`, `benchmarks/tasks/normalization.yaml`, `benchmarks/tasks/scene-enrichment.yaml`, `benchmarks/tasks/qa-pass.yaml`, `benchmarks/tasks/entity-discovery.yaml`, `benchmarks/tasks/script-bible.yaml` - add GPT-5.5/GPT-5.5 Pro providers.
- `benchmarks/providers/openai_responses_provider.py` - focused promptfoo provider for Responses API models.
- `benchmarks/results/gpt55-*-2026-04-24.json` - raw eval result evidence.
- `benchmarks/results/gpt55pro-scene-extraction-rerun-2026-04-24.json` - Pro output-budget timeout evidence.
- `docs/evals/registry.yaml` - measured result rows and mismatch/runtime notes.
- `src/cine_forge/ai/llm.py` - GPT-5.5/GPT-5.5 Pro pricing constants.
- `scripts/extract-eval-metrics.py` - GPT-5.5/GPT-5.5 Pro pricing constants for registry extraction helpers.
- `docs/stories/story-189-gpt-55-frontier-eval-refresh.md` - story truth and work log.

## Redundancy / Removal Targets

- None. The custom provider is only for model transports that promptfoo cannot currently call through its stock OpenAI Chat/Completions providers.
- No default model lane becomes redundant because GPT-5.5 Pro is too slow/expensive and GPT-5.5 does not dominate the suite.

## Notes

- Official OpenAI docs list `gpt-5.5` at `$5/$30` per 1M input/output tokens, with Chat Completions and Responses support.
- Official OpenAI docs list `gpt-5.5-pro` at `$30/$180`, available via the Responses API and potentially taking several minutes; background mode is recommended for long requests.
- GPT-5.5 Pro scene extraction is a transport/runtime failure for this task, not a semantic quality result: it produced partial high-quality JSON at 12k output tokens, then timed out at a 24k output-token floor and 900s timeout.

## Plan

The implementation is already mostly complete because the user asked to run the evals directly. Finish by running validation, compiling methodology surfaces, and closing the story if the checks pass. Do not change production defaults unless a later story performs a value-default update with the registry evidence from this refresh.

## Work Log

20260424-1805 - discovery-and-eval-run: live discovery found `gpt-5.5`, `gpt-5.5-2026-04-23`, `gpt-5.5-pro`, and `gpt-5.5-pro-2026-04-23`. Added GPT-5.5 to existing promptfoo OpenAI lanes and added a focused Responses API provider for Pro after stock promptfoo providers could not call it. Ran the text eval matrix and saved result JSON under `benchmarks/results/gpt55-*-2026-04-24.json`. Next step: finish registry/methodology validation.
20260424-1806 - registry-and-classification: updated `docs/evals/registry.yaml` with GPT-5.5 and GPT-5.5 Pro rows for all 12 text evals. Main findings: GPT-5.5 is strong but not a suite-wide value default; Pro is rarely worth the latency/cost; both models false-negatived the known-good QA case (`model-wrong`, runtime-blocking if used as QA default); Pro scene extraction is runtime-blocking due truncation/timeout. Next step: run checks, compile generated planning surfaces, and close the story if clean.
20260424-1808 - validation-and-closeout: required checks passed after benchmark wiring, registry updates, and story creation. Evidence: `make test-unit PYTHON=.venv/bin/python` passed (`814 passed, 179 deselected, 1 existing acceptance mark warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/providers/openai_responses_provider.py scripts/extract-eval-metrics.py` passed, `.venv/bin/python scripts/check-compromises.py` confirmed C2/C3/C4 remain not-yet gates with GPT-5.5 as a stronger but still incomplete C3 candidate, `pnpm methodology:compile` regenerated planning surfaces, `pnpm methodology:check` reported outputs current with only the existing `api_service_and_operator_console` architecture warning, YAML loading passed, and `git diff --check` passed. Next step: `/check-in-diff`.
