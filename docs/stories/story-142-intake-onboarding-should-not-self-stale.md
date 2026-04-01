# Story 142 — Initial Intake Should Not Self-Stale

**Priority**: High
**Status**: Pending
**Ideal Refs**: R1 (story understanding), R12 (radical transparency), R15 (intelligent change propagation)
**Spec Refs**: spec:1.3 (Revision and Change Propagation), spec:2 (Story Intake & Understanding), spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), `docs/design/decisions.md` ("Staleness and Re-run", "Inline stale indicators")
**Depends On**: Story 031 (semantic impact layer), Story 062 (3-stage ingestion), Story 127 (artifact health semantics)

## Goal

Make the initial two-step onboarding path behave like a coherent first import instead of generating its own attention debt. On a fresh project, `basic breakdown -> deep breakdown` should either land in a current/ready state or surface a specific real problem with an honest next action. It must not end by telling the user to clean up stale or review states created only by CineForge's own intermediate intake churn.

## Acceptance Criteria

- [ ] Running the current initial intake path on a fresh project does not leave [ProjectHome.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectHome.tsx) or [ProjectInbox.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectInbox.tsx) showing attention items caused only by the system's own transition from basic breakdown artifacts to deep-breakdown artifacts.
- [ ] If fresh onboarding genuinely hits a blocking issue, the operator sees a specific explanation and next action grounded in the actual artifact or run state; a generic "X artifacts need attention" banner is not the only outcome for this path.
- [ ] Project home, inbox, and artifact-group APIs agree on which post-intake items are actionable. Non-actionable intermediary artifacts such as onboarding-only review artifacts, superseded structural artifacts, or equivalent internal churn do not inflate the initial health summary.
- [ ] Focused regression coverage reproduces the original failure mode and proves the chosen fix, and browser verification on a seeded fresh project confirms that successful onboarding no longer ends with false attention debt.

## Out of Scope

- Redesigning the entire inbox or artifact-health system beyond what this onboarding bug requires
- Suppressing legitimate normalization, parsing, or dependency errors just to keep the home page green
- Reworking historical run polling or stale chat cards; that remains Story 139
- Replacing the two-stage intake/deep-breakdown flow established by Story 062

## Approach Evaluation

