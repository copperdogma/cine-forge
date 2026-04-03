---
name: triage
description: Identify the highest-leverage Ideal/spec/build-map gap, then recommend the next action that best advances it
user-invocable: true
---

# /triage [stories|inbox|evals] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current build-map phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

`/triage` is the proactive meta-skill. Its job is to choose the **most important live methodology gap** before looking for convenient work.

The required order is:

1. **Ideal** — what major user promise or simplification opportunity is most visibly unmet?
2. **Spec** — which active constraint or requirement expresses that gap?
3. **Build map** — which category owns it, and is the correct move `climb`, `hold`, `converge`, or `unplanned`?
4. **ADRs / design docs** — what decisions constrain the next move?
5. **Existing work** — which stories, inbox items, or evals already advance that exact gap?

Stories, inbox items, and evals are **not** the source of priority. They are candidate continuations of the priority established by Ideal/spec/build-map reasoning.

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

When invoked with no scope, run a methodology-first orchestration pass:

1. **Read the shared frame**
   - `docs/ideal.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/spec.md`
   - `docs/build-map.md`
   - recent `git log --oneline -20`
   - Goal: identify the biggest live gap or simplification opportunity before reading stories as a backlog.

2. **Name the primary gap**
   - State the unmet Ideal promise or overscaffolded compromise in plain language
   - Map it to the owning spec section(s)
   - Map it to the owning build-map category
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
   - But interpret each leaf through one question:
     - what already exists that advances the chosen gap?
   - Do **not** let a smaller ready story outrank the chosen gap just because it is easier to start

5. **Choose one next action**
   Prefer this order:
   - continue an in-flight or ready story that directly advances the chosen gap
   - promote or reshape an existing draft story that is the clearest continuation of the chosen gap
   - create the missing story / ADR / spec update / eval if the gap has no proper home yet
   - only fall back to a smaller unrelated ready story if the larger gap is genuinely not actionable yet, and explain why

6. **Return a short report**

```markdown
## Triage

### Primary Gap
- {Ideal promise or simplification opportunity}
- Spec: {spec refs}
- Build Map: {category + substrate + phase}

### Why
- {2-3 strongest reasons}

### Runner-Ups
- {alternate action}
- {alternate action}

### Domain Notes
- Stories: {which stories do or do not advance the chosen gap}
- Inbox: {which inbox items do or do not map to the chosen gap}
- Evals: {which evals matter for the chosen gap, or why eval work is not the move}

### Health Flags
- {blocker or "none"}

### Recommended Next Step
- Say "yes" to: {one concrete next action phrased so a plain "yes" clearly approves it}
```

The recommendation must be the final section. Write it as an approval-ready handoff, not just a summary label. The user should be able to reply with a plain `"yes"` and unambiguously authorize the recommended next move.

## Guardrails

- Scoped invocations delegate — no duplicate logic here
- Full-sweep mode is read-only
- Do not let `/triage` absorb leaf-skill implementation detail
- Always converge to one recommendation
- Never start from "what stories are ready?" Start from "what gap matters most?"
- If the top gap has no story yet, recommend creating or promoting the right artifact instead of silently skipping it
- Do not let inbox novelty, eval staleness, or small ready work outrank a larger live gap without an explicit explanation
- Put the recommendation at the very end so the user can answer with a simple "yes"
