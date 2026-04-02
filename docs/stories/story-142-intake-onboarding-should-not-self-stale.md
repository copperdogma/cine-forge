# Story 142 — Initial Intake Should Not Self-Stale

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R12 (radical transparency), R15 (intelligent change propagation)
**Spec Refs**: spec:1.3 (Revision and Change Propagation), spec:2 (Story Intake & Understanding), spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), `docs/design/decisions.md` ("Staleness and Re-run", "Inline stale indicators")
**Depends On**: Story 031 (semantic impact layer), Story 062 (3-stage ingestion), Story 127 (artifact health semantics)

## Goal

Make the initial two-step onboarding path behave like a coherent first import instead of generating its own attention debt. On a fresh project, `basic breakdown -> deep breakdown` should either land in a current/ready state or surface a specific real problem with an honest next action. It must not end by telling the user to clean up stale or review states created only by CineForge's own intermediate intake churn.

## Acceptance Criteria

- [x] Running the current initial intake path on a fresh project does not leave [ProjectHome.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectHome.tsx) or [ProjectInbox.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectInbox.tsx) showing attention items caused only by the system's own transition from basic breakdown artifacts to deep-breakdown artifacts.
- [x] If fresh onboarding genuinely hits a blocking issue, the operator sees a specific explanation and next action grounded in the actual artifact or run state; a generic "X artifacts need attention" banner is not the only outcome for this path.
- [x] Project home, inbox, shell badge, and artifact-group APIs agree on which post-intake items are actionable. Non-actionable intermediary artifacts such as onboarding-only review artifacts, superseded structural artifacts, or equivalent internal churn do not inflate the initial health summary.
- [x] Focused regression coverage reproduces the original failure mode and proves the chosen fix, and browser verification on a seeded fresh project confirms that successful onboarding no longer ends with false attention debt.

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

- [x] Reproduce the `/the-mariner` failure mode on a deterministic fresh project and classify the exact source of the attention banner:
  - [x] which artifact groups are counted
  - [x] which health states are involved (`stale`, `needs_review`, `confirmed_valid`, or other)
  - [x] whether the count comes from real latest artifacts or onboarding-only intermediary artifacts
- [x] Implement the smallest coherent fix so initial onboarding either auto-rectifies its own superseded state or surfaces only genuinely actionable issues.
- [x] Align [ProjectHome.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectHome.tsx), [ProjectInbox.tsx](/Users/cam/.codex/worktrees/4c58/cine-forge/ui/src/pages/ProjectInbox.tsx), [AppShell.tsx](/Users/cam/.codex/worktrees/7d18/cine-forge/ui/src/components/AppShell.tsx), and the artifact-group API so they share the same actionability semantics for this path.
- [x] Add focused regression coverage at the narrowest seam the root cause lives in: graph health, artifact-group aggregation, or onboarding UI derivation. Avoid growing generic oversized test files unless there is no cleaner seam.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=python`
  - [x] Backend lint: `PYTHONPATH=src python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: not applicable; no agent tooling or project instruction files changed
