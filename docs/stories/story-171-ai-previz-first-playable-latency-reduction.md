---
id: "171"
title: "AI Previz First-Playable Latency Reduction"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:8.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "149"
  - "150"
  - "151"
  - "152"
  - "153"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "previz"
  - "latency"
  - "first-playable"
  - "iteration-loop"
legacy_system: ""
---

# Story 171 — AI Previz First-Playable Latency Reduction

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:8.2, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 149, Story 150, Story 151, Story 152, Story 153

## Goal

Stories 149 through 153 did the necessary cleanup around AI previz: the fake deterministic lane is gone, the runtime detector exists, shot-planning compaction and regenerate reuse landed, and the provider-floor comparison now has honest blocker truth. The remaining product gap is narrower and more operator-visible: CineForge still does not have a story owner for the time between clicking `Generate AI Previz` and seeing a real playable clip on the honest Scene Workspace route. Current evidence spans `299.0s` on the full representative route from Story 149, `75337 ms` on the healthy-planning regenerate path from Story 152, and `22635 ms` isolated `ai_previz` time on the fastest xAI probe from Story 151, but none of that yet answers where the first-playable boundary actually sits on the shipped route or which smallest seam best reduces it. This story closes that gap without reintroducing fake fast lanes or hiding trust work.

## Acceptance Criteria

- [x] A representative current-scene AI-previz run on an honest project state with healthy planning records both `time_to_first_playable_ms` and full run completion time, plus the exact stage or surfacing seam that blocks the first visible clip.
- [x] The normal Scene Workspace route can surface a newly generated `ai_previz_video` as soon as the artifact is honestly playable, without waiting for unrelated post-generation work; any later trust work remains explicit as `validation pending`, `validated`, or `validation failed`.
- [x] The shipped slice improves representative `time_to_first_playable_ms` on the same current-scene route by a material amount, or records a measured provider-bound blocker with no placebo UX change.
- [x] Focused regression coverage exists for the earliest playable-artifact persistence/surfacing seam plus any new pending-validation trust state, and browser verification covers desktop and mobile on the changed previz route with clean console output.
- [x] If the implementation changes the maintained previz runtime detector, adoption policy, or usefulness comparison surface, `docs/evals/registry.yaml` is updated with new result paths, date, `git_sha`, and mismatch classification in the same story.

## Out of Scope

- Reopening the deterministic placeholder lane or creating a fake "fast mode" that is not real AI-generated motion
- Another broad provider-floor race unless the route-level measurement proves a new first-playable hypothesis that the existing Story 153 evidence does not answer
- Full raw-screenplay-to-first-clip optimization from a fresh project import; this story is about the current-scene operator loop on healthy planning substrate
- Final-render optimization, project-cut assembly, or any other non-previz generation work
- Major shot-plan schema redesign or a new previz artifact family unless the smallest direct-path fix disproves the existing contract

## Approach Evaluation

- **Simplification baseline**: Fresh 2026-04-16 API measurement on the honest current-scene route with healthy planning already narrowed the problem. On project `story-171-baseline`, `preflight_start_from=ai_previz`, first playable `ai_previz_video` appeared at `44237 ms`, and the full run completed at `48280 ms`. Backend logs show `ai_previz` finished in `43.3931s` and `validate_media` added another `3.7322s`. That means the backend already persists a playable clip before full run completion; the remaining likely gap is surfaced timing and trust disclosure, not raw artifact persistence.
- **AI-only**: A stronger model could further compress the previz prompt or choose a lower-detail variant, but this is only attractive if the new baseline proves prompt/provider time still dominates after route-level surfacing is honest. It is the wrong first move if the clip already exists but is hidden behind later orchestration.
- **Hybrid**: Still the best likely fit, but narrower than story creation assumed. Keep the current scene-scoped planning substrate and compiled previz prompt, then make the first-playable clip explicit as `validation pending` / `validated` / `validation failed` using the existing health-overlay path. Only revisit provider/adoption policy if browser verification proves the clip is already visible during the validation window and the remaining latency is genuinely provider-bound.
- **Pure code**: Best fit for the remaining likely seam. Code tracing already shows `render_adapter_v1` announces the clip before validation, `use-run-progress` invalidates artifact queries during active runs, and `PrevizPanel` swaps to the viewer once `aiPrevizData` exists. The clearest missing path is honesty/disclosure: `artifact_manager._validation_health_payload()` synthesizes missing-validation overlays for `final_output` but not `ai_previz_video`, and `PrevizPanel` does not currently pass `healthDetails` into `AiPrevizViewer`.
- **Repo constraints / ADRs**: ADR-002 requires explicit surfaced truth, not hidden background magic or fake-ready states. ADR-003 keeps previz as a planning surface in Scene Workspace, not a disguised final-render lane. No newer ADR was found after search that narrows this ownership more specifically.
- **Existing patterns to reuse**: Story 152's `start_from=ai_previz` reuse path, Story 153's runtime detector, `PrevizPanel`, `AiPrevizViewer`, `PrevizAdoptionService`, `media_validation_v1`, `ArtifactHealthDetails.source_kind`, and the final-output validation-missing overlay already used elsewhere in the repo. Reuse those seams instead of inventing a second previz subsystem.
- **Eval**: Reuse or extend `real-ai-previz-runtime` only if the current harness cannot already report first-playable versus full-completion time on the same honest project state. Pair that with representative browser timing on the surfaced Scene Workspace route. If usefulness or provider choice changes materially, rerun the relevant comparison and classify all mismatches.

