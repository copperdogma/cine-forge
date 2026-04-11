---
name: loop-verify
description: Run a bounded parallel verification-and-fix loop across a file set, diff slice, or work queue using subagents in repeated full rounds. Use when the user explicitly wants delegation, subagents, or parallel review/fix work, especially for requests like checking many files, sharded audits, or repeated sweeps where any real fix should trigger another full pass until an entire round finds no more issues.
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
- Treat a round as clean only when every worker returns `RESULT: no-issue` and
  the main agent did not apply any substantiated fix after reviewing worker
  output.

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
   - Instruct each worker to fix real local issues directly and otherwise
     return `RESULT: no-issue`.
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
   - If any shard is `RESULT: fixed`, rerun the entire round across the full
     original scope.
   - If the main agent had to land a real fix because of a worker finding, that
     also resets the loop.
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

Task: inspect your shard for real issues related to <goal>. Fix any issue that
is local to your shard. Do not widen scope. You are not alone in the codebase;
do not revert others' edits. End with exactly one of RESULT: fixed,
RESULT: no-issue, or RESULT: blocked. List changed files and checks run.
```

## Examples

```text
/loop-verify Check these 40 markdown files for broken internal links and fix
any local issues you find with parallel subagents. If any shard makes a real
fix, rerun the full pass across all 40 files until one complete round comes
back clean.
```

```text
/loop-verify Review all changed TypeScript files for real type-safety or lint
issues. Shard the work across subagents that can fix their own files, and keep
looping over the full changed-file set until every shard reports no issue.
```

## Main-Agent Responsibilities

- Orchestrate the loop instead of redoing every shard review personally.
- Review returned diffs briefly before accepting them.
- Keep a round summary with shard, status, changed files, and any blocker.
- Run the narrowest honest validation after the final clean round.
- Stop and report non-convergence if repeated rounds keep generating new issues
  because the scope is too coupled or workers are interfering indirectly.

## Output Shape

- scope
- round count
- per-round status summary
- final state: converged, blocked, or non-convergent
- checks run

## Guardrails

- Do not use this skill as an excuse to spawn agents for trivial work.
- Do not mark a round clean if any real fix occurred anywhere in that round.
- Do not let workers fight over the same files.
- Do not ignore secondary effects from earlier fixes; rerunning the full loop is
  the point.
- Do not continue indefinitely when the loop is oscillating or widening; say it
  did not converge cleanly.
