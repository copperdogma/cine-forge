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
| 1 | `the-mariner-characters.json` | character-extraction | CLEAN (pass 2) | Pass 1: Added MacAngus family name to MARINER key_facts; added Newfoundland dialect to DAD key_facts; added VINNIE→MARINER adversary relationship. Pass 2: Zero issues — all pass 1 fixes verified correct. Validator PASS, 0 errors, 2 warnings (expected: empty aliases for DAD and VINNIE). |
| 2 | `the-mariner-scenes.json` | scene-extraction | CLEAN (pass 1) | Zero issues. 15 headings verified exactly. RUDDY & GREENE vs GREEN inconsistency correctly mirrors screenplay typo. Characters lists accurate. Summaries no fabrication. Validator PASS, 0 errors, 2 warnings (expected: empty chars on establishing shots). |
| 3 | `the-mariner-locations.json` | location-extraction | CLEAN (pass 2) | Pass 1: Removed phantom alias "shore" from COASTLINE; added "mismatched paintings of different periods" to 15TH FLOOR. Pass 2: Zero issues — all pass 1 fixes verified correct. Validator PASS, 0 errors, 0 warnings. |
| 4 | `the-mariner-props.json` | prop-extraction | CLEAN (pass 2) | Pass 1: Removed phantom OAR scene ref; removed "BOSUN" alias from OAR; cleared PURSE physical_traits; fixed FLARE GUN wording; added AIRTAG prop. Pass 2: Zero issues — all fixes verified, AIRTAG entry confirmed accurate. Validator PASS, 0 errors, 2 warnings (expected: empty physical_traits for PURSE and AIRTAG). |
| 5 | `the-mariner-relationships.json` | relationship-discovery | CLEAN (pass 3) | Pass 1: Fixed 6 evidence strings; fixed prop IDs (oar-bosun, roses-purse); added mariner-flare-gun-weapon; improved false_positive_examples; bumped min_must_find 5→6. Pass 2: Added mariner-airtag-tracking (AIRTAG added to props golden needed corresponding edge). Pass 3: Zero issues — all 11 relationships verified, all evidence verbatim, all IDs cross-checked against entity goldens. Validator PASS, 0 errors, 0 warnings. |
| 6 | `the-mariner-config.json` | config-detection | CLEAN (pass 2) | Pass 1: format.expected_values narrowed; added "superhero" to genre; added dark comedy to tone. Pass 2: Zero issues — all fixes verified correct. Validator PASS, 0 errors, 0 warnings. |
| 7 | `normalize-signal-golden.json` | normalization | CLEAN (pass 2) | Pass 1: expected_scenes[3] fixed to "COMMUNITY RADIO STUDIO - CONTINUOUS"; removed phantom \\! forbidden_pattern. Pass 2: Zero issues — fixes verified. Removal of \\! also noted as correct (\\! would penalize valid Fountain force-action lines). Validator PASS, 0 errors, 0 warnings. |
| 8 | `enrich-scenes-golden.json` | scene-enrichment | CLEAN (pass 2) | Pass 1: Flashback tone "bittersweet"→"joyful"; key_details[2] "(contrasts later dark revelation)"→"(warm, perfect memory)". Pass 2: Zero issues — fixes verified. Elevator time_of_day "NIGHT" is defensible inference. Validator PASS, 0 errors, 0 warnings. |
| 9 | `qa-pass-golden.json` | qa-pass | CLEAN (pass 1) | Zero issues. Both test cases verified accurate. 4 required_issues all grounded in bad_scene data. max_warnings/required_in_summary are inert (scorer gap, not golden bug). Validator PASS, 0 errors, 0 warnings. |
| 10 | `continuity-extraction-golden.json` | continuity-extraction | CLEAN (pass 1) | Zero issues. All key_evidence exact quotes. expected_changes accurate deltas. Entity keys consistent. Jane correctly excluded from dock_night. Confidence ranges calibrated. Validator PASS, 0 errors, 0 warnings. |

## Rules

- Work through fixtures in order (1 -> 10), choosing the first that is NOT "CLEAN"
- After each pass, update this checklist with the result
- If issues were found and fixed, the next pass on that fixture starts fresh
- A fixture only moves to CLEAN after a pass with zero issues
- Once all 10 are CLEAN, verification is complete
- Use the verification protocol: `benchmarks/golden/_verify-golden-outputs.md`
- Run the structural validator after fixes: `.venv/bin/python benchmarks/golden/validate-golden.py`
