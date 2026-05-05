---
name: learning-review
description: Decide whether a completed work episode revealed a durable workflow-learning candidate, with a strict no-candidate default
user-invocable: true
---

# /learning-review [completed-work-episode]

Use this only at the end of a bounded work episode when there is concrete
evidence that this project's workflow may need to learn from what just happened.

This is a detector. It does not edit live skills, `AGENTS.md`, methodology
docs, candidate files, or other project repos. When a candidate is warranted,
hand the finding to `/learning-candidate`.

## Eligible Triggers

Run this detector after:

- `/validate` when validation found material issues, repeated closeout friction,
  a surprising pass/fail result, or a user correction.
- `/finish-and-push` after a full landing run only when the landing exposed
  material check failures, repeated handoff friction, a user correction, a
  surprising result, or a clearly reusable procedure; or after a stopped
  landing with a clear recurring process gap.
- `/loop-verify` when a loop found material repeated issues, blockers,
  non-convergence, a user correction, a missing guardrail, or a reusable
  verification procedure. Do not run it for ordinary material fixes that only
  prove the current loop did useful work.
- `/build-story` only when the build was noisy, failed, widened unexpectedly,
  or exposed a missing guardrail.
- an explicit user correction that appears reusable beyond the current turn.

Do not run it for ordinary successful work unless the user explicitly asks.

## Default Result

Default to:

```text
RESULT: no-candidate
```

The burden of proof is on drafting a candidate, not on saying no.

## Evidence Thresholds

A candidate may be warranted when at least one of these is true:

- A user correction states or implies a reusable workflow rule.
- The same class of friction appears across two or more recent episodes.
- A high-risk process miss occurred, even once, and a small guardrail would have
  prevented it.
- A repeated procedure clearly saved time and should be available to future
  agents.
- Existing skill or methodology wording caused an agent to choose the wrong
  surface, skip a required check, over-broaden scope, or misstate completion.
- A closeout, validation, or handoff expectation was unclear enough that future
  agents are likely to repeat the mistake.

## Rejection Rules

Reject candidate drafting when the only support is:

- novelty: "this was interesting"
- vibes: "this felt useful"
- one clean success
- a one-off workaround for a local incident
- generic process advice with no project-specific target
- wording preference without an explicit user correction or repeated pattern
- model-era compensation that mainly papers over current-model weakness and is
  likely to become obsolete after a model upgrade
- an already-covered rule in the active skill, `AGENTS.md`, story loop, or
  repo-local guidance

Snapshot-bias check: ask whether the proposed change would still help if the
next best model were substantially better at instruction following, tool use,
and planning. If the answer is "probably not," return `no-candidate` unless
the risk is high and the guardrail is tiny.

## Review Inputs

Use the smallest available evidence set:

- the active story, scout, or user request
- the final diff and validation results
- user corrections from the episode
- material findings from `/validate` or `/loop-verify`
- work-log entries and closeout notes
- the relevant skill text when the proposed target is a skill

Do not perform broad repository archaeology unless the finding depends on a
claimed repeated pattern.

## Output Contract

End with exactly one result block.

For no candidate:

```text
RESULT: no-candidate
Reason: <one sentence>
Evidence checked: <short list>
```

For a warranted candidate:

```text
RESULT: candidate-warranted
Target surface: <skill, runbook, ADR, story loop, local planning/scout lane, or none yet>
Trigger class: <user-correction | repeated-friction | high-risk-miss | procedure-discovery | missing-guardrail>
Evidence: <specific source runs, corrections, files, checks, or findings>
Proposed change: <one or two sentences>
Promotion gate: <what must be reviewed or accepted before live behavior changes>
Confidence: <low | medium | high>
Next step: run /learning-candidate to draft the candidate, or explain why drafting should wait
```

For a blocked review:

```text
RESULT: blocked
Blocker: <missing evidence or human decision needed>
Recommended next step: <smallest honest unblock>
```

## Guardrails

- Do not create candidates to make an episode feel productive.
- Do not treat candidate drafting as validation success or story completion.
- Do not promote from this skill.
- Do not change other project repos from this skill.
- Prefer one high-quality candidate over several speculative ones.
- If the candidate target is cross-project methodology, require a Conductor
  alignment or story route and explicit rollout approval before any affected
  project changes.
