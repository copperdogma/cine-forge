# The Ideal-First Methodology

## TL;DR

CineForge is built from the top down:

1. **The Ideal** defines both the perfect product and the perfect execution experience.
2. **The Spec** records the active constraints against those ideals in stable `spec:N` categories.
3. **Methodology state** stores mutable planning truth such as substrate, phase, roadmap focus, and architecture-audit cadence.
4. **Compiled graph + generated dashboards** join authored canon into human-readable views such as `docs/build-map.md` and `docs/stories.md`.
5. **ADRs, Stories, Evals, Skills, and Runbooks** turn those constraints into concrete decisions, implementation slices, and deletion gates.

The spec should shrink over time. The generated dashboards make that shrinkage
visible without turning mutable planning state into hand-edited prose. If AI
capability changes enough to make parts of the methodology stack unnecessary,
the methodology itself should simplify too.

## Core Artifacts

### The Ideal

[docs/ideal.md](ideal.md) is the north star. It now carries two ideals:

- **Product ideal** — what CineForge should feel like for the user if AI were
  perfect, cost were negligible, and implementation constraints disappeared
- **Execution ideal** — what building and changing CineForge should feel like if
  AI no longer needed scaffolding, backlog ceremony, or architecture babysitting

The Ideal answers:
- What experience are we actually trying to create for the user?
- What process overhead still exists only because today's AI/tools are imperfect?
- Which proposals move us toward those ideals?
- Which proposals only optimize today's workaround without serving the long-term product?

### The Spec

[docs/spec.md](spec.md) is the set of active constraints against the ideals.
It is organized as `spec:1` through `spec:11`, and those IDs are the stable
cross-reference surface for stories, ADRs, methodology state, generated
dashboards, and agent guidance.

Each active compromise or execution constraint should name:
- the Ideal behavior
- the limitation forcing the compromise
- the limitation type
- the detection mechanism for when the limitation changes
- what gets deleted or simplified when it resolves

### Methodology State

[docs/methodology/state.yaml](methodology/state.yaml) is the canonical
operational companion to the spec.

It mirrors the spec categories 1:1 and answers:
- What product need does this category serve?
- What tech substrate must exist for it to work?
- Is that substrate `exists`, `partial`, `missing`, or `unplanned`?
- What phase is the live constraint in?
- What roadmap focus, campaign state, or architecture-audit pressure exists?

State exists because the spec alone cannot answer "where does this constraint
live right now?" or "is the right next move a quality climb, a hold pass, or a
convergence deletion?"

### Generated Dashboards

[docs/build-map.md](build-map.md) and [docs/stories.md](stories.md) are
generated views built from canonical sources plus methodology state.

They answer:
- Which stories and ADRs currently own the work?
- How does category state look in one readable dashboard?
- Which overlays, focus areas, and backlog summaries matter right now?

Generated dashboards exist because the raw state and graph are precise but not
pleasant to scan manually. They are views, not writable sources of truth.

## Limitation Types

Not all compromises behave the same way. CineForge uses limitation type to decide whether a compromise should disappear or merely evolve.

| Type | Typical Trigger | Lifecycle |
|---|---|---|
| **AI capability** | Better models, larger context, stronger multimodal reasoning | Usually deletion when the eval passes |
| **Ecosystem / infrastructure** | Pricing shifts, standards, API consolidation | Usually transformation rather than instant deletion |
| **Legal / regulatory** | Policy or compliance changes | Transformation |
| **Physics / cost** | Compute/network limits | Asymptotic optimization |
| **Human factors** | Cognitive load, trust, collaboration needs | Usually permanent in some form |

The important distinction: **AI-capability compromises should usually have deletion gates.** World constraints often become simpler, but do not vanish outright.

## Substrate And Phase Governance

Every methodology category declares both a substrate state and, when relevant, a
phase.

### Substrate

- `exists` — the category has a coherent working foundation
- `partial` — some substrate exists, but important pieces are still missing or fragmented
- `missing` — the need is known but no real substrate exists yet
- `unplanned` — the need is acknowledged without a coherent build path yet