- [x] If evals or goldens are changed: not applicable; no eval or golden artifacts changed
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` and `configs/recipes/recipe-world-building.yaml` own whether deep breakdown creates stale debt during onboarding. `src/cine_forge/api/artifact_manager.py` owns artifact-group summaries, and the UI should consume that truth instead of inventing a parallel "onboarding health" store.
- **Data contracts**: Existing `ArtifactGroupSummary` / `health_details` may be enough. If the chosen fix requires a new actionability field or onboarding-only classification to cross the API boundary, define it in `src/cine_forge/api/models.py` and `ui/src/lib/types.ts` before consuming it in the UI.
- **File sizes**: `make check-size` on 2026-04-01 flagged `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` at 612 lines, `src/cine_forge/api/artifact_manager.py` at 553, `ui/src/pages/ProjectHome.tsx` at 588, `ui/src/lib/types.ts` at 600, and `ui/src/components/AppShell.tsx` at 683. Safer touch points today: `src/cine_forge/driver/artifact_persister.py` (249), `ui/src/pages/ProjectInbox.tsx` (462), `src/cine_forge/api/models.py` (489), `ui/src/lib/health.ts` (50), and `tests/integration/test_world_building_integration.py` (122). The implementation should stay surgical and bias toward extraction if the root cause wants to enlarge already-oversized files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, ADR-002, `docs/design/decisions.md`, Story 031, Story 062, Story 127, and the live `FreshImportView` / artifact-group code paths. No separate ADR appears to govern this exact onboarding-health bug.

## Files to Modify

- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — exclude `scene_index` from per-scene lineage and rebuild the scene enrichment schema for the mock/integration path (612 lines)
- `src/cine_forge/modules/ingest/project_config_v1/main.py` — add a guarded refresh path that only re-emits confirmed system-owned configs during deep breakdown (261 lines after change)
- `src/cine_forge/modules/ingest/project_config_v1/module.yaml` — declare the guarded refresh params
- `configs/recipes/recipe-world-building.yaml` — refresh onboarding-owned `project_config` after `analyze_scenes`
- `ui/src/lib/health.ts` — centralize actionable health, reviewable bible, and gate-review group derivation (50 lines before change)
- `ui/src/pages/ProjectHome.tsx` — consume the shared actionable-health helper in `FreshImportView` (588 lines)
- `ui/src/pages/ProjectInbox.tsx` — consume the shared health/review helpers for attention and gate counts (462 lines)
- `ui/src/components/AppShell.tsx` — align the shell inbox badge with the same health/review/gate semantics (683 lines)
- `tests/unit/test_scene_analysis_module.py` — assert the per-scene lineage exclusion
- `tests/unit/test_project_config_module.py` — cover guarded refresh behavior for missing, user-owned, and system-owned latest configs
- `tests/integration/test_world_building_integration.py` — run a mocked two-step onboarding slice and assert the artifact-group health result

## Redundancy / Removal Targets

- Any onboarding-only artifact-health debt caused by intermediary `stage_review`, superseded structural artifacts, or similar internal churn
- Any duplicate actionability logic that lets home and inbox disagree about what "needs attention" means after onboarding
- Any copy or workflow that effectively tells the user to clean up CineForge's own initial intake transitions

## Notes

- User report that triggered this story: on `http://127.0.0.1:5174/the-mariner`, uploading the script, running the basic breakdown, and then running the deep breakdown ended with `Artifact Health / 14 artifacts need attention.` The user's objection is correct: if this is still part of first-time intake, CineForge should either auto-rectify self-inflicted staleness or tell the operator about a concrete real failure, not dump system debt into the golden path.
- Exploration on 2026-04-01 pinned the current baseline to 14 stale latest artifacts on `the-mariner-64`: 13 enriched `scene:v2` groups plus 1 `project_config:v1`, all with `stale_cause = scene_index:project:v2`. `stage_review` leakage was not present in the reproduced failure.
- Story 062 already documented the false scene-stale half of the bug as a known remaining issue. Recipe inspection explains the remaining `project_config` item: `world_building` updates `scene_index` but does not refresh `project_config`.
- This is not a low-value optimization. It directly protects the Ideal's "easy, fun, and engaging" bar on the first meaningful user journey through the product.

## Plan

### Baseline / Eval

- Deterministic baseline, not promptfoo: inspect live artifact groups against the reproduced onboarding project state, then lock the fix with focused unit/integration tests.
- Current measured state from `ArtifactManager.list_artifact_groups()` on `the-mariner-64`: `156` total groups, `14` attention groups, `0` `stage_review` groups.
- Attention set today:
  - `scene:scene_001` through `scene:scene_013`, latest `v2`, all `stale`, all `stale_cause = scene_index:project:v2`
  - `project_config:project:v1`, `stale`, `stale_cause = scene_index:project:v2`
- Repo evidence: Story 062 already logged this cross-scene stale mechanism as a known remaining issue, and recipe inspection shows `world_building` never refreshes `project_config` after producing `scene_index:v2`.
- Success metric for this story: after `mvp_ingest -> world_building`, fresh onboarding produces no false scene attention items and does not end with a generic attention banner caused only by CineForge's own intake churn.

### Repo-Fit / Chosen Approach

- Choose **pure code** across the substrate, recipe, and UI layers.
- Why this is the right fit here:
  - `src/cine_forge/driver/artifact_persister.py` already exposes `exclude_upstream_lineage_types`, which is the clean repo-native seam for removing false per-scene `scene_index` lineage without inventing new graph rules.
  - Story 062 explicitly called out the same `scene_analysis_v1` lineage shape, so the repo already recognizes this as structural debt rather than a presentation-only issue.
  - The remaining `project_config` stale state is recipe-owned: `world_building` creates a newer `scene_index` but leaves one of its onboarding dependents behind. The honest fix is to refresh or explicitly guard that artifact in the recipe path, not to explain it away in the UI.
  - `ui/src/lib/health.ts` is already the shared seam for attention semantics, so home, inbox, and shell should converge there instead of carrying slightly different filters.
