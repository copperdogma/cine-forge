---
name: triage-adr
description: Inspect an existing ADR, identify what remains undecided, separate Cam-owned preference calls from technical recommendations, and recommend the next route.
user-invocable: true
---

# /triage-adr <ADR path or ADR-NNN>

Use this when an ADR already exists but the remaining decisions, maturity, or
next action are unclear.

This is an advisory triage pass. It does not create a new ADR, choose the final
decision, rewrite the ADR, or run `/align` unless the user explicitly asks for
that follow-up.

## Use When

- Cam asks where an ADR stands or what is left.
- An ADR conversation has become rambling or hard to summarize.
- The ADR appears close to decided, but integration or alignment work is
  unclear.
- A technical option still needs a recommendation before Cam weighs in.
- An ADR may be stale, superseded, blocked, or ready for `/align`.

Skip this for brand-new decisions that need `/create-adr`, ordinary story
triage, and cases where the next action is already explicit in the ADR.

## Read First

1. The named ADR, or the most relevant ADR under `docs/decisions/`.
2. `docs/ideal.md`
3. `docs/spec.md`
4. `docs/methodology/state.yaml`
5. `docs/methodology/graph.json`
6. Relevant stories, alignments, scouts, evals, setup notes, or runbooks linked
   from the ADR.

If the ADR cannot be identified, ask one concise question for the exact ADR.

## Decision Inventory

Classify every meaningful remaining item:

- **Settled**: the ADR already records the decision and rationale.
- **Cam preference / product direction**: the choice has taste, workflow,
  priority, user-experience, downstream ownership, or risk-tolerance
  consequences that Cam should decide.
- **Technical recommendation**: the choice is mainly implementation detail,
  file format, validation route, sequencing, or tool/contract shape. Think it
  through and recommend a path instead of handing back a vague question.
- **Evidence gap**: more repo evidence, research, eval, browser proof, runtime
  proof, or target-project comparison is needed before the decision is honest.
- **Integration gap**: the decision appears made, but specs, stories,
  methodology state/graph, setup surfaces, AGENTS, or follow-up work are not
  aligned yet.

Use `/ideation` only when the remaining blocker is weak option quality. Do not
use it when the blocker is missing evidence.

## Maturity Read

Pick one:

- **Early**: context exists, but options or evidence are still too thin.
- **Discussing**: real options exist and Cam-facing choices remain.
- **Researching**: evidence is the main blocker.
- **Decision-ready**: open choices are clear enough for Cam or an agent
  recommendation.
- **Decision-complete / needs alignment**: decisions are effectively settled;
  route to repo-local `/align`.
- **Blocked**: a named dependency prevents honest closure.
- **Stale / superseded**: the ADR no longer describes the active direction.

## Next Route Rules

Recommend exactly one primary next route:

- **Continue discussion** when a Cam preference/product-direction decision is
  genuinely open.
- **Make technical recommendation** when the remaining choice is technical and
  enough evidence exists.
- **Run research** when evidence is missing and the needed source is clear.
- **Run `/ideation`** when option quality is the blocker.
- **Update the ADR** when decisions are known but not captured.
- **Create or adjust stories** when implementation work has no honest owner.
- **Run `/align`** when the ADR likely affects Ideal, spec, state/graph,
  stories, evals, runbooks, or implementation assumptions.
- **Accept / reject / mark superseded** when the ADR lifecycle state is the only
  remaining work.

## Output Shape

```markdown
## ADR Triage — {ADR}

### Maturity
- {one label and one sentence of evidence}

### Settled Decisions
- {decision and where it is recorded}

### Cam Decisions
- {question, why Cam owns it, downstream consequence}

### Technical Recommendations
- {decision, recommendation, rationale, proof needed}

### Evidence Gaps
- {gap, source/check that would close it}

### Integration Gaps
- {surface or story that must be updated}

### Recommended Next Route
- {one action}
```

Keep the report compact. If there are no items in a section, write `None`.

## Guardrails

- Read the actual ADR; do not summarize from memory.
- Do not reopen settled decisions unless the ADR contradicts current repo
  evidence.
- Do not ask Cam to decide low-level technical details when the agent can make
  and defend a recommendation.
- Do not bury a real product/taste/ownership call inside an agent
  recommendation.
- Do not create stories, ADRs, evals, or alignment updates during triage unless
  Cam explicitly asks for that follow-up.
