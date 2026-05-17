---
name: loop-verify
description: Run a bounded parallel verification loop across a file set, diff slice, or work queue using subagents. Use when the user explicitly wants delegation, parallel review, or a repeated clean-round proof; choose budgeted, docs/ADR, or strict-until-clean mode before launching workers.
user-invocable: true
---

# /loop-verify [task]

Use this to orchestrate parallel verification across a bounded scope without
letting the loop widen or recurse.

## Preconditions

- Use this only when the user explicitly asked for subagents, delegation,
  parallel passes, or a full-loop verify/fix sweep.
- Keep the scope bounded and shardable: file lists, directories, changed-file
  sets, test cases, docs batches, or similarly partitionable work.
- Prefer direct local work instead if the scope is tiny, the required edits are
  tightly coupled, or the main agent can verify the change more cheaply than a
  worker set.
- Do not use this skill from inside another `/loop-verify` worker. Workers run
  one assigned shard pass only.

## Mode Selection

Before launching workers, state the selected mode, budget, materiality gate,
validation tier, and local/upstream boundary. In strict-until-clean mode, also
state the current phase: discovery, systemic-fix, focused-confirmation, or
candidate-close.

### Budgeted Mode

Use this for ordinary broad review/fix work.

- Default budget: one full worker round or roughly 10-15 minutes, whichever
  gives the main agent enough evidence to classify the result honestly.
- Workers may inspect and fix local material issues when write ownership is
  disjoint and the surface is not tightly coupled.
- If the first round finds material issues, classify them and run only the
  narrowest confirmation that fits the budget. If another full round is needed,
  stop with `final state: continuation-needed` and ask Cam to approve the
  continuation.
- Minor-only fixes do not trigger another full round after targeted checks pass.

### Docs/ADR Alignment Mode

Use this for ADR, spec, story, methodology, runbook, and prose alignment work
unless Cam explicitly asks for a strict clean-round proof.

- Default workers to find-only. The main agent applies any fixes so cross-file
  meaning stays coordinated.
- Use narrower documentation materiality. Prose clarity, phrasing, and local
  cleanup are minor unless they change accepted/draft status, contradict a named
  source of truth, break frontmatter, miss an explicit checklist item, desync a
  generated surface, or alter a named cross-file contract.
- If a finding implies related ADRs, specs, stories, generated outputs, target
  repos, or upstream surfaces outside the stated scope, stop and report it as an
  expansion candidate instead of silently editing the wider graph.
- A docs/ADR loop should usually end after one inspection round plus main-agent
  fixes and targeted checks.

### Strict-Until-Clean Mode

Use this only when Cam explicitly asks for a full clean round or when the task is
objectively contract-critical and bounded: executable behavior, tests, scripts,
generated outputs, schemas, API/output contracts, eval correctness, security, or
similarly high-risk validation surfaces.

- Start with a discovery phase before fixing when the risk is cross-cutting:
  portability, privacy, cache identity, manifests, source/user-controlled
  strings, schema/output contracts, security boundaries, generated artifact
  contracts, or other surfaces where one defect class may repeat across files.
- Discovery workers should usually be find-only breadth scanners over disjoint
  threat surfaces, not serial fixers. Their output should be a finding ledger
  grouped by defect class.
- Once a defect class repeats, stop treating each instance as its own loop
  reset. Switch to systemic-fix: map the affected input/output surface, patch
  the class centrally or with one clearly owned implementation slice, then run
  focused confirmation for the whole class.
- Workers may be fix-capable only after discovery when ownership is disjoint and
  the coordinator has identified the class or shard they own.
- Any material fix during candidate-close resets a fresh full pass over the
  original scope. Material fixes before candidate-close reset only the focused
  discovery or confirmation needed for that defect class unless the fix changes
  the overall threat model.
- Continue while material findings are real, convergence is clear, the scope is
  not widening, and validation cost still fits the current phase.
- Stop when a full round is clean, a blocker remains unresolved, findings become
  minor-only, the loop is non-convergent, or continuing would exceed the
  approved scope. Do not keep going just because new adjacent work can be found.

### Validation Tiers

Use validation tiers to avoid paying closeout costs while findings are still
likely.

- Tier 0: direct probes, helper scripts, schema checks, static searches, and
  tiny reproductions.
