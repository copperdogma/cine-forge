---
id: "207"
title: "Grok 4.5 Model-Slot Eval Refresh"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:7"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
  - "200"
category_refs:
  - "spec:2"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
  - "generation_and_visualization"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "grok-4.5"
  - "xai"
legacy_system: "Cross-Cutting"
---

# Story 207 - Grok 4.5 Model-Slot Eval Refresh

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:7, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (model improvements reduce scaffolding only with evidence)
**Depends On**: Story 035, Story 200

## Goal

Evaluate xAI `grok-4.5` as a CineForge text/image reasoning challenger on the same maintained surfaces used for Grok 4.3. Measure screenplay understanding, scene nuance, script-bible synthesis, verification safety, director-facing frame reads, latency, and cost. Do not change defaults from launch claims alone.

## Source

- User request on 2026-07-20 to evaluate Grok 4.5 for CineForge.
- xAI's official announcement is dated 2026-07-16 and names `grok-4.5`, while live CineForge discovery on 2026-07-20 confirmed this account can call it.
- Official API documentation records text/image input, high reasoning by default, Chat Completions and Responses API support, and short-context pricing of `$2/M` input and `$6/M` output tokens.

## Acceptance Criteria

- [x] Live discovery confirms `grok-4.5` is callable and correctly classified as a new SOTA model.
- [x] Official model slug, modalities, reasoning control, context, and pricing are recorded before paid runs.
- [x] Grok 4.5 is run on the five maintained Grok 4.3 comparison surfaces without changing production defaults.
- [x] Raw promptfoo result JSON and the visible-thinking control are saved under `benchmarks/results/`.
- [x] Every mismatch is classified as model-wrong, golden-wrong, or ambiguous, including runtime impact.
- [x] `docs/evals/registry.yaml` records score, latency, cost, date, git SHA, result file, and decision notes.
- [x] Focused tests, full unit tests, lint, YAML/JSON loads, methodology checks, compromise check, and `git diff --check` pass.

## Out of Scope

- Changing production defaults from one launch-day run.
- Re-tuning prompts, scorers, or goldens to help Grok 4.5 pass.
- Re-running xAI image/video generation models such as Grok Imagine.
- Running the full 20-clip video-understanding matrix before the six-anchor pilot clears its quality floor.
- Committing or pushing changes.

## Architectural Fit

- **Owning modules**: live discovery stays in `scripts/discover-models.py`; runtime and extraction pricing stay in existing cost tables; promptfoo task YAML owns benchmark lanes; the registry owns measured truth.
- **Data contracts**: no application contract changes. Grok uses the existing xAI OpenAI-compatible transport and current promptfoo/custom-provider result shapes.
- **Large files**: `make check-size` reports the existing large-file baseline. The only large Python file touched is `src/cine_forge/ai/llm.py` (`987` lines), with one pricing row and no new responsibilities.
- **Decision context**: reviewed ADR-001, ADR-003, Story 200, Stories 204-206, current targets, and current leaders. No new ADR is needed because this is model measurement, not a product architecture change.

## Files Modified

- `scripts/discover-models.py` and `tests/unit/test_discover_models_xai.py` - classify Grok 4.5 as SOTA and prevent cross-family `4.5` registry false matches.
- `src/cine_forge/ai/llm.py` and `scripts/extract-eval-metrics.py` - add official short-context pricing.
- `benchmarks/tasks/{scene-extraction,scene-enrichment,script-bible,qa-pass,video-understanding}.yaml` - add the Grok 4.5 lanes.
- `benchmarks/results/*grok45*2026-07-20.json` - raw scored evidence plus the visible-thinking control.
- `docs/evals/registry.yaml` and `docs/evals/models-available.yaml` - durable measured and discovery truth.
- `docs/stories/story-207-grok-45-model-slot-eval-refresh.md` - story scope, evidence, and decision.

## Result and Decision

