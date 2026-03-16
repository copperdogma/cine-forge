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
- `adr_refs`: relevant decision records in `docs/decisions/` or `docs/design/` (or `None found after search`)
- `depends_on`: story IDs this depends on (if any)
- `status`: Draft (default, skeleton with goal + notes, NOT ready to build) or Pending (fully detailed, ready to build)

## Steps

1. **Run the bootstrap script:**

   ```bash
   .agents/skills/create-story/scripts/start-story.sh <slug> [priority]
   ```

   This creates `docs/stories/story-NNN-<slug>.md` from the template with the next available number. It outputs the file path.

2. **Fill in the story file** — Replace all placeholder text (`{...}`) with real content:
   - Title (replace the slug with the human-readable title)
   - Goal, acceptance criteria, out of scope, tasks, files to modify
   - Ideal refs, spec refs, ADR refs, and dependencies
   - Approach evaluation: simplification baseline, candidate approaches (AI-only, hybrid, code), repo constraints, existing patterns to reuse, and what eval distinguishes them
   - Workflow gates for build handoff, validation, and story closure
   - Redundancy targets: old code or docs this story may make obsolete
   - UI verification work if the story touches the UI
   - If the feature is user-facing and requires both backend/API and UI to be usable, keep that end-to-end path in the same story by default. Split only when the scope is genuinely huge and independently deliverable.

3. **Update story index** — Add a row to the table in `docs/stories.md`:
   `| NNN | Title | Priority | Draft | [link](stories/story-NNN-slug.md) |`
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
- Always include the Approach Evaluation section — list candidate approaches (AI-only, hybrid, code) without pre-deciding. The story should identify what eval would distinguish approaches, what repo constraints matter, and which ADRs / existing patterns constrain the choice. Approach selection happens during build-story's eval-first gate with measured evidence.
- **Simplification baseline gate**: Every story involving new logic must answer: "Can a single LLM call already do this?" If untested, the first task should be measuring that baseline.
- Search `docs/decisions/` and `docs/design/` for relevant ADRs / decision records while drafting. If none apply, say so explicitly instead of leaving the field vague. If a scout doc or runbook materially constrains execution, cite it in Notes or Decision Context too.
- If the story changes existing behavior, name likely redundancy / removal targets up front. New code that supersedes old code should not silently accumulate parallel paths.
- If the story touches the UI, include explicit browser verification work in the task list. Static checks alone are not enough.
- **End-to-end user feature rule**: If a feature needs backend/API plus UI to be usable by a user, keep them in the SAME story by default. Do not create an "API now, UI later" split for an ordinary feature. Only split backend and UI into separate stories when the scope is genuinely huge (`L`/`XL`), independently valuable, and the dependency boundary is explicit in the story text.
- If the story changes agent tooling or project instructions, include `make skills-check` in the task list.
- Always include the Workflow Gates section. These are not ordinary implementation tasks; they enforce the handoff chain: `/build-story` summary → `/validate` → `/mark-story-done`.
- If the story will involve running evals (extraction/pipeline behavior, golden comparison), add a task: "Run `/improve-eval` or equivalent mismatch investigation after the eval — classify all mismatches, fix golden if needed, document verified scores. Re-assess acceptance criteria against verified scores — raw scores do not determine story success."
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
- Do not leave ADR / decision references implicit for architecture-affecting stories

## Work Log Entry Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```
