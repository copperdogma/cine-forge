# Story 073 — Add `after:` ordering-only stage dependency to recipe DSL

**Priority**: Medium
**Status**: Done
**Spec Refs**: N/A
**Depends On**: None

## Goal

The recipe DSL currently uses `needs:` for two different things: data-flow dependencies (stage A
produces outputs that stage B consumes) and ordering constraints (stage B must run after stage A,
but doesn't consume A's outputs). The validator checks schema compatibility on all `needs:`
entries, so using `needs:` for ordering-only triggers false schema mismatch errors — forcing
awkward workarounds (like renaming `store_inputs` keys to avoid overlap). Add `after:` as an
explicit ordering-only key that enforces execution order but is excluded from schema compatibility
checks.

This directly unblocks clean recipe authoring and eliminates an entire class of AI agent errors
discovered during the Story 062 smoke test.

## Acceptance Criteria

- [ ] `RecipeStage` has an `after: list[str]` field (default empty list).
- [ ] `validate_recipe` checks that each `after` entry references a valid stage id (same check as
  `needs`), but does NOT run `_assert_schema_compatibility` on `after` dependencies.
- [ ] `resolve_execution_order` includes `after` in the topological sort so ordering is respected.
- [ ] `_build_parallel_waves` in `engine.py` includes `after` when determining whether a stage is
  eligible to run (a stage blocked by `after` must wait for all `after` stages to complete).
- [ ] `_collect_stage_inputs` in `engine.py` does NOT include `after` stage outputs (ordering only
  — no data is piped).
- [ ] `after` keys do NOT conflict with `store_inputs` keys (overlap check only applies to
  `needs`/`needs_all`).
- [ ] `recipe-world-building.yaml` updated to use `after: [analyze_scenes]` on
  `entity_discovery` instead of the current workaround.
- [ ] Unit tests cover: ordering enforced, schema check skipped, inputs not collected from `after`
  stages, `after` + `needs` can coexist on the same stage.
- [ ] `make test-unit` passes. Ruff passes.

## Out of Scope

- Any changes to `needs_all` semantics.
- Changing how `store_inputs` resolves artifacts.
- UI changes.

## AI Considerations

Pure code — no LLM calls. This is a small, well-scoped DSL extension. The changes are
mechanical: add field, update four specific code paths, update one recipe YAML, write tests.

## Tasks

- [x] Add `after: list[str]` to `RecipeStage` in `src/cine_forge/driver/recipe.py`
- [x] Update `validate_recipe`: validate `after` entries exist in `stage_ids`, remove from
  overlap check
- [x] Update `resolve_execution_order`: include `after` in incoming edge count and children map
- [x] Update `_assert_schema_compatibility`: confirm it only iterates `needs + needs_all` (verify
  `after` is excluded — it already should be, just confirm)
- [x] Update `engine.py` `_compute_execution_waves`: add `stage.after` to deps set
- [x] Update `engine.py` `_collect_inputs`: confirm `after` is NOT included
  (only `needs` passes outputs — verified and left a comment)
- [x] Update `recipe-world-building.yaml`: change `entity_discovery` to `after: [analyze_scenes]`
- [x] Write unit tests in `tests/unit/test_recipe_validation.py` covering the four cases
- [x] Run required checks:
  - [x] `make test-unit PYTHON=.venv/bin/python` — 270 passed
  - [x] `.venv/bin/python -m ruff check src/ tests/` — all checks passed
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data affected.
  - [x] **T1 — AI-Coded:** `after:` is self-explanatory in recipe YAML; comments in engine.py
    explain why it's excluded from input collection.
  - [x] **T2 — Architect for 100x:** Minimal change, no over-engineering.
  - [x] **T3 — Fewer Files:** No new files needed — patch existing recipe.py and engine.py.
  - [x] **T4 — Verbose Artifacts:** Work log captures motivation, decisions, evidence.
  - [x] **T5 — Ideal vs Today:** This IS the ideal — it matches industry standard pipeline DSLs
    (Airflow, Prefect).

## Files to Modify