- `scene-extraction`: `0.9066`, `104242 ms`, `$0.0603` estimated. Quality passes, latency fails; GPT-5.2 remains better on score, speed, and cost.
- `scene-enrichment`: `0.9442`, `13728 ms`, `$0.0079` estimated. Passes every target and is cheaper than Sonnet 4.6, but remains below the repeatedly verified Sonnet quality lane. Keep as a challenger, not a default after one run.
- `script-bible`: `0.9750`, `41760 ms`, `$0.0247` estimated. Ties the single-run quality lead and improves materially on Grok 4.3, but misses latency/cost budgets and loses the value comparison to Grok 4.1 Fast Reasoning.
- `qa-pass`: `0.5982`, `10152 ms`, `$0.0092` estimated. It caught the bad fixture but invented seven errors in the known-good fixture. Model-wrong and runtime-blocking for QA adoption.
- `video-understanding`: `0.7017`, `6622 ms`, `$0.0067` estimated. Passes 3/6 anchors and clears latency/cost, but misses the `0.80` quality floor. The three misses are model-wrong: weak cut/motion nuance on the prop swap, a hallucinated static geometric scene instead of the neon crane reveal, and an incorrect central-subject/emotion read in the muzak tableau.
- **Recommendation**: do not adopt Grok 4.5 as a CineForge default. Retain it as a frontier comparison/fallback for script-bible and a promising scene-enrichment challenger. C2 and C3 do not shrink because QA remains unsafe and no single model dominates the slot matrix.

## Work Log

20260720-1220 - discovery-and-scope: the supplied worktree no longer existed, so the canonical checkout was inspected and a clean `codex/grok-45-eval-20260720` worktree was created to preserve an unrelated `docs/deploy-log.md` edit on `main`. Ran the repo's discovery skill; all provider keys were available and xAI returned `grok-4.5`. The script incorrectly labeled it tested because fuzzy matching confused Grok 4.5 with Claude-family 4.5 labels. Added a cross-family regression test and fixed matching; discovery then reported Grok 4.5 as new SOTA. Reviewed official xAI launch/API/pricing pages, ADR-001, ADR-003, Story 200, recent model-refresh stories, registry targets, and `make check-size` output.

20260720-1224 - harness-audit: the first scene-enrichment control exposed `reasoning_content` ahead of otherwise valid JSON because promptfoo defaults `showThinking` to true. This reproduced Grok 4.3's recorded parse symptom but proved it was a harness-display issue rather than a valid model-quality classification. Preserved the control artifact, set `showThinking: false` on strict JSON lanes so final content is scored while reasoning tokens remain in usage/cost, and reran the task successfully.

20260720-1230 - targeted-results-and-classification: completed the five-lane suite. Grok 4.5 passed scene extraction, both scene enrichment fixtures, and script bible; it false-negatived the known-good QA fixture and passed 3/6 video anchors. Manually inspected raw outputs and classified all six significant mismatches as model-wrong: one runtime-blocking QA judgment and five non-runtime-blocking/default-selection misses across latency/value or director-facing frame interpretation. No golden-wrong or ambiguous mismatches were found. Registry rows and live model cache were updated; defaults remain unchanged.

20260720-1240 - validation-and-closeout: focused Grok/discovery/runtime/video-provider tests passed (`48 passed`); touched Python Ruff passed; all benchmark YAML, registry/cache YAML, and six Grok 4.5 JSON artifacts loaded; full unit suite passed (`915 passed, 186 deselected`, one existing acceptance-mark warning); `pnpm methodology:compile` and `pnpm methodology:check` passed with existing architecture-audit and stale UI-scout warnings only; compromise checks kept C2, C3, C4, C5, and C7 at `not yet`; `git diff --check` passed. UI was not touched, so browser verification is not applicable. No redundant runtime path was created; the benchmark-only `showThinking: false` setting is required while promptfoo exposes reasoning by default.
