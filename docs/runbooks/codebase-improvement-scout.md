# Runbook: Codebase Improvement Scout

## Context

Use this runbook when you want a recurring or on-demand repo-hygiene scan that finds high-value cleanup work without turning into noisy autonomous refactoring.

The companion skill is `/codebase-improvement-scout`.

## Prerequisites

- Repo root available and readable
- Project-native checks available (`make`, `.venv`, `pnpm`, `ui/` toolchain as applicable)
- Understanding that the default mode is report-first, not auto-fix-first
- Read `AGENTS.md`, especially the story execution protocol and ADR discipline

## Steps

1. **[script] Bootstrap the scan**
   - Run `.agents/skills/codebase-improvement-scout/scripts/start-scan.sh`
   - This creates the dated report file and initializes `memory/codebase-improvement-state.yaml` if needed

2. **[judgment] Decide the operating mode**
   - Default: report-only
   - Use `--create-story` when the goal is to turn the best finding into tracked work
   - Use `--autofix` only for narrow, behavior-preserving cleanup on a side branch
   - If the worktree is dirty and edits were not explicitly authorized, stay report-only

3. **[script] Run deterministic discovery**
   - Run repo-native checks first (`ruff`, `pytest`, `pnpm lint`, `tsc`, duplication lint, hotspot/history scans, `rg` marker scans)
   - Run optional tools only if they are already installed / configured

4. **[judgment] Classify findings**
   - Auto-fix only if the change is mechanical, small, and verifiable
   - Draft a story for structural or architectural issues
   - Suppress or ignore low-value or intentionally-accepted findings
   - Rank by leverage, not issue count

5. **[judgment] Produce the scan artifact**
   - Fill the report with top findings, evidence, and one recommended next step
   - Update `memory/codebase-improvement-state.yaml` so recurring runs do not rediscover the same accepted exceptions forever

6. **[script] Optional execution**
   - If `--create-story`: create or link one best-fit story, then follow the normal story chain
   - If `--autofix`: create a side branch, apply only narrow safe cleanup, run checks, and stop at `/check-in-diff`

## Boundaries

Always do:
- Use deterministic detectors before AI judgment
- Read relevant ADRs before suggesting structural cleanup
- Prefer report + story over speculative edits
- Keep summaries short and high-signal

Ask first:
- Installing new hygiene tooling
- Editing on top of a dirty worktree
- Broad auto-fix passes
- Structural cleanup that spans multiple subsystems

Never do:
- Unconstrained "make the repo better" refactors
- Cosmetic churn
- Architecture relitigation that ignores ADRs
- More than 5 changed files in one auto-fix cluster
- Commit or push without explicit permission

## Troubleshooting

- **Dirty worktree**
  - Stay report-only unless the user explicitly approves edits on top of local changes

- **Optional detectors missing**
  - Record the missing tool in the report as infrastructure debt; do not silently install it

- **Too many findings**
  - Reduce to the top 3-5 by leverage and move the rest into suppressed / ignored / backlog sections

- **Autofix fails checks**
  - Revert that candidate after two attempts and downgrade it to a story

- **UI cleanup affects behavior**
  - Stop treating it as hygiene autofix; route it through a story and require browser verification

## Lessons Learned

- 2026-03-12 — Research synthesis strongly favored deterministic discovery + AI triage + narrow auto-fix lanes. Free-form autonomous refactoring was consistently noisy and low-trust.
