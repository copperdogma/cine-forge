---
name: create-story
description: Scaffold a numbered story file and update the story index
user-invocable: true
---

# /create-story [title]

Create a new story in `docs/stories/` with consistent format.

## Inputs

- `title`: human-readable story title
- `slug`: kebab-case slug (derived from title if not provided)
- `priority`: High / Medium / Low (default: Medium)
- `spec_refs`: relevant spec.md sections
- `depends_on`: story IDs this depends on (if any)

## Steps

1. **Run the bootstrap script:**

   ```bash
   .agents/skills/create-story/scripts/start-story.sh <slug> [priority]
   ```

   This creates `docs/stories/story-NNN-<slug>.md` from the template with the next available number. It outputs the file path.

2. **Fill in the story file** — Replace all placeholder text (`{...}`) with real content:
   - Title (replace the slug with the human-readable title)
   - Goal, acceptance criteria, out of scope, tasks, files to modify
   - Spec refs and dependencies
   - AI considerations for this specific story

3. **Update story index** — Add a row to the table in `docs/stories.md`:
   `| NNN | Title | Priority | Pending | [link](stories/story-NNN-slug.md) |`

4. **Verify** — Confirm the file exists, numbering is consistent, and the stories.md row is correct.

## Conventions

- Acceptance criteria must be testable and concrete
- Explicitly call out what is in/out of scope
- Tasks should be implementation-oriented and ordered
- Always include the AI Considerations section — force the "LLM call vs code" question
- Always include the tenet verification checklist with individual checkboxes per tenet
- "Files to Modify" is gold for AI agents — fill it in when known
- Stories are living documents — the AI reads them repeatedly during implementation

## Guardrails

- Never overwrite an existing story file — the script will error if the file exists
- Never commit or push without explicit user request
- Verify numbering is sequential — no gaps, no duplicates

## Work Log Entry Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```
