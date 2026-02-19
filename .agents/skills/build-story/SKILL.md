---
name: build-story
description: Implement a story with checklist hygiene, validation, and work-log discipline.
user-invocable: true
---

# build-story

Use this skill to execute a story in `docs/stories/` from planning through implementation updates.

## Inputs

- Story reference: id, title, or path.
- Optional scope constraints (files/modules to focus on).

## Steps

1. Resolve the target story from `docs/stories.md` if needed.
2. Open story file and verify required sections:
   - Goal
   - Acceptance Criteria
   - Tasks
   - Work Log
3. Normalize tasks:
   - ensure actionable checkbox items exist
   - preserve intent of existing items
4. Execute implementation for selected scope.
5. Run relevant checks (`make test-unit` minimum).
6. Update:
   - task checkboxes
   - acceptance criteria status (if tracked)
   - work log entries with evidence and next steps

## Work Log Entry Format

- `YYYYMMDD-HHMM — action summary`
- Result status
- Evidence (files/commands)
- Next step or blocker

## Guardrails

- Do not mark story done without explicit validation.
- Do not commit or push unless user asks.
