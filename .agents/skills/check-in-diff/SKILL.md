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
5. Ensure CHANGELOG.md is updated:
   - Check whether `CHANGELOG.md` appears in `git diff --stat` or `git status --short`.
   - If CHANGELOG.md is already in the diff, verify the entry covers the current changes.
   - If CHANGELOG.md is absent from the diff, write an entry now:
     - Analyze the staged/unstaged changes to determine what was added, changed, or fixed.
     - Prepend a new entry after the `# Changelog` header using Keep a Changelog format:

       ```
       ## [YYYY-MM-DD] - Short summary

       ### Added
       - ...

       ### Changed
       - ...

       ### Fixed
       - ...
       ```

     - Use today's date. Only include subsections that apply.
     - Include CHANGELOG.md in the staging plan.
6. Draft:
   - concise commit message (why-focused)
   - staging plan (which files to include — always include CHANGELOG.md)

## Output Template

- Change summary by area
- Risk findings (if any)
- CHANGELOG.md status (already updated / entry written)
- Proposed commit message
- Suggested staging/commit commands

## Guardrails

- Never commit/push unless the user explicitly asks.
- Never suggest committing secrets or local runtime outputs.
