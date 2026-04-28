---
name: triage-inbox
description: Process inbox items into stories, research spikes, ADRs, or spec updates
user-invocable: true
---

# /triage-inbox [scan]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Go through accumulated inbox items together with the user.

## Modes

- default: interactive processing mode
- `scan`: read-only scan mode for `/triage` orchestration. Summarize the top inbox items and likely dispositions, but do not create artifacts or delete anything.

## Lane Packet Mode

When full-sweep `/triage` asks for `scan`, return up to three neutral inbox
candidates or stop conditions. Do not choose the repo-wide winner and do not
process items. For each candidate include the Ideal/spec value, evidence from
`docs/inbox.md` and any obvious existing home, why now, suggested action shape,
whether it is story-worthy or too small, validation/stop condition, blockers,
and reasons not now.

Use this scan-mode output shape for full-sweep `/triage`:

```markdown
## Inbox Triage Lane Packet

### Lane Packet
- <neutral inbox candidate + Ideal/spec value + evidence + why now + action shape + stop condition + blockers + reasons not now>

### Stop Conditions
- <why no inbox action is warranted now, if applicable>
```

Do not include a final repo-wide recommendation, artifact-creation handoff, or
direct yes/no handoff in scan mode.

## Steps

1. **Read the methodology frame first**
   - Read `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, and `docs/build-map.md`
   - Goal: identify the current live gaps before letting inbox novelty drive priority

2. **Read inbox** — Load `docs/inbox.md`. List all untriaged items.

3. **Map inbox items to methodology gaps** — Before diving into individual items:
   - Identify which active gap or category each inbox item plausibly advances
   - If an item does not advance any meaningful gap, say so plainly

4. **Prioritize** — Evaluate the full inbox and present a prioritized disposition list:
   - Read the current generated story index (`docs/stories.md`) and recent project state to understand what's in flight
   - Group items by theme if natural clusters exist (e.g., "these 3 are all chat UI bugs").
   - Identify a **top 3-5** to triage first, with a short "why" for each:
     - What Ideal/spec/state gap does it address?
     - Does it advance the highest-leverage live gap or just a side issue?
     - Is it blocking current work?
     - Does it fill missing or partial substrate in an active methodology category?
     - Does it unlock other deferred items?
     - Is it time-sensitive (external API, model availability)?
   - Flag items that are probably **defer/discard** candidates so the user can batch-dismiss them.
   - Let the user adjust the order or override before proceeding.

5. **If running in `scan` mode, stop after the prioritized scan**
   - Return the top items, likely dispositions, and any health flags.
   - Include a `### Lane Packet` section with neutral candidates for
     full-sweep `/triage`.
   - Do not create artifacts.
   - Do not delete inbox entries.

6. **For each item, evaluate and discuss with the user:**

   a. **Challenge first: "What if we don't do this?"** — Before proposing a disposition, ask: what happens if we ignore this entirely? If the answer is "nothing much" or "20 lines in an existing module," it may not warrant a story or any action at all. This prevents backlog inflation.

   b. **Check for existing homes** — Before creating a new story, search existing Draft/Pending/In Progress stories for a natural fit. Often the best disposition is adding a design note to an existing story's Notes section rather than creating tracking overhead. Check:
      - Does an existing story already cover this scope?
      - Would this naturally fit as a task or note within an existing story?
      - Is there a Draft story that could absorb this?
      - Does the current methodology state reveal a larger gap that this item should be attached to rather than tracked as a standalone feature?

   c. **Propose disposition:**
      - **Fold into existing story** → Add as a note/task to that story's Notes section (preferred when a home exists)
      - **New story** → Create story file, add to index (only when truly independent)
      - **Research spike** → Set up deep-research project
      - **ADR** → Needs a decision, create ADR draft
      - **Spec update** → Update spec.md directly
      - **Backlog/defer** → Note why and revisit later
      - **Discard** → Remove from inbox with brief rationale

7. **Create artifacts** — For each decision, create the appropriate artifact immediately.

8. **Delete from inbox** — Remove processed items from `docs/inbox.md`. The inbox is a processing queue, not an archive. Once an item has landed in a story, ADR, spec, or been explicitly discarded, it has no purpose remaining in the inbox. The artifact it created is now the source of truth.

9. **Summarize** — Quick summary of what was processed and any follow-up actions.

## Guardrails

- Always discuss with the user before creating artifacts — don't auto-triage
- Keep the inbox clean — every item should end up somewhere or be explicitly discarded
- If an item needs investigation before triaging, say so and move on to the next
- Prefer folding into existing stories over creating new ones — fight backlog inflation
- Always ask "what if we don't do this?" before committing to a story
- `scan` mode is read-only — never create artifacts or delete inbox items there
- Do not let inbox novelty outrank a larger live Ideal/spec/state gap without saying why
