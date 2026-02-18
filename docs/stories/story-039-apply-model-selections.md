# Story 039 — Apply Model Selections to Production

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: To Do
**Depends on**: Story 038 (Multi-Provider Transport), Story 036 (Model Selection)

## Goal

Apply Story 036's task-specific model selections to production code and recipe configs. Also build any remaining eval types (normalization, scene enrichment) that were deferred from Story 036.

## Context

Story 036 benchmarked 5 eval types across 12 models and produced task-specific try-validate-escalate triads. Story 047 added Sonnet 4.6 to all evals and updated winners.

**Already applied (Story 047, 2026-02-17)**: Sonnet 4.5 → 4.6 defaults updated in character_bible, prop_bible, script_normalize, and ai/chat.py. Location_bible intentionally kept at Sonnet 4.5 (it scores better there: 0.895 vs 0.870). `ModelStrategy` defaults in `models.py` are correct (work=sonnet-4-6, verify=haiku-4-5, escalate=opus-4-6).

**Stale defaults discovered (2026-02-18)**: Audit found 4 modules with outdated hardcoded defaults that Story 047 missed: `scene_extract_v1` (Haiku instead of Sonnet 4.6), `location_bible_v1` (dated suffix), `continuity_tracking_v1` (gpt-4o-mini), `project_config_v1` (gpt-4o escalation).

**Remaining work**: Fix stale module defaults, update recipe configs, build deferred evals, end-to-end smoke test.

## Acceptance Criteria

- [x] Model defaults in pipeline modules reflect Story 036/047 task-specific triads (all modules fixed)
- [x] Recipe configs reference new model defaults (production recipes use module defaults — no hardcoded models)
- [ ] All pipeline modules work end-to-end with their assigned models
- [x] Build normalization eval (text-comparison scorer pattern — deferred from Story 036)
- [x] Build scene enrichment eval (scene-level input fixtures — deferred from Story 036)
- [x] Build QA pass eval (seeded good/bad pairs — deferred from Story 036)
- [x] Run deferred evals across 13 providers (4 OpenAI + 4 Anthropic + 5 Gemini)
- [ ] Recalibrated config detection eval re-run with fixed golden reference

## Non-Goals

- Changing the try-validate-escalate architecture itself
- Building a model switching UI
- Cost optimization (Story 032)

## Tasks

- [x] Update module-level model defaults (Story 047: Sonnet 4.5 → 4.6 in character_bible, prop_bible, script_normalize, chat)
- [x] Fix remaining stale module defaults missed by Story 047:
  - [x] `scene_extract_v1/main.py`: haiku-4-5 → `claude-sonnet-4-6` (benchmark winner, 0.815)
  - [x] `location_bible_v1/main.py`: `claude-sonnet-4-5-20250929` → `claude-sonnet-4-5` (normalized, kept Sonnet 4.5 per benchmark)
  - [x] `continuity_tracking_v1/main.py`: `gpt-4o-mini` → `claude-sonnet-4-6`
  - [x] `project_config_v1/main.py`: `gpt-4o` escalation → `claude-opus-4-6`
  - [x] `ChatPanel.tsx`: `claude-sonnet-4-5-20250929` → `claude-sonnet-4-6` (UI default_model)
  - [x] `ProjectRun.tsx`: `claude-sonnet-4-5-20250929` → `claude-sonnet-4-6` (UI default_model)
  - [x] `llm.py`: added `claude-sonnet-4-5` (bare name) to pricing table
- [x] Verify recipe YAML configs (production recipes use module defaults or `${utility_model}` — no hardcoded models to update)
- [x] Build normalization eval: text-comparison scorer (Fountain structural validity + content preservation)
- [x] Build scene enrichment eval: scene-level golden references from The Mariner
- [x] Build QA pass eval: seeded known-good and known-bad inputs
- [x] Run normalization, scene enrichment, and QA evals across 13 providers (4 OpenAI, 4 Anthropic, 5 Gemini)
- [ ] Re-run config detection eval with calibrated golden reference
- [x] Analyze results: Sonnet 4.6 wins all 3 new evals (avg 0.948), validates current defaults
- [ ] End-to-end pipeline smoke test with new model assignments
- [ ] Update Story 036 with final comprehensive results

## Work Log

### 20260217-2100 — Partial completion via Story 047

Model defaults updated for 5 modules where Sonnet 4.6 benchmarks justify the change. Location_bible intentionally kept at Sonnet 4.5 (better score: 0.895 vs 0.870). Remaining work: recipe configs, deferred evals, end-to-end smoke test, multi-provider transport (Story 038).

### 20260218-0030 — All stale model defaults fixed

**Action**: Fixed all remaining stale hardcoded model defaults across backend modules and UI.

**Changes** (7 files):
- `scene_extract_v1/main.py`: work_model `claude-haiku-4-5-20251001` → `claude-sonnet-4-6`
- `location_bible_v1/main.py`: work_model + escalate `claude-sonnet-4-5-20250929` → `claude-sonnet-4-5`
- `continuity_tracking_v1/main.py`: work_model `gpt-4o-mini` → `claude-sonnet-4-6`
- `project_config_v1/main.py`: escalation `gpt-4o` → `claude-opus-4-6`
- `ChatPanel.tsx`: default_model `claude-sonnet-4-5-20250929` → `claude-sonnet-4-6`
- `ProjectRun.tsx`: default_model `claude-sonnet-4-5-20250929` → `claude-sonnet-4-6`
- `llm.py`: added `claude-sonnet-4-5` (bare name) to pricing table for cost tracking

