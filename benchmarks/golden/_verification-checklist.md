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
| 1 | `the-mariner-characters.json` | character-extraction | PENDING | |
| 2 | `the-mariner-scenes.json` | scene-extraction | PENDING | |
| 3 | `the-mariner-locations.json` | location-extraction | PENDING | |
| 4 | `the-mariner-props.json` | prop-extraction | PENDING | |
| 5 | `the-mariner-relationships.json` | relationship-discovery | PENDING | |
| 6 | `the-mariner-config.json` | config-detection | PENDING | |
| 7 | `normalize-signal-golden.json` | normalization | PENDING | |
| 8 | `enrich-scenes-golden.json` | scene-enrichment | PENDING | |
| 9 | `qa-pass-golden.json` | qa-pass | PENDING | |
| 10 | `continuity-extraction-golden.json` | continuity-extraction | PENDING | |

## Rules

- Work through fixtures in order (1 -> 10), choosing the first that is NOT "CLEAN"
- After each pass, update this checklist with the result
- If issues were found and fixed, the next pass on that fixture starts fresh
- A fixture only moves to CLEAN after a pass with zero issues
- Once all 10 are CLEAN, verification is complete
- Use the verification protocol: `benchmarks/golden/_verify-golden-outputs.md`
- Run the structural validator after fixes: `.venv/bin/python benchmarks/golden/validate-golden.py`
