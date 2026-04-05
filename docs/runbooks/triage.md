# Triage

## Context

Use this runbook when you need a full methodology sweep to decide the highest-value next action across backlog, inbox, and eval/convergence work.

This is the operational companion to `/triage`.

## Prerequisites

- The leaf triage skills exist and are healthy:
  - `/triage-stories`
  - `/triage-inbox`
  - `/triage-evals`
- `/triage-architecture`
- [docs/methodology/state.yaml](../methodology/state.yaml) exists
- generated dashboards such as [docs/build-map.md](../build-map.md) are current
- You know whether the invocation is full-sweep or scoped (`stories`, `inbox`, `evals`, `architecture`)

## Steps

1. **[script] Decide routing mode**
   - If the user passed `stories`, `inbox`, `evals`, or `architecture`, route
     directly to the leaf skill and stop.
   - If no scope was passed, continue with full-sweep mode.

2. **[script] Read the shared frame**
   - Open:
     - `docs/ideal.md`
     - `docs/methodology-ideal-spec-compromise.md`
     - `docs/spec.md`
     - `docs/methodology/state.yaml`
     - `docs/build-map.md`
   - Optionally inspect recent `git log --oneline -20` for momentum context.
   - Goal: identify the highest-leverage live gap before looking at the backlog.

3. **[judgment] Name the primary gap**
   - State the unmet Ideal promise or overscaffolded compromise
   - Map it to the owning spec section(s)
   - Map it to the owning methodology category, substrate, and phase
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
   - Architecture: `/triage-architecture scan`
   - Goal: find which existing artifacts already advance the chosen gap, especially active or recently advanced lines that should be continued, reopened, expanded, or consolidated before inventing a new shell
   - Filter blocked stories with unmet unblock conditions and eval retries whose
     triggers remain exhausted into health flags before ranking candidates

6. **[judgment] Synthesize one next action**
   - Prefer:
     - continuing, reopening, expanding, or consolidating the strongest existing story line under the chosen gap
     - promoting or reshaping the draft that best advances the chosen gap
     - creating the missing story / ADR / spec update / eval if the gap has no home
   - Only fall back to smaller unrelated ready work when the larger gap is not actionable yet
   - Story existence is packaging context and tie-breaker only; it should not outrank a more important live gap by itself
   - A blocked line with an unmet unblock condition is not actionable even if it
     is the most continuous recent work
   - Good output: one recommended action, plus runner-ups, with an explicit reason the chosen gap won.

## Boundaries

### Always do

- Keep full-sweep `/triage` read-only
- Let leaf skills own their domain logic
- End with one clear recommendation
- Start from Ideal/spec/state gaps, not the backlog
- Keep blocked stories with unmet unblock conditions and exhausted eval retry
  triggers in health flags / deferrals instead of promoting them as the next move

### Ask first

- Before turning a full-sweep triage into implementation work
- Before adding new triage domains beyond the current leaf set

### Never do

- Never duplicate leaf-skill logic in `/triage`
- Never let full-sweep `/triage` modify inbox items or other files
- Never return three equal-priority recommendations without choosing one
- Never let "easy and ready" silently outrank "important and under-owned"
- Never let continuity or recent commits override a recorded blocker or an
  exhausted retry trigger

## Troubleshooting

- **Leaf recommendations conflict**
  - Fix: go back to the named primary gap and prefer the recommendation that most directly advances it.

- **A leaf skill is stale or missing**
  - Fix: call out the gap instead of pretending the full sweep is complete.

- **Generated dashboard is thin or stale**
  - Fix: read `docs/methodology/state.yaml` directly, call out the freshness
    problem, and downgrade confidence in convergence-based ranking.

- **The only active-looking line is blocked**
  - Fix: surface it as a health flag, restate the unmet unblock condition, and
    choose a different actionable next move unless the user explicitly wants the
    unblock path.

## Lessons Learned

- 2026-03-15 — `/triage` works best as an orchestrator. CineForge already had useful eval-triage logic; folding that into a monolith would have been a regression.
- 2026-03-20 — Orchestration still has to be methodology-first. If triage
  starts from stories or eval queues, the backlog begins prioritizing itself
  instead of serving the Ideal/spec/state spine.
- 2026-04-04 — Continuity is a positive bias only for actionable lines. A
  blocked story or exhausted eval retry should stay visible as a health flag,
  not become the default recommendation by process of elimination.
