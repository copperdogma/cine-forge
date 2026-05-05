---
name: loop-verify
description: Run a bounded parallel verification-and-fix loop across a file set, diff slice, or work queue using subagents in repeated full rounds. Use when the user explicitly wants delegation, subagents, or parallel review/fix work, especially for requests like checking many files, sharded audits, or repeated sweeps where material fixes should trigger another full pass until a complete round finds no material issues.
user-invocable: true
---

# /loop-verify [task]

Use this to orchestrate repeated parallel verification across a bounded scope.

## Preconditions

- Use this only when the user explicitly asked for subagents, delegation,
  parallel passes, or a full-loop verify/fix sweep.
- Keep the scope bounded and shardable: file lists, directories, changed-file
  sets, test cases, docs batches, or similarly partitionable work.
- Prefer direct local work instead if the scope is tiny or the required edits
  are too tightly coupled to shard honestly.

## Defaults

- Default to worker agents that both inspect and fix their owned scope.
- Default to the inherited model and reasoning level. Only downshift if the
  work is clearly easy and the failure cost is low.
- Use fresh agents each round. Do not rely on stale worker context after files
  changed underneath them.
- Default to fix-capable workers. Only fall back to find-only workers if shared
  write surfaces make delegated edits unsafe.
- Treat a round as clean when every worker returns `RESULT: no-issue`, or when
  the only fixes made were clearly minor/local and passed a targeted check.
- Reset the full loop for material fixes: semantic changes, executable changes,
  contract/API changes, generated-surface changes that could affect other
  shards, or any fix whose secondary effects are not obviously local.
- Do not chase nits indefinitely. A loop is for catching material secondary
  effects, not for perfecting every typo, whitespace mark, or phrasing
  preference.
- Do not impose a fixed round cap. If each round keeps finding solid material
  issues, keep running fresh full rounds until a full round is clean, blocked,
  or clearly non-convergent.

## Materiality Gate

Before starting the first round, define what counts as a material finding for
this task. Use these defaults unless the user gives a stricter threshold.

Material findings:

- executable behavior, tests, scripts, generated outputs, or build/validation
  behavior changed
- prompt, skill, API, schema, output-shape, or cross-file contract changed
- a fix may affect another shard's correctness or interpretation
- a user-visible bug, data-loss risk, security risk, or validation blocker was
  found
- the change invalidates previous evidence gathered in the round

Minor findings:

- typo, grammar, whitespace, line wrapping, or formatting cleanup
- wording clarity that does not change the contract, ranking, or expected
  behavior
- strictly local documentation cleanup with no generated or cross-file effect
- already-equivalent code style cleanup that local checks cover

Minor findings may be fixed, but they do not make the round fail by themselves.
Use a targeted check for the touched shard, then continue to final validation.
If a worker finds one minor issue, or a small bounded set of minor issues, that
usually should not trigger another full round. If a worker finds many minor
issues, it should fix only the obvious bounded set or report the pattern. Do
not start another full round just to hunt for more minor issues.

## Round Protocol

1. Define the exact scope.
   - Name the task in one sentence.
   - List the files, paths, or items in scope.
   - Decide the sharding plan before launching agents.
2. Partition into disjoint ownership.
   - Give each worker a unique shard.
   - Avoid overlapping write ownership inside a round.
   - If a cross-cutting rule touches all files, still shard by file set and let
     the next round catch secondary effects.
3. Record the baseline.
   - Inspect `git status --short` and the relevant diff so the round's changes
     are easy to attribute.
4. Launch a full worker set in parallel.
   - Use `spawn_agent` with worker agents for fix-capable lanes.
   - Tell each worker it is not alone in the codebase, it must not revert
     others' edits, and it owns only its assigned shard.
   - Instruct each worker to focus on material issues, fix bounded minor issues
     only when they are obvious, and otherwise return `RESULT: no-issue`.
   - Tell workers not to broaden into nit-hunting or style cleanup outside the
     task's materiality gate.
