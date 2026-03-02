---
name: golden-create
description: Create a golden reference output from input data — research the format, process inputs, produce expected output files.
user-invocable: true
---

# /golden-create [fixture-id | input-path]

Create a golden reference test fixture from input data. The output doesn't need to
be perfect — `/golden-verify` catches issues on subsequent passes.

**Usage:**
```
/golden-create character-extraction         # existing golden by eval name
/golden-create ~/scripts/new-screenplay/    # any input path
/golden-create                              # scan inbox, pick first item
```

## Prerequisites

The golden workspace must exist at `benchmarks/golden/` with at least a
`README.md` format spec. If it doesn't, tell the user to run `/setup-golden` first.

## Where Things Live

- **Format spec:** `benchmarks/golden/README.md` — canonical schema reference
- **Verification protocol:** `benchmarks/golden/_verify-golden-outputs.md` — write with this in mind
- **Existing golden files:** Browse any existing golden for a concrete example
- **Inbox:** `benchmarks/golden/_inbox/`
- **Validator:** `.venv/bin/python benchmarks/golden/validate-golden.py [fixture-id]`
- **Checklist:** `benchmarks/golden/_verification-checklist.md`
- **Eval configs:** `benchmarks/tasks/` — promptfoo YAML configs that consume goldens
- **Scorers:** `benchmarks/scorers/` — Python scoring scripts

## Workflow

1. **Research the format fresh.** Read README.md and one existing golden file every time.
   Don't assume you know the schema from prior context — it may have changed.

2. **Find the input.** Check the given path, inbox, or existing fixture directory.
   If nothing exists, tell the user where to drop inputs.

3. **Read the input completely.** Build a thorough mental model of every entity,
   relationship, and detail before writing anything. This step determines output quality.
   For screenplays: read the full script (or relevant scenes), note every character,
   location, prop, relationship, and scene boundary.

4. **Write the golden output** — JSON files matching the schema in README.md.
   Set up the fixture directory if needed (move from inbox, name files per convention).

5. **Validate and track.** Run the validator until it passes clean. Add a PENDING
   entry to the checklist. Update the coverage matrix if it exists.

6. **Report** what was created, entity counts, anything interesting, and that
   verification is pending.

## Principles That Matter

These are what the verifier will reject you for violating:

- **Evidence must be grounded.** Every extracted entity must trace to specific
  screenplay text. If you can't point to where in the script a character appears,
  either the entry shouldn't exist or you missed something in the input.
- **Don't over-extract.** A character mentioned once in a stage direction with no
  lines or significance doesn't need a full bible entry. Match the extraction
  depth to the entity's narrative importance.
- **Preserve ambiguity.** Guessing wrong is worse than flagging uncertainty. If
  a relationship type is unclear, note it rather than picking one.
- **Don't aim for perfection.** A good-faith 90% golden is more valuable than no
  golden. `/golden-verify` exists for the last 10%.

## Guardrails

- Never create goldens without reading the full input first
- Never accept AI-generated golden outputs without at least one review pass
- Always run the structural validator before declaring done
- Always update the verification checklist with a PENDING entry
