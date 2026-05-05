---
name: learning-candidate
description: Draft, review, and promote structured workflow-learning candidates without changing live behavior unless explicitly approved
user-invocable: true
---

# /learning-candidate [draft|review|accept|dismiss|promote] [finding]

Use this after `/learning-review` returns `RESULT: candidate-warranted`, or
when Cam explicitly asks to draft, review, accept, dismiss, or promote a
workflow-learning candidate.

This skill manages candidate artifacts. It does not silently mutate live
skills, `AGENTS.md`, methodology docs, or other project repos.

## Storage

Store candidates under:

```text
docs/learning-candidates/
```

Use this filename shape:

```text
candidate-YYYYMMDD-<short-slug>.md
```

Use `docs/learning-candidates/template.md` as the file shape.

## Lifecycle

- `Draft`: written because evidence may warrant a change, but not yet proposed
  as ready to accept.
- `Proposed`: evidence and target are clear enough to ask Cam to accept or
  dismiss the change.
- `Accepted`: Cam accepted the candidate as worth promoting into the target
  surface.
- `Dismissed`: Cam or validation rejected the candidate.
- `Promoted`: the accepted change was actually applied to the target surface
  through the appropriate repo-native workflow, with evidence linked.

Only Cam's explicit approval, or a direct user instruction in the current turn,
can move a candidate to `Accepted` or authorize promotion.
`Dismissed` is terminal unless fresh evidence reopens the candidate; reopening
must move it back through `Draft` or `Proposed` before it can be accepted or
promoted.

Allowed transitions:

- `Draft -> Proposed` after review finds the evidence and target clear enough.
- `Proposed -> Accepted` only after Cam explicitly accepts it.
- `Proposed -> Dismissed` after Cam or validation rejects it.
- `Accepted -> Promoted` only through promote mode with target, action, and
  validation fields present.
- `Accepted -> Dismissed` only before promotion when Cam explicitly reverses
  acceptance.
- `Dismissed -> Draft` or `Dismissed -> Proposed` only when fresh evidence is
  recorded; stop before acceptance or promotion.
- `Promoted` is terminal for this workflow. Do not reapply live changes from an
  already promoted candidate; route reversals or follow-up behavior changes
  through a new story or candidate.

## Required Fields

Every candidate must include:

- title
- status
- created date
- target surface
- trigger class
- review cadence
- source runs
- user corrections
- evidence summary
- observed pattern
- proposed change
- why it matters
- rejection checks
- promotion gate
- promotion action
- validation plan
- decision history

If a required field does not apply, record that explicitly instead of omitting
it. For example, use `user corrections: none recorded` when the evidence did
not come from a user correction. Do not invent source runs, user corrections,
or evidence to satisfy the template. If there is no concrete source run, or if
the evidence summary is missing or unsupported, do not draft, propose, accept,
or promote the candidate.

## Draft Mode

When drafting:

1. Read the detector output and the smallest evidence set needed to support it.
   If Cam explicitly asked for a draft without a detector output, first apply
   `/learning-review` evidence thresholds, rejection rules, and snapshot-bias
   checks to the available evidence. If the evidence would return
   `RESULT: no-candidate`, do not create a file; report why the draft was not
   warranted.
2. Check whether an existing candidate already covers the same target and
   pattern.
3. Create one candidate file in `Draft` unless the evidence is already strong
   enough to set `Proposed`. Fill every required field before saving the file;
   if a required evidence field cannot be completed honestly, do not create the
   candidate.
4. Set a review cadence: review now, observe until another same-class episode,
   revisit after the next matching closeout, or leave unproposed if no new
   evidence appears.
5. Quote or summarize concrete evidence without importing whole transcripts.
6. Keep the proposed change smaller than the episode that produced it.
7. End by stating whether the candidate should be reviewed now or observed for
   more evidence.

Do not edit the target surface in draft mode.

## Review Mode

When reviewing an existing candidate:

1. Record the candidate's current status before choosing a lifecycle branch.
2. If the candidate is `Promoted`, treat review as a no-op evidence check and
   end with `RESULT: candidate-unchanged`; route reversals or follow-up
   behavior changes through a new story or candidate.
3. If the candidate is `Accepted`, do not promote or dismiss it from review
   mode. Report whether it is ready for promote mode or blocked on missing
   required fields, target, action, or validation fields.
4. If the candidate is `Dismissed`, stop unless fresh evidence justifies
   reopening it to `Draft` or `Proposed`; do not accept or promote a reopened
   candidate in the same operation.
5. Re-check the source evidence.
6. Apply the rejection rules from `/learning-review`.
7. Check that every required field is present before moving a candidate to
   `Proposed` or reporting an `Accepted` candidate ready for promotion. If
   fields are missing, keep it as `Draft` when possible, name the missing
   fields, and end with `RESULT: candidate-updated` or `RESULT: blocked`
   depending on whether the file changed.
8. Decide one of:
   - keep as `Draft` and name the missing evidence
   - move to `Proposed` and ask Cam to accept or dismiss it
   - move an already `Proposed` candidate to `Dismissed` with a short reason
9. Update the candidate's decision history.

Review does not promote.

