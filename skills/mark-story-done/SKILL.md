---
name: mark-story-done
description: Validate a story is complete and update story statuses safely.
user-invocable: true
---

# mark-story-done

Use this skill to close a completed story.

## Inputs

- Story id/title/path (optional if inferable from context).

## Validation Steps

1. Resolve story file.
2. Validate:
   - tasks complete
   - acceptance criteria met
   - work log current
   - dependency constraints addressed
   - relevant tests/checks executed
3. Produce completion report with any remaining gaps.

## Apply Completion

If complete (or user approves remaining gaps):

1. Set story file status to `Done`.
2. Update corresponding row in `docs/stories.md` to `Done`.
3. Append completion note to story work log with date and evidence.

If not complete, stop and list blockers.

## Guardrails

- Never hide gaps; always report unmet criteria explicitly.
- Ask for confirmation when unresolved items remain.
