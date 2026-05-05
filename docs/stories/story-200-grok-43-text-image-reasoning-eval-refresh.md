---
id: "200"
title: "Grok 4.3 Text and Image Reasoning Eval Refresh"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:4"
  - "spec:6"
  - "spec:7"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
category_refs:
  - "spec:2"
  - "spec:4"
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
  - "C4"
  - "C5"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
  - "generation_and_visualization"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "grok-4.3"
  - "xai"
legacy_system: "Cross-Cutting"
---

# Story 200 - Grok 4.3 Text and Image Reasoning Eval Refresh

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:4, spec:6, spec:7, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (models improve as a design principle and prompt compilation handles model upgrades)
**Depends On**: Story 035 (model benchmarking system)

## Goal

Evaluate xAI `grok-4.3` as a CineForge text/image reasoning model, separate from existing xAI image/video generation notes. Measure scene/script understanding, director-facing shot/clip reasoning, prompt-compilation-adjacent behavior, verification-slot behavior, latency, and per-run cost against current registry baselines. Do not change model defaults unless maintained eval evidence beats the current model-slot strategy.

## Source

- Inbox item dated 2026-05-01 from Conductor Scout 028: `/Users/cam/.codex/worktrees/414d/conductor/docs/scout/scout-028-grok-4-3-api-eval-opportunities.md`

## Eval Ladder Context

- **Root / parent need**: `spec:8` needs current model-slot evidence; `spec:2` needs strong scene/script understanding; `spec:4`, `spec:6`, and `spec:7` need director/shot planning and prompt-compilation reasoning that can reduce scaffolding only when measured.
- **Parent evals**: maintained promptfoo evals for `scene-extraction`, `scene-enrichment`, `script-bible`, `qa-pass`, and `video-understanding`.
- **Measured trigger**: Conductor Scout 028 reported current xAI API documentation for `grok-4.3`; local xAI model discovery must confirm account availability before running paid evals.
- **Child eval / baseline**: add Grok 4.3 lanes to existing eval configs, run only Grok 4.3, and compare score/latency/cost against registry leaders and current runtime default slots.

## Acceptance Criteria

- [ ] Live xAI model discovery confirms `grok-4.3` is available on this account.
- [ ] xAI discovery, text runtime transport, pricing helpers, and video-understanding provider support Grok 4.3 without changing production defaults.
- [ ] Grok 4.3 is wired into maintained promptfoo configs covering scene/script understanding, QA verification, and image/frame-based director-facing clip reasoning.
- [x] Raw promptfoo results are saved under `benchmarks/results/`.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification for each new result.
- [x] The story explicitly states whether Grok 4.3 beats any current model-slot strategy; defaults stay unchanged unless the registry evidence supports a change.
- [x] Required tests, lint, methodology compile/check, YAML load, and `git diff --check` pass.
- [x] The completed inbox item is removed from `docs/inbox.md`.

## Out of Scope

- Changing production model defaults from hypothesis or public benchmark snapshots alone.
- Re-tuning prompts, scorers, or goldens to help Grok 4.3 pass.
- Re-evaluating xAI image/video generation models such as Grok Imagine.
- Running full Big Fish or live generated-video provider-floor evals.
- Committing or pushing changes.

## Approach Evaluation

- **Simplification baseline**: if Grok 4.3 dominates the maintained suite at lower cost/latency, C3 tiering pressure drops. This story measures that directly instead of assuming public benchmarks transfer to CineForge.
- **AI-only**: the benchmarked model work is AI reasoning already. Use current promptfoo tasks and deterministic plus LLM-rubric scoring.
- **Hybrid**: provider plumbing and cost extraction stay in code; quality remains measured by maintained eval harnesses and registry notes.
- **Pure code**: appropriate only for adding xAI discovery/transport/provider support and tests.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment. ADR-003 says prompt compilation and model upgrades should remove scaffolding only when actual model capability makes that honest.
- **Existing patterns to reuse**: Story 189's model-refresh pattern, `scripts/discover-models.py`, `cine_forge.ai.llm`, `benchmarks/providers/video_understanding_provider.py`, `scripts/extract-eval-metrics.py`, promptfoo task configs, and `docs/evals/registry.yaml`.

