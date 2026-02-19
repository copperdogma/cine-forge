---
name: validate
description: Evaluate implementation quality and requirement coverage from local diffs.
user-invocable: true
---

# validate

Use this skill to assess what was built against requirements.

## Inputs

- Optional requirement source (story/ticket path).

## Steps

1. Collect full local changes:
   - `git status --short`
   - `git diff --stat`
   - `git diff`
   - `git ls-files --others --exclude-standard`
2. Review changed files (including untracked).
3. If story/ticket known:
   - map each requirement/task to `Met`, `Partial`, `Unmet`
   - provide evidence per item
4. Run/inspect relevant test and lint evidence:
   - `.venv/bin/python -m pytest -m unit --tb=short -q` — all unit tests pass
   - `.venv/bin/python -m ruff check src/ tests/` — lint clean
   - `cd ui && npx tsc -b` — TypeScript build check (must use `-b`, NOT `--noEmit` — see note below)
5. Produce findings prioritized by severity.

**IMPORTANT**: Always use `tsc -b` (build mode), never `tsc --noEmit`. The root `tsconfig.json` has `"files": []` with no linting rules — `tsc --noEmit` skips the strict checks in `tsconfig.app.json` (like `noUnusedLocals`). `tsc -b` follows `references` and applies the full config, matching what `npm run build` does in production.

## Output Format

- Findings (highest risk first)
- Requirement scorecard (`Met/Partial/Unmet`)
- Overall grade (`A`-`F`) with rationale
- Concrete next-step plan

## Guardrails

- Treat important `Partial`/`Unmet` requirements as blocking unless explicitly deferred.
- Prefer specific evidence over generic summaries.
