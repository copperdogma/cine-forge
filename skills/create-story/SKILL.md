---
name: create-story
description: Scaffold a numbered story file and update the story index.
user-invocable: true
---

# create-story

Use this skill to create a new story in `docs/stories/` with consistent format.

## Inputs

- `title`: human-readable story title.
- `slug`: kebab-case slug.
- `phase`: roadmap phase label.
- `priority`: High/Medium/Low.
- `spec_refs`: relevant spec section ids.

## Steps

1. Determine next story number from `docs/stories/story-*.md`.
2. Create file:
   - `docs/stories/story-{NNN}-{slug}.md`
3. Include sections:
   - Status
   - Created date
   - Spec refs
   - Depends on
   - Goal
   - Acceptance Criteria
   - Tasks
   - Notes
   - Work Log
4. Update `docs/stories.md` index with:
   - id
   - title
   - phase
   - priority
   - status
   - link
5. Verify numbering consistency and cross-links.

## Conventions

- Keep acceptance criteria testable and concrete.
- Explicitly call out what is in/out of scope.
- Keep tasks implementation-oriented and ordered.
