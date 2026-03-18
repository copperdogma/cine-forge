---
name: triage
description: Orchestrate the triage leaf skills and synthesize the highest-value next action
user-invocable: true
---

# /triage [stories|inbox|evals] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current build-map phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

`/triage` is the proactive meta-skill. It does **not** own all domain logic itself. It dispatches to focused leaf skills and, in full-sweep mode, fans them out and synthesizes one recommendation.

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

When a scope is provided, hand off completely to the leaf skill. Do **not** keep a second implementation here.

## Leaf Skills

- `/triage-stories` — backlog prioritization, dependency bottlenecks, story readiness
- `/triage-inbox` — inbox processing, plus read-only `scan` mode for orchestration
- `/triage-evals` — eval health, compromise leverage, rerun candidates

## Full-Sweep Mode

When invoked with no scope, run a lightweight orchestration pass:

1. **Read the shared frame**
   - `docs/ideal.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/spec.md`
   - `docs/build-map.md`
   - relevant ADRs / decision docs
   - recent `git log --oneline -20`

2. **Run the leaf sweeps**
   - Stories: `/triage-stories`
   - Inbox: `/triage-inbox scan`
   - Evals: `/triage-evals`

3. **Collect leaf outputs**
   Each leaf should provide:
   - its top recommendation
   - 1-3 reasons
   - major blockers / health flags
   - whether the next step is read-only or action-taking

4. **Synthesize one next action**
   Choose using:
   - Ideal alignment
   - blocking power
   - substrate leverage
   - phase-appropriate leverage
   - urgency / staleness
   - momentum from recent work
   - operator cost

5. **Return a short report**

```markdown
## Triage

### Recommended Action
- {one next action}

### Why
- {2-3 strongest reasons}

### Runner-Ups
- {alternate action}
- {alternate action}

### Domain Notes
- Stories: {summary}
- Inbox: {summary}
- Evals: {summary}

### Health Flags
- {blocker or "none"}
```

## Guardrails

- Scoped invocations delegate — no duplicate logic here
- Full-sweep mode is read-only
- Do not let `/triage` absorb leaf-skill implementation detail
- Always converge to one recommendation