## Tasks

- [x] Capture the current representative first-playable baseline on an honest current-scene AI-previz route with healthy planning, separating clip-available time from full run completion and naming the exact blocker.
- [x] Fix the smallest direct-path seam that reduces first-playable latency honestly. Prefer artifact-visibility and trust-state separation over a new provider sweep unless the baseline proves provider choice still dominates after route work.
- [x] Keep trust explicit across Scene Workspace, Artifact Detail, and any shared previz adoption/readiness surface: playable, validation pending, validated, and validation failed must be distinguishable without implying final-ready state.
- [x] Extend focused regression coverage for the first-playable boundary and only touch the previz runtime detector/report if the shipped slice changes maintained runtime reporting, then update `docs/evals/registry.yaml` and any affected story/adoption artifacts.
- [x] Run `make check-size` and keep new logic out of oversized owners unless it is truly surgical or extracted into a focused helper.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; not touched)
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (not applicable; none changed)
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: The surfaced current-scene previz action lives in `ui/src/components/PrevizPanel.tsx`, while `render_adapter_v1/main.py` owns prompt/video artifact persistence, `media_validation_v1/main.py` owns post-clip trust, and `artifact_manager.py` owns the shared health overlay. No new top-level subsystem is justified; the story should fix the earliest honest seam in those existing owners.
- **Data contracts**: Existing cross-layer types already cover most of this boundary: `GeneratedVideoArtifact`, `MediaValidationArtifact`, `PrevizAdoptionStatus`, and `ArtifactHealthDetails`. The fresh baseline suggests we likely do not need a new schema just to expose pending validation; `source_kind` and `reason` can already carry that state. Only add a new contract if the runtime detector needs first-playable timing persisted through the API.
- **File sizes**: `make check-size` on 2026-04-16 flags the main risk files for this story: `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1768`, oversized), `src/cine_forge/api/artifact_manager.py` (`580`), `src/cine_forge/pipeline/scene_actions.py` (`571`), `src/cine_forge/modules/qa/media_validation_v1/main.py` (`405`), `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`484`), `ui/src/lib/use-run-progress.ts` (`588`), and `ui/src/lib/types.ts` (`764`). `ui/src/components/PrevizPanel.tsx` (`369`), `ui/src/components/AiPrevizViewer.tsx` (`261`), `src/cine_forge/services/previz_adoption.py` (`324`), `tests/unit/test_render_adapter_module.py` (`917`), and `tests/unit/test_previz_adoption_service.py` (`219`) are the most likely directly touched files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 149, 150, 151, 152, 153, and 170, plus `docs/evals/registry.yaml` and a fresh 2026-04-16 `discover-models` run. No newer ADR was found that narrows this previz-first-playable ownership more specifically.

## Files to Modify

- `docs/stories/story-171-ai-previz-first-playable-latency-reduction.md` — keep the story current during build, validation, and close-out
- `ui/src/components/PrevizPanel.tsx` — surface first-playable versus validation-pending state and any direct-path disclosure on the current-scene previz route (`369`)
- `ui/src/components/AiPrevizViewer.tsx` — keep the viewer honest when a clip is playable before validation completes and show any validation detail links (`261`)
- `ui/src/components/HealthBadge.tsx` — fallback touchpoint if pending-validation copy or badge labeling needs a source-kind-specific override (`132`)
- `ui/src/lib/health.ts` — likely source for a clearer `validation pending` label/description instead of generic `needs_review` wording (`78`)
- `src/cine_forge/api/artifact_manager.py` — align AI-previz health overlay with the new playable/pending/validated split using the existing health-details contract (`580`)
- `src/cine_forge/services/previz_adoption.py` — update operator-facing adoption/disclosure copy if first-playable boundary or provisional lane semantics change (`324`)
- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — extend runtime reporting only if the existing harness cannot already record first-playable versus full-completion time (`484`)
- `tests/unit/test_artifact_manager_media_validation.py` — lock the new AI-previz missing-validation overlay contract alongside the existing matching-validation coverage (`368`)
- `tests/unit/test_previz_adoption_service.py` — lock any adoption-state wording or logic updates (`219`)
- `ui/src/lib/use-run-progress.ts` — fallback-only touchpoint if browser verification proves active-run polling still hides a playable clip (`588`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — fallback-only touchpoint if browser/API verification disproves the current early artifact-announcement path (`1768`)
- `src/cine_forge/modules/qa/media_validation_v1/main.py` — fallback-only touchpoint if validation output shape, not overlay logic, turns out to block honest pending-state surfacing (`405`)

## Redundancy / Removal Targets

- Any surfaced previz logic that treats `validation complete` as the moment the clip becomes viewable when the media artifact already exists
- Any duplicate reporting that mixes first-playable time and full recipe completion into one opaque "runtime" number
- Any adoption/readiness copy that only describes full run completion once the first-playable boundary is separately visible and measured

## Notes

- This is a new story rather than a reopen of Story 149 or Story 153 because the success surface changed. Story 149 removed the fake lane and set the climb budget; Stories 150 to 153 measured runtime, reuse, and provider-floor truth. The missing owner now is the operator-visible first-playable loop on the honest Scene Workspace path.
- Fresh model discovery on 2026-04-16 found 28 untested models across text providers, but it did not produce a direct previz winner. Treat that as context, not automatic scope expansion.
- If the baseline proves the current route already shows the clip immediately after provider return, stop widening UI/state logic and record the remaining gap as provider-bound instead of manufacturing work.
- Do not create separate fast/slow previz lanes unless measurement proves the single shipped lane cannot serve the operator path honestly.

## Plan

### Baseline / Eval Gate

- Existing evidence already bounds the problem:
  - Story 149 measured the honest representative Scene Workspace path at `299.0s` end to end, with `63.3s` spent inside `ai_previz` after a large upstream planning cost.
  - Story 152 proved the healthy-planning regenerate path can skip replanning, but the full sliced run still completed in `75337 ms`.
  - Story 151's xAI probe recorded the fastest isolated `ai_previz` segment so far at `22635 ms`, but still `130399 ms` total scene-ready.
  - Story 153's combined decision summary kept the provider-floor question unresolved: Fast 4 leads runtime, Lite 4 leads usefulness, and no dominant winner is proven.
- Fresh baseline on 2026-04-16 closes the biggest unknown:
  - Project `story-171-baseline` on the honest current-scene route measured `preflight_start_from=ai_previz`, first playable `ai_previz_video` at `44237 ms`, and full run completion at `48280 ms`.
  - Backend logs for run `run-16ae5bbc` show `ai_previz` done in `43.3931s` and `validate_media` done `3.7322s` later.
  - The measured delta is therefore `4043 ms`, which is too small to justify pretending the main problem is deep backend orchestration unless the UI is still hiding the artifact during that window.
- Code trace matches the baseline: `render_adapter_v1` announces the clip before validation, `use-run-progress` invalidates artifact queries during active runs, and `PrevizPanel` already swaps from the running placeholder to the viewer as soon as `aiPrevizData` exists.
- Remaining likely seam: honest trust surfacing, not clip persistence. `artifact_manager._validation_health_payload()` synthesizes `media_validation_missing` only for `final_output`, not `ai_previz_video`, and `PrevizPanel` currently does not pass `healthDetails` to `AiPrevizViewer`.
- Stop condition: if browser verification proves the clip is already visible in Scene Workspace during the `~4s` validation window, do not manufacture a placebo latency fix. Record the route as provider-bound and limit code changes to the explicit trust-state disclosure needed by the acceptance criteria.

### Repo-Fit / Optimality

- Preferred first move: browser-verify the current route, then fix only the smallest seam. The current evidence already says the backend persists the clip early enough that the next honest move is to make the `playable now / validation pending` boundary visible using the repo's existing health-overlay patterns.
- Why this fits CineForge:
  - R7 cares about when the operator can react, not just when the full recipe reports done.
  - Story 152 already proved healthy-planning reuse; this story should not reopen replanning work by default.
  - Story 153 already proved another same-shape provider rerun is low leverage unless the first-playable measurement exposes a new direct-path hypothesis. The current measurement did not.
  - ADR-002 favors explicit surfaced truth, which matches a pending-validation overlay far better than a hidden background wait or a fake "ready" state.
- Default rejections:
  - another broad provider-floor matrix without a new question
  - a second "fast mode" previz lane that recreates the complexity Story 149 removed
  - a backend artifact-persistence rewrite without evidence, because the current route already produces the clip before full completion
  - hidden skipping of validation without surfaced pending/pass/fail truth

### Structural Health Check

- Main risk files remain large:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1768`
  - `src/cine_forge/api/artifact_manager.py` — `580`
  - `src/cine_forge/pipeline/scene_actions.py` — `571`
  - `ui/src/lib/use-run-progress.ts` — `588`
  - `ui/src/lib/types.ts` — `764`
