# Triage

## Context

Use this runbook when you need a full methodology sweep to decide the highest-value next action across backlog, inbox, and eval/convergence work.

This is the operational companion to `/triage`.

## Prerequisites

- The leaf triage skills exist and are healthy:
  - `/triage-stories`
  - `/triage-inbox`
  - `/triage-evals`
- [docs/build-map.md](../build-map.md) exists or its absence is understood
- You know whether the invocation is full-sweep or scoped (`stories`, `inbox`, `evals`)

## Steps

1. **[script] Decide routing mode**
   - If the user passed `stories`, `inbox`, or `evals`, route directly to the leaf skill and stop.
   - If no scope was passed, continue with full-sweep mode.

2. **[script] Read the shared frame**
   - Open:
     - `docs/ideal.md`
     - `docs/methodology-ideal-spec-compromise.md`
     - `docs/spec.md`
     - `docs/build-map.md`
     - relevant ADRs with open status
   - Optionally inspect recent `git log --oneline -20` for momentum context.

3. **[script] Run the leaf sweeps**
   - Stories: `/triage-stories`
   - Inbox: `/triage-inbox scan`
   - Evals: `/triage-evals`
   - Goal: gather one recommendation per domain without duplicating leaf logic.

4. **[judgment] Synthesize one next action**
   - Choose the strongest next step using:
     - Ideal alignment
     - blocking power
     - substrate leverage
     - phase-appropriate leverage (`climb`, `hold`, `converge`)
     - urgency/staleness
     - recent momentum
     - operator cost
   - Good output: one recommended action, plus runner-ups.

## Boundaries

### Always do

- Keep full-sweep `/triage` read-only
- Let leaf skills own their domain logic
- End with one clear recommendation

### Ask first

- Before turning a full-sweep triage into implementation work
- Before adding new triage domains beyond the current leaf set

### Never do

- Never duplicate leaf-skill logic in `/triage`
- Never let full-sweep `/triage` modify inbox items or other files
- Never return three equal-priority recommendations without choosing one

## Troubleshooting

- **Leaf recommendations conflict**
  - Fix: prefer the one with the strongest blocking, substrate, or credible convergence leverage and explain why the others lost.

- **A leaf skill is stale or missing**
  - Fix: call out the gap instead of pretending the full sweep is complete.

- **Build map is thin**
  - Fix: still use it, but downgrade confidence in convergence-based ranking.

## Lessons Learned

- 2026-03-15 — `/triage` works best as an orchestrator. CineForge already had useful eval-triage logic; folding that into a monolith would have been a regression.
