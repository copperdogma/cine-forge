# Story 073 — Add `after:` ordering-only stage dependency to recipe DSL

**Priority**: Medium
**Status**: Pending
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

- [ ] Add `after: list[str]` to `RecipeStage` in `src/cine_forge/driver/recipe.py`
- [ ] Update `validate_recipe`: validate `after` entries exist in `stage_ids`, remove from
  overlap check
- [ ] Update `resolve_execution_order`: include `after` in incoming edge count and children map
- [ ] Update `_assert_schema_compatibility`: confirm it only iterates `needs + needs_all` (verify
  `after` is excluded — it already should be, just confirm)
- [ ] Update `engine.py` `_build_parallel_waves` (~line 1281): add `stage.after` to deps set
- [ ] Update `engine.py` `_collect_stage_inputs` (~line 1156): confirm `after` is NOT included
  (only `needs` passes outputs — verify and leave a comment)
- [ ] Update `recipe-world-building.yaml`: change `entity_discovery` from `needs: []` back to
  the intended pattern using `after: [analyze_scenes]`; also clean up the three bible stages if
  they use `after:` more clearly
- [ ] Write unit tests in `tests/unit/test_recipe.py` (or nearest existing test file) covering
  the four cases above
- [ ] Run required checks:
  - [ ] `make test-unit PYTHON=.venv/bin/python`
  - [ ] `.venv/bin/python -m ruff check src/ tests/`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** No user data affected.
  - [ ] **T1 — AI-Coded:** `after:` is self-explanatory in recipe YAML; comments in engine.py
    explain why it's excluded from input collection.
  - [ ] **T2 — Architect for 100x:** Minimal change, no over-engineering.
  - [ ] **T3 — Fewer Files:** No new files needed — patch existing recipe.py and engine.py.
  - [ ] **T4 — Verbose Artifacts:** Work log should capture why `after` was added.
  - [ ] **T5 — Ideal vs Today:** This IS the ideal — it matches industry standard pipeline DSLs
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

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260222-XXXX — story created: motivated by Story 062 smoke test false schema mismatch when
using `needs:` for ordering-only; `after:` resolves the semantic ambiguity cleanly.
