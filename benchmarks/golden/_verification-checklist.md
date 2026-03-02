# Golden Output Verification Checklist

Track verification passes for each golden fixture. A fixture is "clean" when a full
adversarial pass finds zero issues.

## Status Key

- **PENDING** — Not yet verified
- **PASS N (issues found: X)** — Completed pass N, found X issues, needs another pass
- **CLEAN (pass N)** — Pass N found zero issues. Done.

## Fixtures

| # | Fixture | Eval | Status | Last Pass Notes |
|---|---------|------|--------|-----------------|
| 1 | `the-mariner-characters.json` | character-extraction | CLEAN (pass 2) | Pass 2: Zero issues. All 5 characters verified line-by-line against screenplay. Every key_trait supported by specific script evidence. Every must_have_evidence is a direct quote or close paraphrase findable in text. Every must_mention_scenes matches actual scene headings. Every key_fact grounded in script. All aliases verified (Billy, Will, Mariner for protagonist; Rosey, Rosie for Rose; Mr. Salvatori for antagonist). Relationship targets and types all valid per enum. Narrative roles correct (protagonist for Mariner, supporting for all others). Named minor characters (Rosco, Mikey, Carlos) correctly excluded — no narrative arc or significant relationships. Cross-references to relationships golden consistent. Validator PASS, 0 errors, 2 warnings (expected: empty aliases for DAD and VINNIE). |
| 2 | `the-mariner-scenes.json` | scene-extraction | CLEAN (pass 2) | Pass 2: Zero issues. All 15 scene headings match screenplay text exactly (including BEGIN FLASHBACK prefixes, (FLASHBACK)/(BACK TO PRESENT) suffixes). All int_ext and time_of_day values correct. All character lists complete (named/speaking characters present, unnamed extras consistently excluded). All summaries accurate with no fabricated details. Scene count correct at 15. Sequential numbering with no gaps. Validator PASS, 0 errors, 2 warnings (expected: empty character arrays on establishing shots). |
| 3 | `the-mariner-locations.json` | location-extraction | CLEAN (pass 2) | Pass 2: Zero issues. All 5 locations verified against screenplay text. Every physical_trait traces to specific action lines. Every key_fact grounded in script. Every must_mention_scenes matches actual scene headings. Aliases all justified (e.g., "Ruddy & Green Building" matches INT heading spelling variant). Cross-references to scenes and relationships goldens consistent (15th-floor ID matches). Sub-locations (11th floor, stairwell, 13th floor) reasonably consolidated under building entry. Validator PASS, 0 errors, 0 warnings. |
| 4 | `the-mariner-props.json` | prop-extraction | CLEAN (pass 2) | Pass 2: Zero issues found. All 3 props (OAR, PURSE, FLARE GUN) verified line-by-line against screenplay. Every physical_trait traces to specific action lines (oar: lines 60, 265; purse: line 168; flare gun: lines 256, 261). Every must_mention_scenes maps to actual scene headings where the prop appears or is discussed. Every key_fact grounded in script text. All aliases justified by screenplay text. narrative_significance_must_mention keywords capture correct thematic roles (oar=weapon/maritime/identity/father; purse=MacGuffin/cryptocurrency; flare gun=maritime/weapon/absurd). Prop selection appropriate: AirTag (dialogue-only), submachine gun (generic), tattoo (character element) correctly excluded. Cross-reference note: relationship golden uses simpler prop IDs (oar, purse) vs props golden (oar-bosun, roses-purse) — mismatch is in relationship golden, not here. Validator PASS, 0 errors, 0 warnings. |
| 5 | `the-mariner-relationships.json` | relationship-discovery | CLEAN (pass 2) | Pass 2: Zero issues. All 9 relationships grounded in screenplay text; entity IDs cross-reference correctly to character/location/prop goldens; evidence items findable; directions accurate; confidence calibrated; importance reflects narrative weight. Validator PASS. |
| 6 | `the-mariner-config.json` | config-detection | CLEAN (pass 1) | All fields verified against screenplay text. match_types correct, expected values grounded, confidence thresholds calibrated, importance levels appropriate, cross-references valid. No phantom entries, no missing critical entries. |
| 7 | `normalize-signal-golden.json` | normalization | CLEAN (pass 2) | Pass 2: Zero issues. All 4 expected_scenes match input headings. All 4 expected_characters verified. All 7 required_dialogue fragments traced to input text with correct character attribution. All 7 forbidden_patterns are valid regex and semantically correct (blockquotes, markdown headers, escaped hyphens/bangs, code fences, bold, underline). All 5 structural_rules correct per Fountain spec. Validator PASS, 0 errors, 0 warnings. |
| 8 | `enrich-scenes-golden.json` | scene-enrichment | CLEAN (pass 1) | All fields verified against input excerpts. Headings, locations, time_of_day, int_ext all correct. Characters_present complete for both scenes. Expected tones grounded in text (bittersweet borderline but defensible from flashback framing and Dad's "I try" pause). Beat types all valid enum values and accurately describe scene content. Key details specific and traceable to excerpt text. Cross-references to character golden valid. No phantom entries, no missing critical entries. |
| 9 | `qa-pass-golden.json` | qa-pass | CLEAN (pass 2) | Pass 1 fixed "Greene" typo and phantom "missing thugs". Pass 2: zero issues found — all 4 required_issues grounded in source text, good_scene extraction verified accurate, thresholds (max_errors=0, max_warnings=2, min_errors=2) well-calibrated, JSON valid, no phantom or missing entries. |
| 10 | `continuity-extraction-golden.json` | continuity-extraction | CLEAN (pass 3) | Pass 1 fixed missing emotional_state change in dock_day. Pass 2 found 5 issues (ownership, position, change events, previous_patterns, soaked). Pass 3: zero issues found — all 5 entities correct for dock_day, all 4 for dock_night (Jane correctly excluded). All expected_properties grounded in scene text with appropriate required flags. All expected_changes have accurate previous/new patterns matching entities_block and scene text. All key_evidence items verified as exact quotes. Confidence ranges calibrated. Entity keys consistent across scenes. No phantom entries, no missing entries. Validator PASS, 0 errors, 0 warnings. |

## Rules

- Work through fixtures in order (1 -> 10), choosing the first that is NOT "CLEAN"
- After each pass, update this checklist with the result
- If issues were found and fixed, the next pass on that fixture starts fresh
- A fixture only moves to CLEAN after a pass with zero issues
- Once all 10 are CLEAN, verification is complete
- Use the verification protocol: `benchmarks/golden/_verify-golden-outputs.md`
- Run the structural validator after fixes: `.venv/bin/python benchmarks/golden/validate-golden.py`
