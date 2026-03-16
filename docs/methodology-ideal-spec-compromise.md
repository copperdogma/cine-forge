# The Ideal-First Methodology

## TL;DR

CineForge is built from the top down:

1. **The Ideal** describes the perfect system with zero limitations.
2. **The Spec** records every active compromise against that Ideal.
3. **The Build Map** shows where those compromises live in the system and how close they are to elimination.
4. **ADRs, Stories, and Evals** turn those compromises into concrete decisions, implementation slices, and deletion gates.

The spec should shrink over time. The build map makes that shrinkage visible.

## Core Artifacts

### The Ideal

[docs/ideal.md](ideal.md) is the north star. It describes what CineForge should feel like if AI were perfect, cost were negligible, and implementation constraints disappeared.

The Ideal answers:
- What experience are we actually trying to create?
- Which proposals move us toward that experience?
- Which proposals only optimize today without serving the long-term product?

### The Spec

[docs/spec.md](spec.md) is the set of active compromises against the Ideal.

Each compromise should name:
- the Ideal behavior
- the limitation forcing the compromise
- the limitation type
- the detection mechanism for when the limitation changes
- what gets deleted or simplified when it resolves

### The Build Map

[docs/build-map.md](build-map.md) is the operational companion to the spec.

It combines:
- **system structure** — what major systems exist, how they depend on each other, and what stories cover them
- **compromise convergence** — how each live compromise is being optimized today and what would eliminate it tomorrow

The build map exists because the spec alone cannot answer "where is this compromise implemented?" or "which workaround is closest to deletion?"

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

## Convergence Tracking

Each build-map compromise subsection carries two trajectories:

### Optimize

Make the workaround as good as possible while it still exists.

Examples:
- better model defaults
- cleaner QA loops
- faster scene analysis
- clearer UI around capability boundaries

### Eliminate

Track the condition that would let us delete the workaround entirely.

Examples:
- a compromise eval in [docs/evals/registry.yaml](evals/registry.yaml)
- a registry scan via `scripts/check-compromises.py`
- a pricing or provider-capability threshold from the spec

The build map is where Optimize and Eliminate live side by side.

## Meta-Skills

Two repo-level skills operate across this methodology graph:

### `/triage`

Proactive. Answers: "What is the highest-value next action?"

It reads the shared frame:
- Ideal
- spec
- build map
- relevant ADRs
- leaf triage outputs

It then chooses one next action instead of leaving the operator to reconcile multiple partial signals.

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
Ideal
  ↓
Spec (active compromises)
  ↔ Build Map (systems + convergence)
  ↔ ADRs (decisions that shape the compromises)
  ↓
Stories (implementation slices)
  ↓
Evals (quality measures + deletion gates)
```

This is a graph, not a strict hierarchy. Stories can reveal Ideal gaps. ADRs can reshape the spec. Evals can delete compromises. The build map is the bridge between abstract compromises and concrete system ownership.

## CineForge-Specific Rules

- Do not add infrastructure just because Storybook or another repo has it. CineForge should only adopt patterns that fit its own structure.
- Do not treat every red compromise eval as blocking. Capability-detector evals are often healthy while still red; use runtime-blocking vs non-runtime-blocking semantics.
- Do not flatten leaf triage skills into a monolithic `/triage`. CineForge already has useful specialized logic, especially in `/triage-evals`.
- Do not let the build map become a stale diagram. If the system structure or compromise state changes materially, update it as part of the same story.

## What This Document Is Not

- Not a replacement for [docs/ideal.md](ideal.md)
- Not a duplicate of [docs/spec.md](spec.md)
- Not a roadmap
- Not a changelog

It is the connective tissue that explains how those artifacts work together.
