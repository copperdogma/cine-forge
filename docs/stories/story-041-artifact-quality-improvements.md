# Story 041 — Artifact Quality Improvements

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: To Do
**Depends on**: Story 040 (Pipeline Performance Optimization — Done)

## Goal

Improve the quality of world-building artifacts (character bibles, location bibles, prop bibles) by fixing systematic extraction and classification issues. Quality baseline established from The Mariner (5-page screenplay, `the-mariner-7` run).

Current quality grades:
- **Character Bibles**: A (92/100) — excellent, minor relationship consistency issues
- **Location Bibles**: B+ (8/10) — good, but duplicates and naming inconsistencies
- **Prop Bibles**: C+ (6/10) — costume items dominating, key props missing

## Context

### The Mariner QA Results (the-mariner-7)

Pipeline run: 6m38s, $0.48 total. All artifacts structurally valid. Quality issues are semantic, not structural — the AI extracts real information but makes poor classification and deduplication decisions.

## Issues

### 1. Props: Costume/Wardrobe Items Extracted as Props

**Severity**: High
**Module**: `prop_bible_v1`

5 of 8 extracted props are costume/wardrobe items that should not be classified as props:
- `BANDOLIER` — character wardrobe
- `BRACERS` — character wardrobe
- `FISH_HOOKS` — costume detail (decorative hooks on bracers)
- `FISHING_NET_CAPE` — character wardrobe
- `GUN` — correct prop, but see Issue 3

**Root cause**: The prop extraction prompt does not distinguish between props (objects characters interact with that affect plot) and costume/wardrobe (what characters wear). Costumes should be captured in character bible appearance fields, not as standalone prop entries.

**Fix direction**: Add explicit exclusion guidance in the prop extraction prompt: "Do NOT extract clothing, armor, accessories worn on the body, or costume elements. These belong in character descriptions, not props. Props are objects that characters pick up, use, give, or that drive plot action."

### 2. Props: Missing Key Story Props

**Severity**: High
**Module**: `prop_bible_v1`

Critical plot-driving props were not extracted:
- **Purse with $20M blockchain password** — central MacGuffin of the entire screenplay. Salvatori's thugs are after this. Its absence is a major quality failure.
- **Flare gun** — used in the climactic action sequence. Currently bundled into generic "GUN" entry.

**Root cause**: The LLM over-focuses on visually described items (costumes get detailed prose) and under-weights items mentioned in dialogue or action lines that drive plot. The purse is referenced in dialogue as containing "the password to twenty million dollars in some blockchain" — easy to miss if scanning for physical descriptions.

**Fix direction**: Add prompt guidance to prioritize plot-driving objects: "Pay special attention to objects mentioned in dialogue as important, objects that characters fight over or pursue, and objects used in climactic scenes. A purse containing a password is more important than decorative bracers."

### 3. Props: Generic Bundling of Distinct Items

**Severity**: Medium
**Module**: `prop_bible_v1`

The `GUN` entry bundles all firearms into one generic prop. In The Mariner, there are at least two distinct firearms:
- A flare gun (used in action climax — fires, ignites fuel)
- Conventional firearms (carried by thugs)

These serve completely different narrative functions and should be separate entries.

**Fix direction**: Prompt should instruct: "If multiple instances of a category exist with different narrative functions (e.g., a flare gun vs a handgun), create separate entries for each. Do not bundle distinct items under a generic category name."

### 4. Locations: Duplicate Entries

**Severity**: Medium
**Module**: `location_bible_v1`

Duplicate location detected:
- `LOC_STAIRWELL` and `loc_12th_floor_stairwell` refer to the same location

**Root cause**: The extraction pass creates a new entry each time a location is described with slightly different wording, without deduplication against already-extracted entries.

**Fix direction**: Add a deduplication step — either as post-processing (compare all extracted locations for semantic overlap) or in the prompt itself ("Before creating a new location entry, check if it's the same place as an existing entry described differently").

### 5. Locations: Naming Inconsistency

**Severity**: Low
**Module**: `location_bible_v1`

The building is referred to as both "Ruddy & Green" and "Ruddy & Greene" across different location entries. The canonical name from the screenplay should be used consistently.

**Fix direction**: Post-extraction consistency pass that normalizes proper nouns across all entries. Or instruct the LLM to establish canonical names early and reuse them.

### 6. Locations: Inconsistent entity_id Casing

**Severity**: Medium
**Module**: `location_bible_v1`

Some entity IDs use `LOC_UPPERCASE` while others use `loc_lowercase`. Entity IDs should follow a single convention.

