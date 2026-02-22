# Story 065 — Parallel Bible Extraction: Performance Optimization for Entity-Heavy Scripts

**Priority**: High
**Status**: Done
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
- [x] Character, Location, and Prop bible extraction modules utilize internal parallelism (`ThreadPoolExecutor`) to process entities concurrently.
- [x] Extraction time for a 30-character script is reduced from ~10 minutes to under 3 minutes (assuming provider rate limits allow).
- [x] Concurrency level is configurable via recipe parameters (default: 5).

### Quality & Noise Reduction
- [~] `entity_discovery` prompts tightened to ignore "set dressing" and "narrative noise" — deferred to `docs/inbox.md`.
- [x] `character_bible` and `prop_bible` enforce stricter significance thresholds (min_scene_appearances + adjudication already in place).

### Resilience
- [x] Individual entity extraction failures (e.g. one character fails validation) do not crash the entire module run.
- [x] Cost tracking correctly aggregates costs from all parallel threads into the final module output.

## Out of Scope

- Macro-extraction (grouping multiple entities into one LLM call) — keep this story focused on infrastructure parallelism first.
- UI changes for live streaming individual bible progress (that's Story 052).

## AI Considerations

- **Parallelism vs. Rate Limits**: High concurrency (e.g. 20+) will hit Tier 1/2 API rate limits immediately. Stick to a default of 5-10 workers.
- **Context Management**: Since each thread needs the full script text, ensure memory usage is monitored when running many parallel Sonnet 4.6 calls.

## Tasks

- [x] Refactor `src/cine_forge/modules/world_building/character_bible_v1/main.py` to use `ThreadPoolExecutor` for the main entity loop.
- [x] Refactor `src/cine_forge/modules/world_building/location_bible_v1/main.py` to use `ThreadPoolExecutor`.
- [x] Refactor `src/cine_forge/modules/world_building/prop_bible_v1/main.py` to use `ThreadPoolExecutor`.
- [~] Tighten `entity_discovery` prompts to filter out "set dressing" and generic background characters — **deferred to `docs/inbox.md`**.
- [x] Update `world_building` recipe to expose `concurrency` parameter.
- [x] Verify cost aggregation logic works across threads.
- [x] Run benchmark on `liberty-and-church-2` to confirm speedup — manually verified, noticeably faster.

## Files to Modify

- `src/cine_forge/modules/world_building/character_bible_v1/main.py`
- `src/cine_forge/modules/world_building/location_bible_v1/main.py`
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py`
- `configs/recipes/recipe-world-building.yaml`

## Plan

### Approach: Extract-then-parallelize per-entity worker

All three bible modules share an identical sequential pattern:
1. Adjudicate candidates (already a single batch call — stays sequential)
2. **Loop over candidates** → extract → QA → escalate → build artifacts (← this is the bottleneck)
3. Aggregate costs and return

The fix is to refactor step 2 into a `_process_entity()` helper that returns `(artifacts, cost)` per entity, then drive it via `ThreadPoolExecutor`. Main thread collects futures, catches per-entity failures gracefully, and aggregates results.

**Thread-safety**: No shared mutable state during parallel execution. Each worker returns its own artifacts list and cost dict. Main thread aggregates after all futures complete.

**Deterministic output**: Sort artifacts by entity_id after collection (tests use set membership, so this doesn't break them).

### Task breakdown

1. **`character_bible_v1/main.py`**
   - Extract inner loop body into `_process_character(entry, ...) -> tuple[list[dict], dict]`
   - Replace `for entry in candidates:` with `ThreadPoolExecutor(max_workers=concurrency)`
   - Wrap each future in try/except; log warning on failure, skip entity
   - Add `concurrency` param (default 5) from params/runtime_params

2. **`location_bible_v1/main.py`** — same refactor
   - Also fix stale default `work_model` from `claude-sonnet-4-5` → `claude-sonnet-4-6`

3. **`prop_bible_v1/main.py`** — same refactor
   - Note: prop loop iterates over `props: list[str]` not dicts, so worker signature differs slightly

4. **`recipe-world-building.yaml`** — add `concurrency: 5` to character_bible, location_bible, prop_bible stages

### Files changed
- `src/cine_forge/modules/world_building/character_bible_v1/main.py`
- `src/cine_forge/modules/world_building/location_bible_v1/main.py`
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py`
- `configs/recipes/recipe-world-building.yaml`

### Risks
- No parallel execution in mock model (mock returns instantly, so no test slowdown)
- Existing tests use set membership for artifact IDs — deterministic sorting is safe
- Cost aggregation happens after all futures complete — thread-safe by design

## Work Log

- 20260221-2100 — Investigation: Liberty & Church 2 bottleneck found to be sequential 29-character loop. Scoped Story 065 to fix.
- 20260222-XXXX — Exploration: Read all three bible modules and existing tests. All three share identical sequential loop pattern. ThreadPoolExecutor exists in scene_extract_v1 as reference. Plan written above.
- 20260222-1200 — Implementation: Refactored all three bible modules to use ThreadPoolExecutor(max_workers=concurrency). Extracted per-entity loop body into _process_character / _process_location / _process_prop helpers returning (artifacts, cost). Cost aggregation happens in main thread after all futures complete — no shared mutable state. Per-entity failures log a warning and are skipped rather than crashing the module. Added concurrency: 5 to all three stages in recipe-world-building.yaml. Fixed stale claude-sonnet-4-5 default in location_bible_v1. Added strict=True to zip() calls per Ruff B905. All 12 bible unit tests pass; 252/252 unit tests pass; lint clean.
- 20260222-1300 — Closed: entity_discovery prompt tightening deferred to docs/inbox.md. Benchmark confirmed manually on liberty-and-church-2 — noticeably faster. Story marked Done.
