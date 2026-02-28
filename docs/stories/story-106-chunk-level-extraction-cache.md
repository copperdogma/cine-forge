# Story 106 — Disk-Backed Chunk-Level Extraction Cache

**Priority**: Medium
**Status**: Draft
**Spec Refs**: —
**Depends On**: —

## Goal

Add a chunk-level LLM extraction cache that sits below CineForge's driver-level artifact cache. When iterating on downstream logic (resolution, scoring, schema changes), the expensive LLM extraction calls shouldn't re-run if the input text, model, and prompt haven't changed. Dossier's chunk cache reduced re-runs from 60-90 minutes to <1 second for the extraction stage.

## Notes

- Sourced from Scout 003 (Dossier Story 023 — disk-backed chunk cache)
- Implementation reference: `/Users/cam/Documents/Projects/dossier/src/dossier/cache.py` (~120 lines, self-contained)
- Cache key = SHA256(chunk text + model ID + system prompt + library version)
- Storage: `~/.cache/cine-forge/chunks/` as one JSON file per chunk
- Atomic writes via `tempfile.mkstemp` + `os.rename`
- Disable via `CINEFORGE_NO_CACHE=1` env var
- Design considerations for CineForge:
  - CineForge's artifact store already caches at the stage level (content-addressed fingerprints)
  - This is an inner-loop optimization for development iteration speed
  - Cache key must include relevant version info to prevent stale results
  - Should integrate with the module's existing output path (don't bypass artifact store)
- Depends on understanding which modules make per-chunk LLM calls vs. single-document calls

## Work Log

20260228 — Created as Draft from Scout 003 finding #11.
