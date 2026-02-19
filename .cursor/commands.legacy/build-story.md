# Build Story

Start or continue implementation of a specific story in `docs/stories/`.

## Resolve Target Story

- Accept a story id (`001`), title, or full path.
- If id/title is provided, resolve via `docs/stories.md`.
- If unresolved, stop and ask for clarification.

## Required First Checks

1. Open the target story file.
2. Verify required sections exist and are usable:
   - `## Goal`
   - `## Acceptance Criteria`
   - `## Tasks` with checkbox items
   - `## Work Log`
3. If checklist items are missing, add actionable tasks without removing existing intent.

## Execution Flow

1. Validate story checklist completeness.
2. Implement scoped work for the story.
3. Run relevant checks (`make test-unit` minimum; add integration/smoke as needed).
4. Update checklist items to reflect actual completion.
5. Append work-log entries with concrete evidence.

## Work Log Format

Append-only entries under `## Work Log`:

- Timestamp: `YYYYMMDD-HHMM`
- Action performed
- Result (`Success`, `Partial`, `Blocked`, `Failed`)
- Evidence (files, commands, outputs)
- Next step

## Guardrails

- Do not mark story done unless acceptance criteria are met or user approves gaps.
- Do not run `git commit`/`push` unless explicitly requested by user.
- Never commit `output/` artifacts or secrets.
