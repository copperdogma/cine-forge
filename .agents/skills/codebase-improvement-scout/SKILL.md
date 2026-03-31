---
name: codebase-improvement-scout
description: Periodically inspect the repo for high-value cleanup, draft improvement stories, and optionally apply narrow safe hygiene fixes.
user-invocable: true
---

# /codebase-improvement-scout [scope] [--create-story] [--autofix] [--autonomous]

> ADR check: If this task raises an architectural, workflow, schema, or UX question, read the relevant decision record(s) in `docs/decisions/` and supporting docs in `docs/design/` before choosing an approach. If none apply, say so explicitly.

Run a scheduled or on-demand repo-hygiene scan for codebase drift, AI-generated junk, and high-value cleanup opportunities.

For rationale and prior landscape research, see:
- `docs/research/codebase-improvement-skill/final-synthesis.md`
- `docs/scout/scout-011-codebase-improvement-skill.md`
- `docs/runbooks/codebase-improvement-scout.md`

## Default Behavior

- **Default mode:** report-only. Create a scan artifact, rank the best improvements, and recommend the next step.
- **`--create-story`:** create exactly one best-fit story for the highest-value non-mechanical improvement if no equivalent story already exists.
- **`--autofix`:** allow only narrow, behavior-preserving cleanup work on a side branch.
- **`--autonomous`:** if the user says "you choose and continue", continue through the next approved step without asking again.

This skill is a **repo hygiene scout**, not a free-form refactoring bot. Prefer report + story over speculative code edits.

## Phase 0 — Bootstrap

1. **Create scan artifacts:**

```bash
.agents/skills/codebase-improvement-scout/scripts/start-scan.sh
```

This creates:
- `docs/reports/codebase-improvement/<timestamp>.md`
- `memory/codebase-improvement-state.yaml` (if missing)

2. **Record current state:**
   - `git status --short`
   - `git branch --show-current`
   - `git rev-parse --short HEAD`
   - If the worktree is dirty and the user did not explicitly authorize edits on top of it, stay in report-only mode.

3. **Read repo context:**
   - `AGENTS.md`
   - `docs/ideal.md`
   - `docs/spec.md`
   - relevant ADRs / decision docs for areas likely to be flagged
   - `docs/stories.md`
   - `memory/codebase-improvement-state.yaml` if it exists

## Phase 1 — Deterministic Discovery

Run the strongest available deterministic checks first. Verify tools exist before using them; do not assume optional tooling is installed.

1. **Repo hygiene baseline:**
   - `make check-size` if available; otherwise use `wc -l` on likely hotspots
   - `git log --since='30 days' --name-only --format='' | sed '/^$/d' | sort | uniq -c | sort -rn | head -50`
   - `rg -n "TODO|FIXME|XXX|HACK|TEMP|placeholder|stub" src ui tests docs`

2. **Project-native quality checks:**
   - Backend: `.venv/bin/python -m ruff check src/ tests/`
   - Backend tests when relevant: `make test-unit PYTHON=.venv/bin/python`
   - UI: `pnpm --dir ui run lint`
   - UI typecheck: `cd ui && npx tsc -b`
   - UI duplication lint if available: `pnpm --dir ui run lint:duplication`
   - Skill sync when agent surfaces are involved: `./scripts/sync-agent-skills.sh --check` if `AGENTS.md` or `.agents/skills/` are under review

3. **Optional narrow detectors if installed:**
   - TypeScript dead code / deps: `knip`
   - Duplication: `jscpd`
   - Python dead code: `vulture`
   - Python dependency drift: `deptry`

4. **Targeted reads:**
   - Inspect the top hotspot files
   - Inspect recent stories affecting those areas
   - Check whether an apparent issue is already tracked or intentionally suppressed
   - Explicitly scan for architecture-drift signatures:
     - compatibility shims or fallback layers preserving an obsolete contract
     - duplicate ownership / second homes for the same behavior
     - empty stubs, dead wrappers, or placeholder pass-throughs left after refactors
     - widened types or defensive guards that patch around unclear ownership instead of resolving it

## Phase 2 — Triage and Classification

For each candidate finding, classify it as exactly one of:

- **Auto-fix**
  - mechanical
  - behavior-preserving
  - small blast radius
  - no architecture change
  - verifiable by existing checks
- **Story**
  - structural or architectural
  - likely to touch multiple files / layers
  - needs judgment, test design, or UI review
  - better handled by the normal story workflow
- **Suppress**
  - intentional local convention
  - already reviewed and accepted
  - active work makes the signal misleading right now
- **Ignore**
  - cosmetic only
  - too low-value
  - low confidence

Rank findings by leverage, not raw issue count:
- hotspot score (recent churn × size/complexity)
- user-facing impact
- maintenance drag
- confidence
- drift pressure: whether the issue is likely to cause agents to preserve and duplicate it again on the next edit

Prefer the top 3-5 findings. Low-signal laundry lists are a failure.

## Phase 3 — Write the Scan Report

Fill the generated report with:
- run metadata and scope
- detectors used / unavailable
- top findings with classification
- one recommended next step
- story candidate(s)
- suppressions / ignores with rationale

Also update `memory/codebase-improvement-state.yaml`:
- add newly suppressed findings
- record the run timestamp and top findings
- avoid re-raising recent suppressed items unless the evidence changed

## Phase 4 — Optional Story Creation

If `--create-story` is set or the user explicitly approves:

1. Search `docs/stories.md` and existing story files for overlap.
2. If an equivalent story already exists, link it in the report instead of creating a duplicate.
3. Otherwise create exactly one story for the highest-value non-mechanical improvement.
4. Default to `Draft` if the scope is still fuzzy; use `Pending` only when acceptance criteria and tasks are concrete.
5. Link the report in the story notes.

If the user also explicitly approves execution, continue using the normal chain:
- `/build-story`
- `/validate`
- `/mark-story-done`
- `/check-in-diff`

## Phase 5 — Optional Narrow Auto-Fix Lane

Only enter this phase when `--autofix` is set or the user explicitly approved safe cleanup edits.

1. Create a side branch before editing:
   - `git checkout -b codex/codebase-improvement-<timestamp>-<slug>`

2. Restrict changes to **narrow safe classes**:
   - remove unused imports
   - remove unused dependencies
   - delete provably dead files / exports
   - collapse exact duplicate pure helpers with obvious replacements

3. Hard limits:
   - no more than 5 changed files per cleanup cluster
   - no new abstractions
   - no API or schema changes
   - no structural refactors
   - no UI behavior changes without browser verification

4. Verification:
   - run the relevant native checks
   - if UI changed, run browser verification per `docs/runbooks/browser-automation-and-mcp.md`
   - if checks fail twice, revert that cleanup and downgrade it to a story

5. End with a concise summary and recommend `/check-in-diff` unless the user already approved later git steps.

## Guardrails

- Default to report-first, not code-first.
- Never run unconstrained "make the repo better" edits.
- Never relitigate settled architecture if ADRs already answer the question.
- Never raise the same suppressed finding repeatedly without new evidence.
- Never do cosmetic-only churn.
- Never treat "tests still pass" as sufficient reason to ignore duplicate ownership, obsolete shims, or other drift signatures.
- Never auto-fix structural or architectural issues.
- Never auto-edit on a dirty worktree unless the user explicitly approved that risk.
- Never commit or push without explicit user permission.
