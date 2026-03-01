# Story 107 — Value-Optimized Model Selection Across All Modules

**Priority**: High
**Status**: Pending
**Spec Refs**: Cross-Cutting
**Depends On**: 036 (Model Selection — eval framework), 039 (Apply Model Selections — defaults applied), 092 (Continuity — proved the value-analysis pattern)
**Blocks**: None

## Goal

Stories 036/039/047 selected models by **quality** — always picking the top scorer for each task. Story 092's continuity eval revealed that value analysis (quality per dollar) produces materially better decisions: Haiku 4.5 scores 0.948 vs Sonnet 4.6's 0.978 (3% gap) but costs $0.008/call vs $0.040/call (5x cheaper). Across a 45-scene screenplay, that's $0.36 vs $1.80 for continuity alone — and the pipeline has 10+ AI modules.

This story re-runs all existing evals with value analysis and creates evals for the 4 modules that lack them, then updates every module default to the best-value model.

## Current State

### Modules WITH evals (10 evals, covering ~8 modules)

All existing evals picked the quality winner. None analyzed cost/value.

| Eval | Module | Current Default | Quality Winner | Value Winner? |
|------|--------|----------------|----------------|---------------|
| character-extraction | character_bible_v1 | claude-sonnet-4-6 | Sonnet 4.6 (0.942) | Unknown |
| location-extraction | location_bible_v1 | claude-sonnet-4-5 | Opus 4.6 (0.898) | Unknown |
| prop-extraction | prop_bible_v1 | claude-sonnet-4-6 | Opus 4.6 (0.880) | Unknown |
| relationship-discovery | entity_graph_v1 | claude-sonnet-4-6 | 7-way tie (0.995) | Unknown |
| config-detection | project_config_v1 | gpt-4o | Haiku 4.5 (0.886) | Unknown |
| scene-extraction | scene_breakdown_v1 | claude-sonnet-4-6 | Sonnet 4.6 (0.815) | Unknown |
| normalization | script_normalize_v1 | claude-sonnet-4-6 | Sonnet 4.6 (0.955) | Unknown |
| scene-enrichment | scene_analysis_v1 | claude-sonnet-4-6 | Sonnet 4.6 (0.890) | Unknown |
| qa-pass | scene_analysis_v1 (QA) | claude-haiku-4-5 | Sonnet 4.6 (0.998) | Unknown |
| continuity-extraction | continuity_tracking_v1 | claude-haiku-4-5 | Sonnet 4.6 (0.978) | **Haiku 4.5 (0.948)** — DONE |

### Modules WITHOUT evals (4 AI modules)

| Module | Current Default | Task Type | Eval Difficulty |
|--------|----------------|-----------|-----------------|
| script_bible_v1 | claude-sonnet-4-6 | Full-script bible extraction | Medium — structured output, can use golden ref |
| entity_discovery_v1 | claude-haiku-4-5 | Chunked entity scanning | Medium — entity list comparison |
| editorial_direction_v1 | claude-sonnet-4-6 | Creative direction generation | Hard — subjective quality |
| sound_and_music_v1 | claude-sonnet-4-6 | Sound/music direction | Hard — subjective quality |

Note: `intent_mood_v1` and `look_and_feel_v1` share the same pattern as `editorial_direction_v1` — they're all creative direction modules. One eval pattern covers the class.

### Non-AI modules (no eval needed)

`story_ingest_v1`, `timeline_build_v1`, `track_system_v1` — pure code, no model selection.

## Acceptance Criteria

- [ ] All 9 existing evals (excluding continuity, already done) re-run with value analysis: token counts captured, cost per call computed, value ranking produced
- [ ] A value analysis report produced for each eval showing: model, quality score, cost/call, value (score/$)
- [ ] Module defaults updated to the best-value model where the value winner differs from the quality winner by <5% quality but >2x cost savings
- [ ] At least 2 new evals created for currently-uncovered AI modules (script_bible and entity_discovery are the most tractable)
- [ ] Creative direction modules assessed — either eval created or documented justification for why eval isn't feasible yet (with a detection mechanism for when it becomes feasible)
- [ ] All module.yaml defaults reflect eval-validated choices
- [ ] Updated eval catalog in AGENTS.md with value analysis column

## Out of Scope

- Changing the try-validate-escalate architecture
- Per-request dynamic model selection (pick model based on input complexity)
- Cost tracking UI changes
- New providers beyond the existing 13 (4 OpenAI, 4 Anthropic, 5 Google)

## Approach Evaluation

- **Re-running evals is mechanical** — the evals and scorers already exist. The new work is computing cost per call from token counts and comparing value. Pure code.
- **Script bible eval** is straightforward: structured output against a golden reference, same pattern as character/location/prop evals.
- **Entity discovery eval**: compare discovered entity lists against golden character/location/prop lists from The Mariner.
- **Creative direction evals** are the hardest — output is subjective prose. Candidate approaches: (a) LLM-rubric-only eval (no Python structural scorer), (b) rubric + field-presence checker, (c) defer and document why.
- The value analysis script pattern from `benchmarks/scripts/analyze-continuity.js` can be generalized.
- **Eval**: Existing promptfoo evals + new script_bible/entity_discovery evals distinguish model quality. Value analysis distinguishes cost-effectiveness.

## Tasks

- [ ] Generalize `analyze-continuity.js` into a reusable `analyze-eval.js` that reads any eval result JSON and produces a value ranking table
- [ ] Re-run existing evals with `--output` to capture token usage:
  - [ ] character-extraction
  - [ ] location-extraction
  - [ ] prop-extraction
  - [ ] relationship-discovery
  - [ ] config-detection
  - [ ] scene-extraction
  - [ ] normalization
  - [ ] scene-enrichment
  - [ ] qa-pass
- [ ] Run value analysis on each eval's results
- [ ] Create script_bible eval (golden ref + Python scorer + LLM rubric)
- [ ] Create entity_discovery eval (golden ref + Python scorer)
- [ ] Assess creative direction eval feasibility
- [ ] Update module.yaml defaults for any module where best-value differs from current default
- [ ] Update AGENTS.md eval catalog with value analysis column
- [ ] Run `/verify-eval` after each eval — classify all mismatches, fix golden if needed, document verified scores. Re-assess acceptance criteria against verified scores.
- [ ] Run full pipeline smoke test to verify updated defaults produce valid output

## Notes

- The continuity extraction eval (Story 092) proved the pattern: Haiku 4.5 is 5x cheaper than Sonnet 4.6 with only 3% quality loss. Similar results are likely for structured extraction tasks (character/location/prop bibles, entity graph).
- The relationship discovery eval showed a 7-way tie at 0.995 — this almost certainly means the cheapest model (Nano or Flash Lite) is the correct choice.
- Config detection already showed Haiku winning on quality — it's probably also the best value by a wide margin.
- For creative direction modules, the "quality" axis is inherently subjective. An LLM-rubric-only eval with Opus as judge may be sufficient, but the scores will have higher variance than structural evals.
- Cost estimates use published pricing as of March 2026. Re-check pricing before running — model costs change frequently.
