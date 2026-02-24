# Story 080 — LLM-Powered Action Line Entity Extraction

**Priority**: High
**Status**: Pending
**Spec Refs**: World Building / Entity Discovery, Scene Breakdown
**Depends On**: 077 (Character Coverage & Prominence Tiers), 055 (LLM-First Entity Adjudication)

## Goal

Characters and props in screenplays are introduced in **action lines**, not dialogue cues.
Industry convention: a character's first appearance is ALL CAPS in action text (e.g.,
`THE MARINER steps through the door`), often before they ever speak — and some never speak at
all. Today, the scene breakdown structural parser only catches action-line names followed by a
comma or parenthetical (`NAME,` or `NAME (`), missing bare introductions like
`THUG 2 LUNGES at the elevator BUTTON`. Entity discovery (LLM) downstream catches many of
these, but because the scene_index lacks them, they get zero scene-count, zero dialogue-count,
and may fall through cracks in the character bible module.

This story replaces the brittle `_extract_character_mentions` regex in scene_breakdown with a
lightweight LLM call that reads each scene's action lines and extracts all character and prop
mentions. A cheap, fast model (Haiku-class) is more than capable of distinguishing "MARINER"
(character) from "SLAM" (sound effect) from "BOSUN" (prop-name oar) — the kind of contextual
judgment that regex heuristics can never reliably make.

## Acceptance Criteria

- [ ] Scene breakdown uses an LLM call (not regex) to extract character and prop mentions from
  action/description lines in each scene
- [ ] The LLM call runs on a cheap/fast model (Haiku-class or equivalent) to keep cost low
- [ ] Characters mentioned only in action lines (never in dialogue cues) still appear in
  `characters_present` and `unique_characters` in the scene_index
- [ ] Props mentioned in action lines appear in a new `props_mentioned` field per scene entry
  (or augment the existing prop discovery pipeline)
- [ ] The regex-based `_extract_character_mentions` is replaced, not supplemented — no dual path
- [ ] Existing characters found via dialogue cues are preserved (union of structural + LLM)
- [ ] Mock model path produces deterministic output for unit tests
- [ ] `make test-unit` passes; ruff clean; UI lint and `tsc -b` pass if UI touched
- [ ] The Mariner screenplay produces scene_index entries containing "THUG 1", "THUG 2",
  and "YOUNG MARINER" in `characters_present` for the scenes where they appear in action lines

## Out of Scope

- Changing entity_discovery_v1 — it already reads full script text via LLM and works well as a
  downstream safety net. This story improves the structural foundation it builds on.
- Changing scene_analysis_v1 — its gap-fill behavior (only activates when `characters_present`
  is empty) may become redundant but won't be removed in this story.
- UI changes — the scene_index schema change (`props_mentioned`) flows through existing UI
  automatically.
- Locations — action lines rarely introduce locations in a way that differs from scene headings.
  Characters and props are the high-value targets.

## AI Considerations

This story is **entirely AI-first**. The core problem — distinguishing character names from
sound effects, transitions, and general ALL-CAPS emphasis in action lines — is a
reasoning/language problem that regex cannot solve reliably. Examples:

- `MARINER walks across the deck` — MARINER is a character
- `The door SLAMS shut` — SLAMS is a sound effect
- `THUG 2 LUNGES at the elevator BUTTON` — THUG 2 is a character, LUNGES and BUTTON are not
- `She grabs the OAR named BOSUN` — OAR/BOSUN is a prop
- `FADE TO:` — transition, not an entity
- `A HOMELESS MAN watches from across the street` — unnamed character

A Haiku-class model handles this trivially. The prompt should be simple: given action lines from
a scene, return `{characters: [...], props: [...]}`. Structured output with a Pydantic schema
ensures clean parsing.

**Cost estimate**: ~1-2 action lines per scene × 13 scenes = ~15 LLM calls at Haiku pricing
≈ negligible. Could also batch all action lines per scene into a single call.

**Model selection**: Haiku 4.5 or equivalent — this is classification, not reasoning. Benchmark
with promptfoo if uncertain, but the task is well within Haiku capability.

