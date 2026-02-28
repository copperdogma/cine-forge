# Story 105 — Parallel Chunk Extraction via ThreadPoolExecutor

**Priority**: High
**Status**: Draft
**Spec Refs**: —
**Depends On**: —

## Goal

Parallelize LLM API calls within pipeline modules that process independent chunks (per-scene extraction, per-entity bible generation). Currently these run sequentially, making large screenplays take 60-90 minutes. Dossier achieved 28-42x speedup using `ThreadPoolExecutor(max_workers=10)` with thread-safe Instructor/httpx backends. Apply the same pattern to CineForge's extraction modules.

## Notes

- Sourced from Scout 003 (Dossier Story 023 — parallel extraction)
- Implementation reference: `/Users/cam/Documents/Projects/dossier/src/dossier/engine.py` lines 70-110
- Key design points:
  - `ThreadPoolExecutor(max_workers=10)` with `pool.map()`
  - Skip thread pool for single-chunk case (avoid overhead)
  - Configurable `max_workers` parameter
  - Thread-safe: Instructor + httpx backend handles concurrent requests
- CineForge modules to evaluate for parallelization:
  - `entity_discovery_v1` — per-scene character/prop extraction
  - `character_bible_v1` — per-character bible generation
  - `location_bible_v1` — per-location bible generation
  - `scene_enrichment_v1` — per-scene metadata enrichment
- Risk: rate limiting from API providers — may need backoff or lower max_workers
- Consider whether the driver's stage-level caching interacts with inner-loop parallelism

## Work Log

20260228 — Created as Draft from Scout 003 finding #9.
