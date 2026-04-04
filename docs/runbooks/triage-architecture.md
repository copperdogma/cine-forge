# Architecture Triage

## Context

Use this runbook when the question is whether the repo needs a structural
simplification pass rather than a new feature or eval iteration.

This is the operational companion to `/triage-architecture`.

## Why This Exists

Feature work naturally accumulates architecture drift:

- wrappers instead of deletion
- duplicate ownership instead of re-homing
- stale compatibility paths that survive too long
- large files that stay large because no one reclaims boundaries

The architecture-audit lane gives that drift a cadence, memory, and a bounded
target surface. It is not a free-form "make the repo nicer" ritual.

## Inputs

- `docs/methodology/state.yaml` `architecture_audits`
- `docs/methodology/graph.json`
- recent story churn
- recent validation/work-log drift signals
- relevant ADRs/spec slices for the chosen domain

## Due Signals

Treat an architecture audit as due when one or more of these hold:

- `manual_priority` is high
- `open_findings` already exist for the domain
- `stories_since_audit` meets or exceeds the target cadence
- the domain has recent churn but no prior audit
- validation keeps surfacing the same drift pattern
- performance pain or repeated bug-fix churn points back to structure

If none apply strongly, a no-op audit is acceptable. The lane should stay
honest, not busy.

## Domain Selection

Audit domains should be bounded code-ownership surfaces, not vague ideas and
not merely spec categories. CineForge's seeded audit domains are:

- `methodology_tooling`
- `driver_and_runtime`
- `ingest_and_world_building`
- `api_service_and_operator_console`
- `creative_direction_and_chat`
- `generation_and_visualization`

Do not expand the domain list casually. New domains should correspond to real
ownership boundaries that make repeated audits more targeted.

## Audit Procedure

1. Read the methodology frame
   - `docs/ideal.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`

2. Read the chosen domain state
   - last audit date
   - open findings
   - recent story refs
   - any result/summary fields

3. Read recent evidence
   - recent story files in `recent_story_refs`
   - recent validation notes if they flagged drift
   - relevant ADRs/spec slices

4. Inspect current code reality
   - hotspot files
   - churn concentration
   - duplicate ownership
   - stale wrappers/shims
   - structural causes of performance or complexity pain

5. Decide one output
   - no action
   - follow-up story
   - fold into existing story
   - decision escalation

6. Record the result
   - update `docs/methodology/state.yaml`
   - rerun `pnpm methodology:compile`
   - do not create implementation artifacts unless explicitly approved

## Validation Feed

`/validate` is the main feeder into this lane.

When validation finds medium/high drift signals that do not belong to the
current story's shipping slice, it should:

- map the signal to a best-fit `architecture_audits` domain
- cite the story/work-log source
- recommend `/triage-architecture` when the issue is real but not in scope to
  fix immediately

`/triage-architecture` then decides whether to record that finding in state,
clear it as a no-op, or spin it into concrete follow-up work.

## Boundaries

### Always do

- prefer delete / merge / re-home / simplify
- keep audits bounded to 1-2 domains
- record a no-op when that is the honest answer

### Ask first

- before creating a new story from the audit
- before changing audit domains materially
- before escalating to a new ADR

### Never do

- never do repo-wide undirected audits
- never propose a new architecture just because refactoring sounds nice
- never keep stale findings alive after they were disproven
- never use this lane to justify speculative churn
