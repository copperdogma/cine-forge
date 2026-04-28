---
name: triage
description: Orchestrate CineForge triage from Ideal/spec facts and neutral lane packets, then recommend the best next action
user-invocable: true
---

# /triage [stories|inbox|evals|architecture|health] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with
> `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`,
> `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated
> dashboards, and relevant decision records in `docs/decisions/` /
> `docs/design/`. If this work touches a known constraint in `docs/spec.md`,
> respect both its limitation type and current phase. If none apply, say so
> explicitly.

`/triage` is the proactive meta-skill. It does not own the backlog, inbox, eval,
architecture, UI-scout, or health logic itself. In full-sweep mode it starts
from the Ideal/spec/state/graph, gathers neutral lane packets, shows the top
three cross-domain candidates, then synthesizes one recommended next action
under current repo reality.

Important is not enough by itself. `/triage` must answer:

- what gap matters most?
- why is this the right thing to do now?
- how close is the project to the Ideal on today's technology, not just
  against the literal north-star?
- which top three cross-domain candidates are credible, and why did the final
  recommendation beat the other top-three candidates?

CineForge's Ideal test is product-facing: if using the app feels like work,
something is wrong. Story/eval/tooling surfaces exist to move the project
toward that Ideal, not to create backlog motion for its own sake.

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
| `/triage health` | Delegate to `/triage-health scan` |
| `/triage health scan` | Delegate to `/triage-health scan` |

When a scope is provided, hand off completely to the leaf skill. Do not
maintain duplicate logic here.

## Leaf Skills

- `/triage-stories` — backlog prioritization, dependency bottlenecks, story readiness
- `/triage-inbox` — inbox processing, plus read-only `scan` mode for orchestration
- `/triage-evals` — eval health, compromise leverage, rerun candidates
- `/triage-architecture` — architecture-audit cadence, drift signals, simplification routing
- `/triage-health` — read-only freshness packet across UI-scout, codebase
  improvement, eval/model/golden, methodology/tooling, architecture-audit, and
  dependency/provider health
- `/codebase-improvement-scout` — report-first codebase hygiene follow-up when
  triage recommends it
- `/discover-models` — provider/model freshness follow-up when triage recommends it

When full-sweep `/triage` asks a leaf for input, request a compact lane packet
instead of a final repo-wide decision. Each lane packet should provide up to
three neutral candidates with:

- candidate name
- Ideal promise and spec refs
- evidence and source files
- why now
- suggested action shape
- whether it is story-worthy or too small
- validation or stop condition
- blockers, stale evidence, and reasons not to do it now

The main `/triage` thread owns cross-domain ranking. Do not preselect one
"largest gap" so narrowly that leaf lanes ignore stronger evidence in their own
domains.

## Completion Sanity Gate

Before accepting a "nothing ready", "maintenance only", or idle
recommendation, prove that the repo is not hiding undecomposed product scope.
Check the v1/MVP promise, input coverage, future/unplanned state lines, inbox
items, UI-scout truth, and recent stories/evals. If those surfaces show missing
user-facing capability, recommend creating, promoting, reshaping, or validating
that work before routing to routine maintenance. Never equate "no ready story"
with "feature-complete" without concrete evidence.

## Eval Ladder Gate

For AI-capability work, identify the eval ladder before creating or prioritizing
implementation backlog:

- the root Ideal eval or full-path golden, or the explicit reason it is deferred
- the parent eval or latest higher-level result that shows the current failure
- the measured failure mode that makes decomposition necessary
- the child eval, failure-classification attempt, ADR/spec update, or story that
  advances the next unresolved ladder node

Prefer rerunning a root/parent eval when new models, provider changes, code
changes, scorer fixes, or changed constraints could collapse the current
decomposition. Prefer a child eval or failure-classification attempt when the
parent failure is still too vague to choose AI-only, multi-call AI,
deterministic code, or hybrid implementation honestly.

## Full-Sweep Mode

When invoked with no scope:

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
   - `docs/ui-scout.md` and `state.ui_scout` when UI polish, obviousness, or
     workflow truth could be a candidate
   - relevant ADRs under `docs/decisions/` / `docs/design/`
   - recent `git log --oneline -20`
   - Goal: identify a broad candidate set of live gaps and simplification
     opportunities before reading stories as a backlog, without choosing the
     final winner yet.

2. **Start neutral lane evidence, then run the fact collector directly**
   - If the environment and user instructions allow subagents or delegation,
     immediately launch scoped lane packet requests after reading the shared
     frame. Keep packets neutral: ask each lane for its best candidates from
     the broad Ideal/spec/state/graph context, not for a final repo-wide pick
     and not for confirmation of one preselected gap.
   - Ask these lanes for packets:
     - `/triage-stories`
     - `/triage-inbox scan`
     - `/triage-evals`
     - `/triage-architecture scan`
     - `/triage-health scan`
   - In the main thread, while lane packets are running, run:

     ```bash
     python scripts/triage_facts.py --json
     ```

   - Use the facts for branch/dirty state, generated wrapper drift,
     story/eval recommendations, inbox counts, architecture-audit cadence,
     UI-scout status, codebase-improvement freshness, lane presence, and recent
     churn.
   - If the script fails, say so explicitly and continue from the underlying
     docs with lower confidence. Do not pretend the fact pass happened.
   - If delegation is unavailable, still run the direct fact collector here,
     then query the same neutral lane packet contracts sequentially later.

3. **Open candidate gaps without picking a winner yet**
   - State 2-4 plausible unmet Ideal promises or overscaffolded compromises in
     plain language.
   - Map each to owning spec section(s), methodology category, phase,
     UI-scout/architecture health if relevant, and known evidence.
   - Do not pick the final winner before lane packets report.

4. **Run the why-now / actionability gate for plausible winners**
   - What was the last meaningful action on this line?
   - On what date did it happen?
   - What artifact, story, eval, report, or recommendation proves that?
   - What materially changed since then?
   - Treat blocked stories whose unblock condition is still unmet, exhausted
     eval retries, and stale "do this next" notes as health flags unless new
     evidence makes them actionable.

5. **Apply phase-pressure defaults**
   - `converge` -> prefer the smallest honest deletion, simplification, or
     residue-removal move that could retire the compromise or prove why it
     cannot be retired yet.
   - `climb` -> prefer the strongest bounded improvement move that could
     advance the line toward `hold`.
   - `hold` -> prefer thinner / cheaper / faster / simpler / easier-to-operate
     work when no stronger actionable `converge` or `climb` line wins.

   A line does not need a new bug report, inbox item, or external prompt to be
   actionable. If phase plus current repo evidence suggests a bounded,
   falsifiable next move, that is enough unless recent evidence says the same
   move is currently blocked, exhausted, or not worth repeating.

6. **Read decision and architecture constraints for plausible winners**
   - Open relevant ADRs, design docs, and architecture-audit state.
   - If none apply, say so explicitly.
   - Avoid picking a next action that fights a settled architecture decision,
     immutable artifact rule, best-model baseline rule, or headless-operation
     requirement.

7. **Collect lane packets**
   - If packets were launched earlier, collect their reports here.
   - If delegation was unavailable, run the same scoped contracts sequentially.
   - Keep `scripts/triage_facts.py` as a direct main-thread fact source, not a
     delegated lane and not a substitute for lane judgment.

8. **Calibrate against the Ideal**
   - Add one short `Vs Ideal` section.
   - Distinguish literal north-star distance from current-tech progress.
   - Ground the answer in current evidence: what is already strong, what still
     makes the app feel like work, and whether the line of travel is improving,
     mixed, stalled, or blocked.

9. **Build the top-three shortlist**
   Merge lane candidates into the top three cross-domain recommendations. Each
   item must include:
   - recommendation
   - Ideal/spec value
   - why now
   - action shape
   - validation or stop condition
   - why it ranked above or below the other two

   Do not hide the other top-three candidates. Cam may choose recommendation 2
   or 3 when human context changes the call.

10. **Synthesize one cross-domain recommendation**
   Rank the problem first, then choose the vehicle that best advances it
   (continue an active story, expand/reopen a story, create a story, run an
   eval, do architecture work, run UI scout, or no-op).

   Before recommending `create a story`, challenge that choice against the last
   2-4 stories on the same problem line. If the delta is mostly same-line
   progression, test/docs/truth-surface codification, or an input/container
   permutation with the same subsystem and operator-facing outcome, prefer
   `continue`, `expand`, `reopen`, or `consolidate` instead. Do not fragment
   work into tiny story shells that barely advance the app.

11. **Return a short report**

```markdown
## Triage

