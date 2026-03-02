---
name: triage-stories
description: Evaluate the story backlog and recommend what to work on next
user-invocable: true
---

# /triage-stories [story-number]

Evaluate the story backlog and recommend the best next stories to work on.

## Arguments

- `[story-number]` — (optional) If provided, evaluate that specific story's readiness instead of doing a full backlog scan. Assess its dependencies, blockers, and whether it's ready to build.

## Steps

1. **Read project state** — Load `docs/stories.md` (the full story index). Identify all stories by status:
   - **Draft** — scoped but needs detailed ACs and tasks before building; `/build-story` handles the flesh-out phase
   - **Pending** — fully detailed, ready to build
   - **In Progress** — currently being worked on
   - **Done** — complete, validated
   - **Blocked** — waiting on dependency or decision

   **Both Draft and Pending** stories with met dependencies are candidates for recommendation. Do not treat Draft as a disqualifier — priority and Ideal alignment matter more than completeness of the story file. `/build-story` will flesh out ACs and tasks before touching code regardless of starting status.

2. **Read the Ideal** — Load `docs/ideal.md` to ground scoring in what the system should become. Stories that close Ideal gaps rank higher than stories that only optimize compromises.

3. **Read candidate stories** — For every candidate story (Draft or Pending) with met dependencies, read the actual story file to understand its goal, notes, dependencies, and scope. Don't just go by titles.

4. **Score and rank** — Evaluate each candidate story on these dimensions:
   - **Dependency readiness**: Are all upstream stories Done? Does this unblock downstream stories?
   - **Blocking power**: How many other stories depend on this one?
   - **Ideal alignment**: Does this story move toward the Ideal (`docs/ideal.md`) or implement a detection mechanism? Rank higher than stories that only entrench compromises.
   - **Simplification leverage**: Does this story (e.g., an eval harness) unblock future simplification across multiple compromises?
   - **Phase coherence**: Does it continue the current phase or require a context switch?
   - **Momentum**: Does it build on recently completed work (shared context, warm caches, related code)?
   - **Complexity vs. payoff**: Is the effort proportional to the value delivered?
   - **User impact**: Does it visibly improve the product or is it internal plumbing?

5. **Present recommendations** — Show the user a ranked top 3–5 with:
   - Story ID and title
   - Draft or Pending label
   - 2–3 sentence rationale covering the strongest scoring dimensions
   - Any caveats (e.g., "this is large — consider splitting first")

6. **Flag concerns** — Surface any issues noticed during the scan:
   - Stories marked Pending that are actually blocked (missing dependency not recorded)
   - Draft stories that should be promoted to Pending
   - Stories that appear stale or superseded
   - Dependency chains that are bottlenecked

7. **User decides** — Wait for the user to pick a story or ask for more detail on any candidate. Do NOT start building — that's `/build-story`.

## Guardrails

- This is a read-only, advisory skill — do not modify any files
- Always read the actual story files, not just the index titles
- If the backlog is empty or everything is blocked, say so clearly
- Do not recommend stories that depend on unfinished work unless the dependency is trivially close to done
- If the user passes a story ID as an argument (see Arguments above), evaluate that specific story's readiness instead of doing a full scan