- Tier 1: focused regression tests for the affected defect class.
- Tier 2: affected suite or package-level checks.
- Tier 3: generated docs, proof artifacts, snapshots, changelog/story updates,
  and other regenerated evidence surfaces.
- Tier 4: full test suite, advisory review, broad evals, deploy smoke, or other
  expensive final confidence signals.

While the finding ledger is still dirty, stay in Tier 0-1 unless a higher tier
is the only way to reproduce the defect. Run Tier 2 only when focused
confirmation is stable enough to justify it. Run Tier 3-4 only in
candidate-close, after discovery and focused confirmation stop producing new
material defect classes.

## Coordinator Defaults

- Default the coordinator to the inherited model and reasoning level. For
  worker agents, choose the cheapest model and reasoning level that can honestly
  inspect the shard. Downshift for mechanical checks, generated wrapper parity,
  typo-only docs cleanup, and other low-risk local work; keep inherited strength
  or escalate reasoning for semantic contracts, API boundaries, security, eval
  correctness, cross-repo rollouts, or anything where a miss would cause
  expensive rework.
- Do not hard-code "best model" as the default for every worker. If you override
  model or reasoning per shard, record the short rationale in the round plan and
  keep the override tied to task risk, not prestige.
- Use fresh agents each round. Do not rely on stale worker context after files
  changed underneath them.
- Before launching workers, close no-longer-needed old agents when practical. If
  old agents later return summaries from a previous task, treat them as
  unrelated noise unless they are explicitly tied to the current round.
- Default to fix-capable workers only for budgeted or strict modes where write
  ownership is disjoint and local effects are contained. Default to find-only
  workers for docs/ADR alignment, shared write surfaces, uncertain ownership, or
  tightly coupled semantic work.
- Treat a round as clean when every worker returns `RESULT: no-issue`, or when
  the only fixes made were clearly minor/local and passed a targeted check.
- Do not chase nits. A loop is for catching material secondary effects, not for
  perfecting every typo, whitespace mark, or phrasing preference.
- Keep coordinator context compact: finding ledger grouped by defect class,
  disposition, touched files, current strict-mode phase, current validation
  tier, and remaining blockers. Do not manually reread huge diffs or logs every
  cycle unless a disposition depends on it.

## Materiality Gate

Before the first round, define what counts as a material finding for this task.
Use these defaults unless the user gives a stricter threshold.

Material findings:

- executable behavior, tests, scripts, generated outputs, or build/validation
  behavior changed
- prompt, skill, API, schema, output-shape, or named cross-file contract changed
- a fix may affect another shard's correctness or interpretation
- a user-visible bug, data-loss risk, security risk, or validation blocker was
  found
- the change invalidates previous evidence gathered in the round

Docs/ADR material findings:

- accepted/draft/deprecated status or decision state is wrong
- frontmatter, indexes, generated outputs, or wrapper surfaces are stale or
  broken
- two in-scope artifacts contradict each other about a named requirement,
  contract, stop condition, or source-of-truth relationship
- an explicit story acceptance item, checklist item, or decision constraint is
  missed
- the current docs would route future work to the wrong repo, wrong owner,
  unsafe execution path, or obsolete behavior

Minor findings:

- typo, grammar, whitespace, line wrapping, or formatting cleanup
- wording clarity that does not change the contract, ranking, routing, accepted
  behavior, or expected output
- strictly local documentation cleanup with no generated or cross-file effect
- already-equivalent code style cleanup that local checks cover

Minor findings may be fixed, but they do not make the round fail by themselves.
Use a targeted check for the touched shard, then continue to final validation.
If a worker finds one minor issue, or a small bounded set of minor issues, that
usually should not trigger another full round. If a worker finds many minor
issues, it should fix only the obvious bounded set or report the pattern.

## Finding Disposition

Keep a concise finding ledger for every worker report or verifier signal that
claims an issue:

- `accepted`: a real in-scope defect, regression, missed contract, or material
  validation gap that must be fixed or reported as a blocker
- `rejected`: not actually an issue after checking the real code, docs,
  artifacts, or task contract; record the short reason
- `follow-up`: valid but upstream-owned, expansion work, or outside the current
  loop scope

Group accepted findings by defect class when the same kind of issue appears in
multiple places. A repeated class is a signal to patch the class systemically,
not to keep running instance-by-instance reset loops.

Treat model or worker findings as evidence, not truth. The coordinator owns the
final disposition and should verify findings against the scoped task before
fixing or resetting the loop.