- `src/cine_forge/driver/recipe.py` — add `after` field to `RecipeStage`; update
  `validate_recipe`, `resolve_execution_order`; confirm `_assert_schema_compatibility` excludes
  `after`
- `src/cine_forge/driver/engine.py` — update `_build_parallel_waves` (~line 1281) to include
  `after`; confirm `_collect_stage_inputs` excludes `after`
- `configs/recipes/recipe-world-building.yaml` — use `after:` on `entity_discovery` and
  potentially clean up bible stage `needs:` ordering
- `tests/unit/test_recipe.py` (or `tests/unit/test_engine.py`) — add `after:` test cases

## Notes

**The bug that motivated this story (Story 062 smoke test):**

`entity_discovery` needed to run *after* `analyze_scenes` (so the enriched `scene_index` is
available in the store before entity extraction reads it), but `entity_discovery` does not consume
`analyze_scenes` outputs directly — it pulls `canonical_script` from the store. Using
`needs: [analyze_scenes]` triggered `_assert_schema_compatibility`, which checks schema
intersection between `analyze_scenes` (produces `scene`, `scene_index`) and `entity_discovery`
(requires `canonical_script`) — intersection is empty → false error.

The current workaround in `recipe-world-building.yaml` sets `needs: []` on `entity_discovery`
and uses `needs: [entity_discovery, analyze_scenes]` on the bible stages. This works but is
semantically wrong: it implies entity_discovery can run concurrently with analyze_scenes, then
the bibles wait for both. In practice this is fine since the bibles then pick up the enriched
scene_index from the store — but it's confusing to read and fragile to reason about.

With `after:`, the intent is expressed directly:
```yaml
- id: entity_discovery
  module: entity_discovery_v1
  after: [analyze_scenes]        # wait for enriched scene_index in store
  store_inputs:
    normalize: canonical_script  # still reads canonical_script, not scene data
```

## Plan

### Exploration Notes (2026-02-22)

**Confirmed file locations:**
- `recipe.py`: `RecipeStage` (line 16), `validate_recipe` (line 67), `resolve_execution_order` (line 108), `_assert_schema_compatibility` (line 136). All 179 lines — small, clean file.
- `engine.py`: `_collect_inputs` (line 1035) — iterates `stage.needs` and `stage.needs_all` only; `after` naturally excluded. `_compute_execution_waves` (line 1347) — uses `set(stage.needs) | set(stage.needs_all)` at line 1365 — needs `after` added here. `_build_stage_fingerprint` (line 1316) — includes `stage.needs` at line 1331; should include `stage.after` too for cache correctness.
- `recipe-world-building.yaml`: `entity_discovery` currently has `needs: []` (line 19) — can cleanly become `after: [analyze_scenes]`.
- `tests/unit/test_recipe_validation.py`: existing test file, 138 lines — add new tests here.

