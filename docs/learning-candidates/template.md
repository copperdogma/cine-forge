---
title: ""
status: "Draft"
created: "YYYY-MM-DD"
target_surface: ""
trigger_class: ""
review_cadence: ""
confidence: "low"
source_runs: []
user_corrections: ["none recorded"]
evidence_summary: ""
evidence: []
proposed_change: ""
promotion_gate: ""
---

# Candidate - <Title>

## Summary

One or two sentences describing the workflow correction.

## Evidence

- Evidence summary:
- Source run, user correction, story, scout, validation finding, or loop result.

## Source Runs And User Corrections

- Source runs:
- User corrections: none recorded

## Required Evidence Gate

- Concrete source provenance present?
- Evidence summary present?
- User-correction evidence quoted/summarized, or explicitly `none recorded`?
- Draft, propose, accept, or promote? No unless concrete source provenance and a
  source-backed evidence summary are present. Do not invent evidence to satisfy
  the template.

## Trigger And Cadence

- Trigger class:
- Review cadence:

## Lifecycle State

- Current status:
- Allowed next transition:
- Live changes in this candidate operation: none unless an `Accepted` candidate
  is being promoted with separate Cam approval.
- Accepted-state check: `Accepted` can move to `Dismissed` before promotion
  only when Cam explicitly reverses acceptance.
- Terminal-state check: `Dismissed` requires fresh evidence before reopening,
  and `Promoted` must not apply the same live change again.

## Observed Pattern

Describe what keeps going wrong or what repeatable procedure was discovered.

## Proposed Change

State the smallest live change that could prevent the problem or preserve the
useful procedure.

## Why It Matters

Explain the future work or risk this would reduce.

## Rejection Checks

- Novelty only?
- Vibes only?
- One-off success?
- Generic process advice?
- Model-era compensation likely to go stale?
- Already covered by an existing skill, doc, or repo-local guidance?

## Promotion Gate

What must Cam accept, verify, or decide before this changes live behavior?

## Promotion Action

Which exact file, skill, story, planning note, or repo-local workflow would be
changed after acceptance?

## Validation Plan

Which checks or manual inspection should prove the promoted change is safe?

## Decision History

- `YYYY-MM-DD` — Drafted from `<source>`.
