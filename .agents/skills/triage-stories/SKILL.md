---
name: triage-stories
description: Evaluate the story backlog and recommend what to work on next
user-invocable: true
---

# /triage-stories [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Evaluate the story backlog and recommend the best next stories to work on.

## Arguments

- `[story-number]` — (optional) If provided, evaluate that specific story's readiness instead of doing a full backlog scan. Assess its dependencies, blockers, and whether it's ready to build.

## Steps

1. **Read project state** — Load `docs/stories.md` (the full story index). Identify all stories by status:
   - **Draft** — scoped but needs detailed ACs and tasks before building; it must be promoted to `Pending` before `/build-story` can execute it
   - **Pending** — fully detailed, ready to build
   - **In Progress** — currently being worked on
   - **Done** — complete, validated
   - **Blocked** — waiting on dependency or decision

   **Both Draft and Pending** stories with met dependencies are candidates for recommendation. Do not treat Draft as a disqualifier for prioritization, but be explicit that a Draft story still needs scoping and promotion to `Pending` before `/build-story`.

2. **Read the shared frame** — Load:
   - `docs/ideal.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/build-map.md`
   Stories that close Ideal gaps or materially advance build-map convergence rank higher than stories that only optimize compromises.

3. **Read candidate stories** — For every candidate story (Draft or Pending) with met dependencies, read the actual story file to understand its goal, notes, dependencies, and scope. Don't just go by titles.

4. **Score and rank** — Evaluate each candidate story on these dimensions:
   - **Dependency readiness**: Are all upstream stories Done? Does this unblock downstream stories?
   - **Blocking power**: How many other stories depend on this one?
   - **Ideal alignment**: Does this story move toward the Ideal (`docs/ideal.md`) or implement a detection mechanism? Rank higher than stories that only entrench compromises.
   - **Convergence value**: Does this story advance a build-map Optimize path or move a compromise closer to elimination?
   - **Simplification leverage**: Does this story (e.g., an eval harness) unblock future simplification across multiple compromises?
   - **Phase coherence**: Does it continue the current phase or require a context switch?
   - **Momentum**: Does it build on recently completed work (shared context, warm caches, related code)?
   - **Complexity vs. payoff**: Is the effort proportional to the value delivered?
   - **User impact**: Does it visibly improve the product or is it internal plumbing?

5. **Present recommendations** — Show the user a ranked top 3–5 with:
   - Story ID and title
   - Draft or Pending label
   - If Draft: a short note on what must be scoped before it can be built
   - 2–3 sentence rationale covering the strongest scoring dimensions
   - Any caveats (e.g., "this is large — consider splitting first")

6. **Flag concerns** — Surface any issues noticed during the scan:
   - Stories marked Pending that are actually blocked (missing dependency not recorded)
   - Draft stories that should be promoted to Pending before build
   - Stories that appear stale or superseded
   - Dependency chains that are bottlenecked

7. **User decides** — Wait for the user to pick a story or ask for more detail on any candidate. Do NOT start building — that's `/build-story`.

## Guardrails

- This is a read-only, advisory skill — do not modify any files
- Always read the actual story files, not just the index titles
- If the backlog is empty or everything is blocked, say so clearly
- Do not recommend stories that depend on unfinished work unless the dependency is trivially close to done
- If the user passes a story ID as an argument (see Arguments above), evaluate that specific story's readiness instead of doing a full scan
