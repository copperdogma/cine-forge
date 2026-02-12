# Mark Story Done

Mark a story as done in both `docs/stories.md` and its story file after validation.

## Resolve Story

- If a story id/path/title is provided, use it.
- Otherwise infer from:
  - current conversation
  - story file status
  - recent files touched
- If ambiguous, ask user to specify.

## Pre-Completion Validation

Before updating status:

1. Tasks checklist complete?
2. Acceptance criteria met?
3. Work log up to date?
4. Dependencies satisfied or explicitly accepted?
5. Relevant tests/checks executed?

## Completion Report

Report:

- Story id/title
- Tasks complete (`X/Y`)
- Acceptance criteria met (`X/Y`)
- Outstanding gaps (if any)
- Recommended next step

## Apply Status Changes

If complete (or user approves remaining gaps):

1. Set story file `**Status**: Done`
2. Update `docs/stories.md` row status to `Done`
3. Add a `Work Log` note with completion date and verification summary

If not complete, list blockers and stop.
