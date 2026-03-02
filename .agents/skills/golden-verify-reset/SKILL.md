---
name: golden-verify-reset
description: Reset the golden verification checklist to force re-verification of all fixtures.
user-invocable: true
---

# /golden-verify-reset [--all | fixture-id]

Reset golden fixture verification status to force re-verification.

**Why:** After schema changes, model upgrades, or when you want to double-check
previous verifications with fresh eyes. Useful before running `/golden-verify`
to force a complete re-check.

**Usage:**
```
/golden-verify-reset              # reset all CLEAN fixtures to PENDING
/golden-verify-reset character    # reset one specific fixture (partial match)
/golden-verify-reset --all        # reset everything including PASS entries
```

## What It Does

1. Read `benchmarks/golden/_verification-checklist.md`
2. Reset statuses:
   - Default: `CLEAN (pass N)` → `PENDING — reset for re-verification`
   - `--all`: also resets `PASS N (issues found: X)` entries
   - `fixture-id`: resets only that entry (partial match supported)
3. Preserve audit trail — set Last Pass Notes to `Reset YYYY-MM-DD. Previous: {old status}`
4. Report how many fixtures were reset

## Example

Before:
```
| 1 | the-mariner-characters | CLEAN (pass 1) | All good. |
```

After:
```
| 1 | the-mariner-characters | PENDING — reset for re-verification | Reset 2026-03-01. Previous: CLEAN (pass 1) |
```

## Guardrails

- Only modifies `_verification-checklist.md` — never touches golden output files
- Previous status is always preserved in Last Pass Notes for auditability
