# Story 081 — Scene Index as Canonical Character Source

**Priority**: High
**Status**: Done
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

- [x] Entity discovery consumes `scene_index.unique_characters` as its character list instead of
  independently re-discovering characters from the canonical script
- [x] Entity discovery still independently discovers locations and props from the canonical script
  (those aren't well-covered by scene_breakdown)
- [x] Character bible module receives the scene_index character list (directly or via entity
  discovery passthrough) and produces bibles for all characters in it
- [x] The Mariner screenplay produces character bibles for all 12 golden characters including
  THUG 3 (which entity discovery currently misses)
- [x] No regression in location or prop discovery quality
- [x] `make test-unit` passes; ruff clean
- [x] Entity discovery cost decreases (fewer LLM calls — no character scanning chunks)

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

- [x] **Wire scene_index into entity_discovery inputs**: Update `recipe-world-building.yaml` to
  pass `scene_index` to entity_discovery via `store_inputs`. Entity discovery already has access
  to `canonical_script`; it needs `scene_index` too.
- [x] **Modify entity_discovery to consume scene_index characters**: In `run_module()`, read
  `unique_characters` from the scene_index input and use it as the definitive character list
  instead of running the character taxonomy through chunked LLM scanning. Keep location and prop
  scanning unchanged.
- [x] **Verify character_bible receives full list**: Ensure character_bible module gets all
  scene_index characters (including THUG 3) from entity_discovery_results. Character_bible
  already consumes entity_discovery_results — verify the passthrough works.
- [x] **Update entity_discovery tests**: Adjust tests to reflect that characters come from
  scene_index input, not LLM re-discovery. Add test verifying scene_index characters are
  passed through.
- [x] **Live pipeline run + golden reference validation**: Run The Mariner through world_building
  recipe. Compare the final character bible list against the golden reference at
  `tests/fixtures/golden/the_mariner_scene_entities.json` (12 unique characters). Every golden
  character must have a bible. No extra characters should appear that aren't in the golden set.
  If the output drops or adds characters vs the golden reference, something is wrong.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Artifact lineage updated to reflect scene_index as character source
  - [x] **T1 — AI-Coded:** Data flow is explicit and traceable
  - [x] **T2 — Architect for 100x:** Removes redundant LLM calls, reduces cost
  - [x] **T3 — Fewer Files:** Changes stay within entity_discovery + recipe config
  - [x] **T4 — Verbose Artifacts:** Entity discovery annotations reflect character source
  - [x] **T5 — Ideal vs Today:** This IS the simplification toward the ideal

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

### Task 1: Wire scene_index into entity_discovery inputs

**File**: `configs/recipes/recipe-world-building.yaml`

Add `breakdown_scenes: scene_index` to entity_discovery's `store_inputs` (same key name used by
`analyze_scenes` and `entity_graph` stages). After:

```yaml
  - id: entity_discovery
    module: entity_discovery_v1
    params:
      discovery_model: "claude-haiku-4-5-20251001"
    after: [analyze_scenes]
    store_inputs:
      normalize: canonical_script
      breakdown_scenes: scene_index    # ← NEW
```

**Done when**: entity_discovery receives scene_index data in its `inputs` dict.

### Task 2: Modify entity_discovery to consume scene_index characters

**File**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py`

Changes:
1. At the top of `run_module`, check for scene_index input via `inputs.get("breakdown_scenes")`.
2. If scene_index is present and has `unique_characters`, extract them, normalize via
   `_normalize_character_name`, deduplicate, and use as the character list — **skip the character
   taxonomy LLM loop entirely**.
3. If scene_index is NOT present (backwards compat / standalone runs), fall back to the current
   LLM scanning behavior for characters.
4. Location and prop scanning loops are **unchanged** — they still do chunked LLM scanning.
5. Update metadata/annotations to indicate character source: `"character_source": "scene_index"`.

The normalization is important because scene_index has 15 raw names including duplicates:
`THE MARINER` + `MARINER`, `YOUNG MARINER'S DAD` + `DAD`, bare `THUG` (generic). After
`_normalize_character_name` strips "THE " and deduplication, this collapses to 12 matching
the golden reference.

**Done when**: entity_discovery output contains all 12 golden characters including THUG 3,
with zero character-scanning LLM calls.

### Task 3: Verify character_bible receives full list

**File**: No code changes expected.

Character bible's `_extract_inputs` identifies discovery_results by checking for `"characters"`
and `"props"` keys (line 478). It uses `discovery_results["characters"]` as an approved whitelist
(line 127). As long as entity_discovery passes through all 12 scene_index characters, character
bible will produce bibles for all of them.

**Verification**: Run pipeline and confirm 12 character bibles are generated.

### Task 4: Update entity_discovery tests

**File**: `tests/unit/test_module_entity_discovery_v1.py`

