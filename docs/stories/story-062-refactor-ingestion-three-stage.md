# Story 062 — 3-Stage Ingestion: Intake, Breakdown, Analysis

**Priority**: High
**Status**: Pending
**Spec Refs**: docs/spec.md#pipeline-processing
**Depends On**: story-061

## Goal

Refactor the ingestion pipeline to split structural extraction (Inventory) from creative analysis (Insight). This architectural pivot addresses the "lc-3 bottleneck" where users must wait for deep narrative analysis before seeing a basic script index or character list.

## Acceptance Criteria

- [ ] Pipeline split into three distinct stages:
    1.  **Intake**: Source -> Clean Fountain (Deterministic Lock).
    2.  **Breakdown**: Scenes + Entities (The Skeleton/Inventory).
    3.  **Analysis**: Beats + Tone + Subtext (The Creative Layer/Insight).
- [ ] `Breakdown` stage delivers a navigable scene index and cast list without waiting for LLM narrative analysis.
- [ ] `Analysis` stage is technically optional and can be toggled or deferred.
- [ ] `Analysis` implements "Macro-Analysis" (processing multiple scenes in a single LLM call) to improve narrative consistency and reduce API latency overhead.
- [ ] Data integrity preserved: Enriched analysis artifacts are correctly merged with or linked to the structural scene artifacts.

## Out of Scope

- Implementing a "streaming" UI for analysis results (this story is pipeline-centric).
- Rewriting the core Fountain normalization logic.

## AI Considerations

- **Tiered Intelligence**: `Breakdown` is an identity/categorization problem; it can use faster, cheaper models (e.g., Claude Haiku). `Analysis` is a reasoning problem; it requires high-end models (e.g., Claude Sonnet/Opus or Gemini Pro).
- **Contextual Synergy**: While splitting stages requires re-reading the script, processing 5-10 scenes at once in the `Analysis` stage is more token-efficient and provides better story-arc consistency than per-scene calls.

## Tasks

- [ ] Define updated schemas for `SceneInventory` (structural) vs. `SceneInsight` (narrative).
- [ ] Create `scene_breakdown_v1` module by extracting the structural logic from the current `scene_extract_v1`.
- [ ] Create `scene_analysis_v1` module to handle beats, tone, and subtext.
- [ ] Implement "Macro-Analysis" logic in `scene_analysis_v1` to batch 5-10 scenes per LLM call.
- [ ] Update `mvp_ingest` recipe to reflect the new 3-stage flow.
- [ ] Update `ProjectConfig` to include a toggle for `perform_deep_analysis`.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5).

## Files to Modify

- `src/cine_forge/modules/ingest/scene_breakdown_v1/main.py` — New module.
- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — New module.
- `configs/recipes/recipe-mvp-ingest.yaml` — Update execution order.
- `src/cine_forge/schemas/scene.py` — Potential schema splits.
- `docs/spec.md` — Update stage definitions.

## Notes

### The Reasoning (Inventory vs. Insight)
In the previous architecture, `scene_extract_v1` was a bottleneck because it performed "Creative Labor" (summarizing beats and analyzing tone) sequentially or in parallel but *before* the stage could be marked done. For a 30-scene script, this created a multi-minute "black box" where the user couldn't even see their character list.

By splitting them:
1.  **Breakdown** provides the "Skeleton" (Inventory) almost immediately. It identifies that "DANTE" is a character and "ACT ONE" is a marker.
2.  **Analysis** provides the "Meaning" (Insight). It can run while the user is already navigating the Breakdown results.

### Macro-Analysis
Moving analysis out of the critical path allows us to stop doing "per-scene" analysis calls. Instead, we can send "Act 1" or "Scenes 1-10" to a model. This gives the AI visibility into the **pacing and character arcs**, leading to much higher quality narrative beats than looking at scenes in isolation.

## Work Log

- 2026-02-21 — created story-062 / architectural pivot based on performance analysis
