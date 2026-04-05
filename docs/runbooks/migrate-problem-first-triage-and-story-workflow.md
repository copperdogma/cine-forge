# Migrate Problem-First Triage and Story Workflow

> Living migration runbook for Story 147.
> Purpose: help other repos adopt the same story-progression, triage-weighting,
> and anti-fragmentation changes without replaying local false starts.
>
> Update rule: only write settled decisions and landed changes here. Do not log
> abandoned options or temporary experiments.

## When To Use This

Use this runbook when a repo already has:

- story files as the canonical execution record
- agent skills or commands for story creation, build, validation, and close-out
- a backlog or triage layer that chooses the next action

This migration is for repos where the current workflow has started to drift into
any of these failure modes:

- coherent work gets split into serial micro-stories
- `/build-story` dead-ends on paperwork for stories that are already detailed
  enough to build
- `Draft` or `Pending` story existence gets treated as priority by itself
- a blocked line keeps resurfacing as the "next move" because continuity bias
  outweighs blocked-state truth
- the same eval retry trigger keeps getting treated as fresh work even though
  nothing materially changed
- user-facing functionality gets planned as backend-only stories with no UI
  slice, leaving plumbing progress but no usable feature
- `Rescope then close` pressure encourages premature story closure instead of
  keeping one coherent problem line together

## Settled Direction

### 1. Keep the five-status model

Keep:

- `Draft`
- `Pending`
- `In Progress`
- `Blocked`
- `Done`

The problem is not the existence of five statuses. The problem is dishonest or
high-friction transitions between them.

### 2. Statuses must describe repo reality

- `Draft`: worth preserving, but still incomplete, underspecified, or not yet
  substrate-verified enough to claim build-readiness
- `Pending`: fully fleshed out and honestly buildable now
- `In Progress`: currently being built
- `Blocked`: concrete enough to preserve, but cannot proceed because of a named
  blocker with explicit evidence and an unblock condition
- `Done`: built, validated, and formally closed

`Blocked` must not mean "hard" or "probably later." It must mean "cannot
honestly proceed now because of X."

Blocked-story truth should be inspectable. Add a canonical blocker summary,
blocker evidence, and unblock condition to the story artifact, and surface that
truth in the compiler or generated outputs if the repo uses those surfaces for
triage.

### 3. `/create-story` should choose the honest initial state

`/create-story` should be able to end in:

- `Draft`
- `Pending`
- `Blocked`

based on what it actually finds while fleshing the story out.

Default rule:

- if the story is still rough or missing verified substrate: `Draft`
- if the story is concrete and honestly buildable now: `Pending`
- if the story is concrete enough to preserve but already proven blocked:
  `Blocked`

`/create-story` should also bias toward whole usable slices for user-facing
functionality. If the capability needs a UI to be used or inspected honestly,
the default story shape should include that UI unless the story explicitly
records why the UI is intentionally deferred or owned elsewhere.

This check needs a hard stop, not just advisory wording. If the requested work
still belongs to the same subsystem, validation boundary, and success surface
as an existing story, `/create-story` should stop before bootstrapping a new ID
and return the existing story to expand or reopen instead.

### 4. `/build-story` should promote or block based on evidence

`/build-story` should not hard-stop on a detailed `Draft` story just because
the status label is still `Draft`.

Instead:

- promote `Draft -> Pending` when the story is already detailed enough and the
  substrate check passes
- promote `Pending -> In Progress` when implementation starts
- move `Draft` or `Pending -> Blocked` when exploration proves a real blocker

### 5. Triage must be problem-first, not backlog-first

The existence of a story shell should not create major priority by itself.

Triage should rank:

1. movement toward the Ideal
2. real problem pressure
3. leverage and unblock power
4. readiness
5. cost
6. continuity and momentum

Story existence should act as packaging context and a tie-breaker, not as a
primary value signal.

### 6. Continuity bias is still good

Continuity should remain a positive bias for active or recently advanced work
lines with an unresolved success surface.

Example: if the repo is actively pushing one capability line, triage should
prefer finishing that coherent line over random context switching unless a
clearly higher-leverage problem overrides it.

But continuity stops at blocked-state truth. If a story is `Blocked` and its
unblock condition is still unmet, it should be surfaced as a health flag rather
than the recommended next action.

Eval retry triggers need the same honesty. A `retry_when` condition is a
detector, not a standing backlog item; once the same trigger has already been
checked and found unchanged, it stays exhausted until a materially new trigger
appears.

### 7. Anti-fragmentation rule

Work should stay in one story when it remains in the:

- same subsystem
- same validation boundary
- same success surface

Split into a new story only when the work becomes materially distinct, crosses a
new runtime or ownership seam, or would make validation unclear.

## Consumer Hotspots

These are the typical surfaces that need to move together.