- **Simplification baseline**: A single LLM call is not the right baseline here. The reported defect is that the system is surfacing false or non-actionable health debt after its own onboarding path. That is a graph-health / aggregation / UI contract problem, not a missing reasoning pass.
- **AI-only**: Wrong fit. Asking an LLM to "explain away" onboarding attention would paper over incorrect substrate state and make trust worse.
- **Hybrid**: Possible only if the root cause turns out to involve reusing existing semantic-impact machinery for one narrow onboarding transition. Even then, the truth source still needs to be deterministic.
- **Pure code**: Strongest starting point. The likely causes are deterministic: latest-artifact grouping, stage-review leakage, stale propagation on initial deep breakdown, or home/inbox actionability drift.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` require stale indicators for real upstream changes and clear next actions, not self-inflicted onboarding debt. Story 062 deliberately split intake into shallow and deep phases; Story 031 and Story 127 made live health authoritative across the UI. The fix must respect those contracts instead of special-casing the home page into lying.
- **Existing patterns to reuse**: `ArtifactManager.list_artifact_groups()` live health payloads, `DependencyGraph` health context, `ui/src/lib/health.ts`, Story 031 health/provenance work, Story 127 shared semantics, and Story 130's preflight-honesty pattern for golden-path user trust.
- **Eval**: A deterministic reproduce-first harness is the discriminator. Seed a fresh project, run the same intake/deep-breakdown sequence, inspect returned artifact groups and health causes, then verify the home/inbox/browser result. No promptfoo eval is warranted unless the bug turns out to depend on AI assessment state, which currently looks unlikely.

## Tasks

- [ ] Reproduce the `/the-mariner` failure mode on a deterministic fresh project and classify the exact source of the attention banner:
  - [ ] which artifact groups are counted
  - [ ] which health states are involved (`stale`, `needs_review`, `confirmed_valid`, or other)
  - [ ] whether the count comes from real latest artifacts or onboarding-only intermediary artifacts
- [ ] Implement the smallest coherent fix so initial onboarding either auto-rectifies its own superseded state or surfaces only genuinely actionable issues.
- [ ] Align [ProjectHome.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectHome.tsx), [ProjectInbox.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectInbox.tsx), and the artifact-group API so they share the same actionability semantics for this path.
- [ ] Add focused regression coverage at the narrowest seam the root cause lives in: graph health, artifact-group aggregation, or onboarding UI derivation. Avoid growing generic oversized test files unless there is no cleaner seam.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `src/cine_forge/api/artifact_manager.py` owns artifact-group summaries, `src/cine_forge/artifacts/graph.py` owns live health truth, and the current onboarding view in `ui/src/pages/ProjectHome.tsx` consumes that summary. Do not create a parallel "onboarding health" store.
- **Data contracts**: Existing `ArtifactGroupSummary` / `health_details` may be enough. If the chosen fix requires a new actionability field or onboarding-only classification to cross the API boundary, define it in `src/cine_forge/api/models.py` and `ui/src/lib/types.ts` before consuming it in the UI.
- **File sizes**: `make check-size` on 2026-04-01 flagged `src/cine_forge/api/artifact_manager.py` at 553 lines, `ui/src/pages/ProjectHome.tsx` at 588, `ui/src/lib/types.ts` at 600, and `ui/src/lib/use-run-progress.ts` at 539. Safer touch points today: `src/cine_forge/artifacts/graph.py` (345), `ui/src/pages/ProjectInbox.tsx` (462), `src/cine_forge/api/models.py` (489), and `ui/src/lib/health.ts` (50). The implementation should stay surgical and bias toward extraction if the root cause wants to enlarge already-oversized files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, ADR-002, `docs/design/decisions.md`, Story 031, Story 062, Story 127, and the live `FreshImportView` / artifact-group code paths. No separate ADR appears to govern this exact onboarding-health bug.

## Files to Modify

- `src/cine_forge/api/artifact_manager.py` — tighten artifact-group actionability/health aggregation for onboarding if the bug lives at the API summary layer (553 lines)
- `src/cine_forge/artifacts/graph.py` — adjust live health semantics only if the root cause is structural invalidation or stale-cause handling on latest artifacts (345 lines)
- `src/cine_forge/api/models.py` — add typed summary fields if new actionability metadata must cross the API boundary (489 lines)
- `ui/src/lib/types.ts` — frontend support for any new API summary fields (600 lines)
- `ui/src/lib/health.ts` — keep shared actionability semantics authoritative (50 lines)
- `ui/src/pages/ProjectHome.tsx` — fix `FreshImportView` onboarding health summary / CTA behavior (588 lines)
- `ui/src/pages/ProjectInbox.tsx` — keep inbox attention derivation aligned with home summary (462 lines)
- `ui/src/lib/use-run-progress.ts` — only if onboarding completion messaging or run-finished cleanup is part of the real root cause (539 lines)

## Redundancy / Removal Targets

- Any onboarding-only artifact-health debt caused by intermediary `stage_review`, superseded structural artifacts, or similar internal churn
- Any duplicate actionability logic that lets home and inbox disagree about what "needs attention" means after onboarding
- Any copy or workflow that effectively tells the user to clean up CineForge's own initial intake transitions

## Notes

- User report that triggered this story: on `http://127.0.0.1:5174/the-mariner`, uploading the script, running the basic breakdown, and then running the deep breakdown ended with `Artifact Health / 14 artifacts need attention.` The user's objection is correct: if this is still part of first-time intake, CineForge should either auto-rectify self-inflicted staleness or tell the operator about a concrete real failure, not dump system debt into the golden path.
- The likely root cause is still open. It may be real latest-artifact staleness, `stage_review` / `needs_review` leakage into the same summary bucket, or a mismatch between API grouping and UI actionability semantics. That uncertainty is acceptable because the story is still fully scoped around one coherent user-facing bug.
- This is not a low-value optimization. It directly protects the Ideal's "easy, fun, and engaging" bar on the first meaningful user journey through the product.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260401-1642 — triage: created from inbox report that `/the-mariner` basic breakdown followed by deep breakdown ended with `Artifact Health / 14 artifacts need attention.` Existing homes checked: Story 062 owns the tier split, Story 031 owns health propagation, and Story 127 owns shared health semantics, but no current story owns self-inflicted onboarding attention debt. Decision=`new Pending story` because this is a golden-path trust break, not a side issue. Next=`/build-story` when ready.
