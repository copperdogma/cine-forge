---
name: triage
description: Process inbox items into stories, research spikes, ADRs, or spec updates
user-invocable: true
---

# /triage

Go through accumulated inbox items together with the user.

## Steps

1. **Read inbox** — Load `docs/inbox.md`. List all untriaged items.

2. **For each item, discuss with the user:**
   - What is it? (Summarize if not already summarized)
   - How does it relate to the current project state?
   - What should we do with it?
     - **New story** → Create story file, add to index
     - **Research spike** → Set up deep-research project
     - **ADR** → Needs a decision, create ADR draft
     - **Spec update** → Update spec.md directly
     - **Note on existing story** → Add to that story's notes
     - **Backlog/defer** → Move to a "Deferred" section
     - **Discard** → Remove from inbox

3. **Create artifacts** — For each decision, create the appropriate artifact immediately.

4. **Mark triaged** — Move processed items to the Triaged section with a reference to what was created:
   ```
   - 2026-02-18 — [Item description] → created story-015 / updated spec / deferred
   ```

5. **Summarize** — Quick summary of what was processed and any follow-up actions.

## Guardrails

- Always discuss with the user before creating artifacts — don't auto-triage
- Keep the inbox clean — every item should end up somewhere or be explicitly discarded
- If an item needs investigation before triaging, say so and move on to the next
