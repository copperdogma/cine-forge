# Validate

Validate implemented work against requirements and changed files.

## Change Review

Always inspect full local delta:

- `git status --short`
- `git diff --stat`
- `git diff`
- `git ls-files --others --exclude-standard`

Open changed files (including untracked) and validate behavior against requirements.

## Story-Aware Validation

If a story/ticket is known, extract:

- Acceptance criteria / requirements
- Task checklist

Then produce:

- Per-item status: `Met`, `Partial`, `Unmet`
- Evidence for each item
- Explicit remaining gaps with concrete next steps

## Validation Checklist

- Architecture boundaries and contracts respected
- Code quality and project conventions followed
- Edge cases and error behavior considered
- Tests/lint coverage appropriate for scope
- Docs/story work log updated

## Output Contract

Return:

1. Findings ordered by severity (bugs, regressions, risks first)
2. Requirement scorecard (`Met/Partial/Unmet`)
3. Overall quality grade (`A`-`F`) with rationale
4. Concrete next-step plan user can approve
