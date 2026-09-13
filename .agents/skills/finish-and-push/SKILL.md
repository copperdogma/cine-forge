---
name: finish-and-push
description: Complete, validate, and land current work and linked repo changes. Use for close-out and push requests, or an audit-only readiness review.
user-invocable: true
---

# /finish-and-push [story-number] [--audit-only] [--cleanup]

Complete the requested work, satisfy each owning repo's completion requirements,
and land the validated changes on its remote main branch. Keep this skill shared
across repos; obtain local commands, artifact conventions, and branch policy from
the owning repo's instructions rather than embedding project-specific recipes here.

## Authorization and scope

An execution request invoking this skill authorizes scoped close-out fixes,
story closure when applicable, commits, execution-branch pushes, integration with
the latest remote main, and fast-forward pushes to main in every repo belonging
to the same request. Mentioning or reviewing the skill does not invoke it.
Continue through completion without renewed approval for these actions.

Scope includes the current repo and linked repo worktrees or branches created or
updated for the same user request, story, alignment, or scout, unless the user
narrows it. Establish that relationship from task evidence; other dirty work or
membership in a project registry does not establish scope. Honor explicit branch
targets and repo policies; use the repo's actual remote and main branch names.

`--audit-only` is read-only: inspect and report readiness, gaps, and proposed
fixes without edits, story closure, generation, staging, commits, pushes, or
cleanup. Run checks only if they do not mutate the workspace or external state;
identify any remaining validation needed. This mode takes precedence over
`--cleanup` and all execution instructions below.

## Coordination

The invoking agent owns completion. Delegate bounded, independent work to the
lowest-cost model with demonstrated capability when the expected savings exceed
coordination and verification overhead. Handle small tasks directly. Escalate
ambiguous or consequential decisions to a sufficiently capable model.

Give workers the relevant intent, bounded scope, and evidence to return. Parallel
repo checks and independent reviews are useful candidates. Keep one writer in
charge of each repo's Git state; the coordinator owns scope, integration and
landing decisions, and the final outcome. When no capable delegate is available,
handle work directly within the invoking agent's capability or report the limit.

## Completion contract

Resolve the intended outcome from the user's current request and the relevant
story, alignment, scout, or other source artifact, including a source in another
repo when applicable. State a short validation target. A story is not required
for work whose scope is already clear.

Inspect the actual changes and satisfy the validation policy below and the
owning repo's artifact requirements. Fix scoped, understood issues and continue; pause only
the affected work when proceeding requires missing intent, new authorization,
an unresolved safety or ownership issue, or a substantive scope decision. Report
unmet requirements honestly instead of marking partial work complete.

Include reviewed inbox capture (`inbox.md` or `docs/inbox.md`) by default unless
the user excludes it. Reconcile inbox-only edits from the primary checkout when
working in isolation, preserving live capture and leaving the source checkout
untouched. Remove or mark handled only notes whose resolution is supported by
the completed work or durable routing. Ambiguous notes remain live; conflicting
edits or unsafe contents need resolution before inclusion.

Close an in-scope story once its substantive work is validated, using the local
story-close skill if available, otherwise the repo's documented convention.
Skip an already completed closure unless its evidence or status needs repair.
Include required changelog and generated-surface updates before final validation.

## Validation proportional to the change

The coordinator selects and briefly explains the smallest sufficient validation
from the actual changed behavior and its dependencies, without routine user
approval. This policy governs close-out and its story-close/validation handoffs;
local documentation supplies commands and specific acceptance requirements.

- Evidence or documentation only: inspect the claims, provenance, links, schemas,
  and generated records affected by the diff. Do not run product suites.
- Isolated eval or development tooling: run focused tests and lint for the
  changed tooling and affected shared interfaces. A Python file or a "do not
  adopt" verdict alone does not determine the validation scope.
- Runtime, shared libraries, dependencies, build configuration, or generated
  executable artifacts: check affected consumers and broaden to integration or
  full suites when the possible effects warrant it. Inspect actual artifacts
  where semantic or visual correctness matters.

Keep explicit user-required checks, acceptance gates, and mandatory CI/release
gates. If coverage or isolation is unclear, inspect the relevant dependency path
and broaden checks as needed; do not label a change low-risk merely to skip work.
Do not rerun paid evaluations or repair unrelated failures as part of landing
without the corresponding authorization.

Carry evidence from implementation through validation, story closure, commit,
and landing. Record the command, result, tested content (tree/diff or relevant
file identities), and relevant environment/check configuration. Reuse a result
when those inputs still apply to the candidate. A new commit SHA, branch push,
story checkbox, or documentation-only edit does not by itself invalidate code
tests; validate the changed records instead. If a check depends on Git metadata,
include that metadata among its inputs.

After fixes or integration, compare inputs and rerun only affected checks.
Avoid separate pre-commit and post-commit full-suite runs over unchanged inputs.
Broad rules such as "fresh this pass" or "full suite before Done" mean applicable
evidence for the current candidate, not compulsory repetition. Report the check
selection, reused evidence, and any limits honestly; passing commands alone does
not prove the requested outcome is complete.

## Landing and recovery

Before pushing any repo, preflight all in-scope repos for known completion,
validation, ownership, and integration blockers. Keep a compact per-repo record
of scope, candidate commit, validation, destination, and landing state. Resolve
known blockers before beginning the multi-repo landing.

Stage only the reviewed intended files or hunks, including the reviewed inbox
changes; never use `git add .`. Preserve unrelated changes and existing staged
work. Review the full candidate diff against its destination, including existing
branch commits. Integrate off main in a task branch or dedicated worktree, using
a clean integration worktree when needed to preserve an active checkout. Do not reset,
stash, or synchronize unrelated primary-checkout work as part of landing.

Push the execution branch and land each validated candidate by fast-forwarding
remote main, respecting repo-required review or CI gates. Land dependencies
before their consumers and supervisor completion records after the work they
describe. Refresh remote state before landing; if it advances, integrate and
revalidate affected surfaces before retrying. Do not force-push main.

Multi-repo pushes are not atomic. If a later repo fails, retain successful
landings, stop dependent landings, and report each repo as landed,
validated-but-unlanded, or blocked, with commit IDs and the next recovery action.
Do not roll back successful pushes automatically. Resume from verified remote
state rather than replaying completed actions. Verify the intended commit is
present on each destination remote branch before reporting it landed.

## Optional cleanup and learning

Without `--cleanup`, retain task worktrees and branches. With it, remove only
identified task-owned temporary worktrees and local branches after verifying
their commits are on remote main, their worktrees have no uncommitted or
untracked work or valuable ignored files, and no other task is using them.
Inspect ignored contents too; a clean Git status is insufficient. Keep primary
checkouts, remote branches, stashes, and anything with uncertain ownership;
report retained items.
Do not use force deletion to bypass these checks.

If a local learning-review skill exists and recurring friction or a material
user correction warrants it, use it as a read-only detector after the episode.
Report worthwhile candidates for separate drafting; do not create a post-landing
diff or promote workflow changes as a side effect of close-out.

Report the outcome against the validation target, relevant checks and limits,
story closure if applicable, each repo's commit and remote landing result, and
cleanup performed or retained. Name remaining work precisely when blocked.