**No surprises:**
- `_assert_schema_compatibility` already only iterates `stage.needs + stage.needs_all` (line 142) — `after` is naturally excluded, just needs a comment.
- `_collect_inputs` early-exit check (line 1043-1050) only checks `needs`/`needs_all`/`store_inputs` — `after` should NOT be added there (ordering only, no data).
- `_build_stage_fingerprint` includes `stage.needs` — should also include `stage.after` so cache correctly invalidates when ordering changes.
- The overlap check in `validate_recipe` (line 80-90) checks `needs + needs_all` against `store_inputs` keys — `after` should be excluded from this check (can't be a data key anyway, but correct to leave it out).

**Files at risk of breaking:** None — `after` is a new optional field with an empty default. All existing recipes parse fine. All tests pass unchanged.

### Task-by-Task Plan

#### Task 1 — `RecipeStage.after` field (`recipe.py`)
Add `after: list[str] = Field(default_factory=list)` after `needs_all`. One line.

#### Task 2 — `validate_recipe` (`recipe.py`)
- Validate `after` entries exist in `stage_ids` (same check as `needs`): extend line 77 loop to also cover `stage.after`.
- `after` must NOT be in the overlap check — leave lines 80-90 unchanged (only `needs + needs_all` vs `store_inputs`).
- No schema compatibility check for `after` — `_assert_schema_compatibility` already only touches `needs + needs_all`.

#### Task 3 — `resolve_execution_order` (`recipe.py`)
Line 112: `dependencies = stage.needs + stage.needs_all` → `dependencies = stage.needs + stage.needs_all + stage.after`. This makes the topological sort respect `after` ordering.

#### Task 4 — `_compute_execution_waves` (`engine.py`)
Line 1365: `deps = set(stage.needs) | set(stage.needs_all)` → `deps = set(stage.needs) | set(stage.needs_all) | set(stage.after)`. Add a comment explaining `after` is ordering-only (no data piped, but stage must wait).

#### Task 5 — `_collect_inputs` (`engine.py`, confirm + comment)
Confirm that `after` is NOT iterated (it isn't — only `needs` and `needs_all` are). Add a brief comment: `# stage.after is intentionally excluded — ordering only, no data is piped`.

#### Task 6 — `_build_stage_fingerprint` (`engine.py`)
Add `"stage_after": stage.after` to the payload dict alongside `stage_needs` (line 1331). Ensures cache invalidates if `after` ordering changes.

#### Task 7 — `recipe-world-building.yaml`
Change `entity_discovery` from `needs: []` to `after: [analyze_scenes]`. The three bible stages (`character_bible`, `location_bible`, `prop_bible`) use `needs: [entity_discovery, analyze_scenes]` — this is correct (they consume data from both), keep as-is.

#### Task 8 — Unit tests (`tests/unit/test_recipe_validation.py`)
Four new `@pytest.mark.unit` tests:
1. `test_after_enforces_ordering` — `after` stage runs after the `after` dependency; verify execution order.
2. `test_after_skips_schema_check` — stage with incompatible schemas succeeds when connected via `after` (would fail with `needs`).
3. `test_after_inputs_not_collected` — `_collect_inputs` does not include `after` stage outputs.
4. `test_after_and_needs_coexist` — stage with both `after: [a]` and `needs: [b]` works correctly.

### Impact Analysis
- **No breaking changes** — `after` defaults to `[]`, all existing recipes parse without modification.
- **Cache fingerprint** — `stage.after` included in fingerprint, so changing `after` ordering invalidates cache correctly.
- **No UI changes** — purely backend DSL extension.
- **No new dependencies** — standard library only.

## Work Log

20260222-XXXX — story created: motivated by Story 062 smoke test false schema mismatch when
using `needs:` for ordering-only; `after:` resolves the semantic ambiguity cleanly.

20260222 — exploration complete: confirmed all 4 touch points in recipe.py and engine.py, located
existing test file, verified after is naturally excluded from _assert_schema_compatibility and
_collect_inputs. Plan written above. Ready for human gate.

20260222 — implemented and Done.

  **Changes made:**
  - `recipe.py` `RecipeStage`: added `after: list[str]` field with comment explaining ordering-only semantics.
  - `recipe.py` `validate_recipe`: extended missing-dependency check to cover `after` entries; overlap check left unchanged (only `needs`/`needs_all` vs `store_inputs`).
  - `recipe.py` `resolve_execution_order`: `after` included in `dependencies` so topological sort respects ordering constraints.
  - `recipe.py` `_assert_schema_compatibility`: added comment confirming `after` intentionally excluded — no schema contract.
  - `engine.py` `_compute_execution_waves`: `stage.after` added to `deps` set so a stage waits for all `after` stages before running.
  - `engine.py` `_collect_inputs`: comment added confirming `after` excluded — no data piped.
  - `engine.py` `_build_stage_fingerprint`: `stage_after` added to fingerprint payload — cache invalidates correctly when ordering changes.
  - `recipe-world-building.yaml`: `entity_discovery` changed from `needs: []` to `after: [analyze_scenes]` with explanatory comment.
  - `tests/unit/test_recipe_validation.py`: 4 new tests — ordering enforced, schema check skipped, no overlap conflict, `after`+`needs` coexist.

  **Evidence:**
  - 270 unit tests pass (up from 266), ruff clean.
  - Live recipe parse: `entity_discovery.after = ['analyze_scenes']`, execution order `['analyze_scenes', 'entity_discovery', 'character_bible', 'location_bible', 'prop_bible']`.