When the scoped verifier is clean, stop. Do not run extra loop rounds only to
get nicer wording, a redundant second opinion, or a stronger-sounding closeout
line. Escalate to `/validate` for closure judgment; do not turn `/loop-verify`
into story closure.

## Non-Convergence And Systemic Audit Trigger

Stop the normal loop and switch to `final state: systemic-audit-needed` or
`final state: non-convergent` when the loop shows that it is still mapping the
defect landscape rather than closing a candidate:

- two consecutive passes find same-class material issues
- two material resets happen without narrowing the remaining risk
- workers keep finding new instances after a class-level pattern is already
  visible
- the scope expands beyond the original threat model, owner boundary, or
  approved file/output surface
- candidate validation becomes more expensive than another discovery pass is
  likely to justify
- full-suite, proof-generation, docs, changelog, or methodology work is being
  repeated after non-final fixes

When this triggers, stop fixing instance by instance. Report the defect class,
known affected surfaces, local impact, focused probes already run, and the
smallest recommended systemic audit or follow-up story. If local work can still
be validated independently, separate that from the systemic follow-up.

## Upstream And Expansion Boundary

Before launching workers and while classifying findings, state the boundary
between the current repo/scope and any upstream, outside-owned, or expansion
surface.

Upstream-owned findings include:

- the root cause is in another tracked repo, provider, external tool, source
  artifact, or service that is not in the current loop scope
- the current repo can only paper over the issue rather than fix it honestly
- validation depends on a dependency, fixture, generated artifact, or upstream
  contract that is already wrong
- fixing the issue would require editing a target repo that has not been placed
  in an explicit dedicated worktree for this task

Expansion findings include:

- fixing the issue would require related ADRs, specs, stories, runbooks, or
  generated outputs not named in the original scope
- the worker discovered a new project lane or follow-up story rather than a
  defect in its assigned shard
- the finding is valid but belongs to a later route, not the current loop

When a worker finds an upstream-owned or expansion issue:

- do not let the worker broaden into that repo, service, doc graph, or surface
- require the worker to report the surface, evidence, local impact, and whether
  any local work can still be validated independently
- stop as `blocked` if the issue prevents honest local verification
- otherwise continue only the local loop, keep a concise upstream/expansion
  issue list, and finish when the current scope has no further material local
  issues
- if the surface is a repo Cam controls, name the repo/path and the smallest
  suggested follow-up route; do not claim it is fixed until that repo receives
  its own scoped work

## Round Protocol

1. Define the exact scope.
   - Name the task in one sentence.
   - Select `budgeted`, `docs/ADR alignment`, or `strict-until-clean` mode.
   - State the budget, continuation rule, validation tier, and, for strict
     mode, the current phase.
   - List the files, paths, or items in scope.
   - Decide the sharding plan before launching agents.
   - State what is in-bounds local work and what should be reported as
     upstream-owned or expansion work instead of fixed inside this loop.
2. Partition into disjoint ownership.
   - Give each worker a unique shard.
   - Avoid overlapping write ownership inside a round.
   - For docs/ADR alignment or shared semantic surfaces, use find-only workers
     and let the main agent apply coordinated fixes.
   - For strict-mode discovery over cross-cutting contracts, shard by threat
     surface or data flow first and default workers to find-only.
   - If a cross-cutting rule touches all files, still shard by file set and let a
     later approved round catch secondary effects.
3. Record the baseline.
   - Inspect `git status --short` and the relevant diff so the round's changes
     are easy to attribute.
4. Launch the worker set in parallel.
   - Use `spawn_agent` with worker agents only when the user requested
     delegation and the task is large enough to justify it.
   - Tell each worker it is not alone in the codebase, it must not revert
     others' edits, and it owns only its assigned shard.
   - Tell each worker this is a single-pass shard assignment: do not invoke
     `/loop-verify`, do not spawn subagents, do not widen scope, and do not
     continue into another round.
   - Instruct each worker to focus on material issues, fix bounded minor issues
     only when assigned fix-capable ownership and the fix is obvious, and
     otherwise return `RESULT: no-issue`.