- Rejected alternatives:
  - **AI-only**: wrong layer; it would narrate around incorrect lineage truth.
  - **Hybrid-only**: unnecessary until substrate and recipe fixes are in place. If a real post-fix artifact still needs semantic triage, we can add typed actionability then.

### Recommended Scope Adjustment

- **XS**: fold `ui/src/components/AppShell.tsx` into this story. It derives the inbox badge with its own `isAttentionHealth` filter, so skipping it would leave the shell out of sync with the fixed home/inbox path.

### Task 1 — Fix False Scene Staleness at the Source

- **Files**: `src/cine_forge/modules/ingest/scene_analysis_v1/main.py`, `src/cine_forge/driver/artifact_persister.py` only if helper changes are needed
- **Change**:
  - Mark per-scene outputs from `scene_analysis_v1` to exclude upstream `scene_index` lineage while keeping `canonical_script` lineage intact.
  - Preserve lineage on the updated `scene_index` output so downstream consumers still see the enriched index as the latest truth.
- **Impact / risk**:
  - `scene_analysis_v1/main.py` is already 612 lines, so the change must stay surgical and avoid adding new branching inside oversized helpers.
  - Main regression risk is weakening legitimate stale propagation for scene outputs; tests must prove only the false cross-scene path disappears.
- **Done**:
  - Latest enriched scenes no longer self-stale via sibling BFS after `world_building`.
  - Other stale propagation behavior still works.

### Task 2 — Stop `world_building` from Leaving `project_config` Stale on Fresh Onboarding

- **Files**: `configs/recipes/recipe-world-building.yaml`, `src/cine_forge/modules/ingest/project_config_v1/main.py` only if a safe refresh guard is needed
- **Change**:
  - Add a `project_config_v1` refresh step after `analyze_scenes` for the fresh onboarding path, or gate it to auto-generated confirmed configs if the module needs to avoid overriding later human-curated configs.
  - Preserve the existing confirmation contract; do not reintroduce draft/review debt on a path that already has a confirmed config.
- **Impact / risk**:
  - This is the honest fix for the remaining `project_config` stale group because the current recipe is producing the upstream change without refreshing the dependent artifact.
  - Need to avoid a later rerun of `world_building` silently superseding an intentionally user-curated config. If the metadata does not let us distinguish that safely, stop at a narrower explicit-actionability fix instead of clobbering.
- **Done**:
  - Fresh `basic breakdown -> deep breakdown` no longer ends with a stale `project_config` created by the recipe itself.
  - Confirmation semantics remain unchanged for manual config workflows.

### Task 3 — Align UI Attention Semantics Around the Same Truth Source

- **Files**: `ui/src/lib/health.ts`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/ProjectInbox.tsx`, `ui/src/components/AppShell.tsx`
- **Change**:
  - Centralize the onboarding/actionable attention filter in `ui/src/lib/health.ts`.
  - Update home, inbox, and shell badge derivation to use the same helper and the same exclusions/next-action logic.
  - Only add new API fields in `src/cine_forge/api/models.py` and `ui/src/lib/types.ts` if Tasks 1-2 leave an unavoidable post-intake state that current `health` + `health_details` cannot represent honestly.
- **Impact / risk**:
  - `ProjectHome.tsx` (588 lines) and `AppShell.tsx` (683 lines) are already oversized. Prefer small helper extraction over inline condition growth.
  - Keep API contract changes conditional; avoid inventing onboarding-only state unless current typed fields are proven insufficient.
- **Done**:
  - Home, inbox, and shell badge agree on the post-onboarding attention count.
  - A fresh successful onboarding path shows no generic attention debt banner driven only by system churn.

### Task 4 — Regression Coverage and Verification

- **Files**: `tests/unit/test_scene_analysis_module.py`, `tests/unit/test_artifact_persister.py` only if persister behavior changes, `tests/integration/test_world_building_integration.py`
- **Change**:
  - Add a unit test proving per-scene outputs exclude `scene_index` lineage while the updated `scene_index` output still includes the expected refs.
  - Add an integration regression for `mvp_ingest -> world_building` that asserts latest scene groups are not stale and `project_config` is current on a fresh project.
  - Use browser verification on the seeded onboarding path; capture screenshot and console status. Fallback runbook: `docs/runbooks/browser-automation-and-mcp.md`.
- **Done**:
  - Regression tests fail on current baseline, then pass on the fix.
  - Browser verification on `/the-mariner` or an equivalent seeded project confirms the generic attention banner is gone or replaced by a concrete artifact-specific issue.

### Structural Health Check

- Planned touch points and current sizes:
  - `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — 612
  - `src/cine_forge/driver/artifact_persister.py` — 249
  - `src/cine_forge/api/artifact_manager.py` — 553, only if substrate and recipe fixes still leave ambiguous onboarding attention
  - `src/cine_forge/api/models.py` — 489, only if new typed actionability fields are required
  - `ui/src/lib/types.ts` — 600, only if new typed actionability fields are required
  - `ui/src/lib/health.ts` — 50
  - `ui/src/pages/ProjectHome.tsx` — 588
  - `ui/src/pages/ProjectInbox.tsx` — 462
  - `ui/src/components/AppShell.tsx` — 683
  - `tests/unit/test_scene_analysis_module.py` — 331
  - `tests/unit/test_artifact_persister.py` — 198
  - `tests/integration/test_world_building_integration.py` — 122
