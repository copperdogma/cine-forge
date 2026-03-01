# Story 092 — Continuity AI Detection & Gap Analysis

**Priority**: Medium
**Status**: Done
**Spec Refs**: 6 (Bibles, Entity Graph, Continuity)
**Depends On**: 011 (Continuity Tracking — schemas + skeleton)
**Blocks**: 025 (Shot Planning — shots consume continuity states)

## Goal

Story 011 landed the continuity infrastructure: schemas (`ContinuityState`, `ContinuityEvent`, `ContinuityIndex`, `EntityTimeline`), the `continuity_tracking_v1` module skeleton, and the `narrative_analysis` recipe. But the AI brain was never implemented — for non-mock models, the module returns empty properties, zero change events, and a hardcoded 0.5 confidence score.

This story implements the actual LLM-powered continuity detection: reading script text scene-by-scene, tracking how entity state changes (costume, injuries, emotional state, lighting, time of day, prop condition), detecting continuity events with evidence, and flagging gaps where state is ambiguous or contradictory. It also fixes the `NODE_FIX_RECIPES` mapping that currently points continuity at the wrong recipe.

## Acceptance Criteria

- [x] For non-mock models, `continuity_tracking_v1` calls the LLM to extract state properties from actual script text for each entity present in each scene
- [x] `ContinuityEvent` records are produced when a property value changes between scenes, with `previous_value`, `new_value`, `reason`, `evidence` (script quote), and `is_explicit` (stated vs inferred)
- [x] State properties cover at minimum: costume/wardrobe, physical condition/injuries, emotional state, and location-specific state (lighting, time of day, weather)
- [x] `EntityTimeline.gaps` is populated with scene IDs where entity state is ambiguous or contradictory
- [x] `ContinuityIndex.total_gaps` reflects actual detected gaps, not hardcoded 0
- [x] `ContinuityIndex.overall_continuity_score` is computed from actual confidence scores across all timelines
- [x] `NODE_FIX_RECIPES["continuity"]` is corrected from `"world_building"` to `"narrative_analysis"`
- [x] The module reads actual script text for each scene (from `canonical_script` input, sliced by scene boundaries from `scene_index`)
- [x] LLM calls include previous scene state as context so the model can detect changes
- [x] Cost tracking (`total_cost`) is populated with real token counts from LLM calls
- [x] Unit tests cover: state extraction from script text, change event detection, gap detection, cost accumulation
- [x] Integration test runs the module with a real model and produces semantically meaningful output (not empty/placeholder)

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

