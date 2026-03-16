# Align

## Context

Use this runbook when a change might ripple across CineForge's methodology graph and you need to assess the fallout without editing files directly.

This is the operational companion to `/align`.

## Prerequisites

- The triggering change is known, or you can infer it from recent work
- [docs/ideal.md](../ideal.md), [docs/spec.md](../spec.md), and [docs/build-map.md](../build-map.md) are available
- You know whether any relevant ADRs or eval results changed

## Steps

1. **[script] Identify the trigger**
   - Determine whether the change came from an ADR, a story, an eval result, a spec edit, or an external capability/ecosystem shift.
   - Good output: one sentence stating what changed.

2. **[script] Read the current graph**
   - Open:
    - `docs/ideal.md`
    - `docs/methodology-ideal-spec-compromise.md`
    - `docs/spec.md`
    - `docs/build-map.md`
    - `docs/stories.md`
     - relevant ADRs under `docs/decisions/` and `docs/design/`
     - relevant eval entries in `docs/evals/registry.yaml`
   - Goal: see the current truth before reasoning from memory.

3. **[judgment] Check each layer for impact**
   - Ask:
     - Ideal: did the change reveal a new requirement or preference?
     - Spec: did it create, simplify, or delete a compromise?
     - Build Map: did system scope, dependencies, or compromise progress change?
     - Stories: are any Draft/Pending/In Progress stories now wrong, blocked, or unnecessary?
     - Evals: should any be re-run, added, or removed?
     - ADRs: does the change contradict an accepted decision or require a new one?
   - Good output: short, layer-by-layer findings.

4. **[judgment] Recommend concrete actions**
   - End with ordered actions such as:
     - update build map
     - revise a story
     - add or rerun an eval
     - create or update an ADR
     - no action
   - Good output: specific next actions, not abstract warnings.

## Boundaries

### Always do

- Read the actual documents before calling something aligned or misaligned
- Use the build map when the change affects system ownership or compromise progress
- Keep the report short and actionable

### Ask first

- Before rewriting the Ideal based on a weak signal
- Before deleting a compromise or ADR without supporting evidence
- Before creating new stories or ADRs on the user's behalf

### Never do

- Never edit files from `/align`
- Never guess from memory when the docs are available
- Never treat a new eval result as self-explanatory without checking its runtime impact

## Troubleshooting

- **The change is vague**
  - Fix: start from recent git history or ask the user what changed.

- **Build map is missing or stale**
  - Fix: note that explicitly and route the follow-up into the current implementation story.

- **A change seems to affect everything**
  - Fix: focus on the strongest ripple first: spec, build map, and active stories.

## Lessons Learned

- 2026-03-15 — A rename-only migration is not enough: `align` has to check the full methodology graph, not just ADR text, or it misses build-map and eval ripple effects.
