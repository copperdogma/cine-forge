---
name: reflect
description: Propagate implications of a change across ideal.md, spec.md, stories, and evals
user-invocable: true
---

# /reflect [what-changed]

Trace the implications of a change across the project's core documents.
Read-only and advisory — surfaces what needs attention, doesn't rewrite anything.

## When to Use

Any time something changes that might affect other documents:

- An ADR is decided (`/create-adr` calls this as its last step)
- The Ideal is updated (new requirement or preference discovered)
- The spec changes (compromise added, removed, or modified)
- An eval newly passes (a compromise may be deletable)
- An external change occurs (new SOTA model, ecosystem shift, regulatory change)
- A story reveals something about the Ideal that wasn't articulated before

## What This Skill Produces

A short impact report, either printed to the user or appended to the relevant
work log. No files are modified — the user decides what to act on.

## Steps

1. **Identify the change** — Either from the argument, the most recent git diff,
   or by asking the user: "What just changed?"

2. **Read current state:**
   - `docs/ideal.md` — the Ideal and requirements
   - `docs/spec.md` — compromises, untriaged ideas
   - `docs/stories.md` — story index (skim relevant story files if needed)
   - `evals/` — eval configurations and recent results (if they exist)

3. **Trace implications** — For the change, ask:

   **Ideal impact:**
   - Does this reveal a new ideal that wasn't articulated? (e.g., seeing a bad
     output makes you realize what "good" means)
   - Does this change an existing requirement or preference?
   - Does this make an implicit ideal explicit?

   **Spec impact:**
   - Does this add a new compromise? (If so, it needs a limitation type and
     detection mechanism.)
   - Does this make an existing compromise deletable? (If so, which eval
     should be re-run to confirm?)
   - Does this change the limitation type or evolution path of a compromise?
   - Are any untriaged ideas now relevant or now obsolete?

   **Story impact:**
   - Are any Pending or Draft stories affected? (scope change, new dependency,
     now unnecessary)
   - Are any Done stories invalidated? (behavioral change that affects
     completed work)
   - Should new stories be created? (don't create them — just flag)

   **Eval impact:**
   - Should any evals be re-run? (new model, changed golden reference,
     deleted compromise)
   - Are any evals now obsolete? (compromise was deleted)
   - Are new evals needed? (new compromise without a detection mechanism)

4. **Produce the impact report:**

```
## Reflect — {what changed}

### Ideal
- {impact or "No change needed"}

### Spec
- {impact or "No change needed"}

### Stories
- {stories affected, with IDs and brief reason}

### Evals
- {evals to re-run, create, or remove}

### Recommended Actions
- [ ] {specific action, ordered by priority}
```

5. **Suggest next steps** — Point the user to the appropriate skill:
   - Ideal needs updating → edit `docs/ideal.md` directly
   - Spec needs updating → edit `docs/spec.md` or run `/setup-spec`
   - Stories need realignment → create inbox items or flag for `/triage-stories`
   - Evals need re-running → `cd evals && promptfoo eval`
   - New compromise needs detection eval → `/setup-evals` or create a story

## Guardrails

- This is read-only and advisory. Never modify files.
- Always read the actual documents — don't guess from memory.
- Keep the impact report short and actionable. No essay.
- If there are no implications, say so: "No downstream impact detected."
- Don't create stories or inbox items — flag them for the user to create.
