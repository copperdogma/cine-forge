---
name: retrofit-ideal
description: Apply Ideal-first methodology to an existing project — extract the Ideal from what's already built
user-invocable: true
---

# /retrofit-ideal

Apply the Ideal-first methodology to a project that's already underway. Instead
of starting from scratch, extract the Ideal from existing specs, stories,
architecture, and code — then annotate what's already built as Ideal vs.
Compromise.

## When to Use

- Project has an existing spec but no `docs/ideal.md`
- Project has stories and code but compromises aren't tagged as temporary
- You want the benefits of the Ideal-first framework without starting over

## What This Skill Produces

1. **`docs/ideal.md`** — Extracted from existing docs + conversation with user.
2. **Annotated `docs/spec.md`** — Existing spec sections tagged as Ideal
   requirement or Compromise, with limitation types and detection mechanisms.
3. **Gap analysis** — What's missing: detection evals, golden references,
   untraceable stories.
4. **Updated `docs/setup-checklist.md`** — Retrofit-specific checklist.

## Steps

### Phase 1: Read Everything

Read the project thoroughly before talking to the user:

1. Read existing spec (`docs/spec.md` or equivalent)
2. Read all ADRs (`docs/decisions/`)
3. Read AGENTS.md for stated principles
4. Read story index and skim all stories — note which are Done, In Progress, Pending, Draft
5. Read the codebase structure — what pipeline stages, services, or components exist?
6. Read existing tests and fixtures — are there golden references already?
7. Read any existing evals

Build a mental model of: what does this system DO, what does it WANT to be,
and where is there complexity that might be a compromise?

### Phase 2: Draft the Ideal

Using everything you've read, draft `docs/ideal.md` following the template
in `docs/prompts/ideal-app.md`.

Key heuristic: for every pipeline stage, config option, or architectural
component, ask: "Would this exist if there were no limitations?" Adapt by
context: "if AI were perfect" for transformation components, "if infrastructure
were unlimited" for integration components, "if users could express intent
perfectly" for interaction components. If no, the Ideal describes what would
exist instead.

Present the draft to the user. This is where the Socratic conversation happens —
but it's informed by existing architecture, so you can ask much sharper questions:

- "The spec has a 6-stage pipeline. In the Ideal, this is one call. Is that right?"
- "There's a coreference resolution stage that's marked removable. The Ideal
  doesn't mention coreference at all — it just works. Correct?"
- "The config has three depth presets. Are those genuine user intents or
  cost workarounds?"

Surface implicit ideals (security, trust, performance, accessibility) as
described in `/setup-ideal`.

### Phase 3: Annotate the Spec

Go through the existing spec section by section. For each:

1. **Is this an Ideal requirement?** Move it to ideal.md (or confirm it's there).
2. **Is this a compromise?** Tag it:
   - Limitation type (AI capability, Ecosystem, Legal, Physics, Human)
   - Detection mechanism (eval, ecosystem monitor, permanent)
   - Compromise-level preferences attached to it
   - What gets deleted/transformed when the limitation resolves
3. **Is this a raw idea without clear status?** Move to `## Untriaged Ideas`.

Reorganize the spec into the structure from `/setup-spec`:
- Untriaged Ideas (top)
- AI Compromises (with deletion evals)
- World Compromises (with evolution paths)
- Decomposition Trees
- Architecture Summary

### Phase 4: Gap Analysis

Identify what's missing:

**Missing detection evals:**
- List every AI compromise that doesn't have a corresponding eval in `evals/`
- For each: what eval would prove this compromise can be deleted?
- Priority: compromises with the most downstream complexity first

**Missing golden references:**
- List every Ideal requirement that doesn't have a golden reference in
  `tests/fixtures/golden/`
- For each: what's the smallest evaluable input/output pair?

**Untraceable stories:**
- List stories that don't trace back to either an Ideal requirement or a
  spec compromise
- These are either scope creep or missing documentation — flag for triage

**Missing "simplification evals":**
- For the most significant AI compromises: is there a baseline eval that
  tests "can a single model call do this?" — the dumbest-possible-approach test
- If not, these should be created first (they're the highest-leverage evals)

Write the gap analysis to `docs/retrofit-gaps.md`.

### Phase 5: Create Retrofit Checklist

Create `docs/setup-checklist.md` (or update it if it exists) with
retrofit-specific items:

```markdown
# {Project Name} — Retrofit Checklist

Retrofitting Ideal-first methodology onto existing project.

## Completed
- [x] Existing docs, stories, and code reviewed
- [x] `docs/ideal.md` created
- [x] Existing spec annotated with limitation types and detection mechanisms
- [x] Gap analysis written to `docs/retrofit-gaps.md`

## Remaining (prioritized)
- [ ] Create simplification evals for top 3 AI compromises
- [ ] Create golden references for requirements without them
- [ ] Add `ideal_refs` to all Pending/Draft stories
- [ ] Run baseline: "can a single model call do this?" for each AI compromise
- [ ] Record baseline results in `evals/baseline-results.md`
- [ ] Update stories.md with Ideal-alignment notes
```

### Phase 6: Update AGENTS.md

Add a prominent reference to `docs/ideal.md` at the top of AGENTS.md:

> **The Ideal (`docs/ideal.md`) is the most important document in this project.**
> It defines what the system should be with zero limitations. Every architectural
> decision should move toward the Ideal. Every compromise in the spec should
> carry a detection mechanism for when it's no longer needed.

## What This Skill Does NOT Do

- Does NOT rewrite existing stories. Flag misaligned stories for triage.
- Does NOT create evals or golden references. Flag gaps. Those are separate
  skills (`/setup-golden`, `/setup-evals`).
- Does NOT restructure code. The architecture stays as-is until eval results
  prove something can be simplified.
- Does NOT discard existing work. Everything gets categorized, nothing gets lost.

## Guardrails

- Read the entire project before drafting anything. The Ideal must be grounded
  in what the project actually does, not what you imagine it should do.
- Don't rewrite the spec — annotate it. The existing spec has valuable context
  and decisions. Add structure, don't replace.
- Raw ideas stay in Untriaged until explicitly incorporated or discarded.
- The gap analysis is a prioritized list, not a mandate. The user decides
  what to tackle and when.
- Never create stories or rewrite architecture during retrofit. This skill
  is analysis and documentation only.
- Update the setup checklist when done.
