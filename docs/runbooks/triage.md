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
   - Optionally inspect recent `git log --oneline -20` for momentum context.
   - Goal: identify the highest-leverage live gap before looking at the backlog.

3. **[judgment] Name the primary gap**
   - State the unmet Ideal promise or overscaffolded compromise
   - Map it to the owning spec section(s)
   - Map it to the owning build-map category, substrate, and phase
   - Name 1-2 runner-up gaps
   - Goal: decide what actually matters before looking for convenient work

4. **[script] Read decision constraints for that gap**
   - Open the relevant ADRs / design docs
   - If none apply, say so explicitly
   - Goal: make sure the next move fits the chosen architecture

5. **[script] Query existing work under that gap**
   - Stories: `/triage-stories`
   - Inbox: `/triage-inbox scan`
   - Evals: `/triage-evals`
   - Goal: find which existing artifacts already advance the chosen gap

6. **[judgment] Synthesize one next action**
   - Prefer:
     - continuing the strongest existing story under the chosen gap
     - promoting or reshaping the draft that best advances the chosen gap
     - creating the missing story / ADR / spec update / eval if the gap has no home
   - Only fall back to smaller unrelated ready work when the larger gap is not actionable yet
   - Good output: one recommended action, plus runner-ups, with an explicit reason the chosen gap won.
   - Put the recommendation last, and phrase it so the user can reply `"yes"` to approve the next move without needing to restate it.

## Boundaries

### Always do

- Keep full-sweep `/triage` read-only
- Let leaf skills own their domain logic
- End with one clear recommendation
- End with that recommendation as the final section, in approval-ready wording
- Start from Ideal/spec/build-map gaps, not the backlog

### Ask first

- Before turning a full-sweep triage into implementation work
- Before adding new triage domains beyond the current leaf set

### Never do

- Never duplicate leaf-skill logic in `/triage`
- Never let full-sweep `/triage` modify inbox items or other files
- Never return three equal-priority recommendations without choosing one
- Never let "easy and ready" silently outrank "important and under-owned"

## Troubleshooting

- **Leaf recommendations conflict**
  - Fix: go back to the named primary gap and prefer the recommendation that most directly advances it.

- **A leaf skill is stale or missing**
  - Fix: call out the gap instead of pretending the full sweep is complete.

- **Build map is thin**
  - Fix: still use it, but downgrade confidence in convergence-based ranking.

## Lessons Learned

- 2026-03-15 — `/triage` works best as an orchestrator. CineForge already had useful eval-triage logic; folding that into a monolith would have been a regression.
- 2026-03-20 — Orchestration still has to be methodology-first. If triage starts from stories or eval queues, the backlog begins prioritizing itself instead of serving the Ideal/spec/build-map spine.