### Policy and operating contract

- `AGENTS.md`
- `docs/spec.md`
- `docs/methodology-ideal-spec-compromise.md`

### Story lifecycle skills

- `triage`
- `triage-stories`
- `create-story`
- `build-story`
- `validate`
- `mark-story-done`

### Templates and generated surfaces

- story template
- methodology graph/compiler
- generated story index / graph output
- targeted regression coverage for the compiler contract

## Migration Procedure

### 1. Audit current failure modes

Record local evidence before changing anything:

- examples of fragmented story chains
- places where story presence is being treated as priority
- places where Draft/Pending friction is blocking obvious work
- places where close-out behavior encourages premature splitting

Do not generalize from intuition alone. Cite local repo evidence.

### 2. Lock the status semantics

Before changing skills, define the exact meaning of:

- `Draft`
- `Pending`
- `In Progress`
- `Blocked`
- `Done`

Also define the legal transitions between them.

### 3. Patch the story template

Add a canonical place for blocked-story recording:

- blocker summary
- blocker evidence
- unblock condition

Do this before teaching agents to emit `Blocked`, so the artifact has somewhere
stable to carry the truth.

### 4. Patch `/create-story`

Make it:

- check whether the requested work actually belongs in an existing story
- stop before bootstrapping a new story ID when the honest move is to expand or
  reopen an existing story
- justify new-story creation when the work touches the same recent problem line
- choose `Draft`, `Pending`, or `Blocked` based on actual research
- default user-facing functionality toward a UI-complete slice instead of a
  backend-only partial, unless the story explicitly records why the UI is not in
  scope

### 5. Patch `/build-story`

Make it:

- auto-promote detailed `Draft` stories when the substrate and sections are ready
- mark stories `Blocked` when exploration proves a real blocker
- stop treating status paperwork as a reason not to continue obviously buildable
  work

### 6. Patch triage

Update both the story leaf and the meta-synthesizer:

- `triage-stories` should recommend continuing, reopening, expanding, or
  consolidating an existing problem line, not only selecting the next story
  shell
- `triage` should weight real leverage and continuity above mere backlog-shell
  existence
- blocked stories with unmet unblock conditions should downgrade to health flags
  instead of recommended next actions
- exhausted eval retry triggers should stay deferred until materially new
  evidence appears

### 7. Patch close-out

Patch both validation and close-out:

- `validate` should stop preferring `Rescope then close` for coherent
  same-surface remaining work
- `mark-story-done` should prefer keeping same-surface work in the current story

Use rescope-and-close only when the remaining work is genuinely separate.

### 8. Update the repo operating contract

Rewrite the repo-level instructions so the written policy matches the tool
behavior.

### 9. Rebuild generated artifacts and tests

If the repo validates statuses, sorts stories by status, or compiles a graph:

- update compiler logic
- update tests
- regenerate generated artifacts

## Certification Checklist

- graph/index/compiler build passes
- graph/index/compiler drift check passes
- story skill or agent-tooling checks pass
- targeted methodology tests pass
- updated generated artifacts were manually inspected
- the migration document reflects landed behavior, not abandoned paths

## Behavior Certification Matrix

Do not certify this migration from clean docs or graph rebuilds alone. Check
the behavior of the workflow against concrete scenarios.

### Required scenarios

1. Rough idea -> `Draft`
   - Input: a user idea or partial scope with missing acceptance criteria,
     missing tasks, or unverified substrate
   - Expected result: `/create-story` preserves it as `Draft`

2. Concrete and buildable -> `Pending`
   - Input: a fleshed-out story with concrete acceptance criteria, tasks, and
     verified enough substrate to build now
   - Expected result: `/create-story` emits `Pending`

3. Concrete but blocked -> `Blocked`
   - Input: a fleshed-out story where research proves a real blocker
   - Expected result: `/create-story` emits `Blocked` and records blocker
     summary, blocker evidence, and unblock condition in the canonical story
     surface

4. Buildable `Draft` -> promote instead of stop
   - Input: `/build-story` is pointed at a `Draft` that is already detailed
     enough and whose substrate check passes
   - Expected result: the workflow promotes it instead of dead-ending on status
     paperwork

5. Proven blocker during build -> `Blocked`
   - Input: `/build-story` exploration finds a blocker that makes the story not
     honestly buildable now
   - Expected result: the workflow records the blocker and marks the story
     `Blocked`

6. Continuity beats unrelated shell
   - Input: triage is comparing an active unresolved work line against an
     unrelated `Draft` or `Pending` shell with similar leverage
   - Expected result: triage preserves continuity on the active work line rather
     than jumping tracks just because another story exists

