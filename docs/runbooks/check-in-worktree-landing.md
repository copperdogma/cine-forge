# Runbook: Check-In And Worktree Landing

## Context

Use this runbook when the user explicitly wants a task branch checked in and landed onto `main`.

This is the operational companion to `/check-in-diff`. It is optimized for parallel branch/worktree development:

- one task = one branch = one worktree = one agent
- `main` stays stable
- conflicts are resolved on the task branch, not on `main`

## Prerequisites

- The user explicitly requested check-in / landing
- The current worktree is the one that owns the task changes
- You know whether you are on a task branch or on `main`
- Relevant project validation commands are available

## Steps

1. **[script] Inspect git context**
   - `git branch --show-current`
   - `git status --short`
   - `git worktree list`
   - `git fetch origin main`

2. **[judgment] Choose the execution path before committing**
   - Preferred: current branch is a task branch
   - Direct-main fallback: current branch is `main` and `origin/main` is already an ancestor of `HEAD`
   - Main integration fallback: current branch is `main` but integration with `origin/main` is required; create a temporary integration branch before staging or committing

3. **[script] Audit and prepare on the execution branch**
   - Review diff
   - Check for secrets / accidental files
   - Update `CHANGELOG.md`
   - Stage intended files only
   - Commit the intended change set
   - Push the execution branch now only if it is not `main`

4. **[script] Sync the execution branch with latest `origin/main` when needed**
   - If the execution branch is not `main`, prefer `git rebase origin/main`
   - If rebase is unsuitable, use `git merge origin/main`
   - Resolve conflicts on the non-main execution branch
   - Re-run relevant validation after integration
   - In direct-main fallback mode, validate before the first push of `main`

5. **[script] Land onto `main`**
   - If the validated branch is `main`, push updated `main`
   - If the validated branch is not `main`, update local `main` from `origin/main` and fast-forward with `git merge --ff-only <branch>`
   - If another worktree already has `main` checked out, `/check-in-diff` may use git-only commands there for this landing step; do not edit project files in that sibling worktree
   - Push updated `main`

6. **[judgment] Optional cleanup**
   - Delete branch and remove worktree only if the user requested cleanup

## Boundaries

Always do:
- Resolve conflicts on the task branch, not on `main`
- Re-run relevant validation after integrating latest `main`
- Use `--ff-only` when moving `main`
- Keep `main` local until validation passes when using the direct-main fallback

Ask first:
- Deleting the finished branch
- Removing the worktree
- Switching from rebase to merge for nontrivial reasons

Never do:
- Non-fast-forward merge into `main`
- Panic just because the current branch is `main`
- Resolve integration conflicts directly on `main`
- Edit project files in a sibling worktree during landing
- Commit or push without explicit user approval

## Troubleshooting

- **Current branch is `main`**
  - If `origin/main` is already an ancestor of `HEAD`, direct push is fine only after validation
  - If integration with `origin/main` is required, create a temporary `codex/checkin-*` branch and resolve there

- **Another worktree already has `main` checked out**
  - Use `git -C <path> ...` there for the final fast-forward landing only
  - Do not do implementation edits or conflict resolution in that sibling worktree

- **Rebase becomes messy**
  - Fall back to merging `origin/main` into the task branch
  - Still validate before landing

- **Validation fails after sync**
  - Stop and report
  - Do not land to `main`

## Lessons Learned

- 2026-03-12 — The key policy is not “always use branches” in the abstract; it is “never resolve integration conflicts on `main`.” Supporting `main` as a fallback is fine as long as the skill branches for integration when needed.