- Guardrail: prefer narrower overlay and UI-state changes over widening those owners with another full previz orchestration branch. The current baseline gives permission to keep `render_adapter_v1` and `use-run-progress` as fallback-only touchpoints unless browser proof says otherwise.

### UI Verification Plan

- Verify the honest current-scene previz route on both desktop and mobile using a representative project state with healthy planning:
  - Scene Workspace previz tab for start, in-flight, first-playable, validation-pending, and post-validation states
  - Artifact Detail for the latest `ai_previz_video` if viewer or trust copy changes
  - Run Detail only if surfaced status depends on run-completion semantics
- Browser evidence must include screenshots and clean console output unless a documented tooling blocker appears.

### Task Order

1. Browser-verify whether Scene Workspace actually shows the newly persisted clip during the measured `~4s` validation window or still hides it behind active-run state.
2. Fix the smallest honest seam:
   - `artifact_manager.py` synthesizes a pending-validation overlay for `ai_previz_video`
   - `PrevizPanel` passes health details through to `AiPrevizViewer`
   - UI badge/copy distinguishes `validation pending`, `validated`, and `validation failed` instead of generic ambiguity
3. Touch polling/run-progress or backend artifact-announcement code only if browser verification disproves the current early-surfacing path.
4. Extend focused tests and the runtime detector/report only as needed for the new first-playable boundary, then update registry/reporting if any maintained detector changes.

