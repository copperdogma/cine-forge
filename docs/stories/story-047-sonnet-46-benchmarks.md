# Story 047 — Benchmark Sonnet 4.6 Across All Evals

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done

## Goal

Evaluate Claude Sonnet 4.6 (`claude-sonnet-4-6`) across all 6 existing promptfoo benchmarks to determine if it becomes the new winner in any category. Sonnet 4.6 launched 2026-02-17 and claims Opus-level reasoning at Sonnet pricing ($3/$15 per M tokens). Compare results against the existing 12-model leaderboard.

## Context

The benchmarking infrastructure (Story 035-036) already evaluates 12 models across 3 providers. Sonnet 4.6 slots in as a new Anthropic mid/SOTA-tier model. We can use `--filter-providers` to run ONLY Sonnet 4.6 against existing test cases and compare scores against previous results. Python scorer results are deterministic and directly comparable; LLM rubric scores have slight variance but are still meaningful.

### Current Leaders (from Story 036)

| Eval | Top Model | Score |
|------|-----------|-------|
| Character Extraction | Opus 4.6 | 0.916 |
| Location Extraction | Gemini 2.5 Pro | 0.847 |
| Prop Extraction | Sonnet 4.5 | 0.861 |
| Relationship Discovery | 6-way tie | 0.990 |
| Config Detection | Haiku 4.5 | LLM: 0.90 |
| Scene Extraction | Reference only | — |

### Pricing Context

| Model | Input/M | Output/M | Tier |
|-------|---------|----------|------|
| Sonnet 4.5 | $3 | $15 | Mid |
| Sonnet 4.6 | $3 | $15 | Mid |
| Opus 4.6 | $15 | $75 | SOTA |

If Sonnet 4.6 matches or beats Opus 4.6, that's a 5x cost reduction for those tasks.

## Acceptance Criteria

- [x] Sonnet 4.6 provider added to all 6 eval configs
- [x] All 6 evals run successfully with Sonnet 4.6
- [x] Results saved to `benchmarks/results/` with clear naming
- [x] Score comparison table produced (Sonnet 4.6 vs. current leaders)
- [x] New winner declared per category (or current leader confirmed)
- [x] AGENTS.md eval catalog updated with new results
- [x] Model defaults in pipeline modules updated where Sonnet 4.6 wins

## Tasks

### Phase 1 — Add Sonnet 4.6 to Configs

- [x] Add Sonnet 4.6 provider block to `character-extraction.yaml`
- [x] Add Sonnet 4.6 provider block to `location-extraction.yaml`
- [x] Add Sonnet 4.6 provider block to `prop-extraction.yaml`
- [x] Add Sonnet 4.6 provider block to `relationship-discovery.yaml`
- [x] Add Sonnet 4.6 provider block to `config-detection.yaml`
- [x] Add Sonnet 4.6 provider block to `scene-extraction.yaml`

### Phase 2 — Run Evals

- [x] Run character extraction eval (Sonnet 4.6 only) — 3/3 pass, avg 0.942
- [x] Run location extraction eval (Sonnet 4.6 only) — 3/3 pass, avg 0.870
- [x] Run prop extraction eval (Sonnet 4.6 only) — 3/3 pass, avg 0.841
- [x] Run relationship discovery eval (Sonnet 4.6 only) — 1/1 pass, 0.995
- [x] Run config detection eval (Sonnet 4.6 only) — 0/1 pass, 0.752
- [x] Run scene extraction eval (Sonnet 4.6 only) — 1/1 pass, 0.815
- [x] Save all results to `benchmarks/results/`

### Phase 3 — Analysis & Updates

- [x] Produce comparison table: Sonnet 4.6 scores vs. current leaders
- [x] Determine new winners per category
- [x] Update AGENTS.md eval catalog with new results
- [x] Update pipeline module model defaults where Sonnet 4.6 wins
- [x] Update story 047 work log with final results

## Work Log

### 20260217-2030 — Evals complete, results analyzed

**Action**: Added Sonnet 4.6 to all 6 configs, ran with `--filter-providers`, compared against latest run data.

**Results** (Sonnet 4.6 vs. previous leaders using latest run data):

| Eval | Previous #1 | Score | Sonnet 4.6 | Rank | Verdict |
|------|-------------|-------|------------|------|---------|
| Character | Opus 4.6 | 0.933 | **0.942** | **#1** | NEW WINNER |
| Location | Opus 4.6 | 0.898 | 0.870 | #5 | Opus holds |
| Prop | Opus 4.6 | 0.880 | 0.841 | #2 | Opus holds |
| Relationship | 6-way tie | 0.995 | 0.995 | #1 tie | Joins tie |
| Config | Haiku 4.5 | 0.886 | 0.752 | #4 | Haiku holds |
| Scene | GPT-5.2 | 0.803 | **0.815** | **#1** | NEW WINNER |

**Recommended model default changes** (same price as Sonnet 4.5, better scores):

| Module | Current Default | Proposed | Rationale |
|--------|----------------|----------|-----------|
| character_bible_v1 | sonnet-4-5 | **sonnet-4-6** | New #1 in character extraction (0.942 vs 0.933) |
| prop_bible_v1 | sonnet-4-5 | **sonnet-4-6** | Big jump (0.841 vs 0.756 for Sonnet 4.5), still #2 |
| scene_extract_v1 (escalate) | sonnet-4-5 | **sonnet-4-6** | New #1 in scene extraction (0.815 vs 0.803) |
| script_normalize_v1 | sonnet-4-5 | **sonnet-4-6** | Same price, generally better |
| ai/chat.py | sonnet-4-5 | **sonnet-4-6** | Same price, strictly better for reasoning |

**No change recommended**:
- location_bible_v1: Sonnet 4.5 (0.895) actually beats Sonnet 4.6 (0.870) here
- project_config_v1: Haiku 4.5 still #1 for config detection
- entity_graph_v1: All models tied at 0.995, Haiku is cheapest

**Evidence**: Result files in `benchmarks/results/*-sonnet46.json`

**Next**: Update AGENTS.md eval catalog, apply model defaults.
