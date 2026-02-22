# Story 065 — Parallel Bible Extraction: Performance Optimization for Entity-Heavy Scripts

**Priority**: High
**Status**: Pending
**Spec Refs**: 6 Bibles & Entity Graph, 2.7 Cost Transparency
**Depends On**: 008, 009, 055, 060

## Goal

Optimize the world-building pipeline by parallelizing character, location, and prop bible extraction. Current modules process entities sequentially, creating a massive bottleneck (up to 10-15 minutes) for scripts with many candidates (e.g. Liberty & Church 2 with 29 characters and 100+ props).

**The Problem:**
In project `liberty-and-church-2`, the pipeline "hung" for nearly 10 minutes on `character_bible`. Investigation revealed:
- `entity_discovery` was over-liberal, extracting 29 characters and 100+ props (including noise like "WIRES" and "SAUCES").
- `character_bible_v1` loops through these 29 characters sequentially.
- Each character requires at least 2 LLM turns (Work + Verify), totaling ~20s per entity.
- 29 entities x 20s = 580s (9.6 minutes) of serial execution.

## Acceptance Criteria

### Performance
- [ ] Character, Location, and Prop bible extraction modules utilize internal parallelism (`ThreadPoolExecutor`) to process entities concurrently.
- [ ] Extraction time for a 30-character script is reduced from ~10 minutes to under 3 minutes (assuming provider rate limits allow).
- [ ] Concurrency level is configurable via recipe parameters (default: 5).

### Quality & Noise Reduction
- [ ] `entity_discovery` prompts tightened to ignore "set dressing" (static objects characters don't interact with) and "narrative noise" (minor generic characters without names).
- [ ] `character_bible` and `prop_bible` enforce stricter significance thresholds before proceeding to high-fidelity extraction.

### Resilience
- [ ] Individual entity extraction failures (e.g. one character fails validation) do not crash the entire module run.
- [ ] Cost tracking correctly aggregates costs from all parallel threads into the final module output.

## Out of Scope

- Macro-extraction (grouping multiple entities into one LLM call) — keep this story focused on infrastructure parallelism first.
- UI changes for live streaming individual bible progress (that's Story 052).

## AI Considerations

- **Parallelism vs. Rate Limits**: High concurrency (e.g. 20+) will hit Tier 1/2 API rate limits immediately. Stick to a default of 5-10 workers.
- **Context Management**: Since each thread needs the full script text, ensure memory usage is monitored when running many parallel Sonnet 4.6 calls.

## Tasks

- [ ] Refactor `src/cine_forge/modules/world_building/character_bible_v1/main.py` to use `ThreadPoolExecutor` for the main entity loop.
- [ ] Refactor `src/cine_forge/modules/world_building/location_bible_v1/main.py` to use `ThreadPoolExecutor`.
- [ ] Refactor `src/cine_forge/modules/world_building/prop_bible_v1/main.py` to use `ThreadPoolExecutor`.
- [ ] Tighten `entity_discovery` prompts in `src/cine_forge/modules/ingest/scene_extract_v1` (or equivalent discovery modules) to filter out "set dressing".
- [ ] Update `world_building` recipe to expose `concurrency` parameter.
- [ ] Verify cost aggregation logic works across threads.
- [ ] Run benchmark on `liberty-and-church-2` to confirm speedup.

## Files to Modify

- `src/cine_forge/modules/world_building/character_bible_v1/main.py`
- `src/cine_forge/modules/world_building/location_bible_v1/main.py`
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py`
- `configs/recipes/recipe-world-building.yaml`

## Work Log

- 20260221-2100 — Investigation: Liberty & Church 2 bottleneck found to be sequential 29-character loop. Scoped Story 065 to fix.