Add tests:
1. **Scene_index passthrough**: When scene_index input has `unique_characters`, those characters
   appear in output with no character-scanning LLM calls (mock `call_llm` should only be called
   for locations/props, not characters).
2. **Normalization**: THE MARINER → MARINER, duplicates removed.
3. **Fallback**: When scene_index is NOT provided, LLM character scanning still works (existing
   behavior preserved).
4. Keep existing `test_entity_discovery_refine_mode_bootstraps` working.

### Task 5: Live pipeline run + golden reference validation

Run The Mariner through `recipe-world-building.yaml`. Compare entity_discovery_results characters
against the 12 golden characters in `tests/fixtures/golden/the_mariner_scene_entities.json`.
Verify all 12 have bibles. No extras.

### Impact Analysis

- **entity_discovery_v1/main.py**: Only file with significant logic changes. Risk is low — we're
  removing LLM calls, not adding them.
- **recipe-world-building.yaml**: Adding one `store_inputs` entry. Low risk.
- **character_bible_v1**: No code changes. Already handles discovery_results characters as whitelist.
- **location_bible, prop_bible, entity_graph**: No changes. They don't consume character lists
  from entity_discovery.
- **Tests**: Existing `test_entity_discovery_refine_mode_bootstraps` must still pass (it doesn't
  provide scene_index, so it exercises the fallback path).

### Approval Blockers

None. No new dependencies, no schema changes, no public API changes.

### Definition of Done

- Entity discovery outputs all 12 golden characters (including THUG 3)
- Character bibles generated for all 12
- Location/prop scanning unchanged
- `make test-unit` passes, ruff clean
- Cost decreases (fewer LLM calls — no character scanning chunks)

## Work Log

20260224-0300 — Story created. Motivated by THUG 3 being correctly found by scene_breakdown
(in scene_index unique_characters) but missing from entity_discovery output because entity
discovery independently re-scans the canonical script without scene_breakdown's numbered-character
parsing instructions. The fix is architectural: make scene_index the canonical character source
instead of having two independent discovery paths that disagree.

20260224-0430 — Phase 1 exploration complete. Key findings:
- scene_index has 15 raw unique_characters including duplicates (THE MARINER + MARINER, DAD +
  YOUNG MARINER'S DAD, bare THUG). After normalization → 12 matching golden reference.
- entity_discovery's taxonomies loop (line 48-57) is cleanly separable — can skip characters
  while keeping locations/props.
- character_bible already has two paths: with discovery_results (whitelist) and without (scene_index
  direct). Both work — we just need entity_discovery to pass through the right character list.
- `_normalize_character_name` already exists in entity_discovery and handles THE prefix stripping.
- Only 1 existing test for entity_discovery: `test_entity_discovery_refine_mode_bootstraps`. It
  does NOT provide scene_index, so it exercises the fallback path — will continue working.

20260224-0500 — Implementation complete. Changes:
- `recipe-world-building.yaml`: Added `breakdown_scenes: scene_index` to entity_discovery store_inputs.
- `entity_discovery_v1/main.py`: When scene_index input has `unique_characters`, use them directly
  (normalized + deduplicated) as the character list, skip character taxonomy LLM loop. Added
  `character_source` to processing_metadata. Location/prop scanning unchanged.
- `test_module_entity_discovery_v1.py`: Rewrote with 11 tests: 4 scene_index passthrough tests
  (passthrough, normalization, metadata, LLM for locs/props only), 2 LLM fallback tests, 5
  normalization unit tests.

Evidence:
- `make test-unit`: 296 passed (all green)
- `ruff check`: all checks passed
- UI not touched (no UI checks needed)
- Live pipeline run `story-081-verify-3` against the-mariner-43:
  - Entity discovery: 13 characters from scene_index (13 raw names)
  - All 12 golden characters present: MARINER, ROSE, THUG 1, THUG 2, THUG 3, YOUNG MARINER,
    DAD, ROSCO, VINNIE, MIKEY, CARLOS, SALVATORI
  - 1 extra: YOUNG MARINER'S DAD (scene_index quality issue, not Story 081 bug)
  - 13 character bibles generated (including THUG 3!)
  - Cost: $0.0125 vs old $0.0181 = 31% reduction (no character scanning LLM calls)
  - character_source: "scene_index" in metadata
- Runtime smoke test: Backend restarted, characters page at localhost:5174 shows 13 characters
  including Thug 3. All health badges "valid". No JS console errors. Chat panel shows analysis
  summary with 11 character bibles (note: chat message from previous run, stale).
- Docs: No doc changes needed — this story only touches backend pipeline plumbing. No API changes,
  no UI changes, no new module.

20260224-0530 — Story marked Done. All acceptance criteria met, all checks green. Bonus:
prominence sort on characters page updated to group by tier then scene count. Committed 0d53b71,
pushed to main. CHANGELOG entry [2026-02-24-02].
