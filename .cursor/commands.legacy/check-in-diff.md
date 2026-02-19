# Check In Diff

Review local changes and prepare a safe commit plan.

## Review Commands

Run and inspect:

- `git status --short`
- `git diff --stat`
- `git diff`
- `git ls-files --others --exclude-standard`

Include untracked files in review.

## Validate Change Set

- Verify no secrets/tokens/credentials are included.
- Verify `output/` artifacts are not staged.
- Confirm docs are updated when behavior or workflow changed.
- Confirm relevant tests/lint were run for touched code.

## Commit Guidance

- Stage only intentional files.
- Craft commit message focused on _why_.
- Commit only when user explicitly asks.
- Push only when user explicitly asks.

## Output Format

Provide:

1. What changed (grouped by area)
2. Risks or missing checks
3. Suggested commit message
4. Ready-to-run commit command sequence