5. Wait for round results and classify them.
   - `RESULT: fixed` means the worker made a real corrective change, or it
     surfaced a real issue that the main agent then fixed before the round
     ended.
   - `RESULT: no-issue` means no real problem was found in that shard.
   - `RESULT: blocked` means the worker hit a real ambiguity, shared-surface
     conflict, or required human judgment.
6. Decide whether the loop resets.
   - If any shard is `RESULT: blocked` and the blocker is still unresolved at
     the end of the round, the round is blocked even if other shards returned
     `RESULT: fixed`.
   - For every `RESULT: fixed`, classify the change as material or minor.
   - If any shard made a material fix, rerun the entire round across the full
     original scope.
   - If the main agent had to land a material fix because of a worker finding,
     that also resets the loop.
   - Minor fixes do not automatically reset the loop. Accept them only when the
     secondary effect is obviously confined to that shard and a targeted check
     passes.
   - If a round contains only minor fixes, do not launch another full round
     unless those minor fixes exposed a broader material pattern.
   - Do not stop just because the loop has run many rounds. Ten rounds is
     acceptable if each round keeps finding solid material issues and the work
     is still converging.
   - If all shards are `RESULT: no-issue`, stop the loop and run final
     top-level validation.
   - If any shard is `RESULT: blocked`, stop and report the blocker unless the
     main agent can resolve it locally without widening scope.
7. Rebuild context before the next round.
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
- a terse explanation of the issue or blocker
- any checks run

Use a prompt shape like:

```text
Use $loop-verify for this shard.

You own only:
- path/a
- path/b

Task: inspect your shard for material issues related to <goal>. Fix material
issues that are local to your shard. You may fix obvious bounded typos or
formatting issues, but do not hunt for nits or broaden into cleanup. Do not
widen scope. You are not alone in the codebase; do not revert others' edits.
End with exactly one of RESULT: fixed, RESULT: no-issue, or RESULT: blocked.
List files inspected, changed files, checks run, and whether each fix was
material or minor.
```

## Main-Agent Responsibilities

- Orchestrate the loop instead of redoing every shard review personally.
- Review returned diffs briefly before accepting them.
- Keep a round summary with shard, status, changed files, and any blocker.
- Classify every fix as material or minor before deciding whether the loop
  resets.
- Run the narrowest honest validation after the final clean round.
- Stop and report non-convergence if repeated rounds keep generating new issues
  because the scope is too coupled or workers are interfering indirectly.
- Stop instead of burning time when repeated rounds are only producing nits.
- Continue instead of stopping when repeated rounds are still producing solid
  material fixes and the results are converging.

## Output Shape

- scope
- round count
- per-round status summary
- materiality decision for any `RESULT: fixed`
- final state: converged, blocked, or non-convergent
- checks run


## Reviewed Learning Hook

At loop closeout, run or explicitly consider `/learning-review` only when the
loop exposed material repeated issues, blockers, non-convergence, an explicit
user correction, a missing guardrail, a high-risk miss, or a reusable
verification procedure. Omit it for ordinary clean loops, minor-only loops, or
material fixes that only prove the current loop did useful work. If it returns
`RESULT: candidate-warranted`, report the finding or draft it through
`/learning-candidate`; do not promote candidates as part of loop closeout.

## Guardrails

- Do not use this skill as an excuse to spawn agents for trivial work.
- Do not mark a round clean if any material fix occurred anywhere in that
  round.
- Do not reset the full loop for harmless typo/formatting fixes once their
  local check has passed.
- Do not ask workers to exhaustively polish prose, formatting, comments, or
  style unless that is the user's explicit task.
- Do not use a hard maximum round count. Stop for cleanliness, unresolved
  blockers, non-convergence, or minor-only results; do not stop only because a
  number of rounds has been reached.
- Do not let workers fight over the same files.
- Do not ignore secondary effects from earlier fixes; rerunning the full loop is
  the point.
- Do not continue indefinitely when the loop is oscillating or widening; say it
  did not converge cleanly.
