# Story 055 — LLM-First Entity Adjudication for Character, Location, and Prop

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done
**Spec Refs**: `docs/spec.md` §2.4 (AI-Driven at Every Stage), §2.6 (Explanation Is Mandatory), §2.8 (Quality Validation), §6.1 (Asset Masters)
**Depends On**: Story 008, Story 009, Story 041, Story 054

## Goal

Redesign world-building extraction so semantic entity validity is decided explicitly by LLM adjudication before bible emission. This prevents known false positives (characters/locations/props) while keeping deterministic code for cheap orchestration and evidence prep, and applies the same pattern across character, location, and prop pipelines.

## Acceptance Criteria

- [x] A shared adjudication contract exists (schema + helper) that can classify candidates as valid, invalid, or retyped with rationale/confidence.
- [x] `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` call adjudication before generating bibles, and skip invalid candidates deterministically.
- [x] Rejected candidates are persisted in module metadata/audit context (at least stage-level annotation or debug payload) so operators can inspect what was filtered and why.
- [x] Unit tests cover false-positive suppression and valid-entity retention for all three modules.
- [x] Existing world-building integration tests continue passing.

## Out of Scope

- Full cross-run cache layer for adjudication results.
- UI redesign for rejected-candidate visualization.
- Large prompt benchmark campaign (promptfoo) for new adjudication prompts.

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- What parts of this story are reasoning/language/understanding problems? → LLM call
- What parts are orchestration/storage/UI? → Code
- Have you checked current SOTA capabilities? Your training data may be stale.
- See AGENTS.md "AI-First Problem Solving" for full guidance.

For this story:
- Entity validity (character vs location vs prop vs non-entity) is a reasoning problem and should be LLM-adjudicated via structured output.
- Candidate collection, dedupe, persistence, and test fixtures remain deterministic code.
- Keep LLM calls efficient: per-stage batch adjudication, compact evidence, and no duplicate passes for rejected candidates.

## Tasks

- [x] Add shared entity adjudication schema(s) and helper utility under `src/cine_forge/`.
- [x] Implement LLM adjudication pass in `character_bible_v1` before extraction loop.
- [x] Implement same adjudication pattern in `location_bible_v1`.
- [x] Implement same adjudication pattern in `prop_bible_v1` (including initial discovery output cleanup).
- [x] Persist adjudication decisions/rejections in stage output metadata for auditability.
- [x] Add/update unit tests:
  - [x] Character module rejects known non-character tokens.
  - [x] Location module rejects invalid location candidates.
  - [x] Prop module rejects non-prop candidates.
- [x] Run world-building integration tests to ensure end-to-end behavior remains stable.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — add adjudication gate before bible generation.
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — add adjudication gate before bible generation.
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — add adjudication gate before bible generation.
- `src/cine_forge/schemas/` — add shared adjudication schema(s) and exports.
- `src/cine_forge/ai/` — add or update shared helper for batched entity adjudication.
- `tests/unit/test_character_bible_module.py` — regression coverage for non-character suppression.
- `tests/unit/test_location_bible_module.py` — regression coverage for invalid-location suppression.
- `tests/unit/test_prop_bible_module.py` — regression coverage for non-prop suppression.
- `tests/integration/test_world_building_integration.py` — validate pipeline still completes with mock model settings.
- `docs/stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md` — work log and verification evidence.
- `docs/stories.md` — story status/index row.

## Notes

Use Liberty Church false positives from Story 054 as seed cases.

Implementation intent:
1. Batch adjudicate candidate list with compact evidence.
2. Keep only verdict `valid` for current entity type.
3. Optionally allow `retype` verdict to emit into future cross-type queue (for now: record and skip).

## Work Log

20260219-1530 — story initialized: created Story 055 for LLM-first adjudication across character/location/prop extraction, evidence=`start-story.sh` output path, next=implement shared adjudication schema/helper and wire all three modules.
20260219-1544 — added shared adjudication contract: created `src/cine_forge/schemas/entity_adjudication.py` and `src/cine_forge/ai/entity_adjudication.py`, exported via package `__init__` files, evidence=new schema classes (`EntityAdjudicationDecision`, `EntityAdjudicationBatch`) and helper `adjudicate_entity_candidates`, next=wire modules to call adjudicator pre-extraction.
20260219-1553 — wired adjudication gates into world-building modules: `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` now run adjudication before emitting bibles, merge valid canonical names, and attach rejected-candidate audit annotations in artifact metadata, evidence=module helpers `_adjudicate_candidates` + `entity_adjudication` annotations in metadata, next=add regression tests.
20260219-1558 — added regression tests for suppression behavior: updated unit tests to monkeypatch adjudication decisions and verify invalid candidates are skipped for character/location/prop modules, evidence=3 new unit tests across module test files, next=run test suite and lint.
20260219-1607 — resolved integration hang and model-slot fallback gap: world-building modules now read model slots from `context.runtime_params` (`default_model`, `utility_model`, `sota_model`) when stage params are unset, evidence=integration run `test-world-building-4990ed3a` completed all stages `done`, next=final validation checks and close story.
20260219-1611 — validated and closed story: executed `make test-unit PYTHON=.venv/bin/python` (`218 passed, 54 deselected`), `.venv/bin/python -m ruff check src/ tests/` (`All checks passed!`), and `PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_world_building_integration.py -q` (`1 passed`), next=ready for operator validation against Liberty Church rerun.
20260219-1620 — post-validate hardening: added explicit `retype` adjudication regression test in `tests/unit/test_character_bible_module.py` to ensure retyped candidates are not emitted as character bibles, evidence=`test_run_module_skips_retyped_candidates` plus full checks (`219 passed, 54 deselected`; Ruff clean), next=prepare separate commits for Story 054 artifacts and Story 055 implementation.