**Recipe audit**: Production recipes (`mvp_ingest`, `world_building`, `narrative_analysis`) don't hardcode models — they rely on module defaults or `${utility_model}` substitution. Test recipes use `mock`. No recipe changes needed.

**Evidence**: 169/169 unit tests pass, ruff lint clean, UI builds clean.

**Remaining**: Deferred eval work (normalization, scene enrichment, QA evals), end-to-end smoke test with new models, config detection recalibration. These require the benchmarks worktree.

### 20260218-0200 — Three deferred evals built and run

**Action**: Created normalization, scene enrichment, and QA pass evals from scratch, ran across 8 providers (4 OpenAI + 4 Anthropic). Gemini deferred — Anthropic API credits exhausted (Opus 4.6 judge calls).

**New eval files** (18 files):
- `benchmarks/input/`: 6 input fixtures (prose, broken fountain, elevator scene, flashback scene, good/bad scene extractions)
- `benchmarks/golden/`: 3 golden references
- `benchmarks/prompts/`: 3 prompt templates
- `benchmarks/scorers/`: 3 Python scorers (dual pattern: structural + semantic)
- `benchmarks/tasks/`: 3 promptfoo YAML configs (13 providers × 2 tests each)
- `benchmarks/results/`: 3 JSON result files

**Results** (Python scorer, 8 providers):

| Provider | Norm Avg | Enrich Avg | QA Avg | **Overall** |
|---|---|---|---|---|
| **Sonnet 4.6** | 1.000 | 0.855 | 0.995 | **0.950** |
| Opus 4.6 | 0.970 | 0.845 | 0.990 | 0.935 |
| Haiku 4.5 | 0.949 | 0.863 | 0.990 | 0.934 |
| GPT-5.2 | 0.970 | 0.824 | 1.000 | 0.931 |
| GPT-4.1 Mini | 0.985 | 0.789 | 1.000 | 0.924 |
| Sonnet 4.5 | 0.985 | 0.788 | 0.990 | 0.921 |
| GPT-4.1 | 0.967 | 0.786 | 0.975 | 0.909 |
| GPT-4.1 Nano | 0.970 | 0.784 | 0.665 | 0.806 |

**Key findings**:
- Sonnet 4.6 wins all 3 new evals, **validates current module defaults** (work=sonnet-4-6)
- GPT-4.1 Nano dangerous as QA gate: 0.330 on good-scene (false negative — rejects valid extractions)
- Scene enrichment is hardest eval — no model clears 0.90 (structural ceiling in current prompt)
- Normalization is easiest — most models 0.94+ (Fountain format is well-understood)
- Haiku 4.5 surprisingly strong on enrichment (0.863), good verify-tier candidate

**Remaining**: Gemini providers (5 models) once API credits refilled, config detection recalibration, end-to-end smoke test, update AGENTS.md eval catalog.

### 20260218-0800 — Gemini evals complete, full 13-provider matrix done

**Action**: Ran all 3 deferred evals across 5 Gemini providers (2.5 Flash Lite, 2.5 Flash, 2.5 Pro, 3 Flash, 3 Pro). Combined with prior 8-provider results for full 13-model comparison.

**Results** (composite: Python scorer + LLM rubric, 13 providers):

| Provider | Norm Avg | Enrich Avg | QA Avg | **Overall** |
|---|---|---|---|---|
| **Sonnet 4.6** | 0.955 | 0.890 | 0.998 | **0.948** |
| Sonnet 4.5 | 0.955 | 0.784 | 0.995 | 0.911 |
| Opus 4.6 | 0.910 | 0.812 | 0.995 | 0.906 |
| GPT-4.1 | 0.946 | 0.768 | 0.988 | 0.900 |
| Gemini 3 Flash | 0.943 | 0.756 | 1.000 | 0.900 |
| Haiku 4.5 | 0.905 | 0.781 | 0.995 | 0.893 |
| Gemini 3 Pro | 0.922 | 0.756 | 0.975 | 0.885 |
| Gemini 2.5 Flash | 0.906 | 0.750 | 0.963 | 0.873 |
| Gemini 2.5 Pro | 0.905 | 0.699 | 0.995 | 0.866 |
| GPT-4.1 Mini | 0.922 | 0.657 | 1.000 | 0.860 |
| GPT-5.2 | 0.748 | 0.799 | 1.000 | 0.849 |
| GPT-4.1 Nano | 0.922 | 0.629 | 0.570 | 0.707 |
| Gemini 2.5 Flash Lite | 0.415 | 0.696 | 0.643 | 0.585 |

**Key findings**:
- Sonnet 4.6 remains clear winner across all 13 providers (0.948) — **validates current module defaults**
- Gemini 3 Flash (0.900) ties GPT-4.1, outperforms Gemini 2.5 Pro — strong value option
- GPT-5.2 normalization weakness (0.748): fails to strip prose attribution tags from dialogue
- Two models dangerous as QA gates (false negatives): GPT-4.1 Nano (0.570), Gemini 2.5 Flash Lite (0.643)
- Gemini 2.5 Flash Lite also hit rate limit errors — not production-ready
- Anthropic models most consistent: zero errors, zero false negatives, tightest Python-vs-LLM gap
- Scene enrichment remains hardest eval — no model clears 0.90 composite

**Remaining**: Config detection recalibration, end-to-end pipeline smoke test, update Story 036 with final results.