- [x] Fix `NODE_FIX_RECIPES["continuity"]` in `src/cine_forge/pipeline/graph.py` — change `"world_building"` to `"narrative_analysis"`
- [x] Add scene text slicing utility: given `canonical_script` content and `scene_index` entries, extract the script text for a specific scene
- [x] Design and implement the continuity extraction prompt template — input: entity info (from bible), previous state properties, scene script text; output: structured JSON with properties and change events
- [x] Implement the real AI path in `_generate_state_snapshot()` — call LLM with the prompt, parse response into `ContinuityState` with populated `properties` and `change_events`
- [x] Wire `canonical_script` text into the module (currently the module receives scene_index but doesn't use the actual script text)
- [x] Implement gap detection: compare adjacent scene states per entity, flag scenes where confidence is low or state contradicts prior state without explanation
- [x] Compute real `overall_continuity_score` from per-entity timeline confidence averages
- [x] Populate `total_cost` with actual LLM token usage
- [x] Add unit tests: mock LLM responses, verify state extraction, change event logic, gap detection
- [x] Add integration test with real model, verify output has populated properties/events
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 441 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — all checks passed
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk. Immutable artifacts preserved. New artifacts are additive.
  - [x] **T1 — AI-Coded:** Clear module structure, docstrings, type hints. Another AI session can pick up easily.
  - [x] **T2 — Architect for 100x:** No over-engineering. Single LLM call per scene, simple gap detection.
  - [x] **T3 — Fewer Files:** Single main.py for the module. Response schemas are module-internal, not new files.
  - [x] **T4 — Verbose Artifacts:** Work log has exploration findings, plan, and implementation evidence.
  - [x] **T5 — Ideal vs Today:** Directly implements R3 (perfect continuity). Per-scene batching is efficient.

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

### Architecture Decision: Per-Scene Batched LLM Calls

One LLM call per scene covering all present entities (characters + location + props). This is 45 calls for The Mariner vs ~200+ per-entity calls. The prompt includes all entities' previous states, so the model can reason about interactions. If quality is poor for minor characters, we can split later.

**Response schema**: A lightweight `SceneContinuityExtraction` Pydantic model (not persisted — only for LLM response parsing) containing a list of per-entity state extractions. Each extraction maps to individual `ContinuityState` artifacts.

### Task-by-Task Plan

**Task 1: Fix `NODE_FIX_RECIPES`** — `graph.py:352`
- Change `"continuity": "world_building"` to `"continuity": "narrative_analysis"`
- Also fix `"entity_graph": "world_building"` → `"entity_graph": "narrative_analysis"` (same bug — entity_graph is in the narrative_analysis recipe, not world_building)
- Done when: fix recipe correctly triggers for stale continuity/entity_graph nodes

**Task 2: Wire `canonical_script` into the module** — `main.py:25-30`
- In the input parsing loop, detect `canonical_script` by checking for `"script_text"` key (same pattern as `character_bible_v1` line 474)
- Store as `script_text: str` variable
- Add `_extract_scene_text(script_text, scene_entry)` helper using the established `source_span` pattern: `lines[start_line - 1 : end_line]`
- Done when: each scene's text is available in the processing loop

**Task 3: Include props in `present_entities`** — `main.py:72-77`
- Add props from `scene_entry.get("props_mentioned", [])` to the `present_entities` list
- Use `f"prop:{_slugify(prop)}"` key format (matches existing entity key pattern)
- Done when: props are tracked alongside characters and locations

**Task 4: Full model selection chain** — `main.py:45`
- Replace single-line `work_model` with the 3-tier pattern from `character_bible_v1`: `work_model` / `verify_model` / `escalate_model` with full `params` → `runtime_params` fallback chain
- Done when: model selection matches established convention

**Task 5: Create LLM response schema** — `main.py` (new, top of file)
- `EntityStateExtraction(BaseModel)`: `entity_key: str`, `properties: list[StateProperty]`, `change_events: list[ContinuityEvent]`, `confidence: float`
- `SceneContinuityExtraction(BaseModel)`: `scene_id: str`, `entity_states: list[EntityStateExtraction]`
- These are internal to the module (not registered in schema registry — they're LLM response envelopes, not persisted artifacts)
- Done when: models defined and importable

**Task 6: Build the continuity extraction prompt** — `main.py` (new function)
- `_build_continuity_prompt(scene_entry, scene_text, present_entities, entity_infos, previous_states) -> str`
- Prompt structure:
  1. Role: "You are a Script Supervisor analyzing scene continuity"
  2. Scene context: heading, scene number, full scene text
  3. For each entity: type, name, previous state properties (or "First appearance")
  4. Instructions: extract current properties (costume, physical condition, emotional state, props carried; for locations: lighting, time of day, weather, damage), detect changes with evidence quotes, flag explicit vs inferred
  5. Output format: JSON matching `SceneContinuityExtraction` schema
- Done when: prompt produces well-structured output from a test call

**Task 7: Implement the real AI path** — `main.py:80-83` (replace `pass` stub)
- In the scene loop, when `work_model != "mock"`:
  1. Collect entity infos and previous states for all `present_entities`
  2. Extract scene text via `_extract_scene_text()`
  3. Build prompt via `_build_continuity_prompt()`
  4. Call `call_llm(prompt, model=work_model, response_schema=SceneContinuityExtraction, max_tokens=4096)`
  5. Map each `EntityStateExtraction` to the corresponding `ContinuityState` artifact
  6. Accumulate cost
- Refactor: move the per-entity artifact creation inside the AI path so the LLM response directly populates `properties` and `change_events`
- The mock path remains unchanged (per-entity `_generate_state_snapshot` continues to work for tests)
- Done when: real model calls produce populated `ContinuityState` artifacts with properties and events

**Task 8: Implement gap detection** — `main.py` (new function after all scenes processed)
- `_detect_gaps(timelines, all_states) -> dict[str, list[str]]` returns `{entity_key: [gap_scene_ids]}`
- Gap criteria:
  - Entity present in scene but average property confidence < 0.5
  - Property value contradicts previous scene's value AND no change event explains it
  - Entity has no properties extracted for a scene where it's present
- Populate `EntityTimeline.gaps` for each entity
- Done when: gaps are detected and recorded

**Task 9: Compute real `overall_continuity_score` and `total_gaps`** — `main.py:126-129`
- `overall_continuity_score` = weighted average of per-entity timeline confidence (weighted by number of scenes)
- `total_gaps` = sum of all entity timeline gap counts
- Done when: index reflects real computed values

**Task 10: Wire cost tracking** — `main.py:59-64`
- After each `call_llm()`, accumulate `input_tokens`, `output_tokens`, `estimated_cost_usd` into `total_cost`
- Use `_update_total_cost()` helper (same pattern as character_bible_v1)
- Done when: `total_cost` in return value reflects actual LLM usage

**Task 11: Unit tests** — `tests/unit/test_continuity_tracking_module.py`
- Test 1: Scene text extraction — verify `_extract_scene_text()` slices correctly
- Test 2: Mock LLM response → verify `ContinuityState` artifacts have populated properties and change events
- Test 3: Gap detection — craft states with low confidence / contradictions → verify gaps flagged
- Test 4: Cost accumulation — verify `total_cost` sums correctly
- Test 5: Props included in `present_entities`
- Approach: patch `call_llm` to return canned `SceneContinuityExtraction` responses
- Done when: all tests pass with `pytest -m unit`

**Task 12: Integration test** — `tests/integration/test_continuity_integration.py`
- Run continuity module against The Mariner fixture with a real model
- Assert: at least some `ContinuityState` artifacts have non-empty `properties`
- Assert: at least some `change_events` are produced
- Assert: `total_cost.estimated_cost_usd > 0`
- Mark with `@pytest.mark.integration` (not run in CI)
- Done when: test passes with real model

**Task 13: Fix `module.yaml` default** — `module.yaml`
- Change `default: "gpt-4o"` to `default: "claude-sonnet-4-6"` to match project conventions
- Done when: consistent with other modules

### Impact Analysis

- **No schema changes** — existing `ContinuityState`, `ContinuityEvent`, `StateProperty`, `EntityTimeline`, `ContinuityIndex` are sufficient
- **No recipe changes** — `recipe-narrative-analysis.yaml` already wires `canonical_script` and `scene_index` into the module
- **No UI changes** — the ContinuityViewer already renders `ContinuityState` data; richer data will display automatically
- **Existing mock test** (`test_continuity_tracking_module_mock`) should continue passing — mock path is unchanged
- **Risk**: if `call_llm` with `SceneContinuityExtraction` as response_schema fails for some providers, the retry/escalation in `llm.py` handles it

### Approval Blockers

None — no new dependencies, no schema changes, no public API changes, no recipe changes.

## Work Log

20260228-1400 — Phase 1 Exploration complete.
- Ideal alignment: directly implements R3 (perfect continuity). Quality bar: "Billy punched in Scene 12 → every subsequent scene notes injury." Clear Ideal gap closure.
- Key findings: (1) module skeleton exists but AI path is `pass` stub returning empty properties/0.5 confidence, (2) `canonical_script` declared in recipe but never consumed by module, (3) scene text slicing has established pattern across 5+ modules (`source_span.start_line - 1 : end_line`), (4) `NODE_FIX_RECIPES` maps continuity AND entity_graph to wrong recipe, (5) props never included in `present_entities` despite being parsed, (6) `total_cost` never updated, (7) `total_gaps=0` and `overall_continuity_score=0.9` are hardcoded
- Files that will change: `main.py` (major), `graph.py` (trivial fix), `module.yaml` (default fix), new test files
- Files at risk: none — mock path preserved, UI reads same schema, recipe unchanged
- Patterns to follow: `character_bible_v1` for model selection + cost accumulation, `scene_analysis_v1:301-311` for scene text extraction, `ai/llm.py:call_llm()` for structured LLM calls
- Next: write plan, get approval, implement

20260301-0100 — Implementation complete.
- **Architecture**: One LLM call per scene covering all present entities (characters + location + props). Uses `SceneContinuityExtraction` response schema for structured output, then maps to individual `ContinuityState` artifacts.
- **Files changed**:
  - `src/cine_forge/pipeline/graph.py` — Fixed `NODE_FIX_RECIPES`: continuity and entity_graph now map to `narrative_analysis`
  - `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` — Full rewrite of AI path: wired `canonical_script`, added scene text slicing, created LLM prompt with carry-forward state, implemented `_extract_scene_continuity()`, `_detect_and_record_gaps()`, real score computation, cost tracking, props in `present_entities`
  - `src/cine_forge/modules/world_building/continuity_tracking_v1/module.yaml` — Fixed stale `gpt-4o` default to `claude-sonnet-4-6`
  - `tests/unit/test_continuity_tracking_module.py` — 14 unit tests: mock path (2), scene text extraction (3), AI path with patched LLM (4), gap detection (5)
  - `tests/integration/test_continuity_ai_integration.py` — Integration test with real Haiku model, 3-scene synthetic script
- **Evidence**:
  - 441 unit tests passed, 0 failures
  - Full lint clean (`ruff check src/ tests/`)
  - Integration test: 11 state artifacts (all with properties), 4 gaps detected, $0.019 cost, 0.903 continuity score
  - Mock path unchanged — original Story 011 test continues passing
  - No schema changes, no recipe changes, no UI changes needed

20260301-1500 — Runtime testing & bug fixes.
- **Pydantic forward ref bug**: `from __future__ import annotations` in `main.py` broke `SceneContinuityExtraction` model resolution at runtime. Fixed by removing the import (Python 3.12+ native syntax covers all use cases).
- **Engine `_preload_upstream_reuse` bug**: `start_from` resumption only traversed `stage.needs`, not `stage.needs_all`. Fixed by iterating both in `engine.py`.
- **Stale bible progress spinners**: Bible progress chat messages not resolved when individual stages complete — only on full run finish. Fixed in `use-run-progress.ts` by removing messages per-stage.
- **World-building recipe wiring**: Added `continuity_tracking` stage to `recipe-world-building.yaml` with `needs_all: [character_bible, location_bible, prop_bible]`.
- **Model default updated**: Eval results show Haiku 4.5 at $0.019/run vs Sonnet 4.6 at ~$0.25/run with comparable quality. Updated `module.yaml` default to `claude-haiku-4-5-20251001`.
- Runtime verified on `the-mariner-55`: all stages green, 43 continuity states, 1 continuity index.

20260301-1530 — Validation and closure.
- **Grade: A** — All 12 acceptance criteria met. All checks pass (441 tests, lint clean, UI lint/typecheck/build clean).
- **Eval**: 25/26 assertions pass. 1 failure = GPT-4.1 Nano on `dock_day` LLM rubric (0.70) — classified **model-wrong** (missed emotional state). Expected for cheapest model.
- **Ideal alignment**: Directly implements R3 (perfect continuity). No compromises introduced.
- Story 108 (Continuity UI Page) created as Draft for visualization.