## Accept Or Dismiss Mode

When Cam explicitly accepts or dismisses a specific candidate:

1. Re-read the candidate and record its current status before choosing a
   lifecycle branch.
2. If the candidate is `Draft`, review it first. For either an accept or
   dismiss request, move it to `Proposed` only when the evidence supports
   proposal, then stop and ask Cam to accept or dismiss that proposed
   candidate. If the evidence does not support proposal, keep it as `Draft`,
   record why it is not proposal-ready, and do not move it to `Dismissed`,
   `Accepted`, or `Promoted` in the same operation.
3. If the candidate is `Dismissed`, stop unless fresh evidence in the current
   episode justifies reopening it to `Draft` or `Proposed`; do not accept or
   promote a reopened candidate in the same operation.
4. If the candidate is already `Accepted`, treat another accept request as a
   no-op decision-history note and end with `RESULT: candidate-unchanged`
   unless the current request also explicitly asks for promotion; in that case,
   record the instruction and continue through Promote Mode. A dismiss request
   may move it to `Dismissed` only before promotion and only when Cam explicitly
   reverses acceptance.
5. If the candidate is `Promoted`, do not move it back to `Dismissed` from this
   mode; end with `RESULT: candidate-unchanged` and route reversals or
   follow-up behavior changes through a new story or candidate.
6. Move a `Proposed` candidate to `Accepted` only when every required field is
   present. If required fields are missing, stop with `RESULT: blocked` and
   `Live changes: none`. A `Proposed` candidate may still move to `Dismissed`
   when Cam or validation rejects it.
7. Record the user instruction, date, and short rationale in decision history.
8. Do not edit the target surface or promote from accept/dismiss mode. If Cam
   explicitly requested acceptance and promotion in the same turn, first record
   the accepted state, then continue through Promote Mode and end with the
   promotion, blocked, or unchanged output contract.

## Promote Mode

Promote only after the candidate is `Accepted`. If the current request asks to
promote a `Proposed` candidate without also explicitly accepting it, stop with
`RESULT: blocked`; live changes require acceptance first. If Cam explicitly
instructs both acceptance and promotion for a `Proposed` candidate in the
current turn, first record that instruction as acceptance in the candidate's
decision history, move the candidate to `Accepted`, and then promote only if
the artifact has a clear target surface, promotion gate, promotion action,
validation plan, and all other required fields. If the candidate is `Draft`,
review it first and ask for acceptance before promotion. If the
candidate is `Dismissed`, stop; if fresh evidence warrants reopening, move it
back to `Draft` or `Proposed` and require a later acceptance before promotion.
If the candidate is already `Promoted`, do not reapply live changes; report the
existing promotion evidence with `RESULT: candidate-unchanged` and stop.
If required fields, target, action, or validation fields are missing, update the
candidate first or stop with a blocker; do not patch live behavior from an
underspecified candidate.

Promotion means applying the approved change to the target surface through the
smallest honest workflow:

- skill patch: edit the named `.agents/skills/<name>/SKILL.md`, sync generated
  wrappers if needed, and run the repo-native skill wrapper check.
- runbook or methodology doc: patch the named doc and run the relevant repo
  checks.
- local planning or scout note: create or update the repo-local artifact and route any
  follow-up as a story or inbox note.
- outside-this-repo changes are not a promotion target for this repo-local
  workflow; report the routing need instead.

After promotion, update the candidate to `Promoted` and link the commit, story,
diff, or validation evidence that proves live behavior changed.

## Output Contract

End with exactly one result block.

For a draft request that is not warranted:

```text
RESULT: draft-not-warranted
Reason: <one sentence>
Evidence checked: <short list>
Live changes: none
```

For candidate artifact changes:

```text
RESULT: candidate-updated
Action: <drafted | reviewed | reopened | accepted | dismissed>
Candidate: <path>
Status: <Draft | Proposed | Accepted | Dismissed>
Live changes: none
Next step: <review, observe, accept/dismiss, promote, or none>
```

For no-op lifecycle requests:

```text
RESULT: candidate-unchanged
Reason: <already accepted, already promoted, dismissed without fresh evidence, or no supported transition>
Candidate: <path>
Status: <Draft | Proposed | Accepted | Dismissed | Promoted>
Live changes: none
Next step: <review, observe, accept/dismiss, promote, new story/candidate, or none>
```

For promotion:

```text
RESULT: candidate-promoted
Candidate: <path>
Target surface: <path or surface name>
Live changes: <short summary>
Checks run: <short list>
Evidence linked: <commit, story, diff, or validation evidence>
```

For a blocked candidate operation:

```text
RESULT: blocked
Blocker: <missing candidate, evidence, approval, required fields, target, promotion action, or validation plan>
Live changes: none
Recommended next step: <smallest honest unblock>
```

## Guardrails

- Do not draft multiple candidates from one episode unless the targets and
  evidence are genuinely distinct.
- Do not accept or promote based on agent confidence alone.
- Do not use candidates as a substitute for fixing the current bug.
- Do not turn every successful procedure into methodology.
- Do not promote cross-project methodology without a Conductor alignment or
  story route and explicit approval.
