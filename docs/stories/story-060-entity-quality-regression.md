# Story 060 — Entity Quality Regression

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done
**Depends on**: Story 041, Story 059

## Goal

Investigate and fix a critical quality regression where the protagonist ("The Mariner") was dropped from the character bible in a recent run (`the-mariner-10`), despite being correctly extracted in previous runs (`the-mariner-9`).

## Context

User report:
- `the-mariner-9` (Success): Correctly extracted char/location/prop bibles.
- `the-mariner-10` (Failure): Missing "THE MARINER" (protagonist) in the Character Bible.

This suggests a regression in `entity_discovery_v1` or `character_bible_v1`, likely introduced during the recent Refine Mode or caching updates.

## Investigation Plan

### 1. Compare Artifacts
- [x] Inspect `entity_discovery_results` for `the-mariner-9` vs `the-mariner-10`.
  - Found: Discovery *did* find "THE MARINER" in `the-mariner-10`.
- [x] Compare against `scene_index`.
  - Found: `scene_index` uses "MARINER" (the parser's canonical name), while discovery found "THE MARINER".
  - Discrepancy: "THE MARINER" (Discovery) vs "MARINER" (Index).

### 2. Analyze Code Changes
- [x] Review `character_bible_v1` matching logic.
- [x] Review `entity_discovery_v1` prompt changes (did we encourage "THE" prefixing?).

### 3. Hypothesis Generation
- [x] **Hypothesis A:** The mismatch between "THE MARINER" and "MARINER" causes the character bible stage to skip him because it thinks he has 0 scenes.
- [x] **Hypothesis B:** The `character_bible_v1` module's case-insensitive matching (fixed in Story 041) is too strict for partial name matches (like "The" prefixes).

## Tasks

- [x] Compare `entity_discovery_results` JSONs.
- [x] Audit `character_bible` logs/artifacts.
- [x] Run reproduction test with `promptfoo` or local script.
- [x] Fix the root cause.
- [x] Verify with a new run (`the-mariner-11`).

## Acceptance Criteria

- [x] "The Mariner" is reliably extracted in a fresh run of the screenplay.
- [x] Refine Mode still works (doesn't duplicate/delete entities).
- [x] Unit/Regression test added to prevent recurrence.

## Tenet Verification

- [x] Immutability: N/A
- [x] Lineage: N/A
- [x] Explanation: N/A
- [x] Cost transparency: N/A
- [x] Human control: N/A
- [x] QA: Regression testing.

## Work Log

20260221-0000 — setup: Scaffolded story to track missing protagonist regression.
20260221-0030 — investigation: Identified name mismatch between `entity_discovery` ("THE MARINER") and `scene_index` ("MARINER") in `the-mariner-10`. Discovery found him, but bibles were not produced because normalization failed to strip the "THE " prefix, causing a stopword rejection in the character bible module.
20260221-0100 — fix: Unified character name normalization across `entity_discovery_v1` and `character_bible_v1`. Fixed regex to correctly strip "THE " prefixes even with spaces. Added `tests/unit/test_character_naming_regression.py` to safeguard extraction. Verified with local dev run.