Substrate answers "how built is this category?"

### Phase

- `climb` — improve capability or close missing substrate
- `hold` — keep an existing workaround coherent, cheaper, faster, or simpler
- `converge` — deletion work is now justified because the detection gate is effectively green
- `unplanned` — there is no credible execution path yet

Phase answers "what kind of work is correct right now?"

Examples:
- `climb` — scene-understanding quality, missing visualization substrate, missing execution tooling
- `hold` — cost reduction, UX simplification, keeping model defaults current
- `converge` — delete a QA stage or routing layer once the detection eval truly passes

`docs/methodology/state.yaml` is where substrate and phase live side by side.
The generated build map should make the correct next move legible without
needing to reconstruct the whole repo from memory.

## Meta-Skills

Two repo-level skills operate across this methodology graph:

### `/triage`

Proactive. Answers: "What is the highest-value next action?"

It starts from the planning spine, in order:
- Ideal
- spec
- methodology state / generated dashboards
- relevant ADRs

Only after naming the primary live gap does it consult leaf triage outputs
(stories, inbox, evals) to find the best continuation of that gap.

Stories, inbox items, and evals are not the source of priority. They are the
execution surfaces that may or may not already advance the chosen gap.

The state/dashboard layer matters here because a strong next step in a `climb` category is
different from a strong next step in `hold` or `converge`.

### `/align`

Reactive. Answers: "What just rippled?"

Use it after:
- deciding an ADR
- changing the spec
- creating or removing a compromise
- landing a story that materially changes system structure
- seeing a new eval/capability result that may simplify the design

It surfaces which artifacts now need attention across the methodology graph.

## Artifact Relationship

```text
Ideal (product + execution)
  ↓
Spec (active product constraints + execution constraints)
  ↔ Methodology State (categories + substrate + phase + roadmap + audit cadence)
  ↔ Generated Dashboards (`docs/build-map.md`, `docs/stories.md`)
  ↔ ADRs (decisions that shape the constraints)
  ↓
Stories (implementation slices)
  ↔ Skills / Runbooks (execution scaffolding)
  ↓
Evals (quality measures + deletion gates)
```

This is a graph, not a strict hierarchy. Stories can reveal Ideal gaps. ADRs can
reshape the spec. Evals can delete compromises. Methodology state plus compiled
views bridge abstract constraints and concrete system ownership.

## CineForge-Specific Rules

- Do not add infrastructure just because Storybook or another repo has it. CineForge should only adopt patterns that fit its own structure.
- Keep the category-aligned `spec:1` through `spec:11` structure coherent. Do
  not create parallel planning surfaces for the same responsibility.
- Treat execution constraints as first-class. Story lifecycle, build-map upkeep,
  verification discipline, and agent tooling live in `spec:11`, not in an
  undocumented side channel.
- Keep authored truth separate from generated views. Update
  `docs/methodology/state.yaml` or story/ADR metadata, then rerun
  `pnpm methodology:compile`; do not hand-edit generated dashboards.
- Keep Timeline / Playable Assembly explicit. It is a real product lane, not a
  footnote under another category.
- Do not treat every red compromise eval as blocking. Capability-detector evals are often healthy while still red; use runtime-blocking vs non-runtime-blocking semantics.
- Do not flatten leaf triage skills into a monolithic `/triage`. CineForge already has useful specialized logic, especially in `/triage-evals`.
- Do not let the generated build map become a stale diagram. If the system
  structure, substrate, or phase changes materially, update canonical inputs
  and regenerate it as part of the same story.
- Treat the methodology itself as a compromise when appropriate. If better AI or
  better tooling removes the need for a planning ritual, delete the ritual.

## What This Document Is Not

- Not a replacement for [docs/ideal.md](ideal.md)
- Not a duplicate of [docs/spec.md](spec.md)
- Not a roadmap
- Not a changelog

It is the connective tissue that explains how those artifacts work together.