### Candidate Gaps
- {candidate gap + spec/category/phase}
- {candidate gap + spec/category/phase}

### Actionability
- Last relevant action: {date + story/eval/artifact}
- Why now: {materially new trigger or phase/evidence pressure}
- Health flags: {blocked/exhausted/stale lines or none}

### Vs Ideal
- Literal north-star: {how far the project still is from the true Ideal}
- Current-tech read: {how close the project is to a strong present-day version of the Ideal}
- Direction: {getting closer | mixed | stalled | blocked} - {why}

### Top Three
1. {recommendation}
   - Ideal/spec value: {refs + value}
   - Why now: {trigger}
   - Action shape: {continue story | expand story | create story | eval | audit | scout | no-op}
   - Stop condition: {validation or proof}
   - Rank rationale: {why this ranks above or below the other top-three candidates}
2. {recommendation}
   - Ideal/spec value: {refs + value}
   - Why now: {trigger}
   - Action shape: {continue story | expand story | create story | eval | audit | scout | no-op}
   - Stop condition: {validation or proof}
   - Rank rationale: {why this ranks above or below the other top-three candidates}
3. {recommendation}
   - Ideal/spec value: {refs + value}
   - Why now: {trigger}
   - Action shape: {continue story | expand story | create story | eval | audit | scout | no-op}
   - Stop condition: {validation or proof}
   - Rank rationale: {why this ranks above or below the other top-three candidates}

### Final Recommendation
- {one next action}
- Action shape: {continue story | expand story | create story | eval | audit | scout | no-op}

### Why
- {2-3 strongest reasons}

### Handoff
Reply yes to proceed with: {exact next command or concrete action}.
```

## Guardrails

- Scoped invocations delegate; do not duplicate leaf-skill logic here.
- Full-sweep mode is read-only.
- Always include a short `Vs Ideal` read.
- Surface the top three recommendations before the final recommendation.
- Start from Ideal/spec/state gaps, not from "what stories are ready?"
- Do not pick the final winner before neutral lane evidence can surface
  stronger domain-specific candidates.
- Do not hide the lower-ranked top-three candidates.
- Do not recommend a blocked line while the unblock condition is unmet.
- Do not treat an exhausted `retry_when` condition as fresh evidence.
- Do not recommend a new story for same-line progression, docs/test
  codification, or input/container permutations unless the runtime seam or
  validation boundary materially changed.
- Do not recommend "no action" unless every plausible phase-aligned move is
  blocked, exhausted, or lacks a bounded falsifiable next step.
