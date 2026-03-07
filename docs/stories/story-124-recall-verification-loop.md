# Story 124 — Recall Verification Loop for Entity Discovery

**Priority**: Medium
**Status**: Done
**Spec Refs**: None (entity discovery quality improvement)
**Depends On**: None
**Scout Ref**: Scout 010 (`docs/scout/scout-010-openai-prompt-guidance.md`) — "Empty Result Recovery" pattern

## Goal

Add a post-extraction verification pass to entity discovery that cross-references discovered entities against structural signals from the scene index, then re-prompts the model with specific missing-entity hints when recall gaps are detected.

## Context

Scout 010 (OpenAI GPT-5.4 Prompt Guidance) identified "Empty Result Recovery" as a valuable pattern. Our entity discovery module processes full screenplays in chunks but has no mechanism to detect when it silently drops entities. AGENTS.md notes: "LLM resolution degrades from synthetic to real data" — small test fixtures pass but real screenplays with 40-80+ entities show recall gaps.

**Current architecture**:
- Characters: scene_index passthrough (Story 081) — no LLM discovery needed, already canonical
- Locations: LLM chunked discovery, scene_index has `unique_locations` but it's NOT used as cross-reference
- Props: LLM chunked discovery, scene_index has per-scene `props_mentioned` but NOT aggregated or cross-referenced

The scene_index already contains the structural signals needed for verification — they're just not being used.

## Approach Evaluation

**Candidate C (Hybrid) selected** based on analysis:

- **Rule-based gap detection**: Extract location headings from scene_index `unique_locations` and per-scene `props_mentioned`, diff against discovered entities. Zero LLM cost for detection.
- **LLM re-prompt only when gaps found**: Pass missing entity hints to one additional discovery chunk. Targeted cost — zero overhead when discovery is complete.
- **Why not Candidate A (full LLM verification)**: Doubles cost on every run, even when discovery is complete. Violates the 20% cost ceiling on the common case.
- **Why not Candidate B (pure rule-based)**: Can't handle aliases (e.g., "RUDDY & GREENE BUILDING" vs "THE BUILDING"). The re-prompt needs semantic judgment.

**Baseline to beat**: Gemini 2.5 Flash Lite at 0.905 overall, $0.001/call.

## Acceptance Criteria

- [x] **AC1**: After LLM discovery completes for locations, cross-reference results against `scene_index.unique_locations`. If >0 locations from scene_index are missing (after normalization), trigger a verification re-prompt.
- [x] **AC2**: After LLM discovery completes for props, aggregate `props_mentioned` from all scene_index entries into a unique set. If >0 props from scene_index are missing (after normalization), trigger a verification re-prompt.
- [x] **AC3**: The verification re-prompt includes the specific missing entity names as hints: "The scene index mentions these locations/props not in your list: X, Y, Z. Review the full screenplay and add any that meet the taxonomy definition."
- [x] **AC4**: Verification adds at most 1 additional LLM call per entity type (locations, props). Characters are exempt (scene_index passthrough).
- [x] **AC5**: When no gaps are detected, zero additional LLM calls are made (no cost overhead on the happy path).
- [x] **AC6**: `processing_metadata` records verification results: `verification_ran: bool`, `locations_gap_count: int`, `props_gap_count: int`, `verification_cost_usd: float`.
- [x] **AC7**: Unit tests cover: (a) no-gap happy path (no extra calls), (b) gap-detected path (re-prompt fires), (c) normalization handles aliases.
- [x] **AC8**: Entity discovery eval score on The Mariner does not regress (>= 0.905 overall).

## Tasks

- [x] T1: Add `_extract_scene_index_signals()` helper — extracts unique locations and aggregated props from scene_index
- [x] T2: Add `_normalize_entity_name()` general-purpose normalizer (extend `_normalize_character_name` pattern for locations/props)
- [x] T3: Add `_find_recall_gaps()` — compares discovered list against scene_index signals using normalized matching
- [x] T4: Add `_build_verification_prompt()` — builds a targeted re-prompt with missing entity hints
- [x] T5: Wire verification into `run_module()` — after each taxonomy's chunked discovery, run gap detection and optional re-prompt
- [x] T6: Update `processing_metadata` with verification fields
- [x] T7: Add unit tests for gap detection, normalization, and verification flow
- [x] T8: Run entity discovery eval, verify no regression, update registry

## Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` | 206→337 | Added 4 helper functions + verification wiring in run_module |
| `tests/unit/test_module_entity_discovery_v1.py` | 186→301 | Added 12 new tests across 4 new test classes |
| `tests/acceptance/test_entity_discovery_verification.py` | NEW | Live acceptance test against The Mariner with Gemini |
| `docs/evals/registry.yaml` | — | Updated Gemini 2.5 Flash Lite entry with Story 124 note |

## Tenet Checklist
- [x] T0 — No data loss: verification only adds entities, never removes
- [x] T1 — AI-friendly code: clear function names, docstrings, separation of concerns
- [x] T2 — Not over-engineered: minimal additions, reuses existing patterns
- [x] T3 — Files appropriately sized: main.py 337 lines, test file 301 lines
- [x] T4 — Work log verbose enough: see below
- [x] T5 — Moves toward Ideal: improves entity recall, a foundation for better downstream bibles

## Links

- Scout 010: `docs/scout/scout-010-openai-prompt-guidance.md`
- Entity discovery module: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py`
- Entity discovery eval: `benchmarks/tasks/entity-discovery.yaml`
- Entity discovery golden: `benchmarks/golden/the-mariner-entity-discovery.json`
- Eval registry: `docs/evals/registry.yaml`
- Scene schema: `src/cine_forge/schemas/scene.py` (SceneIndex, SceneIndexEntry)

## Work Log

20260307-1800 — Story promoted from Draft to Pending. Detailed exploration of entity_discovery_v1 module (206 lines), scene schema signals, eval config, golden reference, and scorer. Key finding: scene_index already has `unique_locations` and per-scene `props_mentioned` — just not used for cross-referencing. Characters exempt via scene_index passthrough (Story 081).

20260307-1810 — Plan approved. Implementing Candidate C (hybrid): rule-based gap detection + LLM re-prompt only when gaps found. Zero cost on happy path.

20260307-1815 — T1-T6 implemented in `entity_discovery_v1/main.py`. Added 4 helper functions:
- `_normalize_entity_name()`: generalizes character normalization for locations (strips INT./EXT., time-of-day) and props
- `_extract_scene_index_signals()`: extracts normalized locations from `unique_locations`, aggregates props from per-scene `props_mentioned`
- `_find_recall_gaps()`: bidirectional substring matching (handles aliases) between discovered and reference lists
- `_build_verification_prompt()`: targeted re-prompt with missing hints + bounded screenplay context (30k chars)
Verification wired into `run_module()` after each taxonomy's chunked discovery. Only fires when scene_index available AND gaps detected.

20260307-1820 — T7: Added 12 unit tests across 4 new test classes. All 26 tests pass. Full suite: 509 passed.

20260307-1825 — T8 eval results:
- **promptfoo eval (raw model)**: Gemini 2.5 Flash Lite: Python=0.99, Rubric=0.82, Overall=0.905. No regression from baseline.
- **Live acceptance test (module pipeline)**: The Mariner with scene_index cross-reference:
  - WITHOUT verification: 13 locations, 25 props — 100% required recall, 2 optional entities missed (DOCK, NET CAPE)
  - WITH verification: 14 locations, 26 props — 100% required recall, +2 optional entities recovered
  - Verification cost: $0.0008 (only when gaps detected, zero on happy path)
  - Total cost with verification: $0.0017 vs $0.0009 without
- **Conclusion**: Verification loop is a safety net. On The Mariner (short screenplay, 2 chunks), required recall is already 100% without verification. The loop catches optional entities that chunked processing drops. Value increases on longer screenplays with more chunks where required entity drops are more likely.

20260307-1840 — Story marked Done. All 8 ACs met, all 8 tasks complete, all checks pass (509 unit tests, lint clean), eval confirmed no regression (0.905). Validation grade: A.
