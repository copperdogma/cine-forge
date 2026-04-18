---
name: triage
description: Identify the highest-leverage Ideal/spec/state gap, then recommend the next action that best advances it
user-invocable: true
---

# /triage [stories|inbox|evals] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current state phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

`/triage` is the proactive meta-skill. Its job is to choose the **most important live methodology gap** before looking for convenient work, then recommend the highest-leverage actionable move under current repo reality.

Important is not enough by itself. `/triage` must answer both:

- what gap matters most?
- why is this the right thing to do now?

A primary gap can stay primary while still be the wrong recommended action if
nothing materially changed since the last attempt, recommendation, or
measurement pass.

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
existing story line before creating or prioritizing a new shell. Before
recommending a new story shell, challenge that choice against the last 2-4
stories on the same problem line. If the delta is mostly same-line
later-state progression, test/docs/truth-surface codification, or a
container/input permutation with the same subsystem and operator-facing
outcome, prefer continuing, reopening, expanding, or consolidating the
existing line instead.

Continuity bias never overrides blocked-state truth. A `Blocked` story with an
unmet unblock condition is not an actionable continuation; surface it under
Health Flags unless the user is explicitly asking how to unblock it or the
unblock condition is now materially satisfied.

Eval retry metadata works the same way: a `retry_when` entry is a dormant
detector, not a standing recommendation. If the same trigger was already
checked and nothing materially changed, treat that eval follow-on as exhausted
and report it as a health flag / deferral, not the next move.

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
   - Prefer the compiled actionability surfaces in
     `graph["spec"]["compromises"][*]["actionability"]`,
     `graph["stories"][*]["actionability"]`, and
     `graph["evals"][*]["actionability"]` before reconstructing retry posture
     or recency manually from story/eval prose.
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

3. **Run the why-now / actionability gate**
   - Before recommending work under the primary gap, answer:
     - what was the last meaningful action on this line?
     - on what date did it happen?
     - what artifact, story, eval, or recommendation proves that?
     - what materially changed since then?
   - If the gap has no live trigger and no genuinely new question, keep it as
     the primary gap or a health flag, but do not recommend repeating that
     line just because it is still important.

4. **Apply phase-pressure defaults**
   Phase is not tie-break metadata. It creates default pressure to keep moving
   the repo toward the Ideal:
   - `converge` -> prefer the smallest honest deletion, simplification, or
     residue-removal move that could retire the compromise or prove why it
     cannot be retired yet
   - `climb` -> prefer the strongest bounded improvement move that could
     advance the line toward `hold` (quality, proof widening, substrate
     hardening, or a more capable approach)
   - `hold` -> prefer thinner / cheaper / faster / simpler / easier-to-operate
     work when no stronger actionable `converge` or `climb` line wins

   A line does not need a new bug report, inbox item, or external prompt to be
   actionable. If phase plus current repo evidence suggests a bounded,
   falsifiable next move, that is enough unless recent evidence says the same
   move is currently blocked, exhausted, or not worth repeating.

5. **Read decision constraints for that gap**
   - Open the relevant ADRs / design docs for the chosen gap
   - If none apply, say so explicitly
   - Goal: avoid picking a next action that fights a settled architecture decision

6. **Query the existing work under that gap**
   - Stories: `/triage-stories`
   - Inbox: `/triage-inbox scan`
   - Evals: `/triage-evals`
   - Architecture: `/triage-architecture scan`
   - UI product-truth freshness: always inspect `state.ui_scout`; if the lane
     is overdue, the canonical scenario is still `never`, or the latest report
     is marked `issues_found` / `recheck_due`, inspect `docs/ui-scout.md` and
     the latest relevant report in `docs/ui-scout/` before deciding whether the
     right next action is a fresh scout run or the follow-up story line
   - But interpret each leaf through one question:
     - what already exists that advances the chosen gap?
   - Do **not** let a smaller ready story outrank the chosen gap just because it is easier to start
   - Do **not** let a blocked story or an exhausted eval retry masquerade as
     actionable just because it is the most continuous existing line

7. **Choose one next action**
   Only rank actionable candidates here. Blocked stories with unmet unblock
   conditions and eval retries whose triggers remain exhausted belong under
   `Health Flags`, not `Recommended Action`.
   Prefer this order:
   - continue, reopen, expand, or consolidate an in-flight or recently advanced story that directly advances the chosen gap
   - promote or reshape an existing draft story that is the clearest continuation of the chosen gap
   - before recommending `create the missing story / ADR / spec update / eval`,
     challenge that choice against the last 2-4 stories on the same problem
     line; if the subsystem, validation boundary, and success surface are still
     materially the same, prefer continuing, reopening, expanding, or
     consolidating the existing line instead
   - create the missing story / ADR / spec update / eval if the gap has no proper home yet
   - do not silently outrank overdue UI-scout freshness with smaller unrelated
     ready work unless the stronger line is genuinely not actionable yet
   - only fall back to a smaller unrelated ready story if the larger gap is genuinely not actionable yet, and explain why

   Choose among those options with the strongest combined signal across:
   - movement toward the Ideal
   - real problem pressure
   - phase pressure (`converge` > actionable `climb` > actionable `hold`,
     unless blocker or recency evidence says otherwise)
   - blocking power / dependency leverage
   - simplification leverage
   - continuity from active unresolved work lines

   `No-op` is the last resort, not the default safe answer. It is only honest
   when every plausible phase-aligned move is blocked by missing external
   capability, was just retried on the same premise without a new trigger, or
   lacks a bounded falsifiable next step.

8. **Return a short report**

```markdown
## Triage

### Primary Gap
- {Ideal promise or simplification opportunity}
- Spec: {spec refs}
- State: {category + substrate + phase}

### Actionability
- Last relevant action: {date + story/eval/artifact}
- Why now: {materially new trigger or "none"}
- If "none": {why the primary gap is not the recommended action today}

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
- {blocked story with unmet unblock condition, exhausted eval retry, or "none"}
```

## Guardrails

- Scoped invocations delegate — no duplicate logic here
- Full-sweep mode is read-only
- Do not let `/triage` absorb leaf-skill implementation detail
- Always converge to one recommendation
- Never start from "what stories are ready?" Start from "what gap matters most?"
- If the top gap has no story yet, recommend creating or promoting the right artifact instead of silently skipping it
- Do not let inbox novelty, eval staleness, or small ready work outrank a larger live gap without an explicit explanation
- Do not recommend a new story for same-line later-state progression,
  tests/docs/truth-surface codification, or input/container permutations on an
  already-supported behavior class unless the runtime seam or validation
  boundary materially changed
- Never recommend a blocked line just because continuity or recent commits make
  it feel active; if the unblock condition is unmet, keep it in `Health Flags`
- Never treat a previously consumed `retry_when` condition as fresh evidence
  without a materially new trigger
- Never recommend repeating a line just because it is still the biggest open
  gap; cite the last attempt and the current why-now trigger explicitly
- Do not treat lack of a fresh external trigger as sufficient reason for
  `no-op` when a bounded phase-aligned improvement move still exists
- Prefer recommending the best next attempt, simplification, or new story shell
  over `no-op` unless the repo is genuinely out of actionable phase-aligned
  moves
- `Converge` means "try to delete or collapse residue," not "wait until
  something else happens."
