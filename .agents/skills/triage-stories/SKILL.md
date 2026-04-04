---
name: triage-stories
description: Find which stories best advance the highest-leverage Ideal/spec/state gap
user-invocable: true
---

# /triage-stories [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Evaluate the story backlog as a **continuation surface** for methodology gaps. The backlog does not define priority by itself.

## Arguments

- `[story-number]` — (optional) If provided, evaluate that specific story's readiness instead of doing a full backlog scan. Assess its dependencies, blockers, and whether it's ready to build.

## Steps

1. **Read the shared frame first** — Load:
   - `docs/ideal.md`
   - `docs/spec.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/methodology/state.yaml`
   - `docs/build-map.md`
   - Goal: identify the highest-leverage live gap before reading candidate stories.

2. **Read project state** — Load `docs/stories.md` (the full story index). Identify all stories by status:
   - **Draft** — scoped but needs detailed ACs and tasks before building; it must be promoted to `Pending` before `/build-story` can execute it
   - **Pending** — fully detailed, ready to build
   - **In Progress** — currently being worked on
   - **Done** — complete, validated
   - **Blocked** — waiting on dependency or decision

   **Both Draft and Pending** stories with met dependencies are candidates for recommendation. Do not treat Draft as a disqualifier for prioritization, but be explicit that a Draft story still needs scoping and promotion to `Pending` before `/build-story`.

3. **Name the top 1-3 live gaps**
   - For each gap, state:
     - the unmet Ideal promise or overscaffolded compromise
     - the owning spec section(s)
     - the methodology category, substrate, and phase
   - Prefer:
     - missing or partial substrate in `climb`
     - credible `converge` opportunities
     - trust-critical breaks
   - De-prioritize:
     - isolated polish in `hold` when a bigger `climb` gap is still open

4. **Read candidate stories as possible continuations of those gaps**
   - Read the actual story files for every Draft or Pending story that plausibly advances one of the named gaps
   - Don't just go by titles
   - If a top gap has no matching story, say so explicitly instead of quietly ranking smaller unrelated work

5. **Score and rank** — Evaluate each candidate story on these dimensions, in this order:
   - **Gap fit**: Does this story directly advance the top methodology gap, or is it a side quest?
   - **Spec / state leverage**: Does it close missing substrate in `climb`, execute a real `converge` step, or is it merely `hold` polish?
   - **Dependency readiness**: Are all upstream stories Done? Does this unblock downstream stories?
   - **Blocking power**: How many other stories depend on this one?
   - **Simplification leverage**: Does this story remove scaffolding or unblock future deletion of a compromise?
   - **Phase coherence**: Does it continue the category's current phase cleanly?
   - **Momentum**: Does it build on recently completed work?
   - **Complexity vs. payoff**: Is the effort proportional to the value delivered?
   - **User impact**: Does it materially improve the product or execution experience?

   A `Pending` story does **not** automatically outrank a `Draft` story if the draft is the clearer continuation of the highest-priority gap. In that case, recommend promoting or reshaping the draft.

6. **Present recommendations** — Show the user a ranked top 3–5 with:
   - Story ID and title
   - Draft or Pending label
   - Which named gap it advances
   - If Draft: a short note on what must be scoped before it can be built
   - 2–3 sentence rationale covering the strongest scoring dimensions
   - Any caveats (e.g., "this is large — consider splitting first")

7. **Flag concerns** — Surface any issues noticed during the scan:
   - Stories marked Pending that are actually blocked (missing dependency not recorded)
   - Draft stories that should be promoted to Pending before build
   - Stories that appear stale or superseded
   - Dependency chains that are bottlenecked
   - Major methodology-category gaps that have no story coverage or only weak story coverage
   - Ready stories that are real but lower leverage than the top methodology gap

8. **User decides** — Wait for the user to pick a story or ask for more detail on any candidate. Do NOT start building — that's `/build-story`.

## Guardrails

- This is a read-only, advisory skill — do not modify any files
- Always read the actual story files, not just the index titles
- If the backlog is empty or everything is blocked, say so clearly
- Do not recommend stories that depend on unfinished work unless the dependency is trivially close to done
- If the user passes a story ID as an argument (see Arguments above), evaluate that specific story's readiness instead of doing a full scan
- Never start from "what is easiest to build?" Start from "what gap does this story close?"
- If no existing story advances the top gap, say that explicitly and recommend creating or promoting the right story
