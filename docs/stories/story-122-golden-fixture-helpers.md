# Story 122 — Golden Fixture Helpers

**Priority**: Medium
**Status**: Done
**Spec Refs**: None (test infrastructure quality)
**Depends On**: None
**Scout Ref**: Scout 009, Finding 7 (from Dossier Story 047)

## Goal

CineForge has one golden fixture (`tests/fixtures/golden/the_mariner_scene_entities.json`) with no shared helper infrastructure and no structural integrity tests. When future golden files are added, each will need its own ad-hoc loading and validation code. Dossier solved this with a `golden_fixture_helpers.py` module: a typed registry of fixture specs, standardized loaders, and shared assertion helpers (cross-reference integrity, count assertions, field non-emptiness). This story adopts that pattern: create the shared helper module, add structural integrity tests for the existing golden, and document the approach so future golden files follow it consistently.

## Acceptance Criteria

- [ ] `tests/unit/golden_fixture_helpers.py` exists with:
  - `GoldenFixtureSpec` dataclass holding `slug`, `scene_count`, `expected_character_count`, `expected_prop_count` (or equivalent counts for the schema)
  - `GOLDEN_SPECS` tuple listing all known golden fixtures
  - `load_golden(spec)` — loads and validates the JSON against the expected structure
  - `assert_scene_count(graph, spec)` — verifies scene count matches spec
  - `assert_entities_non_empty(graph)` — verifies no scene has empty required fields (heading, scene_number)
  - `assert_no_duplicate_scene_numbers(graph)` — verifies scene_number uniqueness
- [ ] `tests/unit/test_golden_fixtures.py` exists with a compact structural test class for `the_mariner_scene_entities.json` using the helpers
- [ ] All structural assertion helpers are documented with docstrings explaining what invariant they check and why
- [ ] `docs/runbooks/golden-build.md` updated with a "Test Coverage" section explaining how to add a new fixture to `GOLDEN_SPECS` and write the structural test class
- [ ] All existing unit tests pass: `.venv/bin/python -m pytest -m unit`
- [ ] Lint passes: `.venv/bin/python -m ruff check src/ tests/`

## Out of Scope

- Adding new golden fixtures (separate story)
- Modifying the golden fixture content
- Offset/span verification (the scene entity schema has no text spans — that's a promptfoo eval concern)

## Approach Evaluation

- **Pure code**: Yes — test infrastructure and documentation. No AI reasoning needed.

## Tasks

- [ ] Read `tests/fixtures/golden/the_mariner_scene_entities.json` to understand the full schema (scenes, per-scene characters_in_action, characters_in_dialogue, props)
- [ ] Create `tests/unit/golden_fixture_helpers.py`:
  - `GoldenFixtureSpec` dataclass
  - `GOLDEN_SPECS` with the_mariner entry (15 scenes)
  - `load_golden(spec)` — reads JSON, validates top-level keys, returns typed dict
  - Assertion helpers: `assert_scene_count`, `assert_entities_non_empty`, `assert_no_duplicate_scene_numbers`
- [ ] Create `tests/unit/test_golden_fixtures.py`:
  - `TestMarinerSceneEntitiesStructure` class: `test_load`, `test_scene_count`, `test_no_empty_headings`, `test_no_duplicate_scene_numbers`
  - All tests marked `@pytest.mark.unit`
- [ ] Update `docs/runbooks/golden-build.md` with "Test Coverage" section
- [ ] Run unit tests and lint to verify

## Files to Create / Modify

| File | Action | Notes |
|------|--------|-------|
| `tests/unit/golden_fixture_helpers.py` | Create | New shared module |
| `tests/unit/test_golden_fixtures.py` | Create | New structural test suite |
| `docs/runbooks/golden-build.md` | Modify | Add "Test Coverage" section |

## Work Log

### 2026-03-03 — Implementation complete

**Files created:**
- `tests/unit/golden_fixture_helpers.py` — `GoldenFixtureSpec` dataclass,
  `GOLDEN_SPECS` tuple (1 entry: `the_mariner_scene_entities`, 15 scenes),
  `load_golden()` loader with top-level key validation, and 6 assertion
  helpers: `assert_metadata_present`, `assert_scene_count`,
  `assert_no_empty_headings`, `assert_no_duplicate_scene_numbers`,
  `assert_source_lines_valid`, `assert_characters_are_strings`.
- `tests/unit/test_golden_fixtures.py` — `TestMarinerSceneEntitiesStructure`
  class with 6 `@pytest.mark.unit` tests (one per assertion helper).

**Files modified:**
- `docs/runbooks/golden-build.md` — added "Test Coverage" section documenting
  the spec registration process, the test class pattern, and a table of all
  assertion helpers with their invariants.

**Evidence:**
- New tests: 6 passed in `tests/unit/test_golden_fixtures.py`
- Full unit suite: 505 passed, 0 failures (`pytest -m unit`)
- Lint: `ruff check` — All checks passed on both new files
