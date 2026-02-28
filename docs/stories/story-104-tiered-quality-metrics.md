# Story 104 — Tiered Quality Metrics for Eval Scoring

**Priority**: High
**Status**: Draft
**Spec Refs**: —
**Depends On**: —

## Goal

Add importance tier tagging (major/supporting/minor) to golden reference entities and implement per-tier recall thresholds in eval scorers. Flat recall metrics hide whether the pipeline misses protagonists or unnamed extras. Dossier demonstrated that 0.67 flat recall = 1.00 major + 0.93 supporting — the pipeline was actually useful but the metric said otherwise. Apply the same insight to CineForge's character, location, and prop extraction evals.

## Notes

- Sourced from Scout 003 (Dossier's ImportanceTier + tiered_recall pattern, Story 024)
- Implementation reference: `/Users/cam/Documents/Projects/dossier/src/dossier/scoring.py` — `tiered_recall()` is ~60 lines
- Golden files to tag: `benchmarks/golden/the-mariner-characters.json`, `-locations.json`, `-props.json`
- Tier assignment criteria: major = significant plot role / multiple scenes, supporting = named with arc impact, minor = mentioned once or background
- Per-tier thresholds: major >= 0.90, supporting >= 0.70, minor = informational only
- Flat recall kept as catastrophic regression bar (e.g., >= 0.50)
- Update Python scorers in `benchmarks/scorers/` to report per-tier metrics
- Benchmark workspace is in the `cine-forge-sidequests` worktree

## Work Log

20260228 — Created as Draft from Scout 003 finding #8.
