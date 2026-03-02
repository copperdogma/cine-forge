# Story 110 — Improve Search: Fuzzy Matching + Scene Shorthand

**Priority**: Medium
**Status**: Done
**Ideal Refs**: Easy, fun, and engaging — fast navigation is core to the feel
**Spec Refs**: None
**Depends On**: None

## Goal

The global search (Cmd+K / `/`) is currently exact substring-only. Typos return nothing — "marinner" finds no results when "Mariner" is right there. Abbreviations don't work — "ym" should surface "Young Mariner". Scene shorthand doesn't work — "sc2" or "sc 2" should jump straight to Scene 2. This story upgrades search to feel intelligent: tolerant of typos, responsive to abbreviations and initials, and aware of scene numbering shorthand.

## Acceptance Criteria

- [x] Typing "marinner" (one extra 'n') returns "Mariner" character in results
- [x] Typing "ym" returns "Young Mariner" (initials match)
- [x] Typing "sc2" or "sc 2" returns Scene 2 in results (scene number shorthand)
- [x] Typing "sc" alone returns all scenes (prefix shorthand)
- [x] Exact matches still rank above fuzzy matches (no ranking regression)
- [x] Performance: search feels instant (< 100ms perceived latency for typical project sizes)

## Out of Scope

- AI/semantic search (e.g., "sad scene by the ocean")
- Cross-project search
- Full-text search through scene content / dialogue

## Approach Evaluation

- **Pure code (backend)**: Add `rapidfuzz` (Python) to `search_entities` for fuzzy substring matching. Handles typos. Fast, deterministic, no AI cost. Scene shorthand needs a small pre-processing step: detect `sc\d+` pattern and match against scene number. This is the most straightforward path.
- **Pure code (frontend)**: Move search to client-side using `fuse.js` after loading all entity data. Works offline, but requires loading all entities up front — wasteful for large projects. Not preferred.
- **Hybrid**: Backend handles fuzzy + shorthand, frontend applies additional client-side re-ranking for UX (e.g., exact matches first). Reasonable extension if backend results feel misordered.
- **AI-only**: Overkill. Fuzzy match is a solved library problem — no LLM needed.
- **Eval**: Manual spot-check with "marinner", "ym", "sc2" on The Mariner project. No automated eval needed — this is deterministic code.

**Recommended approach**: Pure code (backend) with `rapidfuzz`. Install via `pyproject.toml`, replace the `q in field.lower()` check with fuzzy ratio threshold (e.g., ≥ 80% similarity) plus scene number shorthand pre-processing.

## Tasks

- [x] Add `rapidfuzz` to `pyproject.toml` dependencies
- [x] Update `search_entities` in `src/cine_forge/api/service.py`:
  - Add scene number shorthand detection: `sc2`, `sc 2`, `sc-2` → match scene with `index == 2`
  - Replace exact `q in field.lower()` with fuzzy match using `rapidfuzz.fuzz.partial_ratio` (threshold 75)
  - Also add initials matching: "ym" matches "Young Mariner" (first letter of each word)
  - Keep exact matches in results (they already pass the fuzzy threshold)
- [x] Verify scenes, characters, locations, and props all benefit from fuzzy matching
- [x] Manual test on The Mariner project: "marinner", "ym", "sc2", "sc" all return expected results
- [x] Run required checks:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 441 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — clean
- [x] Search docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk — read-only search operation
  - [x] **T1 — AI-Coded:** Simple, well-named utility function is AI-readable
  - [x] **T2 — Architect for 100x:** `rapidfuzz` is well-maintained; not over-engineered
  - [x] **T3 — Fewer Files:** All changes in `service.py` — no new files needed
  - [x] **T4 — Verbose Artifacts:** Work log documents decisions and discovered bug
  - [x] **T5 — Ideal vs Today:** Fuzzy search moves toward frictionless navigation

## Files to Modify

- `src/cine_forge/api/service.py` — update `search_entities` with fuzzy + shorthand logic
- `pyproject.toml` — add `rapidfuzz` dependency

## Notes

- `rapidfuzz.fuzz.partial_ratio` computes how well a short query matches within a longer string. Good for "ym" in "Young Mariner". `rapidfuzz.fuzz.ratio` is symmetric — better for typo detection on similar-length strings. Use both: `max(partial_ratio, ratio) >= threshold`.
- Scene shorthand pre-processing: if query matches `^sc\s*(\d+)$` (case-insensitive), extract number and match `entry.get("index") == int(number)` or match against `scene_number` field. Check what field stores scene number in `scene_index` entries.
- Initials matching: split query into chars, split entity name into words, check first char of each word. "ym" matches "Young Mariner" because Y=Young, M=Mariner. Only apply when query is 2-4 chars, all letters (to avoid false positives).
- Consider ranking: exact > initials > fuzzy. Return results with a `match_type` field if frontend needs to sort differently. For now, exact matches already satisfy the fuzzy threshold so they'll appear regardless.

## Plan

Add `rapidfuzz` to pyproject.toml, add three module-level helpers (`_parse_scene_number`,
`_is_scene_all`, `_fuzzy_match`) to service.py, update scene + bible entity matching to use
them, add unit test cases for the new behavior.

Files: `pyproject.toml`, `src/cine_forge/api/service.py`, `tests/unit/test_api.py`

## Work Log

20260302-1200 — explore: Read story, ideal.md, existing search code. `search_entities` uses
exact substring only. `SceneIndexEntry` has `scene_number` field. `rapidfuzz` not yet installed.
Existing test `test_search_returns_scenes_and_entities` exercises exact match only.

20260302-1210 — implement: Added `rapidfuzz>=3.0.0` to pyproject.toml; installed into .venv.
Added three module-level helpers to service.py: `_parse_scene_number` (regex sc[ene]N → int),
`_is_scene_all` (bare "sc"/"scene" → all scenes), `_fuzzy_match` (exact + initials + fuzzy).
Threshold = 75; fuzzy only fires for queries ≥ 4 chars to keep noise low. Initials for 2–5
all-alpha chars.

20260302-1215 — bug discovered: `list_versions(artifact_type="scene_index", entity_id=None)`
resolves to `artifacts/scene_index/__project__/` but the pipeline saves scene_index with
`entity_id="project"`. Search was always returning 0 scenes for real projects. Fixed by trying
"project" first, then falling back to None (for unit test data).

20260302-1220 — verify: API tests: "night" → 5 scenes; "sc2" → scene_002; "marinner" → 3
Mariner characters; "ym" → YOUNG MARINER; "sc" → 13 scenes. UI smoke test on The Mariner
(13 scenes, 13 chars, 6 locations, 25 props): all 4 cases verified visually in command palette.

20260302-1225 — tests: Added `test_search_fuzzy_and_shorthand` covering typo/initials/sc-N/sc-all.
441 unit tests pass. Ruff clean. No docs needed — no API contract change.

20260302-1300 — scene_number display: User noticed scene number wasn't visible in results.
Added `scene_number` to `SearchResultScene` Pydantic model (models.py), included it in the
service response dict, updated `SearchResultScene` TS type, and rendered `#N` before heading
in CommandPalette. All checks re-run: 441 pass, ruff clean, UI lint 0 errors, tsc -b clean.
UI smoke test confirmed: "sc3" → "#3 EXT. RUDDY & GREENE BUILDING - REAR - NIGHT".

20260302-1305 — closed: /validate grade A. All 6 ACs met, all checks green, UI smoke-tested.
