# Finish And Push

## Context

Use this runbook when the user explicitly wants a completed story closed,
checked in, and landed onto `main` in one request.

This is the operational companion to `/finish-and-push`. It does not replace the
existing close-out and landing workflows; it sequences them safely.

## Prerequisites

- The user explicitly requested bundled close-out and landing; invoking
  `/finish-and-push` counts
- The target story is known or can be inferred unambiguously
- The current worktree owns the target changes
- The leaf skills exist and are healthy:
  - `/mark-story-done`
  - `/check-in-diff`
- `docs/runbooks/check-in-worktree-landing.md` is available for the landing half

## Steps

1. **[script] Resolve the target and current git context**
   - Read the target story file.
   - Inspect `git branch --show-current`, `git status --short`, and a small diff
     summary.
   - Confirm the current worktree actually contains the intended story changes.
   - If the story or ownership is ambiguous, stop and ask.

2. **[script] Run `/mark-story-done` first**
   - Reuse the leaf skill's workflow-gate checks, validation requirements,
     generated planning-surface refresh, and `CHANGELOG.md` behavior.
   - Do not jump straight to git check-in.

3. **[judgment] Triage close-out findings**
   - Minor findings: fix them inline, rerun the minimum required validation, and
     update the story work log before continuing.
   - Major findings: stop before commit/push and recommend the correct
     disposition (`Rescope then close`, `Keep open`, or `Mark blocked`).

4. **[script] Run `/check-in-diff` in full landing mode**
   - Treat `/finish-and-push` as explicit approval for the full check-in flow.
   - Reuse `/check-in-diff` for staging, commit, push, sync-with-main,
     validation, and fast-forward-only landing.
   - Pass through `--cleanup` only if the user explicitly requested it.

5. **[judgment] Triage landing findings**
   - Minor mechanical issues: fix them inline and continue after rerunning the
     required checks.
   - Major integration or safety issues: stop and report the safest next action
     instead of forcing the landing.

6. **[script] Report the outcome**
   - State whether the story was closed.
   - State whether the execution branch was committed/pushed.
   - State whether `main` was fast-forwarded and pushed.
   - State whether cleanup was performed.

## Boundaries

### Always do

- Run `/mark-story-done` before any commit/push flow
- Preserve the fast-forward-only rule for landing onto `main`
- Rerun the minimum required validation after every inline fix
- Keep the leaf-skill guardrails intact

### Ask first

- When the target story is ambiguous
- Before branch/worktree cleanup unless the user requested `--cleanup`
- When closing the story would require scope renegotiation or a major rescope

### Never do

- Never bypass `/mark-story-done`
- Never land partial work just because only a small issue remains
- Never weaken `/mark-story-done` or `/check-in-diff` guardrails
- Never resolve integration conflicts directly on `main`
- Never treat `/finish-and-push` as approval to land unrelated changes

## Troubleshooting

- **Target story is ambiguous**
  - Fix: stop before editing or staging and ask which story or branch is meant.

- **`/mark-story-done` finds substantive gaps**
  - Fix: stop before commit/push, classify the gap, and recommend one explicit
    disposition instead of trying to land partial work.

- **`/check-in-diff` hits integration conflicts**
  - Fix: resolve them on the non-`main` execution branch or stop if the conflict
    is not purely mechanical.

- **Another worktree already has `main` checked out**
  - Fix: follow `check-in-worktree-landing.md` and use git-only commands there
    for the final fast-forward step only.

## Lessons Learned

- 2026-03-18 — The wrapper is valuable because it bundles permission and
  sequencing, not because it invents a second landing workflow.
