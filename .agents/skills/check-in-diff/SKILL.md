---
name: check-in-diff
description: Audit git changes before commit — review diff, flag risks, draft commit message
user-invocable: true
---

# /check-in-diff

Audit current git changes before committing.

## Steps

1. **Review state:**
   - `git status` — what's modified, staged, untracked?
   - `git diff` — what are the actual changes?
   - `git diff --staged` — what's already staged?

2. **Flag risks:**
   - Secrets, API keys, credentials, .env files?
   - Large binary files or build artifacts?
   - Changes outside the scope of the current story?
   - Schema changes without migrations?
   - Deleted tests or weakened assertions?

3. **Check alignment:**
   - Do changes match the story's task list?
   - Are docs updated for any behavioral changes?
   - Are new files in the right locations per project structure?

4. **Ensure CHANGELOG.md is updated:**
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

5. **Draft commit message:**
   - Summary line (imperative, <72 chars)
   - Body: what changed and why
   - Reference story number if applicable

6. **Propose staging plan:**
   - Which files to stage (specific files, not `git add .`)
   - Any files to exclude from this commit
   - Always include CHANGELOG.md
   - Suggest splitting into multiple commits if changes are unrelated

## Guardrails

- NEVER commit or push without explicit request from the user
- NEVER suggest committing secrets, credentials, .env files, or build artifacts
- NEVER use `git add .` or `git add -A` — always stage specific files
- Flag any changes that look unintentional or outside current story scope