## Tasks

- [ ] **Design schema**: Define a small Pydantic response model for action-line entity
  extraction: `ActionLineEntities(characters: list[str], props: list[str])`. Keep it minimal.
- [ ] **Write the LLM prompt**: Short, focused prompt that takes action lines from one scene and
  returns character names and prop names found. Include negative examples (sound effects,
  transitions, emphasis). Use structured output.
- [ ] **Replace `_extract_character_mentions`**: In scene_breakdown_v1, replace the regex-based
  function with a call to the new LLM extractor. Batch action lines per scene into one call.
  Union the results with dialogue-cue characters for `characters_present`.
- [ ] **Add `props_mentioned` to scene entries**: New optional field on scene index entries.
  Populate from the LLM response. Wire through to scene_index output.
- [ ] **Mock model path**: Add deterministic mock output for `model="mock"` so unit tests work
  without LLM calls. The mock should return a plausible set of characters/props.
- [ ] **Update scene_index schema**: If `props_mentioned` is a new field, ensure the Pydantic
  schema accepts it. Default to empty list for backward compatibility.
- [ ] **Regression tests**: Test that:
  - Dialogue-cue characters are still found (no regression)
  - Action-only characters appear in `characters_present`
  - Sound effects and transitions are NOT extracted as characters
  - Props in action lines populate `props_mentioned`
  - Mock model path produces consistent output
- [ ] **Integration check**: Verify that downstream modules (entity_discovery, character_bible)
  correctly consume the richer scene_index without breaking
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Scene_index is immutable — new runs produce new versions
  - [ ] **T1 — AI-Coded:** LLM extraction is self-documenting via prompt
  - [ ] **T2 — Architect for 100x:** Haiku-class model keeps cost negligible at scale
  - [ ] **T3 — Fewer Files:** Changes stay within scene_breakdown_v1 module
  - [ ] **T4 — Verbose Artifacts:** Scene_index provenance annotation updated
  - [ ] **T5 — Ideal vs Today:** Could scene_analysis_v1 gap-fill be retired? Evaluate.

## Files to Modify

- `src/cine_forge/modules/ingest/scene_breakdown_v1/main.py` — replace
  `_extract_character_mentions` regex with LLM call, add `props_mentioned` extraction
- `src/cine_forge/schemas/` — add `ActionLineEntities` response model if needed; update scene
  entry schema for `props_mentioned`
- `tests/unit/test_scene_breakdown_module.py` — regression tests for action-line extraction
- `configs/recipes/` — may need to wire model param for the new LLM call (or inherit from stage)

## Notes

- The current `_extract_character_mentions` regex (line 637-645 in scene_breakdown_v1/main.py)
  only matches ALL-CAPS names followed by `,` or `(`. This misses bare mentions like
  `THUG 2 LUNGES` or `YOUNG MARINER enters`.
- Scene_analysis_v1 has a gap-fill path but only fires when `characters_present` is empty for a
  scene — it doesn't add missing characters to scenes that already have some from dialogue cues.
- Entity discovery catches most missing characters but operates on the full script, not per-scene,
  so its output doesn't help with per-scene `characters_present` accuracy.
- Consider batching: one LLM call per scene (all action lines concatenated) vs one call per
  action line. Per-scene batching is almost certainly better (fewer calls, more context).
- The same LLM call can extract both characters and props from action lines simultaneously,
  which is more efficient than separate passes.
- "THUG 1", "THUG 2", "YOUNG MARINER" in The Mariner are the concrete motivating cases.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260223-2200 — story created. Motivated by THUG 1/THUG 2/YOUNG MARINER being found by entity
discovery but missing from scene_index because the structural action-line regex in
scene_breakdown only catches names followed by comma or parenthetical. The user's insight: this
is fundamentally a language understanding problem, not a regex problem. A cheap LLM (Haiku) can
trivially distinguish characters from sound effects in action lines. Replaces regex with LLM
call at the scene_breakdown level so downstream modules (entity_discovery, character_bible) get
richer input from the start.
