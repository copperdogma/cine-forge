---
name: triage-inbox
description: Process inbox items into stories, research spikes, ADRs, or spec updates
user-invocable: true
---

# /triage-inbox

Go through accumulated inbox items together with the user.

## Steps

1. **Read inbox** — Load `docs/inbox.md`. List all untriaged items.

2. **Prioritize** — Before diving into individual items, evaluate the full inbox and present a prioritized recommendation:
   - Read the current story index (`docs/stories/index.md`) and recent project state to understand what's in flight.
   - Group items by theme if natural clusters exist (e.g., "these 3 are all chat UI bugs").
   - Recommend a **top 3-5** to triage first, with a short "why" for each:
     - Is it blocking current work?
     - Is it a quick win (bug fix, small story)?
     - Is it high user-impact?
     - Does it unlock other deferred items?
     - Is it time-sensitive (external API, model availability)?
   - Flag items that are probably **defer/discard** candidates so the user can batch-dismiss them.
   - Let the user adjust the order or override before proceeding.

3. **For each item, evaluate and discuss with the user:**

   a. **Challenge first: "What if we don't do this?"** — Before proposing a disposition, ask: what happens if we ignore this entirely? If the answer is "nothing much" or "20 lines in an existing module," it may not warrant a story or any action at all. This prevents backlog inflation.

   b. **Check for existing homes** — Before creating a new story, search existing Draft/Pending/In Progress stories for a natural fit. Often the best disposition is adding a design note to an existing story's Notes section rather than creating tracking overhead. Check:
      - Does an existing story already cover this scope?
      - Would this naturally fit as a task or note within an existing story?
      - Is there a Draft story that could absorb this?

   c. **Propose disposition:**
      - **Fold into existing story** → Add as a note/task to that story's Notes section (preferred when a home exists)
      - **New story** → Create story file, add to index (only when truly independent)
      - **Research spike** → Set up deep-research project
      - **ADR** → Needs a decision, create ADR draft
      - **Spec update** → Update spec.md directly
      - **Backlog/defer** → Note why and revisit later
      - **Discard** → Remove from inbox with brief rationale

4. **Create artifacts** — For each decision, create the appropriate artifact immediately.

5. **Delete from inbox** — Remove processed items from `docs/inbox.md`. The inbox is a processing queue, not an archive. Once an item has landed in a story, ADR, spec, or been explicitly discarded, it has no purpose remaining in the inbox. The artifact it created is now the source of truth.

6. **Summarize** — Quick summary of what was processed and any follow-up actions.

## Guardrails

- Always discuss with the user before creating artifacts — don't auto-triage
- Keep the inbox clean — every item should end up somewhere or be explicitly discarded
- If an item needs investigation before triaging, say so and move on to the next
- Prefer folding into existing stories over creating new ones — fight backlog inflation
- Always ask "what if we don't do this?" before committing to a story