- Oversized-file rule:
  - `scene_analysis_v1`, `artifact_manager.py`, `ProjectHome.tsx`, `AppShell.tsx`, and `ui/src/lib/types.ts` need surgical edits.
  - If Task 3 requires more than a small helper extraction, pause and split the UI work rather than growing those files blindly.

### Redundancy / Removal Plan

- Remove any one-off onboarding attention filtering duplicated across home, inbox, and shell.
- Do not leave a parallel frontend-only "ignore this stale" special case once the substrate/recipe fix exists.
- If `artifact_manager.py` needs a temporary rule during implementation, remove it once the substrate and recipe changes prove sufficient or record a concrete follow-up.

### Checks and Human-Approval Blockers

- Required checks:
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Browser verification plan:
  - Open the seeded project home
  - Run `basic breakdown`, then `deep breakdown`
  - Verify home, inbox, and shell badge counts
  - Inspect console and capture a screenshot
- No new dependency or external API blocker is expected.
- Only notable design risk: whether `project_config` can be safely refreshed on later reruns. If metadata does not let us distinguish fresh auto-generated config from curated config, stop and surface the narrower choice before implementing that part.

## Work Log

20260401-1642 — triage: created from inbox report that `/the-mariner` basic breakdown followed by deep breakdown ended with `Artifact Health / 14 artifacts need attention.` Existing homes checked: Story 062 owns the tier split, Story 031 owns health propagation, and Story 127 owns shared health semantics, but no current story owns self-inflicted onboarding attention debt. Decision=`new Pending story` because this is a golden-path trust break, not a side issue. Next=`/build-story` when ready.
20260401-1948 — exploration: reproduced the user-visible failure against real captured projects `the-mariner-63` and `the-mariner-64` via `ArtifactManager.list_artifact_groups()`. Measured baseline on `the-mariner-64` = `156` total groups, `14` attention groups, `0` `stage_review` groups. Attention set was 13 latest `scene:v2` groups plus `project_config:project:v1`, all `stale` with `stale_cause = scene_index:project:v2`. Inspected artifact metadata and graph JSON; confirmed `scene_analysis_v1` writes per-scene outputs with inherited `scene_index:v1` lineage, which matches Story 062's known remaining issue about sibling self-staleness. Also inspected `recipe-world-building.yaml` and confirmed it updates `scene_index` but never refreshes `project_config`, explaining the final stale config item. Next=`write plan, fold AppShell alignment into scope, and stop at human gate before implementation`.
20260401-2005 — planning: replaced placeholder plan with repo-specific implementation order. Chosen approach=`pure code` because the bug lives in lineage truth, recipe ownership, and shared UI semantics, not model reasoning. Planned fix order=`scene lineage -> project_config refresh guard -> shared UI helper -> regression/browser verification`. Added a small scope expansion to include `AppShell.tsx` so shell badge counts do not drift from home/inbox after the fix. Remaining risk=`safe project_config refresh on later reruns if a user has curated config`; if metadata is insufficient, implementation should stop and surface that narrower choice instead of guessing. Next=`human approval for implementation`.
20260401-2138 — implementation: fixed the false scene stale chain at the source by adding `exclude_upstream_lineage_types=["scene_index"]` to per-scene outputs in `scene_analysis_v1`, then added a guarded `project_config` refresh path that only runs during deep breakdown when the latest config is both confirmed and system-owned. Wired `recipe-world-building.yaml` to refresh `project_config` after `analyze_scenes`, which clears the remaining onboarding-owned stale config without clobbering human-owned configs. Centralized shared UI semantics in `ui/src/lib/health.ts` and switched `ProjectHome`, `ProjectInbox`, and `AppShell` to consume the same actionable-health/review/gate helpers. Also fixed `_SceneEnrichment.model_rebuild()` so the mock integration path does not depend on import order. Evidence=`24 targeted unit tests passed`, `mocked deep-breakdown integration passed`. Next=`full validation + runtime smoke`.
20260401-2326 — verification: `make test-unit PYTHON=python` passed (`633 passed, 141 deselected`), `PYTHONPATH=src python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` passed with 5 pre-existing `react-refresh/only-export-components` warnings in unrelated UI files, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with an existing Vite chunk-size warning only. Runtime smoke: backend served `GET /api/health -> {"status":"ok","version":"2026.04.01-02"}`, seeded project `story-142-smoke` via mocked onboarding under this worktree, and `GET /api/projects/story-142-smoke/artifacts` reported `13` total groups, `0` actionable attention groups, `8` scene groups, and `project_config v2` with `health=valid`. Frontend fallback checks passed: `http://127.0.0.1:5173/story-142-smoke` returned `<title>CineForge` and `GET /src/main.tsx` returned HTTP `200`. Browser MCP verification was attempted, but Playwright was blocked by a stale locked profile; followed `docs/runbooks/browser-automation-and-mcp.md`, ran `python3 scripts/reset_playwright_mcp.py`, which terminated the stale daemons, and the MCP transport then closed for this session before a screenshot/console capture could be re-established. Redundancy outcome=`removed duplicated health/review/gate derivation across home/inbox/shell by centralizing helpers in ui/src/lib/health.ts`. Next=`/validate`.
20260401-2348 — validation: reran required checks in this validation pass. Canonical `.venv` commands were unavailable in this worktree (`make test-unit PYTHON=.venv/bin/python` failed with `.venv/bin/python: No such file or directory`; `.venv/bin/python -m ruff check src/ tests/` failed for the same reason), so fallback checks used the active Python: `make test-unit PYTHON=python` passed (`633 passed, 141 deselected, 1 warning`), `PYTHONPATH=src python -m ruff check src/ tests/` passed, and `PYTHONPATH=src python -m pytest tests/unit/test_scene_analysis_module.py tests/unit/test_project_config_module.py tests/integration/test_world_building_integration.py` passed (`25 passed`). UI checks also passed: `pnpm --dir ui run lint` with the same 5 pre-existing React refresh warnings in unrelated files, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` with the existing Vite chunk-size warning only. Fresh fallback runtime checks passed too: `GET /api/health` returned `{"status":"ok","version":"2026.04.01-02"}`, `http://127.0.0.1:5173/story-142-smoke` returned `<title>CineForge</title>`, `GET /src/main.tsx` returned HTTP `200`, and `GET /api/projects/story-142-smoke/artifacts` reported `13` groups, `0` actionable attention groups, `8` scene groups, and `project_config v2` with `health=valid`. Browser verification is still blocked: after rerunning `python3 scripts/reset_playwright_mcp.py` in this validation pass, Playwright MCP `browser_navigate` still failed with `Transport closed`, so no screenshot or console capture could be collected. Recommendation=`keep story open until browser verification can be completed or explicitly waived, then run /mark-story-done if the UI check is clean`.
20260401-2358 — browser verification + close-out: completed the blocked UI proof with local Python Playwright instead of MCP because the session transport stayed closed. First fixed the browser fixture by uploading `tests/fixtures/sample_screenplay.fountain` to `story-142-smoke` via `POST /api/projects/story-142-smoke/inputs/upload`, which let the real Home view render from the seeded artifacts. Browser evidence then passed with no console or page errors: Home at `http://127.0.0.1:5173/story-142-smoke` showed `Artifact Health` with `All 13 artifacts are current.`, no `need attention` copy, and the shell nav link text remained plain `Inbox`; Inbox at `http://127.0.0.1:5173/story-142-smoke/inbox` showed `All caught up` / `No unread items need attention right now.` Screenshots saved at `tmp/story-142-browser/story-142-smoke-home-fixed.png` and `tmp/story-142-browser/story-142-smoke-inbox.png`. With browser verification complete, this story now closes cleanly. Next=`/check-in-diff`.