5. Wait for round results and classify them.
   - `RESULT: fixed` means the worker made a real corrective change, or it
     surfaced a real issue that the main agent then fixed before the round ended.
   - `RESULT: no-issue` means no real problem was found in that shard.
   - `RESULT: blocked` means the worker hit a real ambiguity, shared-surface
     conflict, upstream-owned issue, expansion finding, or required human
     judgment.
   - Record each issue's defect class, disposition, affected surface, and
     validation tier.
6. Decide whether the loop resets or stops.
   - If any shard is `RESULT: blocked` and the blocker is still unresolved at
     the end of the round, stop and report the blocker unless the main agent can
     resolve it locally without widening scope.
   - For every `RESULT: fixed`, classify the change as material or minor.
   - In strict-until-clean mode, run discovery before candidate-close for
     cross-cutting contracts. Repeated same-class findings switch to
     systemic-fix instead of another full reset. Candidate-close material fixes
     reset the full original scope if the loop is still converging and still
     inside the approved task.
   - In budgeted mode, run at most the confirmation that fits the stated budget;
     if another full pass is needed, stop with `final state:
     continuation-needed`.
   - In docs/ADR alignment mode, do not reset the full loop for prose or related
     doc-graph expansion. Main-agent fixes plus targeted checks are usually the
     honest close.
   - Minor fixes do not automatically reset the loop. Accept them when the
     secondary effect is confined to that shard and a targeted check passes.
   - If all shards are `RESULT: no-issue`, stop the loop and run the narrowest
     final validation appropriate to the current tier and mode.
7. Rebuild context before any approved next round.
   - Refresh `git status --short`, diffs, and any generated surfaces affected by
     the prior round.
   - Start fresh workers for the next full pass rather than reusing prior-round
     threads.

## Worker Prompt Contract

Require every worker to end with exactly one status line:

- `RESULT: fixed`
- `RESULT: no-issue`
- `RESULT: blocked`

Require each worker report to include:

- the files inspected
- the files changed, if any
- a terse explanation of the issue, blocker, upstream finding, or expansion
  finding
- the defect class and affected surface for each finding
- any checks run
- whether each fix was material or minor

Use a fix-capable prompt shape like:

```text
You are one worker in a single-pass verification round.

You own only:
- path/a
- path/b

Task: inspect your shard for material issues related to <goal>. Fix material
issues only when they are local to your shard and your ownership is disjoint.
You may fix obvious bounded typos or formatting issues, but do not hunt for
nits or broaden into cleanup.

You are not alone in the codebase; do not revert others' edits. Do not widen
scope. Do not invoke /loop-verify. Do not spawn subagents. Do not start another
round.

If the root cause appears upstream, outside the current repo, outside your
assigned shard, or in related docs/stories/ADRs not named above, report the
surface, evidence, and local impact instead of fixing outside your scope.

End with exactly one of RESULT: fixed, RESULT: no-issue, or RESULT: blocked.
List changed files, checks run, each finding's defect class and affected
surface, and whether each fix was material or minor.
```

Use a find-only prompt shape like:

```text
You are one worker in a single-pass inspect-only verification round.

You own only:
- path/a
- path/b

Task: inspect your shard for material issues related to <goal>. Do not edit
files. Do not widen scope. Do not invoke /loop-verify. Do not spawn subagents.
Do not start another round.

Report only material findings under this gate: <materiality gate>. Treat prose
clarity, style, wording preference, typos, and formatting as minor unless they
change the named contract or proof surface.

End with exactly one of RESULT: fixed, RESULT: no-issue, or RESULT: blocked.
Because this is inspect-only, use RESULT: fixed only if the main agent fixed a
reported issue before the round ended. List files inspected, checks run, and
each finding's defect class and affected surface.
```

## Examples

```text
/loop-verify Check these 40 markdown files for broken internal links. Use
budgeted mode: one full pass, fix local broken links only, and report any wider
doc-graph cleanup as follow-up. Do not rerun only because a typo or wrapping nit
was fixed.
```

```text
/loop-verify Review all changed TypeScript files for real type-safety or lint
issues. Use strict-until-clean mode because the diff changes API behavior. Shard
the work across fix-capable subagents, rerun the full changed-file set after
material fixes while the loop is converging, and stop for blockers or scope
expansion.
```

```text
/loop-verify Review the portable bundle contract for privacy-safe source strings
and manifest-declared files. Use strict-until-clean mode, starting with
find-only discovery across input strings, generated manifests, cache identity,
and exported artifact metadata. Stay in Tier 0-1 while findings are likely,
switch to systemic-fix if a defect class repeats, and run generated proofs/full
suites only after candidate-close.
```

