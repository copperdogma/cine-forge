# Story 081 — Scene Index as Canonical Character Source

**Priority**: High
**Status**: Pending
**Spec Refs**: World Building / Entity Discovery, Scene Breakdown
**Depends On**: 080 (LLM-Powered Action Line Entity Extraction)

## Goal

After Story 080, scene_breakdown produces a high-quality `unique_characters` list in the
scene_index via per-scene structural parsing + LLM extraction. Entity discovery then
independently re-scans the entire canonical script for characters — doing redundant work that
produces a *worse* result (e.g., it misses THUG 3 because it can't parse "THUGS 2 & 3" from
action lines without the explicit numbered-character prompt instructions that scene_breakdown
has).

This story makes the scene_index's `unique_characters` the **canonical character list** for the
pipeline. Entity discovery stops re-discovering characters and instead consumes the scene_index
character list as a seed. Its job becomes: discover locations, props, and relationships only.
Downstream modules (character_bible, entity_graph) receive a definitive character list instead of
a potentially incomplete one.

**Why this matters:** The pipeline currently discovers characters twice with different quality
levels, creating confusion when they disagree. Single source of truth = simpler architecture,
fewer bugs, and no more "why is THUG 3 missing?" investigations.

## Acceptance Criteria

- [ ] Entity discovery consumes `scene_index.unique_characters` as its character list instead of
  independently re-discovering characters from the canonical script
- [ ] Entity discovery still independently discovers locations and props from the canonical script
  (those aren't well-covered by scene_breakdown)
- [ ] Character bible module receives the scene_index character list (directly or via entity
  discovery passthrough) and produces bibles for all characters in it
- [ ] The Mariner screenplay produces character bibles for all 12 golden characters including
  THUG 3 (which entity discovery currently misses)
- [ ] No regression in location or prop discovery quality
- [ ] `make test-unit` passes; ruff clean
- [ ] Entity discovery cost decreases (fewer LLM calls — no character scanning chunks)

## Out of Scope

- Changing scene_breakdown's character extraction (that's Story 080, already done)
- Improving location or prop extraction quality (separate stories)
- Changing the character_bible module's LLM prompts or output format
- UI changes (the character list page already reads from character bibles)

## AI Considerations

This story is primarily **orchestration/plumbing**, not an AI problem. The AI work (character
extraction from action lines) was already solved in Story 080. This story rewires the data flow
so downstream modules consume that superior result instead of doing their own inferior extraction.

The only LLM-touching change is removing the `characters` taxonomy from entity_discovery's
chunked scanning loop — it should still scan for locations and props.

## Tasks

- [ ] **Wire scene_index into entity_discovery inputs**: Update `recipe-world-building.yaml` to
  pass `scene_index` to entity_discovery via `store_inputs`. Entity discovery already has access
  to `canonical_script`; it needs `scene_index` too.
- [ ] **Modify entity_discovery to consume scene_index characters**: In `run_module()`, read
  `unique_characters` from the scene_index input and use it as the definitive character list
  instead of running the character taxonomy through chunked LLM scanning. Keep location and prop
  scanning unchanged.
- [ ] **Verify character_bible receives full list**: Ensure character_bible module gets all
  scene_index characters (including THUG 3) from entity_discovery_results. Character_bible
  already consumes entity_discovery_results — verify the passthrough works.
- [ ] **Update entity_discovery tests**: Adjust tests to reflect that characters come from
  scene_index input, not LLM re-discovery. Add test verifying scene_index characters are
  passed through.
- [ ] **Live pipeline run + golden reference validation**: Run The Mariner through world_building
  recipe. Compare the final character bible list against the golden reference at
  `tests/fixtures/golden/the_mariner_scene_entities.json` (12 unique characters). Every golden
  character must have a bible. No extra characters should appear that aren't in the golden set.
  If the output drops or adds characters vs the golden reference, something is wrong.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Artifact lineage updated to reflect scene_index as character source
  - [ ] **T1 — AI-Coded:** Data flow is explicit and traceable
  - [ ] **T2 — Architect for 100x:** Removes redundant LLM calls, reduces cost
  - [ ] **T3 — Fewer Files:** Changes stay within entity_discovery + recipe config
  - [ ] **T4 — Verbose Artifacts:** Entity discovery annotations reflect character source
  - [ ] **T5 — Ideal vs Today:** This IS the simplification toward the ideal

## Files to Modify

- `configs/recipes/recipe-world-building.yaml` — add `scene_index` to entity_discovery's
  `store_inputs`
- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — consume scene_index
  characters instead of LLM re-discovery; keep location/prop scanning
- `tests/unit/test_entity_discovery_module.py` — update tests for new character source
- `docs/stories/story-081-scene-index-canonical-characters.md` — work log

## Notes

- Entity discovery currently uses `store_inputs: {normalize: canonical_script}` — it needs
  scene_index added. The scene_index is already in the artifact store from the ingest recipe.
- The `taxonomies` loop in entity_discovery (line 59) iterates over characters, locations, props.
  The change removes characters from this loop and instead reads them from scene_index input.
- Character bible already gets its character list from entity_discovery_results. As long as
  entity_discovery passes through the scene_index characters in its output, character_bible
  should work without changes.
- The `enable_characters` param could be deprecated or repurposed as an override flag.
- This establishes the pattern: **ingest recipe produces structural facts, world_building recipe
  enriches them**. Characters are a structural fact (who appears in which scene). Character
  bibles are enrichment (personality, arc, relationships).
- **Golden reference as regression gate**: The golden reference at
  `tests/fixtures/golden/the_mariner_scene_entities.json` has 12 hand-verified characters. Use
  it to validate the final character bible output — any character dropped or added vs the golden
  set indicates a pipeline bug. This is the whole point of having a golden master.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260224-0300 — Story created. Motivated by THUG 3 being correctly found by scene_breakdown
(in scene_index unique_characters) but missing from entity_discovery output because entity
discovery independently re-scans the canonical script without scene_breakdown's numbered-character
parsing instructions. The fix is architectural: make scene_index the canonical character source
instead of having two independent discovery paths that disagree.
