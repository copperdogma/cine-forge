---
name: ideation
description: Expand and curate divergent option sets before sticky decisions. Use when Codex is drafting or revising docs/ideal.md or docs/spec.md, preparing ADR considered options, shaping story boundaries, planning implementation approaches, or brainstorming product/workflow solutions where direct prompting is producing obvious same-neighborhood ideas. Optional helper only; the caller keeps final decision authority.
user-invocable: true
---

# /ideation [brief]

Use this as an option-discovery helper before a caller skill closes a decision.
It improves the option pool; it does not choose the final answer, create the
owning artifact, or override local Ideal/spec/evidence.

Read `references/open-collider-pattern.md` when the task needs the full
protocol, when using subagents, or when preserving a durable ideation report.

## Use When

- `docs/ideal.md` or `docs/spec.md` generation needs richer possibility space.
- An ADR has thin "considered options" or all options are obvious variants of
  the same answer.
- A story boundary is too vague to score or keeps fragmenting into tiny tasks.
- A build plan has a real solution-space question before implementation.
- Product, workflow, UX, architecture, eval, or methodology brainstorming is
  stuck in familiar patterns.

Skip this for routine triage, straightforward bug fixes, validation, closeout,
or decisions where the blocker is evidence rather than option quality.

## Inputs

Ask the caller for, or infer from the repo artifacts:

- the decision or brainstorm question
- the caller artifact that will own the result
- relevant Ideal/spec/ADR/story constraints
- what a good option must improve
- what directions are out of bounds
- the desired mode: `quick`, `standard`, or `subagent`

If the missing input would change the result materially and cannot be inferred,
ask one concise question. Otherwise proceed with stated assumptions.

## Modes

### Quick

Use during normal planning. Generate:

- 2-3 baseline options
- 3-4 distant domains with mechanisms and bridge questions
- 6-8 candidate options
- a compact kept/rejected packet for the caller

### Standard

Use for `docs/ideal.md`, ADRs, story boundary shaping, or high-impact product
design. Generate:

- 3-5 baseline options
- 5-7 distant domains
- 10-15 candidate options
- a ranked packet with tradeoffs, proof needs, and rejection rationale

### Subagent

Use only when the current user request explicitly authorizes subagents,
delegation, or parallel agent work. The main caller keeps the local north star,
passes a bounded prompt to one worker, and receives a compact option packet.

Subagent prompt shape:

```text
Use /ideation on this bounded question:
<question>

Caller-owned final decision surface:
<artifact or skill>

Local constraints and evidence:
<Ideal/spec/ADR/story excerpts or summary>

Generate baseline options, 5-7 distant domains with mechanisms and bridge
questions, candidate options, and a kept/rejected packet. Do not choose the
final answer. Do not edit files. Do not create stories/ADRs. Do not invoke
/loop-verify. Do not spawn other agents. Return only the option packet for the
caller.
```

## Protocol

1. Frame the brief.
   - State the problem in one sentence.
   - Name local constraints and success criteria.
   - Name the caller artifact that will own any durable result.
2. Generate the baseline.
   - List plausible direct options first.
   - Note why each is useful and why it may be too familiar or insufficient.
3. Build the domain bank.
   - Choose structurally distant domains, not adjacent product categories.
   - For each domain, name the mechanism and a bridge question.
   - Prefer mechanisms such as feedback loops, control surfaces, bottlenecks,
     error recovery, memory, incentives, staged disclosure, provenance,
     queueing, market design, ecological succession, compression, or ritual.
4. Generate candidates.
   - Force each candidate to bridge the local problem to one domain mechanism.
   - Avoid decorative analogies; the mechanism must alter the solution.
   - Keep candidates concrete enough to become an ADR option, story boundary,
     product opinion, or implementation approach.
5. Curate.
   - Keep ideas that improve the caller's option set.
   - Reject generic, unbuildable, evidence-free, or locally incompatible ideas.
   - Preserve rejection rationale when it prevents future rediscovery.
6. Hand back to the caller.
   - Recommend a small packet of strongest options and tradeoffs.
   - Name proof needed before adoption.
   - State explicitly that the caller owns final selection and artifact edits.

## Output Shape

Return this compact structure unless the caller asks for a report:

```markdown
## Ideation Packet

### Brief
- Question:
- Caller artifact:
- Success criteria:
- Hard constraints:

### Baseline Options
- Option:
  - Strength:
  - Limit:

### Distant Domains
- Domain:
  - Mechanism:
  - Bridge question:

### Candidate Options
- Option:
  - Source:
  - Why it may help:
  - Risks / proof needed:
  - Disposition: keep / maybe / reject

### Caller Handoff
- Strongest option:
- Backup option:
- Rejected pattern worth remembering:
- Open question:
```

## Durable Artifacts

Default: place the useful output in the caller artifact:

- `docs/ideal.md` / `docs/spec.md`: integrate only the resulting product
  truth, not the whole brainstorm.
- ADR: add stronger considered options, consequences, and rejected options.
- Story: add the chosen boundary, acceptance criteria, alternatives rejected,
  and proof plan.
- Alignment/scout: summarize the ideation method and adoption decision.

Use `templates/ideation-report.md` only when the ideation run itself is
evidence worth preserving, such as a high-impact ADR, a future cross-project
rollout, or a design session where rejected options matter.

Do not create a per-run folder by default. Do not let ideation reports become a
parallel backlog.

## Guardrails

- Ideation expands options; it does not decide.
- Novelty is not correctness.
- Do not use this to avoid current upstream docs, repo evidence, tests, evals,
  browser proof, or human taste calls.
- Do not make this a mandatory step in normal triage, setup, story creation, or
  validation.
- Do not install or invoke Open Collider tooling unless a separate scout/story
  accepts that overhead.
- For high-stakes domains, treat generated ideas as hypotheses and verify with
  authoritative sources before use.
