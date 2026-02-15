---
name: check-in-diff
description: Audit local git changes and prepare a safe commit checklist and message.
user-invocable: true
---

# check-in-diff

Use this skill when preparing to commit.

## Steps

1. Review local state:
   - `git status --short`
   - `git diff --stat`
   - `git diff`
   - `git ls-files --others --exclude-standard`
2. Include untracked files in analysis.
3. Flag risks:
   - secrets or credentials
   - generated outputs (`output/`)
   - unintended broad edits
4. Confirm docs/tests alignment with code changes.
5. Draft:
   - concise commit message (why-focused)
   - staging plan (which files to include)

## Output Template

- Change summary by area
- Risk findings (if any)
- Proposed commit message
- Suggested staging/commit commands

## Guardrails

- Never commit/push unless the user explicitly asks.
- Never suggest committing secrets or local runtime outputs.