7. User-facing functionality -> UI-complete story
   - Input: a story for functionality that needs an operator or end-user UI to
     actually exist in a usable sense
   - Expected result: the story includes the UI slice by default, or explicitly
     records why UI is intentionally deferred or owned elsewhere

8. Validation keeps coherent work together
   - Input: `/validate` reviews a story with coherent same-surface remaining work
   - Expected result: it recommends `Keep open` rather than defaulting to
     `Rescope then close`

9. Close-out only splits truly separate work
   - Input: `/mark-story-done` reviews a story whose remaining gaps are either
     same-surface or genuinely separate
   - Expected result: it recommends `Keep open` for the former and uses
     `Rescope then close` only for the latter

10. Same-line request -> no new story ID
    - Input: `/create-story` is asked for work that still belongs to the same
      subsystem, validation boundary, and success surface as an existing story
    - Expected result: it stops before bootstrapping a new story and returns the
      existing story to expand or reopen instead

11. Blocked line -> health flag, not recommendation
    - Input: triage sees a blocked story with a named blocker and an unmet
      unblock condition, plus recent commits or continuity on the same line
    - Expected result: the story stays visible as a health flag, but triage does
      not recommend reopening it as the next move

12. Consumed eval retry trigger stays exhausted
    - Input: the latest eval attempt records `retry_when`, but the same trigger
      was already checked and no materially new model, approach, golden fix,
      architecture change, or dependency exists
    - Expected result: triage-evals reports the item as deferred / exhausted
      instead of ranking it as newly actionable

### Evidence to record

For each repo that lands this migration, record:

- which local files or skills were changed
- which scenario(s) were checked
- where the resulting story/runbook/graph evidence lives
- which scenario, if any, remains partially manual

## CineForge Certification Evidence

Story 147 plus the blocked-line loop hardening follow-on certify the twelve
required scenarios in CineForge with direct local
evidence:

- Rough idea -> `Draft`: `.agents/skills/create-story/SKILL.md`
- Concrete and buildable -> `Pending`: `.agents/skills/create-story/SKILL.md`
- Concrete but blocked -> `Blocked`: `.agents/skills/create-story/SKILL.md`,
  `.agents/skills/create-story/templates/story.md`,
  `scripts/methodology-graph.js`, and `tests/unit/test_methodology_graph.py`
- Buildable `Draft` -> promote instead of stop:
  `.agents/skills/build-story/SKILL.md`
- Proven blocker during build -> `Blocked`:
  `.agents/skills/build-story/SKILL.md`
- Continuity beats unrelated shell:
  `.agents/skills/triage/SKILL.md`,
  `.agents/skills/triage-stories/SKILL.md`, and `docs/runbooks/triage.md`
- User-facing functionality -> UI-complete story:
  `.agents/skills/create-story/SKILL.md` and `AGENTS.md`
- Validation keeps coherent work together:
  `.agents/skills/validate/SKILL.md`
- Close-out only splits truly separate work:
  `.agents/skills/mark-story-done/SKILL.md`
- Same-line request avoids new story ID:
  `.agents/skills/create-story/SKILL.md`
- Blocked line -> health flag, not recommendation:
  `AGENTS.md`, `.agents/skills/triage/SKILL.md`,
  `.agents/skills/triage-stories/SKILL.md`,
  `docs/runbooks/triage.md`, `scripts/methodology-graph.js`,
  `tests/unit/test_methodology_graph.py`, and generated `docs/stories.md`
- Consumed eval retry trigger stays exhausted:
  `.agents/skills/triage-evals/SKILL.md`,
  `.agents/skills/improve-eval/SKILL.md`,
  `docs/runbooks/triage-evals.md`, `docs/evals/README.md`,
  `docs/evals/attempt-template.md`, `docs/evals/registry.yaml`, and
  `docs/evals/attempts/002-video-understanding-google-max-output-budget.md`

## Porting Notes

### Keep

- the five-status model
- problem-first triage
- continuity bias for active work lines
- blocked lines as health flags until their unblock conditions are met
- exhausted eval retry triggers until materially new evidence appears
- blocked-story evidence requirements
- anti-fragmentation defaults

### Adapt per repo

- file paths
- exact skill or command names
- compiler or graph implementation details
- validation commands
- any repo-specific status consumers

## CineForge Landing Log

- 2026-04-04: initial migration runbook created for Story 147 with the settled
  direction, certification matrix, and CineForge evidence map.
- 2026-04-04: landed the CineForge implementation pass across `/triage`,
  `triage-stories`, `/create-story`, `/build-story`, `/validate`,
  `/mark-story-done`, the story template, `AGENTS.md`, `docs/spec.md`,
  `docs/methodology-ideal-spec-compromise.md`, the methodology graph/compiler,
  targeted regression coverage, and the generated planning surfaces so
  blocked-story truth is now inspectable and the workflow is problem-first
  end-to-end.