## Tasks

- [x] Verify xAI API availability and `grok-4.3` model listing before wiring evals.
- [x] Read current methodology/spec/ADR context and run `make check-size`.
- [x] Add Grok 4.3 to live model discovery and local cost-estimation helpers.
- [x] Add OpenAI-compatible xAI transport for runtime text reasoning probes.
- [x] Add xAI support to the video-understanding promptfoo provider.
- [x] Add Grok 4.3 lanes to `scene-extraction`, `scene-enrichment`, `script-bible`, `qa-pass`, and `video-understanding`.
- [x] Run the Grok 4.3 eval set and save result JSON.
- [x] Update `docs/evals/registry.yaml` with measured rows and classifications.
- [x] Decide whether any default-changing recommendation is warranted.
- [x] Remove the completed inbox item.
- [ ] Run required checks:
  - [x] Focused unit tests for xAI discovery/runtime/provider support.
  - [x] `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] `.venv` equivalent ruff check for touched Python files.
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] YAML registry/model-discovery loading.
  - [x] `git diff --check`
- [x] UI not touched; browser verification is not applicable.
- [x] Verify Central Tenets (0-5):
  - [x] **T0 - Data Safety:** no user project data mutated; eval artifacts are additive.
  - [x] **T1 - AI-Coded:** provider plumbing is narrow and registry notes explain behavior.
  - [x] **T2 - Architect for 100x:** no default changed without maintained eval proof.
  - [x] **T3 - Fewer Files:** one focused unit test file was added for discovery; existing provider/runtime seams were reused.
  - [x] **T4 - Verbose Artifacts:** raw promptfoo files, registry rows, discovery cache, and work log preserve the evidence.
  - [x] **T5 - Ideal vs Today:** Grok 4.3 was tested as a potential scaffold reducer, but the evidence says keep current slots.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete
- [x] Story marked done

## Architectural Fit

- **Owning class/module**: discovery stays in `scripts/discover-models.py`; shared runtime text transport and cost estimates stay in `src/cine_forge/ai/llm.py`; promptfoo video/frame reasoning support stays in `benchmarks/providers/video_understanding_provider.py`; eval truth stays in `docs/evals/registry.yaml`.
- **Data contracts**: no new application-layer contract. The xAI runtime transport returns the existing OpenAI-compatible response shape; the video provider returns existing promptfoo provider fields.
- **File sizes**: `src/cine_forge/ai/llm.py` is already large (`make check-size` reported 907 lines before this story), so this story only adds a narrow provider branch and pricing row. Existing large generation/shot-planning modules are evaluated through harnesses rather than expanded.
- **Decision context**: ADR-001 and ADR-003 were reviewed. No new ADR is needed because this is eval/provider measurement, not a new product architecture decision.

## Files to Modify

- `scripts/discover-models.py` - add xAI provider discovery and Grok classification.
- `src/cine_forge/ai/llm.py` - add xAI transport, provider parsing, and Grok 4.3 pricing.
- `benchmarks/providers/video_understanding_provider.py` - add xAI multimodal provider branch.
- `benchmarks/tasks/scene-extraction.yaml`, `scene-enrichment.yaml`, `script-bible.yaml`, `qa-pass.yaml`, `video-understanding.yaml` - add Grok 4.3 lanes.
- `scripts/extract-eval-metrics.py` - add Grok 4.3 cost estimation.
- `tests/unit/test_ai_llm.py`, `tests/unit/test_video_understanding_benchmark.py`, `tests/unit/test_discover_models_xai.py` - focused support coverage.
- `benchmarks/results/*-grok43-2026-05-04.json` - raw eval result evidence.
- `docs/evals/registry.yaml` - measured score rows and mismatch/runtime notes.
- `docs/evals/models-available.yaml` - refreshed live discovery cache with xAI language models.
- `docs/inbox.md` - remove the completed item after evidence is recorded.
- `docs/stories/story-200-grok-43-text-image-reasoning-eval-refresh.md` - story truth and work log.

## Redundancy / Removal Targets

- None expected. Grok 4.3 is a new measurable model lane, not a replacement for existing provider integrations unless the maintained registry proves a default-changing win.

## Notes

- Official xAI docs list Grok 4.3 as the recommended Chat API model and note text/image input capabilities for chat models. The account-level `/v1/language-models` endpoint is still the source of truth for whether this workspace can actually call it.
- xAI data/privacy remains a deployment consideration: standard API retention is not the same as enterprise zero-data-retention behavior, so default promotion would need product/privacy review even if eval scores are strong.
- Story 200 result summary:
  - `scene-extraction`: `0.4100`, `116246 ms`, `$0.0291` estimated, failed strict JSON due reasoning preamble.
  - `scene-enrichment`: `0.4000`, `40411 ms`, `$0.0097` estimated, failed both fixtures due reasoning preambles.
  - `qa-pass`: `0.2625`, `24490 ms`, `$0.0062` estimated, unsafe as a QA gate because it false-negatived the known-good case.
  - `script-bible`: `0.9050`, `78664 ms`, `$0.0213` estimated, passed quality but loses the value-default argument to existing full-script lanes.
  - `video-understanding`: `0.5720`, `34739 ms`, `$0.0090` estimated, passed only `1/6` anchor clips and missed director-facing camera/motion/reveal reads.
  - Default decision: no CineForge model defaults change from this evidence.

## Plan

Finish the provider wiring, run the targeted Grok 4.3 eval set, update registry evidence and mismatch classifications, then close the inbox item only if the registry tells a complete story. Production defaults remain unchanged unless Grok 4.3 clearly beats the current model-slot strategy on maintained evals.

## Work Log

20260504-1744 - discovery-and-plan: verified the source inbox item against Conductor Scout 028 and separated this text/image reasoning evaluation from existing xAI image/video generation work. Live xAI account probes returned `grok-4.3` from both `/v1/models` and `/v1/language-models`, while the existing `scripts/discover-models.py` only covered OpenAI, Anthropic, and Google. Reviewed `docs/methodology/state.yaml`, `docs/spec.md`, ADR-001, ADR-003, Story 189, and Story 195. Ran `make check-size`; it reported existing large-file baseline noise including `src/cine_forge/ai/llm.py`, `shot_plan_v1/main.py`, and `render_adapter_v1/main.py`, so this story keeps edits narrow and benchmark-focused. Next step: run the Grok 4.3 promptfoo evals and record registry-backed findings.
20260504-1812 - grok43-eval-results: added xAI discovery/runtime/benchmark support and ran the targeted Grok 4.3 eval set. Raw result files: `benchmarks/results/scene-extraction-grok43-2026-05-04.json`, `benchmarks/results/scene-enrichment-grok43-2026-05-04.json`, `benchmarks/results/qa-pass-grok43-2026-05-04.json`, `benchmarks/results/script-bible-grok43-2026-05-04.json`, and `benchmarks/results/video-understanding-grok43-2026-05-04.json`. Registry updates classify scene extraction/enrichment as model-wrong/output-format failures, QA as model-wrong/output-format plus unsafe false-negative behavior, video understanding as model-wrong director/shot-read misses, and script bible as a quality pass with no value-default win. Defaults remain unchanged. The inbox item is removed because the maintained registry now has the requested evidence. Next step: run full validation and compile methodology surfaces.
20260504-1825 - validation-and-closeout: validation completed for the Grok 4.3 refresh. Evidence: focused xAI support tests passed (`44 passed`), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`852 passed, 183 deselected, 1 existing acceptance mark warning`), ruff passed for touched Python files, registry/model-discovery YAML loaded, all five Grok 4.3 result JSON files parsed, `pnpm methodology:compile` regenerated planning surfaces, `pnpm methodology:check` passed with only the existing architecture-audit warning, and `git diff --check` passed. No UI touched, so browser verification is not applicable. Story 200 is complete; next step is optional `/check-in-diff` if the user wants the branch landed.
