# Verify Golden Outputs — Adversarial Verification Protocol

You are verifying T1 golden reference fixtures for CineForge's promptfoo eval suite.
These goldens are **scorer-side references** — they contain evaluation criteria that
Python scorers check against model output. Accuracy is critical: a wrong golden
silently passes bad models and fails good ones.

## Step 1: Pick the next fixture

Read the checklist:
```
benchmarks/golden/_verification-checklist.md
```

Find the first fixture NOT marked `CLEAN`. That's what you're verifying this session.
If all are CLEAN, say so and stop.

## Step 2: Understand the schema

Read the format specification:
```
benchmarks/golden/README.md
```

This describes all golden types, their field schemas, enum values, and conventions.
Also read the corresponding scorer to understand how each golden field maps to model
output validation:
```
benchmarks/scorers/{eval_name}_scorer.py
```

## Step 3: Read the INPUT first — build your own mental model

Read the source input for the fixture:
- Full screenplay: `benchmarks/input/the-mariner.fountain` (or `.txt`)
- Scene excerpts: the specific scene text referenced in the golden
- Normalization input: `benchmarks/input/signal-in-the-rain-raw.txt`

**Before reading the golden output**, write down what you expect to find. This prevents
anchoring bias — you'll catch both missing entries and phantom entries.

## Step 4: Read the golden and compare adversarially

For each golden type, apply the type-specific checklist below PLUS these universal checks:

### Universal Checks (all types)

- [ ] **JSON validity** — parses cleanly, no trailing commas, no comments
- [ ] **Slug ID conventions** — all IDs are lowercase-hyphenated, no spaces or special chars
- [ ] **Character name conventions** — ALL CAPS where required
- [ ] **Confidence ranges** — all floats in [0.0, 1.0], calibrated to evidence strength
- [ ] **No phantom entries** — every entity/fact/relationship traces to actual input text
- [ ] **No missing entries** — nothing important in the input is absent from the golden
- [ ] **Evidence grounding** — every `must_have_evidence`, `key_evidence`, `must_mention_evidence` is a real quote or paraphrase from the input
- [ ] **Cross-references valid** — entity IDs referenced in other goldens exist and match

---

### Character Extraction (`the-mariner-characters.json`)

- [ ] Every character with meaningful dialogue or action has an entry
- [ ] `character_id` matches kebab-case convention
- [ ] `narrative_role` is correct (`protagonist` vs `supporting`)
- [ ] `key_traits` are supported by actual script evidence, not inferred from genre
- [ ] `aliases` include all names used in script (including parenthetical variants)
- [ ] `must_have_relationships` — each target exists, type is accurate
- [ ] `must_mention_scenes` — each scene heading substring matches a real scene
- [ ] `must_have_evidence` — each item is findable in the screenplay text
- [ ] `key_facts` — each fact is directly stated or strongly implied by the script
- [ ] Relationship type enum compliance: `sibling`, `parent`, `adversary`, `romantic_ex`
- [ ] No character is over-credited (traits/facts that belong to someone else)
- [ ] No character is under-credited (missing key moments or relationships)

### Scene Extraction (`the-mariner-scenes.json`)

- [ ] `scene_count` matches actual number of scene headings in the screenplay
- [ ] Every scene heading in the screenplay has a corresponding entry
- [ ] `int_ext` matches the actual heading prefix
- [ ] `time_of_day` matches the heading suffix
- [ ] `location` is the correct portion of the heading (no INT./EXT., no time)
- [ ] `characters` lists everyone who appears (dialogue + action lines)
- [ ] `summary` accurately describes what happens — no fabrication
- [ ] Scene numbering is sequential with no gaps
- [ ] Flashback/transition markers preserved in headings

### Location Extraction (`the-mariner-locations.json`)

- [ ] Every significant location has an entry (not just main settings)
- [ ] `location_id` matches kebab-case convention
- [ ] `physical_traits` are directly described in the script, not assumed
- [ ] `must_mention_scenes` lists all scenes where this location appears
- [ ] `key_facts` are grounded in script text
- [ ] `narrative_significance_must_mention` captures the thematic role
- [ ] `aliases` include all names used for the location

### Prop Extraction (`the-mariner-props.json`)

- [ ] Every narratively significant prop has an entry (weapons, MacGuffins, symbolic objects)
- [ ] `prop_id` matches kebab-case convention
- [ ] `physical_traits` are directly described, not generic
- [ ] `must_mention_scenes` lists all appearances
- [ ] `key_facts` are grounded in script text
- [ ] `narrative_significance_must_mention` captures thematic/plot function
- [ ] Background props (furniture, generic items) are correctly excluded

### Relationship Discovery (`the-mariner-relationships.json`)

