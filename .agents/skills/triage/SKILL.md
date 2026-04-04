---
name: triage
description: Identify the highest-leverage Ideal/spec/state gap, then recommend the next action that best advances it
user-invocable: true
---

# /triage [stories|inbox|evals] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current state phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

`/triage` is the proactive meta-skill. Its job is to choose the **most important live methodology gap** before looking for convenient work.

The required order is:

1. **Ideal** — what major user promise or simplification opportunity is most visibly unmet?
2. **Spec** — which active constraint or requirement expresses that gap?
3. **Methodology state** — which category owns it, and is the correct move `climb`, `hold`, `converge`, or `unplanned`?
4. **ADRs / design docs** — what decisions constrain the next move?
5. **Existing work** — which stories, inbox items, or evals already advance that exact gap?

Stories, inbox items, evals, and architecture audits are **not** the source of
priority. They are candidate continuations of the priority established by
Ideal/spec/state reasoning.

Story existence is packaging context and a tie-breaker, not a primary value
signal. When the same subsystem, validation boundary, and success surface are
still live, prefer continuing, reopening, expanding, or consolidating the
existing story line before creating or prioritizing a new shell.

Companion runbook: `docs/runbooks/triage.md`

## Routing

| Invocation | Behavior |
|---|---|
| `/triage` | Full-sweep orchestrator mode |
| `/triage stories` | Delegate to `/triage-stories` |
| `/triage stories 129` | Delegate to `/triage-stories 129` |
| `/triage inbox` | Delegate to `/triage-inbox` |
| `/triage inbox scan` | Delegate to `/triage-inbox scan` |
| `/triage evals` | Delegate to `/triage-evals` |
| `/triage evals C3` | Delegate to `/triage-evals C3` |
| `/triage architecture` | Delegate to `/triage-architecture scan` |
| `/triage architecture methodology_tooling` | Delegate to `/triage-architecture scan methodology_tooling` |

When a scope is provided, hand off completely to the leaf skill. Do **not** keep a second implementation here.

## Leaf Skills

- `/triage-stories` — backlog prioritization, dependency bottlenecks, story readiness
- `/triage-inbox` — inbox processing, plus read-only `scan` mode for orchestration
- `/triage-evals` — eval health, compromise leverage, rerun candidates
- `/triage-architecture` — architecture-audit cadence, drift signals, simplification routing

## Full-Sweep Mode

When invoked with no scope, run a methodology-first orchestration pass:

1. **Read the shared frame**
   - `docs/ideal.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`
   - `docs/build-map.md`
   - recent `git log --oneline -20`
   - Goal: identify the biggest live gap or simplification opportunity before reading stories as a backlog.

2. **Name the primary gap**
   - State the unmet Ideal promise or overscaffolded compromise in plain language
   - Map it to the owning spec section(s)
   - Map it to the owning methodology category
   - State why this gap wins right now:
     - missing or partial substrate
     - highest-value `climb`
     - credible `converge`
     - urgent trust break
     - simplification leverage
   - Also name 1-2 runner-up gaps

3. **Read decision constraints for that gap**
   - Open the relevant ADRs / design docs for the chosen gap
   - If none apply, say so explicitly
   - Goal: avoid picking a next action that fights a settled architecture decision

4. **Query the existing work under that gap**
   - Stories: `/triage-stories`
   - Inbox: `/triage-inbox scan`
   - Evals: `/triage-evals`
   - Architecture: `/triage-architecture scan`
   - But interpret each leaf through one question:
     - what already exists that advances the chosen gap?
   - Do **not** let a smaller ready story outrank the chosen gap just because it is easier to start

5. **Choose one next action**
   Prefer this order:
   - continue, reopen, expand, or consolidate an in-flight or recently advanced story that directly advances the chosen gap
   - promote or reshape an existing draft story that is the clearest continuation of the chosen gap
   - create the missing story / ADR / spec update / eval if the gap has no proper home yet
   - only fall back to a smaller unrelated ready story if the larger gap is genuinely not actionable yet, and explain why

6. **Return a short report**

```markdown
## Triage

### Primary Gap
- {Ideal promise or simplification opportunity}
- Spec: {spec refs}
- State: {category + substrate + phase}

### Recommended Action
- {one next action}

### Why
- {2-3 strongest reasons}

### Runner-Ups
- {alternate action}
- {alternate action}

### Domain Notes
- Stories: {which stories do or do not advance the chosen gap}
- Inbox: {which inbox items do or do not map to the chosen gap}
- Evals: {which evals matter for the chosen gap, or why eval work is not the move}
- Architecture: {which audit domains matter, or why architecture work is not the move}

### Health Flags
- {blocker or "none"}
```

## Guardrails

- Scoped invocations delegate — no duplicate logic here
- Full-sweep mode is read-only
- Do not let `/triage` absorb leaf-skill implementation detail
- Always converge to one recommendation
- Never start from "what stories are ready?" Start from "what gap matters most?"
- If the top gap has no story yet, recommend creating or promoting the right artifact instead of silently skipping it
- Do not let inbox novelty, eval staleness, or small ready work outrank a larger live gap without an explicit explanation
