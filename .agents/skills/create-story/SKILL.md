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
- `ideal_refs`: ideal.md requirements this delivers (e.g., Reqs #1, #3)
- `spec_refs`: relevant spec.md sections or compromise numbers
- `depends_on`: story IDs this depends on (if any)
- `status`: Pending (fully detailed, ready to build) or Draft (skeleton with goal + notes, NOT ready to build)

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
   - Approach evaluation: candidate approaches (AI-only, hybrid, code) and what eval distinguishes them

3. **Update story index** — Add a row to the table in `docs/stories.md`:
   `| NNN | Title | Priority | Pending | [link](stories/story-NNN-slug.md) |`
   Insert the row in System order (not at the bottom). IDs may be out of numeric order — that is expected and correct.

4. **Verify** — Confirm the file exists, numbering is consistent, and the stories.md row is correct.

## Story Statuses

- **Draft**: Skeleton with goal + notes but placeholder ACs and tasks. NOT ready to build. Accumulates research and design ideas over time. Promoted to Pending when ready.
- **Pending**: Fully detailed ACs, tasks, files to modify. Ready for `/build-story`.
- **In Progress**: Being built.
- **Done**: Validated complete.

## Conventions

- Acceptance criteria must be testable and concrete
- Explicitly call out what is in/out of scope
- Tasks should be implementation-oriented and ordered
- Always include the Approach Evaluation section — list candidate approaches (AI-only, hybrid, code) without pre-deciding. The story should identify what eval would distinguish approaches, not pick a winner. Approach selection happens during build-story's eval-first gate with measured evidence.
- If the story will involve running evals (extraction/pipeline behavior, golden comparison), add a task: "Run `/verify-eval` after eval — classify all mismatches, fix golden if needed, document verified scores. Re-assess acceptance criteria against verified scores — raw scores do not determine story success."
- Always include the tenet verification checklist with individual checkboxes per tenet
- "Files to Modify" is gold for AI agents — fill it in when known
- Stories are living documents — the AI reads them repeatedly during implementation
- Every story should trace back to an Ideal requirement or spec compromise (via `Ideal Refs` / `Spec Refs`). Untraceable stories are potential scope creep.
- **Ideal alignment check** — Before writing the story file, verify alignment:
  - Does this story close an Ideal gap? → Good, proceed.
  - Does it move AWAY from the Ideal? → Push back. Explain why and suggest alternatives.
  - Does it only optimize a compromise without closing a gap? → Flag as low-value.
  - A story that references a spec compromise is not automatically aligned — it must move toward the Ideal, not entrench the compromise further.
  - If the story implements a new AI compromise: note whether a detection eval exists or should be created.
  - If the story adds or modifies an AI-powered capability: check `docs/evals/registry.yaml` for an existing eval. If none exists, note in the story that an eval entry should be created during implementation.

## Guardrails

- Never overwrite an existing story file — the script will error if the file exists
- Never commit or push without explicit user request
- Verify numbering is sequential — no gaps, no duplicates

## Work Log Entry Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```