- [ ] Every critical relationship between entities is captured
- [ ] `source_id` and `target_id` match IDs from character/location/prop goldens
- [ ] `source_type` and `target_type` are correct (`character`, `prop`, `location`)
- [ ] `relationship_type_keywords` are specific, not generic ("sibling" not "related")
- [ ] `direction` is correct (`symmetric` for mutual, `source_to_target` for directional)
- [ ] `must_mention_evidence` items are findable in the screenplay
- [ ] `min_confidence` is calibrated — explicit relationships higher than implied ones
- [ ] `importance` reflects narrative weight (`critical` for plot-driving relationships)
- [ ] `min_must_find` count is achievable (not set too high for borderline entries)
- [ ] `max_total_edges` is reasonable (not so tight it penalizes thorough models)
- [ ] `false_positive_examples` are genuinely wrong relationships, not edge cases

### Config Detection (`the-mariner-config.json`)

- [ ] Every field has the correct `match_type` for its data shape
- [ ] `expected_value`/`expected_values`/`expected_keywords` match the screenplay
- [ ] `expected_range` bounds are reasonable (not too tight, not too loose)
- [ ] `must_include` lists are complete for critical items
- [ ] `should_include_any` lists cover the right candidates
- [ ] `must_mention` keywords are actually in the screenplay
- [ ] `importance` reflects how central each field is to correct config detection
- [ ] `min_confidence` thresholds match evidence strength
- [ ] `allow_null` is set correctly for optional fields

### Normalization (`normalize-signal-golden.json`)

- [ ] `expected_scenes` matches all scene headings in the input
- [ ] `expected_characters` lists all speaking characters
- [ ] `required_dialogue` — each `{character, fragment}` is a real line from the input
- [ ] `forbidden_patterns` — each regex catches a real formatting artifact (markdown, etc.)
- [ ] `structural_rules` — each boolean reflects Fountain spec requirements
- [ ] Source screenplay is correctly identified (Signal in the Rain, not The Mariner)

### Scene Enrichment (`enrich-scenes-golden.json`)

- [ ] Each scene key maps to the correct scene
- [ ] `heading`, `location`, `time_of_day`, `int_ext` match the actual scene
- [ ] `characters_present` is complete (dialogue + action line characters)
- [ ] `expected_tone` descriptors are supported by the scene's content and mood
- [ ] `expected_beat_types` use valid enum values only
- [ ] `key_details` are specific and grounded — no generic filler
- [ ] Beat types match what actually happens (don't label exposition as "revelation")

### QA Pass (`qa-pass-golden.json`)

- [ ] `good_scene` — the test data actually passes quality checks
- [ ] `bad_scene` — the test data has genuine, identifiable errors
- [ ] `expected_passed` is correct for each test case
- [ ] `max_errors`/`max_warnings` thresholds are calibrated to the test data
- [ ] `min_errors` is achievable — the errors are detectable, not subtle
- [ ] `required_issues` — each `{field, reason}` describes a real error in the test data
- [ ] `required_in_summary` keywords are reasonable expectations for a good-scene summary

### Continuity Extraction (`continuity-extraction-golden.json`)

- [ ] Each scene key maps to the correct scene text
- [ ] `expected_entities` uses correct `type:id` format
- [ ] `expected_properties` — each property key is valid for its entity type
- [ ] `expected_properties` — `value_patterns` are findable in the scene text
- [ ] `expected_changes` — changes actually happen between scenes (not static state)
- [ ] `expected_changes` — `previous_patterns` and `new_patterns` are accurate
- [ ] `key_evidence` items are direct quotes from the scene text
- [ ] `expected_confidence_range` is calibrated to evidence clarity
- [ ] Entity keys are consistent across scenes (same entity, same key)
- [ ] Source screenplay is correctly identified (The Dock, not The Mariner)

---

## Step 5: Fix issues

If you found issues, fix them directly in the golden JSON file. For each fix:
- Note what was wrong and what you changed
- Verify the fix doesn't break cross-references to other goldens
- Run the structural validator after fixing: `.venv/bin/python benchmarks/golden/validate-golden.py`

## Step 6: Update the checklist

Edit `benchmarks/golden/_verification-checklist.md`:
- If issues were found and fixed: `PASS N (issues found: X)` — needs another pass
- If zero issues found: `CLEAN (pass N)` — this fixture is done

## Step 7: Report

Tell the user:
- Which fixture you verified
- How many issues found
- What was fixed (brief list)
- Whether it's CLEAN or needs another pass

## Important Notes

- **Be adversarial.** You're trying to FIND bugs, not confirm correctness. Assume the golden has errors until proven otherwise.
- **Read the input word by word.** Skim reading misses subtle details that become golden errors.
- **Check evidence against actual text.** Don't trust that a `must_have_evidence` string is a real quote — verify it.
- **The golden must not be more confident than the input warrants.** If the script implies something but doesn't state it, the golden shouldn't treat it as established fact.
- **Cross-reference between goldens.** A character mentioned in the relationships golden must exist in the characters golden. A location in the scenes golden must exist in the locations golden.
- **Scorer-side reference principle.** Remember: golden fields are evaluation criteria, not model output mirrors. A field like `key_traits` defines what traits the scorer checks for, not the exact format the model produces.
- **Don't verify what you just created.** If you wrote this golden, you cannot verify it. Context isolation between creator and verifier is essential.
