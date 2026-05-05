# Learning Candidates

This folder holds reviewed workflow-learning candidates for this project.

The lane exists to capture durable workflow corrections without letting a
single run silently rewrite live behavior. Most completed work should produce no
candidate.

## Lifecycle

Normal promotion path:

`Draft -> Proposed -> Accepted -> Promoted`

Dismissal path:

`Draft -> Proposed -> Dismissed`

- `Draft`: evidence may warrant a change, but the candidate is not yet ready
  for an accept/dismiss decision.
- `Proposed`: evidence and target surface are clear enough to ask Cam for a
  decision.
- `Accepted`: Cam approved the candidate as worth promoting.
- `Dismissed`: the candidate was rejected or went stale; dismissed candidates
  are terminal unless reopened through a new review with fresh evidence.
- `Promoted`: the approved change was applied to its target surface and
  validated; promoted candidates are terminal and repeated promotion requests
  must not apply the live change again.

Allowed transitions:

- `Draft -> Proposed` when evidence and target surface are clear enough for a
  decision.
- `Proposed -> Accepted` or `Proposed -> Dismissed` after Cam reviews the
  evidence.
- `Accepted -> Promoted` only after separate Cam approval to change the live
  target surface.
- `Accepted -> Dismissed` only before promotion when Cam explicitly reverses
  acceptance.
- `Dismissed -> Draft` or `Dismissed -> Proposed` only when fresh evidence
  reopens the candidate; stop before acceptance or promotion in the same
  operation.
- `Promoted` is terminal. Further review can record notes, but live behavior
  changes must be `none` unless a new candidate is opened.

## Candidate Rules

- Candidates are inspectable markdown files, not live instructions.
- Live skills, `AGENTS.md`, and methodology docs change only through explicit
  promotion. Files outside this repo are not promotion targets for repo-local
  candidates.
- The default learning-review result is `RESULT: no-candidate`.
- Repeated friction, explicit user corrections, high-risk process misses, and
  reusable procedure discoveries are valid triggers. Each candidate must name
  when it should be reviewed again.
- Novelty, vibes, one-off success, generic advice, and model-era compensations
  are not enough.

## Required Fields

Every candidate must include:

- title
- status: one of `Draft`, `Proposed`, `Accepted`, `Dismissed`, or `Promoted`
- created date
- target surface: the exact skill, doc, story workflow, or
  repo-local workflow that would change if promoted
- trigger class
- review cadence: why the candidate exists and when it should be reviewed again
- source runs: the run ids, thread references, story ids, or other durable
  provenance that make the candidate reviewable later
- user corrections: quoted or summarized correction evidence, or `none
  recorded` when the evidence did not come from a user correction
- evidence summary: the short reviewable explanation of what happened, backed
  by concrete source runs, user corrections, validation findings, loop results,
  or scout/story references
- observed pattern: what keeps going wrong or what repeatable procedure was
  discovered
- proposed change: the smallest live behavior or documentation change under
  consideration
- why it matters
- rejection checks
- promotion gate: the explicit Cam decision, verification result, or repeated
  evidence threshold required before live behavior changes
- promotion action: the exact file, skill, story, planning note, or repo-local
  workflow changed after acceptance
- validation plan
- decision history

Do not invent evidence to satisfy the template. If either concrete source
provenance or a source-backed evidence summary is missing, do not draft,
propose, accept, or promote the candidate. Missing user-correction evidence must
be recorded as `none recorded`, not filled in from inference.

Use `template.md` for new candidate files and keep examples under
`examples/`.
