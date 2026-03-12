---
name: check-in-diff
description: Audit git changes and, when explicitly requested, commit, sync with main, validate, and land work safely
user-invocable: true
---

# /check-in-diff [--autonomous] [--cleanup]

> ADR check: If this task raises an architectural, workflow, schema, or UX question, read the relevant decision record(s) in `docs/decisions/` and supporting docs in `docs/design/` before choosing an approach. If none apply, say so explicitly.

Audit current git changes. When the user explicitly requests check-in, execute the repo's commit/push/sync/validate/land workflow.

Companion runbook: `docs/runbooks/check-in-worktree-landing.md`

## Modes

- **Audit-only (default):** review the diff, flag risks, update `CHANGELOG.md` if needed, and propose the next step.
- **Task-branch landing:** if the current branch is not `main`, commit the intended changes, push the branch, sync it with latest `origin/main`, validate, then fast-forward `main`.
- **Main fallback:** if the current branch is `main`, do not panic. If sync with `origin/main` requires integration work, create a temporary `codex/checkin-*` branch and resolve there instead of resolving conflicts directly on `main`.

## Steps

1. **Inspect git context:**
   - `git branch --show-current`
   - `git status --short`
   - `git diff`
   - `git diff --staged`
   - `git worktree list`
   - `git fetch origin main`
   - Identify:
     - current branch
     - whether this is a task branch or `main`
     - whether another worktree already holds `main`
     - whether local changes are ahead of / diverged from `origin/main`
     - whether `origin/main` is already an ancestor of `HEAD` or integration work is required before landing

2. **Flag risks:**
   - Secrets, API keys, credentials, .env files?
   - Large binary files or build artifacts?
   - Changes outside the scope of the current story?
   - Schema changes without migrations?
   - Deleted tests or weakened assertions?
   - Dirty worktree problems or unrelated changes that should not be included in the check-in?

3. **Check alignment:**
   - Do changes match the story's task list?
   - Are docs updated for any behavioral changes?
   - Are new files in the right locations per project structure?

4. **Ensure CHANGELOG.md is updated:**
   - Check whether `CHANGELOG.md` appears in `git diff --stat` or `git status --short`.
   - If CHANGELOG.md is already in the diff, verify the entry covers the current changes.
   - If CHANGELOG.md is absent from the diff, write an entry now:
     - Analyze the staged/unstaged changes to determine what was added, changed, or fixed.
     - Prepend a new entry after the `# Changelog` header using Keep a Changelog format:

       ```
       ## [YYYY-MM-DD-NN] - Short summary
       ```

     - Use today's date. **Versioning (CalVer)**: Use the `YYYY-MM-DD-NN` format for the header, where `NN` is the release sequence for that day (e.g., `01`, `02`, `03`). Check the previous entry to increment correctly. The API parses this into `YYYY.MM.DD-NN`.
     - Only include subsections that apply.
     - Include CHANGELOG.md in the staging plan.

5. **Draft commit message:**
   - Summary line (imperative, <72 chars)
   - Body: what changed and why
   - Reference story number if applicable

6. **Propose staging plan:**
   - Which files to stage (specific files, not `git add .`)
   - Any files to exclude from this commit
   - Always include CHANGELOG.md
   - Suggest splitting into multiple commits if changes are unrelated

7. **Stop here by default**:
   - If the user did **not** explicitly request commit / push / landing, stop after the audit summary
   - Recommend the next step (`git commit`, `git push`, `land branch`, or stop)
   - If the user already explicitly requested the full check-in flow, continue without asking again

8. **Choose the execution branch before committing**:
   - **Task branch mode** (`current branch != main`):
     - Stay on the current branch
   - **Main direct mode** (`current branch == main` and `origin/main` is already an ancestor of `HEAD`):
     - Stay on `main`
     - Do not push `main` until validation succeeds
   - **Main integration mode** (`current branch == main` and integration with `origin/main` is required):
     - Create a temporary branch (use `codex/checkin-<timestamp>`) before staging or committing
     - Commit, sync, and resolve conflicts on that temporary branch
     - Keep `main` untouched until the validated fast-forward landing step

9. **Commit intended changes on the execution branch**:
   - Stage intended files only
   - Commit them on the execution branch selected in step 8
   - If the execution branch is not `main`, push it to origin now
   - If the execution branch is `main`, keep it local until validation succeeds

10. **Sync the execution branch with latest `origin/main` when needed**:
   - If the execution branch is not `main`:
     - Prefer `git rebase origin/main`
     - If rebase is unsuitable, merge `origin/main` into the execution branch instead
   - If the execution branch is `main` in Main direct mode, skip integration and move to validation
   - Do not resolve integration conflicts directly on `main`

11. **Resolve conflicts on the non-main execution branch**:
   - If conflicts occur during rebase / merge, resolve them on the task or temporary integration branch
   - Record which files conflicted
   - If conflicts cannot be resolved cleanly, stop and report

12. **Run relevant validation after integration**:
   - Re-run validation after conflict resolution or sync with latest `main`
   - In Main direct mode, run validation before the first push of `main`
   - Use changed scope to choose checks:
     - Backend code: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
     - UI code: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
     - If UI behavior changed: browser verification when appropriate
   - If validation fails, stop and report; do not land onto `main`

13. **Land the validated branch tip onto `main`**:
   - If the validated branch is `main`, push updated `main` now
   - If the validated branch is not `main`:
     - Update local `main` from `origin/main`
     - If another worktree already has `main` checked out, `/check-in-diff` may use git-only commands in that worktree for this landing step; do not edit project files there
     - Fast-forward only:
       - `git merge --ff-only <validated-branch>`
     - Push updated `main` to origin
   - Never create a merge commit into `main`

14. **Optional cleanup**:
   - Delete the finished branch and/or remove its worktree only if the user explicitly requested cleanup

15. **Report results**:
   - branch checked in
   - whether rebase or merge-from-main was used
   - whether conflicts occurred
   - which files had conflicts, if any
   - whether tests / build / lint passed
   - whether `main` was fast-forwarded and pushed
   - whether branch / worktree cleanup was performed

## Guardrails

- NEVER commit or push without explicit request from the user
- NEVER suggest committing secrets, credentials, .env files, or build artifacts
- NEVER use `git add .` or `git add -A` — always stage specific files
- NEVER do a non-fast-forward merge into `main`
- NEVER resolve integration conflicts directly on `main`
- NEVER push `main` before validation when using the main fallback path
- NEVER fail just because the current branch is `main`; use the main fallback path instead
- If the branch cannot be cleanly integrated and validated, stop and report
- Flag any changes that look unintentional or outside current story scope