Examples:
- `LOC_STAIRWELL` (uppercase)
- `loc_12th_floor_stairwell` (lowercase)

**Fix direction**: Enforce a consistent casing convention in the prompt and/or add post-extraction normalization. Recommend `loc_snake_case` to match character bible convention.

### 7. Locations: No Parent Building Entry

**Severity**: Low
**Module**: `location_bible_v1`

The Ruddy & Greene building is the primary setting — almost every scene takes place inside it — but there's no umbrella entry for the building itself. Individual floors/rooms are extracted but the building as a whole is missing.

**Fix direction**: Prompt should instruct: "If multiple locations exist within a larger structure (building, ship, campus), create an entry for the parent structure as well, with child locations noted."

### 8. Characters: entity_id Inconsistency in Relationships

**Severity**: Medium
**Module**: `character_bible_v1`

Character entries reference other characters by inconsistent identifiers:
- Character's own entry uses `MR_SALVATORI` as entity_id
- Other characters' relationship fields reference him as `salvatori` (lowercase, no prefix)

This breaks automated cross-referencing between character entries.

**Fix direction**: Enforce that relationship references use the exact `entity_id` of the referenced character. Add validation that all relationship target IDs match existing character entity_ids.

### 9. Characters: Missing Bidirectional Relationships

**Severity**: Low
**Module**: `character_bible_v1`

Salvatori has thugs who work for him, but:
- Salvatori's entry doesn't list relationships to his thugs
- Individual thug entries may not reference Salvatori as their boss

Relationships should be bidirectional — if A relates to B, B should also relate to A.

**Fix direction**: Post-extraction relationship completion pass that ensures bidirectionality. For each relationship A→B, verify B→A exists with the inverse relationship type.

### 10. Scenes: Analysis Depth Degrades for Later Scenes

**Severity**: High
**Module**: `scene_extract_v1` / `scene_enrich_v1`
**Reported by**: Gill (Liberty & Church screenplay)

Later scenes (from "Int. Abe's Office" onward) have noticeably sparser analysis than earlier scenes — missing depth/tension/conflict annotations that the first scenes had. This is a classic long-context LLM attention fade where the model exhausts its budget on early content.

**Fix direction**: Either process scenes independently (each scene gets its own LLM call with full attention), enforce a minimum-fields checklist in the prompt, or add a post-extraction validation pass that flags scenes with missing analysis fields and re-processes them.

## Tasks

### Prop Bible Improvements
- [ ] Add costume/wardrobe exclusion guidance to prop extraction prompt
- [ ] Add plot-importance weighting to prop extraction prompt
- [ ] Add distinct-item separation guidance (no generic bundling)
- [ ] Test with The Mariner — verify purse and flare gun are extracted, costumes excluded
- [ ] Test with Liberty & Church — verify all significant props are extracted (Gill reported only 2 extracted)
- [ ] Run promptfoo eval to confirm no quality regression on other test cases

### Location Bible Improvements
- [ ] Add deduplication guidance or post-processing step
- [ ] Enforce consistent entity_id casing convention (`loc_snake_case`)
- [ ] Add parent-structure extraction guidance
- [ ] Add naming consistency guidance for proper nouns
- [ ] Test with The Mariner — verify no duplicates, consistent naming

### Character Bible Improvements
- [ ] Enforce exact entity_id references in relationship fields
- [ ] Add bidirectional relationship completion (post-processing or prompt)
- [ ] Test with The Mariner — verify cross-references are valid

### Scene Analysis Consistency (Gill)
- [ ] Audit scene analysis output for Liberty & Church — identify which fields degrade in later scenes
- [ ] Add minimum-fields validation to scene enrichment (every scene must have depth, tension, conflict, etc.)
- [ ] Fix root cause: either per-scene LLM calls or post-extraction re-processing of sparse scenes
- [ ] Test with Liberty & Church — verify all scenes have consistent analysis depth

### Cross-Cutting
- [ ] Add schema-level validation for entity_id format consistency
- [ ] Add cross-artifact reference validation (relationships point to real entity_ids)
- [ ] Run full pipeline on The Mariner and compare before/after quality

## Acceptance Criteria

- [ ] Prop bible for The Mariner extracts purse and flare gun as separate entries
- [ ] Prop bible does NOT extract costume items (bandolier, bracers, fishing net cape, fish hooks)
- [ ] Location bible has no duplicate entries for the same physical space
- [ ] Location entity_ids use consistent `loc_snake_case` format
- [ ] Character relationship references use exact entity_ids of referenced characters
- [ ] No quality regression on existing test cases (verify via promptfoo if available)

## Work Log

_No entries yet._
