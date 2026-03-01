---
name: verify-eval
description: Investigate eval mismatches — classify as model-wrong, golden-wrong, or ambiguous. Fix golden when wrong, re-run eval.
user-invocable: true
---

# /verify-eval

Investigate every mismatch between model output and golden reference after an eval
run. Classify each as model-wrong, golden-wrong, or ambiguous. Fix the golden when
it's wrong, re-run the eval, and report verified scores.

**Raw eval scores are meaningless. Only verified scores count.**

## When to Run

After ANY eval that compares model output against golden references:
- promptfoo evals (`cd benchmarks && promptfoo eval -c tasks/<name>.yaml`)
- Acceptance tests (`PYTHONPATH=src .venv/bin/python -m pytest`)
- Ad-hoc comparison scripts
- Any time scores are computed against a golden file

This is not optional. An eval without verification is incomplete.

## Arguments

- `[eval-command]` — (optional) The eval command that was just run. If not provided,
  the skill will ask which eval to verify.
- `[story-file]` — (optional) Path to the story file where the work log should be
  updated. If not provided, the skill will look for the active story.

## Phase 1: Locate Eval Results

1. Identify which eval was run (promptfoo, acceptance tests, ad-hoc script).
2. Find the output showing mismatches — extra entities, missing entities, name
   mismatches, relationship discrepancies, structural failures.
3. If the eval hasn't been run yet, run it now to establish raw scores.

## Phase 2: Enumerate Mismatches

### Getting the comparison data

Eval output (scores, pass/fail) is not enough — you need the actual outputs
side by side. How to get them depends on the eval type:

- **promptfoo evals**: The eval output includes model responses. Load the golden
  from `benchmarks/golden/`. Compare entity lists, field coverage, structural quality.
  Use `promptfoo view` to inspect results interactively if needed.
- **Acceptance tests**: Run the pipeline on the fixture, capture output artifacts.
  Load the golden JSON from `tests/fixtures/golden/`. Compare side by side.
- **Ad-hoc scripts**: Write a short script that runs the comparison and prints both
  outputs sorted for easy diffing.

### Build the mismatch table

For each mismatch between model output and golden reference:

```
| # | Type    | Model says        | Golden says       | Classification | Notes |
|---|---------|-------------------|-------------------|----------------|-------|
| 1 | Extra   | "some entity"     | (not in golden)   | ?              |       |
| 2 | Missing | (not in output)   | "Expected Entity" | ?              |       |
| 3 | Name    | "Dr Bennett"      | "Dr. Bennett"     | ?              |       |
```

Categories to check:
- **Extra entities**: In model output but not matched to any golden entity
- **Missing entities**: In golden but not matched to any model entity
- **Name mismatches**: Matched but with naming discrepancies
- **Structural issues**: Wrong types, missing fields, format problems
- **Semantic issues**: Content present but shallow, wrong, or missing insight
- **Relationship discrepancies**: Wrong type, missing, or extra relationships

## Phase 3: Classify Each Mismatch `[judgment]`

For EVERY mismatch, read the source text and determine:

| Finding | Action |
|---------|--------|
| **Model-wrong** — hallucination, over-extraction, naming error, shallow reasoning | Golden stands. Document as a real failure mode. |
| **Golden-wrong** — missing entity, wrong name, missing alias, inconsistent convention | Fix the golden. See Phase 4. |
| **Ambiguous** — insufficient evidence to decide | Note in work log. Defer until more evidence. |

### How to decide

- Read the actual source text (screenplay, input). What does it say?
- Is the entity a real person/character in the source? -> Should be in golden.
- Is the entity a group, object, pronoun, or non-person? -> Should NOT be in golden.
- Does the golden use a different name than the source? -> Golden may need an alias.
- Is the model using a reasonable variant? -> Golden needs an alias addition, not a model fix.
- Is the model output structurally correct but semantically shallow? -> Model-wrong.

### Thresholds for user consultation

- **Always ask the user** before adding or removing entities from the golden entity list. Entity list changes affect all downstream scoring.
- **Always ask the user** if golden fixes would change >5% of entries.
- Individual alias additions and field corrections can proceed without asking.

## Phase 4: Fix Golden & Re-run `[script]`

If any golden-wrong findings:

1. **Apply fixes** to the golden JSON files in `benchmarks/golden/` or `tests/fixtures/golden/`.
2. **Validate structure**: Run unit tests that validate golden fixture integrity.
3. **Run unit tests**: `.venv/bin/python -m pytest -m unit` — verify golden fixture tests still pass.
4. **Re-run the original eval** to get verified scores.
5. **Document the delta**: raw score -> verified score.

If no golden-wrong findings, skip to Phase 5.

## Phase 5: Report

Write a verification summary in the story work log (or return it to the caller):

```
## Eval Verification — [YYYY-MM-DD]

**Eval**: [command or description]
**Raw scores**: [metric=value, ...]

### Mismatch Classification (N total)

**Model-wrong (N):**
- [entity/issue]: [brief reason]

**Golden-wrong (N):**
- [entity/issue]: [what was fixed]

**Ambiguous (N):**
- [entity/issue]: [why deferred]

### Golden Fixes Applied
- [list of changes to golden files]

### Verified Scores (after golden fixes)
[metric=value, ...]

### Delta
- [metric]: X.XX -> X.XX (raw -> verified)
```

Update `docs/evals/registry.yaml` with the verified scores, `git_sha`, and date.

## Guardrails

- Never skip a mismatch — every one must be classified
- Never assume the golden is right just because it's the golden
- Never assume the model is right just because it's SOTA
- Ask the user before adding/removing entities from the golden entity list
- If golden fixes change >5% of entries, flag for user review before proceeding
- If mismatches reveal a code bug, document it and return to the calling story — this skill fixes goldens, not pipeline code
- Always update `docs/evals/registry.yaml` with verified scores after re-running

## Boundaries

- **In scope**: Mismatch investigation, golden fixes, re-running evals, reporting
- **Out of scope**: Fixing model/pipeline code (return findings to the story), creating new golden files from scratch (use `/setup-golden`), golden structural issues like schema problems