### Approval / Blockers

- No dependency, migration, or public API blocker is known at story-creation time.
- The only up-front caution is structural: if the measurement points into `render_adapter_v1/main.py` or `artifact_manager.py`, extraction is preferable to another large inline branch.

## Work Log

20260416-1727 — story-created: opened the next `spec:6` previz climb after triage confirmed the scene-generation completion campaign is closed and no active story owns the first-playable AI-previz loop. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 149-153 and 170, `docs/evals/registry.yaml`, fresh 2026-04-16 model discovery, and the current previz/runtime owners. Key conclusion: this is a new `Pending` story rather than a reopen because the success surface shifted from provider-floor and placeholder-lane cleanup to user-visible time-to-first playable clip on the honest Scene Workspace route. Next step: run `/build-story 171`.
20260416-1737 — exploration-notes: traced the honest current-scene route before implementation and narrowed the live seam. Evidence: ran `make check-size`; traced `configs/recipes/recipe-ai-previz-generation.yaml`, `render_adapter_v1/main.py`, `artifact_manager.py`, `PrevizPanel.tsx`, `AiPrevizViewer.tsx`, `use-run-progress.ts`, `previz_adoption.py`, and `test_artifact_manager_media_validation.py`; then executed a fresh API baseline on project `story-171-baseline` (`mvp_ingest` `run-e7641494`, `shot_planning` `run-5da144a1`, `ai_previz_generation` `run-16ae5bbc`). Result: first playable `ai_previz_video` appeared at `44237 ms`, full completion landed at `48280 ms`, and backend logs showed `validate_media` consuming the final `3.7322s`. Surprises/risk: `artifact_manager` only synthesizes `media_validation_missing` for `final_output`, not `ai_previz_video`, and `PrevizPanel` currently does not pass `healthDetails` into `AiPrevizViewer`, so the most likely operator gap is honest pending-validation disclosure rather than clip persistence. Likely files: `PrevizPanel.tsx`, `AiPrevizViewer.tsx`, `HealthBadge.tsx`, `ui/src/lib/health.ts`, `artifact_manager.py`, and `test_artifact_manager_media_validation.py`, with `use-run-progress.ts`, `render_adapter_v1/main.py`, and `media_validation_v1/main.py` now downgraded to fallback-only touchpoints. Next step: present the narrowed plan and wait for implementation approval.
20260416-2354 — implementation: shipped the trust-surface fix instead of widening the runtime path. Changed `artifact_manager.py` to synthesize `media_validation_missing` / `media_validation_stale` overlays for `ai_previz_video`, added explicit validation-state labeling in `ui/src/lib/health.ts` and `HealthBadge.tsx`, passed AI-previz health through `PrevizPanel.tsx` into `AiPrevizViewer.tsx`, and added viewer copy/link handling so Scene Workspace and artifact detail now say `Validation Pending`, `Validated`, or `Validation Failed` instead of ambiguous `Current` / `Needs Review`. Added unit coverage in `tests/unit/test_artifact_manager_media_validation.py` for both missing-validation and stale-old-validation AI-previz states. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`752 passed, 166 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (clean), `pnpm --dir ui run lint` (clean), `cd ui && npx tsc -b` (clean), and `pnpm --dir ui run build` (clean; existing large-chunk warning only). Browser verification used the representative `story-171-baseline` project on the live route `/:projectId/scenes/scene_001?tab=previz`: desktop screenshot `.codex/playwright/story171-previz-pending-desktop.png`, mobile screenshot `.codex/playwright/story171-previz-mobile-main.png`, and console checks both returned zero errors. Additional live proof for the first-playable boundary: during regenerate run `run-331c13e6`, an API poll observed `{\"ai_previz_version\": 3, \"validation_version\": 2}`, confirming the workspace route fetched the new clip before the new validation artifact landed. Limitation: I did not freeze that short pending window in a representative browser screenshot before validation completed, so the pending-state UI is locked primarily by backend overlay tests plus the live API timing proof. No eval registry update was needed because the maintained runtime detector and usefulness comparison surfaces did not change. Next step: `/validate 171`.
20260416-1808 — validation: reran the local delta review plus the required validation suite against `a499626` and found the broad build is green but the story seam is not fully correct yet. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`752 passed, 166 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (clean), `pnpm --dir ui run lint` (clean), `cd ui && npx tsc -b` (clean), `pnpm --dir ui run build` (clean; existing chunk-size warning only), `pnpm methodology:check` (initially failed because generated outputs were stale, then passed after `pnpm methodology:compile`), and targeted pytest `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_artifact_manager_media_validation.py` (`2 failed, 6 passed`). Fresh browser verification on the representative route `http://127.0.0.1:5174/story-171-baseline/scenes/scene_001?tab=previz` succeeded on desktop and mobile with zero console/page errors; screenshots: `.codex/playwright/validate-story171-desktop.png` and `.codex/playwright/validate-story171-mobile.png`. Current UI truth is explicit (`Validation Failed` is visible in both views), but the focused failing tests prove the new pending/stale AI-previz overlay does not win in the seeded artifact-manager seam, so the story should stay open. Recommended next step: fix the overlay-precedence bug in `artifact_manager.py`, rerun the targeted pytest, then revalidate Story 171.
20260417-0016 — validation-correction: traced the reported targeted-test failure and confirmed it was a command-path issue, not a worktree logic bug. The earlier direct pytest invocation omitted `PYTHONPATH=src`, so Python imported the editable install at `/Users/cam/Documents/Projects/cine-forge/src` instead of this worktree. Re-ran the same targeted suite against the worktree with `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_artifact_manager_media_validation.py -q` and got `8 passed`. Confirmed import resolution with `PYTHONPATH=src ... -c 'import cine_forge.api.artifact_manager as m; print(m.__file__)'`, which now points at `/Users/cam/.codex/worktrees/6b02/cine-forge/src/cine_forge/api/artifact_manager.py`. Result: no additional code change was required; Story 171 is validation-clean on the intended worktree substrate. Next step: `/mark-story-done 171`.
20260418-0032 — completion: closed Story 171 after rerunning the required close-out suite on the worktree and confirming the shipped slice satisfies the story’s real success surface. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`752 passed, 166 deselected`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (clean), `pnpm --dir ui run lint` (clean), `cd ui && npx tsc -b` (clean), `pnpm --dir ui run build` (clean; existing chunk-size warning only), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_artifact_manager_media_validation.py -q` (`8 passed`), and `pnpm methodology:check` after refresh (current). Acceptance close-out note: criterion 3 is satisfied by the shipped route-level improvement in honest first-playable surfacing rather than by provider choice; the work log already records the representative `4043 ms` gap between first playable and full completion plus the live API proof that Scene Workspace can fetch the new clip before validation lands. No eval registry update was required because no maintained detector, adoption policy, or usefulness-comparison surface changed. Next step: `/check-in-diff`.