```text
/loop-verify Review these ADR and spec files for contradictions about the
source-model contract. Use docs/ADR alignment mode: find-only workers, no
recursive agents, main-agent fixes, and stop if the review discovers related
stories or ADRs outside the named files.
```

## Main-Agent Responsibilities

- Orchestrate the loop instead of redoing every shard review personally.
- Choose and state the mode, budget, materiality gate, and boundary before
  launching workers.
- Review returned diffs briefly before accepting them.
- Keep a round summary with shard, status, changed files, and any blocker.
- Keep a finding ledger grouped by defect class with accepted/rejected/follow-up
  disposition, affected surfaces, touched files, current validation tier, and
  remaining blockers.
- Classify every fix as material or minor before deciding whether the loop
  resets, stops, or needs explicit continuation.
- Apply docs/ADR alignment fixes directly when workers are find-only.
- Run the narrowest honest validation after the final clean, budgeted, blocked,
  or continuation-needed state.
- In strict-until-clean mode, keep Tier 3-4 closeout work frozen until
  candidate-close unless a higher tier is required to reproduce the defect.
- Stop and report non-convergence if repeated rounds keep generating new issues
  because the scope is too coupled, workers are interfering indirectly, or
  verification is discovering new work beyond the intended scope.
- Stop instead of burning time when repeated rounds are only producing nits.
- In strict-until-clean mode, continue only while repeated rounds are producing
  solid material fixes and the results are converging inside the approved scope.

## Output Shape

- scope
- mode, strict-mode phase when applicable, budget, and validation tier
- round count
- per-round status summary
- finding ledger grouped by defect class with accepted/rejected/follow-up
  disposition
- materiality decision for any `RESULT: fixed`
- upstream-owned findings, expansion findings, or blockers, if any, with the
  local impact and suggested follow-up route
- final state: converged, budget-complete, continuation-needed, blocked,
  systemic-audit-needed, or non-convergent
- checks run
- learning-review result when the loop exposed material repeated issues,
  blockers, non-convergence, explicit user correction, missing guardrail, or a
  reusable verification procedure; omit this for ordinary clean or minor-only
  loops. If the detector returns `candidate-warranted`, report or draft through
  `/learning-candidate` only.

## Guardrails

- Do not use this skill as an excuse to spawn agents for trivial work.
- Do not let workers invoke `/loop-verify`, spawn their own subagents, or run
  nested verification loops.
- Do not mark a strict-until-clean round clean if any material fix occurred
  anywhere in that round.
- Do not keep rerunning local shards when the remaining failure is upstream
  owned and outside the current loop scope. Stop blocked, or finish with a
  clearly separated upstream issue list if local verification can still close
  honestly.
- Do not mutate upstream repos, provider config, source artifacts, or external
  services from inside a local loop unless the task explicitly includes that
  upstream surface and a dedicated worktree or safe execution path exists.
- Do not reset the full loop for harmless typo/formatting fixes once their local
  check has passed.
- Do not ask workers to exhaustively polish prose, formatting, comments, or
  style unless that is the user's explicit task.
- Do not continue a budgeted loop past its budget without explicit continuation
  approval.
- Do not continue a docs/ADR loop when the review is discovering new related
  alignment work beyond the intended scope; report the expansion instead.
- Do not run generated docs, proof artifacts, changelog/story closeout,
  methodology compile, full suites, or advisory review after every dirty strict
  pass. Save Tier 3-4 work for candidate-close unless it is required to
  reproduce the defect.
- Do not keep doing instance-by-instance fixes after repeated same-class
  findings show that the honest next step is systemic audit or a class-level
  patch.
- Do not let workers fight over the same files.
- Do not ignore secondary effects from earlier fixes in strict-until-clean mode;
  rerunning the full loop is the point when the approved task needs that proof.
- Do not continue indefinitely when the loop is oscillating, widening, or only
  finding adjacent work; say it did not converge cleanly.
- Do not draft learning candidates from loop novelty alone. Use
  `/learning-review` only when the loop shows a durable workflow correction,
  repeated same-class issue, explicit user correction, missing guardrail,
  high-risk miss, or reusable verification pattern.
- Do not promote candidates as part of ordinary loop closeout. Promotion
  requires separate Cam approval after the candidate evidence has been reviewed.
