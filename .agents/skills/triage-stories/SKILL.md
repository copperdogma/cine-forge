---
name: triage-stories
description: Find which stories best advance the highest-leverage Ideal/spec/state gap
user-invocable: true
---

# /triage-stories [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Evaluate the story backlog as a **continuation surface** for methodology gaps. The backlog does not define priority by itself.

## Eval Ladder Gate

For AI-capability work, identify the eval ladder before creating or prioritizing
implementation backlog:

- the root Ideal eval or full-path golden, or the explicit reason it is deferred
- the parent eval or latest higher-level result that shows the current failure
- the measured failure mode that makes decomposition necessary
- the child eval, failure-classification attempt, ADR/spec update, or story that
  advances the next unresolved ladder node

Prefer rerunning a root/parent eval when new models, provider changes, code
changes, scorer fixes, or changed constraints could collapse the current
decomposition. Prefer a child eval or failure-classification attempt when the
parent failure is still too vague to choose AI-only, multi-call AI, deterministic
code, or hybrid implementation honestly.

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

2. **Read project state** — Load `docs/stories.md` (the full generated story index). Identify all stories by status:
   - **Draft** — worth preserving, but still incomplete, underspecified, or not yet substrate-verified enough to claim build-readiness
   - **Pending** — fully detailed and honestly buildable now
   - **In Progress** — currently being worked on
   - **Blocked** — concrete enough to preserve, but currently blocked by a named blocker with explicit evidence and an unblock condition
   - **Done** — complete, validated

   Story existence is packaging context, not major priority by itself. A `Draft` or `Pending` shell does not outrank an active line merely because it exists.
   A `Blocked` line can preserve continuity, but it is not actionable while its
   unblock condition is unmet.

   If the backlog shells are quiet but the methodology state still has active
   `converge`, `climb`, or meaningful `hold` pressure, do not stop at "no open
   stories." Identify the strongest problem line and consider whether the
   honest recommendation is to create a new story shell for it.

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
   - Read the actual story files for every In Progress, Pending, Draft, or Blocked story that plausibly advances one of the named gaps
   - Don't just go by titles
   - If a top gap has no matching story, say so explicitly instead of quietly ranking smaller unrelated work
   - Ask whether the honest recommendation is to continue, reopen, expand, or consolidate an existing story line before recommending a different shell
   - For `Blocked` stories, read `Blocker Summary`, `Blocker Evidence`, and
     `Unblock Condition` plus the newest work-log guidance. If stale plan text
     still says "proceed" but newer blocker evidence says otherwise, call that
     out as artifact drift before you rank anything

5. **Score and rank** — Evaluate each candidate story on these dimensions, in this order:
   - **Movement toward the Ideal**: Does this story directly advance the top methodology gap, or is it a side quest?
   - **Real problem pressure**: Is this closing a live trust break, missing substrate, or overscaffolded compromise right now?
   - **Leverage and unblock power**: Does it unlock downstream work, reduce fragmentation, or remove scaffolding?
   - **Phase coherence**:
     - `converge`: default pressure to delete, simplify, or collapse residue
     - `climb`: default pressure to improve quality, widen proof, or land the
       next advancement toward `hold`
     - `hold`: lower but still real pressure for efficiency, simplification,
       thinner ownership, or operational hardening when stronger lines are not
       actionable
     - Work that fights the phase is lower priority
     - Lack of a fresh bug report does not zero out a phase-aligned candidate
   - **Readiness**: Can this line honestly continue, reopen, expand, or unblock now?
   - **Cost**: Is the effort proportional to the value delivered?
   - **Continuity / momentum**: Does it build on active or recently advanced work with the same unresolved success surface?

   Story-shell existence is packaging and tie-break context only. It does not create primary priority by itself.
   `Blocked` + unmet unblock condition means `Readiness = not actionable` no
   matter how strong continuity or recent commit history looks.

6. **Present recommendations** — Show the user a ranked top 3–5 with:
   - Story ID and title
   - Recommended action: continue / reopen / expand / consolidate / promote
   - Current status label
   - Which named gap it advances
   - If Draft: a short note on whether it should stay `Draft` or be promoted once built
   - 2–3 sentence rationale covering the strongest scoring dimensions
   - Any caveats (e.g., "this is large — consider splitting first")
   - Exclude blocked stories with unmet unblock conditions from this ranked
     list; report them separately under concerns / health flags

7. **Flag concerns** — Surface any issues noticed during the scan:
   - Stories marked Pending that are actually blocked (missing dependency not recorded)
   - Draft stories that are already honest `Pending` candidates or should stay `Draft`
   - Blocked stories missing blocker truth in the story artifact
   - Blocked stories whose work log or plan text still says "proceed" even
     though newer blocker evidence says "do not reopen yet"
   - Stories that appear stale or superseded
   - Dependency chains that are bottlenecked
   - Major methodology-category gaps that have no story coverage or only weak story coverage
   - Ready stories that are real but lower leverage than the top methodology gap
   - Story lines that should be consolidated instead of extended as separate shells

8. **User decides** — Wait for the user to pick a story or ask for more detail on any candidate. Do NOT start building — that's `/build-story`.

## Guardrails

- This is a read-only, advisory skill — do not modify any files
- Always read the actual story files, not just the index titles
- If the backlog is empty or everything is blocked, say so clearly
- Do not recommend stories that depend on unfinished work unless the dependency is trivially close to done
- If the user passes a story ID as an argument (see Arguments above), evaluate that specific story's readiness instead of doing a full scan
- Never start from "what is easiest to build?" Start from "what gap does this story close?"
- If no existing story advances the top gap, say that explicitly and recommend creating or promoting the right story
- Prefer preserving continuity on an active or recently advanced work line over jumping tracks to an unrelated shell when leverage is comparable
- Never recommend a `Blocked` story with an unmet unblock condition just
  because it is the only active-looking line; keep it visible as a health flag
  instead
- Do not say the backlog is effectively empty when the methodology state still
  shows a bounded actionable `converge`/`climb` pressure line that simply lacks
  a story shell; recommend creating the story instead.
- `No actionable story` is only honest when every plausible phase-aligned move
  is blocked, exhausted, or not yet specific enough to package as a bounded
  story.
