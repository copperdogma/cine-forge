# Story 092 — Continuity AI Detection & Gap Analysis

**Priority**: Medium
**Status**: Pending
**Spec Refs**: 6 (Bibles, Entity Graph, Continuity)
**Depends On**: 011 (Continuity Tracking — schemas + skeleton)

## Goal

Story 011 landed the continuity infrastructure: schemas (`ContinuityState`, `ContinuityEvent`, `ContinuityIndex`, `EntityTimeline`), the `continuity_tracking_v1` module skeleton, and the `narrative_analysis` recipe. But the AI brain was never implemented — for non-mock models, the module returns empty properties, zero change events, and a hardcoded 0.5 confidence score.

This story implements the actual LLM-powered continuity detection: reading script text scene-by-scene, tracking how entity state changes (costume, injuries, emotional state, lighting, time of day, prop condition), detecting continuity events with evidence, and flagging gaps where state is ambiguous or contradictory. It also fixes the `NODE_FIX_RECIPES` mapping that currently points continuity at the wrong recipe.

## Acceptance Criteria

- [ ] For non-mock models, `continuity_tracking_v1` calls the LLM to extract state properties from actual script text for each entity present in each scene
- [ ] `ContinuityEvent` records are produced when a property value changes between scenes, with `previous_value`, `new_value`, `reason`, `evidence` (script quote), and `is_explicit` (stated vs inferred)
- [ ] State properties cover at minimum: costume/wardrobe, physical condition/injuries, emotional state, and location-specific state (lighting, time of day, weather)
- [ ] `EntityTimeline.gaps` is populated with scene IDs where entity state is ambiguous or contradictory
- [ ] `ContinuityIndex.total_gaps` reflects actual detected gaps, not hardcoded 0
- [ ] `ContinuityIndex.overall_continuity_score` is computed from actual confidence scores across all timelines
- [ ] `NODE_FIX_RECIPES["continuity"]` is corrected from `"world_building"` to `"narrative_analysis"`
- [ ] The module reads actual script text for each scene (from `canonical_script` input, sliced by scene boundaries from `scene_index`)
- [ ] LLM calls include previous scene state as context so the model can detect changes
- [ ] Cost tracking (`total_cost`) is populated with real token counts from LLM calls
- [ ] Unit tests cover: state extraction from script text, change event detection, gap detection, cost accumulation
- [ ] Integration test runs the module against The Mariner with a real model and produces semantically meaningful output (not empty/placeholder)

## Out of Scope

- Continuity *repair* or auto-fix suggestions (that's a Continuity Supervisor role concern)
- Story-order vs scene-order dual timelines (future enhancement)
- UI changes to the ContinuityViewer (existing viewer should render the richer data as-is)
- Cross-scene prop tracking (props that move between characters/locations) — track within entity only for now

## AI Considerations

This is almost entirely an LLM reasoning problem:
- **LLM call**: Reading script text and extracting what state an entity is in (costume, injuries, emotion, lighting). This is a comprehension + structured extraction task — classic LLM territory.
- **LLM call**: Comparing previous state to current state and identifying what changed and why. The model needs prior state as context.
- **Code**: Scene text slicing (from canonical_script using scene_index boundaries), state diffing logic for gap detection, cost accumulation, artifact assembly.
- **Code**: Prompt construction — build a prompt template that includes entity info, previous state, and the scene's script text.

Use the existing `src/cine_forge/ai/llm.py` infrastructure for LLM calls (resilience, retries, model escalation). Consider batching — if a scene has 3 characters present, one LLM call per entity or one call for all entities in the scene (the latter is cheaper but may reduce quality).

## Tasks

- [ ] Fix `NODE_FIX_RECIPES["continuity"]` in `src/cine_forge/pipeline/graph.py` — change `"world_building"` to `"narrative_analysis"`
- [ ] Add scene text slicing utility: given `canonical_script` content and `scene_index` entries, extract the script text for a specific scene
- [ ] Design and implement the continuity extraction prompt template — input: entity info (from bible), previous state properties, scene script text; output: structured JSON with properties and change events
- [ ] Implement the real AI path in `_generate_state_snapshot()` — call LLM with the prompt, parse response into `ContinuityState` with populated `properties` and `change_events`
- [ ] Wire `canonical_script` text into the module (currently the module receives scene_index but doesn't use the actual script text)
- [ ] Implement gap detection: compare adjacent scene states per entity, flag scenes where confidence is low or state contradicts prior state without explanation
- [ ] Compute real `overall_continuity_score` from per-entity timeline confidence averages
- [ ] Populate `total_cost` with actual LLM token usage
- [ ] Add unit tests: mock LLM responses, verify state extraction, change event logic, gap detection
- [ ] Add integration test with The Mariner: run with real model, verify output has populated properties/events
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/pipeline/graph.py` — Fix `NODE_FIX_RECIPES["continuity"]` mapping
- `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` — Implement real AI path, scene text slicing, gap detection, cost tracking
- `src/cine_forge/modules/world_building/continuity_tracking_v1/module.yaml` — Verify inputs include `canonical_script` (may already be there via `store_inputs`)
- `tests/unit/test_continuity_tracking.py` — New: unit tests for AI extraction, change events, gaps
- `tests/integration/test_continuity_integration.py` — New or extend: integration test with real model

## Notes

- The existing schemas (`ContinuityState`, `ContinuityEvent`, `StateProperty`, `EntityTimeline`, `ContinuityIndex`) look sufficient for this work. No schema changes expected.
- The `store_inputs` in the recipe already pulls `canonical_script` from the `normalize` stage and `scene_index` from `breakdown_scenes`, plus all three bible types. The module just doesn't use the script text yet.
- Consider one LLM call per scene (covering all present entities) vs one per entity per scene. Per-scene is cheaper but may lose detail for minor characters. Start with per-scene, split if quality is poor.
- LLM resilience (retry + model escalation) is already built into `src/cine_forge/ai/llm.py` — reuse it.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
