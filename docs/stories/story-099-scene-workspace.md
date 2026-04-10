---
id: "099"
title: "Scene Workspace — Readiness Honesty"
status: "Done"
priority: "High"
ideal_refs:
  - "R11 (production readiness per scene)"
  - "R12 (transparency and control)"
  - "R7 (iterative refinement)"
spec_refs:
  - "spec:4.10"
  - "spec:5.2"
  - "spec:5.4"
  - "spec:5.5"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "085"
  - "094"
  - "095"
  - "097"
  - "023"
  - "144"
category_refs:
  - "spec:4"
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-workspace"
  - "readiness"
  - "review-loop"
legacy_system: ""
---

# Story 099: Scene Workspace — Readiness Honesty

**Priority**: High
**Status**: Done
**Created**: 2026-02-27
**Reopened**: 2026-04-10 — the repo now has canonical green-readiness logic plus partial review controls, but the main Scene Workspace still computes readiness from artifact existence only and several concern-group surfaces cannot complete the review loop.
**Source**: Reopened from `/triage` after Story 023 and Story 144 made the remaining `spec:5.5` gap concrete instead of speculative.
**Spec Refs**: spec:4.10 (concern groups), spec:5.2 (explanation), spec:5.4 (human interaction), spec:5.5 (readiness indicators)
**Ideal Refs**: R11 (production readiness per scene), R12 (transparency and control), R7 (iterative refinement)
**ADR Refs**: ADR-002 (goal-oriented navigation), ADR-003 (film elements / Scene Workspace)
**Depends On**: Story 085 (pipeline graph), Story 094 (concern-group schemas + readiness model), Story 095 (Intent / Mood layer), Story 097 (artifact editing), Story 023 (Character & Performance first shipped slice), Story 144 (previz trust guardrails)

---

## Goal

Make Scene Workspace readiness honest end to end. The repo already has the canonical `compute_scene_readiness()` model and per-artifact `user_approved` state, but the main workspace summary still collapses readiness to red/yellow based on artifact existence, and review controls are inconsistent across concern groups. This story closes that gap so the five scene concern groups can actually mean:

- **Red**: nothing meaningful exists yet
- **Yellow**: AI draft or partial guidance exists
- **Green**: a human explicitly reviewed and approved the latest direction

The point is not to redesign the workspace. The point is to stop lying about readiness.

## Why (Ideal Alignment)

Story 099 originally shipped the Scene Workspace with the green state explicitly deferred because the workspace did not yet have an honest approval surface or a shared summary contract. That deferral is now the clearest remaining `spec:5.5` gap.

Current repo evidence:

- `src/cine_forge/schemas/readiness.py` already defines the canonical red/yellow/green contract and has focused unit coverage.
- `ui/src/components/CharacterPerformancePanel.tsx` already supports Draft/Reviewed toggling via immutable artifact edits.
- `ui/src/components/StoryWorldPanel.tsx` shows Draft/Approved state but cannot toggle it.
- `ui/src/pages/SceneWorkspacePage.tsx` still computes readiness with a local `getReadiness()` helper that only returns `red` or `yellow` from artifact presence.
- `ui/src/components/DirectionAnnotation.tsx` hides `user_approved`, so the workspace cannot present a coherent review loop for Look & Feel, Sound & Music, or Rhythm & Flow.

This means the missing work is no longer architecture discovery. The schema, edit path, and at least one reviewed concern-group panel already exist. What is missing is a shared readiness surface and consistent review ownership across the workspace.

Closing that gap moves CineForge toward the Ideal in three ways:

- It makes Scene Workspace honest about what is AI-improvised versus actually operator-reviewed.
- It makes direct human control visible and actionable instead of hiding review state inside individual artifacts.
- It preserves creative flow by letting users review concern groups in place instead of inferring readiness from scattered artifact pages.

## Acceptance Criteria

- [x] Scene Workspace summary dots and concern-group tab indicators show canonical red/yellow/green readiness for all five concern groups, based on the latest artifact payloads and `user_approved`, not artifact existence alone.
- [x] A shared typed backend/API readiness surface exists for per-scene concern-group readiness. Scene Workspace no longer reimplements readiness heuristics inline, and any future consumer can reuse the same contract.
- [x] Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, and Story World each expose a consistent Draft/Reviewed control using immutable artifact edits. A group cannot appear green unless the latest relevant artifact version is explicitly reviewed.
- [x] Reviewing or unreviewing a concern group updates the Scene Workspace readiness summary immediately without requiring a manual page reload.
- [x] Missing artifacts, AI-authored drafts, and project-scoped Story World data remain honest. The UI does not silently mark green because some upstream artifact exists.
- [x] Focused regression coverage exists for readiness service/API behavior, review-toggle persistence, and workspace summary rendering, and browser verification covers the Scene Workspace flow in both desktop and mobile layouts with clean console output.

## Out of Scope

- Rebuilding the Scene Workspace layout, tabs, or navigation model
- New AI concern-group generation logic or prompt-quality improvements
- Reworking previz adoption logic, render trust semantics, or pipeline graph policy beyond what the readiness surface directly needs
- A broader Intent / Mood approval redesign outside the five scene concern groups
- New promptfoo evals or creative-quality benchmarks unless implementation unexpectedly changes model behavior

## Approach Evaluation

- **Simplification baseline**: no new AI step is needed. The repo already has deterministic readiness computation in `src/cine_forge/schemas/readiness.py`; the missing work is surfacing and reusing that truth coherently.
- **AI-only**: wrong fit. This is not an authoring problem or a semantic interpretation gap. Letting a model "decide" readiness would make the product less honest.
- **Hybrid**: unnecessary for the first honest slice. A later follow-up could add natural-language explanations of why a group is yellow or red, but the core truth is deterministic.
- **Pure code**: strongest fit. Existing artifact payloads plus `user_approved` flags are enough to compute and persist the right state.
- **Repo constraints / ADRs**: ADR-002 and ADR-003 both require the Scene Workspace to show what is specified, what AI is improvising, and what the user has actually reviewed. Avoid deepening already-large files: `ui/src/pages/SceneWorkspacePage.tsx` (`890`), `ui/src/components/StoryWorldPanel.tsx` (`598`), `ui/src/components/CharacterPerformancePanel.tsx` (`458`), `ui/src/lib/types.ts` (`750`), `src/cine_forge/api/models.py` (`644`), `src/cine_forge/api/service.py` (`1302`), and `src/cine_forge/api/app.py` (`732`) all tripped `make check-size` on 2026-04-10.
- **Existing patterns to reuse**: `compute_scene_readiness()`, `useEditArtifact`, the Character & Performance reviewed/draft toggle, the typed router pattern in `src/cine_forge/api/routers/intent_mood.py`, and the small shared-status pattern used for previz adoption.
- **Eval**: deterministic validation is the correct discriminator here. Success should come from unit coverage plus browser verification, not a new LLM benchmark.

## Tasks

- [x] Confirm the shared readiness contract and add the narrowest backend owner for per-scene readiness summaries, reusing `compute_scene_readiness()` instead of duplicating field heuristics in the UI. Evidence: added `src/cine_forge/services/scene_readiness.py` and kept readiness computation anchored in `src/cine_forge/schemas/readiness.py`.
- [x] Expose a typed API route and frontend hook for scene readiness so Scene Workspace can load canonical red/yellow/green state without overloading the generic artifact-group summary endpoint. Evidence: added `src/cine_forge/api/routers/readiness.py`, frontend types in `ui/src/lib/types.ts`, API fetch in `ui/src/lib/api/artifacts.ts`, and `useSceneReadiness()` in `ui/src/lib/hooks/artifacts.ts`.
- [x] Replace the local red/yellow-only `getReadiness()` helper in `ui/src/pages/SceneWorkspacePage.tsx` with the shared readiness contract for summary dots and tab labels. Evidence: Scene Workspace now maps concern-group tab dots from `SceneReadiness` and only keeps red/yellow artifact-presence fallback for non-concern outputs.
- [x] Add or extract a reusable concern-group review-control seam so Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, and Story World all support the same Draft/Reviewed semantics through immutable artifact edits. Evidence: added `ui/src/components/ArtifactReviewControls.tsx` and reused it across generic concern-group tabs plus Story World and Character & Performance.
- [x] Keep Character & Performance aligned with the shared review semantics and close the missing Story World / generic concern-group approval gap without deepening oversized files unnecessarily. Evidence: removed duplicated approval UI from `CharacterPerformancePanel`, added Story World toggle parity, and kept `SceneWorkspacePage.tsx` changes to wiring plus the extracted control seam.
- [x] Add focused regression coverage for the readiness service/API, review-toggle persistence, and any extracted UI helper or component used by the workspace. Evidence: added `tests/unit/test_scene_readiness_api.py`, extended `tests/unit/test_readiness.py` with Story World narrative-rhythm coverage plus a no-characters Character & Performance case, and committed `scripts/story_099_scene_workspace_smoke.py` for the representative desktop/mobile workspace regression path.
- [x] Check whether the chosen implementation makes any existing code redundant; remove or narrow it if the shared readiness path supersedes it. Evidence: removed the page-local concern-group readiness heuristic and eliminated duplicated approval UI in Character & Performance.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`693 passed, 157 deselected`)
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` not needed — no agent tooling or project instructions changed in this story.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` after marking Story 099 Done refreshed `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`.
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` not needed — no evals or goldens changed.
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views, using a representative project state and recording any console blocker honestly. Evidence: committed and ran `scripts/story_099_scene_workspace_smoke.py` against a temp copy of `/Users/cam/Documents/Projects/cine-forge/output/the-mariner-50`; the Character & Performance artifact was produced through the normal `creative_direction` single-stage run path for `scene_001`; historical run cards rendered the stable unavailable fallback instead of polling dead runs; screenshots saved to `/tmp/story099-scene-workspace-desktop.png` and `/tmp/story099-scene-workspace-mobile.png`; browser/page/network error capture stayed clean with no 4xx/5xx responses.
- [x] Search all docs and update any related to what we touched. Evidence: reopened and maintained this story artifact as the implementation source of truth; `pnpm methodology:check` passed and no additional generated-surface change was required because status/refs stayed stable.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No existing artifact versions are mutated; review changes still create new immutable versions through the existing edit path.
  - [x] **T1 — AI-Coded:** Readiness ownership is explicit and typed across schema/service/API/UI seams, with a focused shared review-control component.
  - [x] **T2 — Architect for 100x:** This reuses the existing deterministic readiness model instead of adding new AI logic or another heuristic layer.
  - [x] **T3 — Fewer Files:** Added only one small backend seam and one small UI seam to avoid deepening already-oversized page/panel files.
  - [x] **T4 — Verbose Artifacts:** Work log now captures implementation, the Story World detector regression, static checks, and browser-blocker evidence.
  - [x] **T5 — Ideal vs Today:** The workspace now reports what is actually reviewed versus merely AI-authored, which is closer to the transparency/control ideal.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: canonical readiness should remain a deterministic schema/service concern, not another page-local heuristic. A small backend readiness seam is a better fit than widening the generic artifact-group listing.
- **Data contracts**: if readiness crosses backend -> UI, define a typed response first. Do not smuggle red/yellow/green through untyped maps or infer it ad hoc from artifact metadata.
- **UI ownership**: `SceneWorkspacePage.tsx` should only wire shared readiness into the existing screen. Review controls should live in a focused reusable component or narrow panel-level seam rather than being copy-pasted into multiple oversized files.
- **Story World nuance**: Story World remains project-scoped but still participates in scene readiness. The shared readiness owner must preserve that distinction instead of forcing Story World into a scene-scoped artifact shape.
- **Decision context**: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/decisions/adr-003-film-elements/adr.md`, Story 094, Story 023, Story 099's original close-out notes, and current UI/API code. No new ADR is needed.

## Files to Modify

- `docs/stories/story-099-scene-workspace.md` — reopen around the remaining readiness gap
- `src/cine_forge/schemas/readiness.py` — prefer reuse as-is; only touch if the shared output contract truly needs a narrow extension
- `src/cine_forge/api/models.py` — typed readiness response models
- `src/cine_forge/api/app.py` or new `src/cine_forge/api/routers/readiness.py` — expose the readiness API without growing the main app file unnecessarily
- `src/cine_forge/api/service.py` or a smaller helper/service seam — load latest concern-group artifacts and compute scene readiness
- `ui/src/lib/types.ts` — frontend readiness response types
- `ui/src/lib/api/artifacts.ts` or a small new readiness API module — scene-readiness fetch
- `ui/src/lib/hooks/artifacts.ts` or a small new readiness hook — query + invalidation wiring
- `ui/src/pages/SceneWorkspacePage.tsx` — replace the local heuristic and consume shared readiness
- `ui/src/components/DirectionAnnotation.tsx` and/or a new reusable concern-group review component — shared review controls for generic concern-group panels
- `ui/src/components/StoryWorldPanel.tsx` — align Story World review controls with the shared readiness loop
- `ui/src/components/CharacterPerformancePanel.tsx` — keep existing review toggle aligned with shared behavior
- `tests/unit/test_readiness.py` — extend only if the canonical contract changes
- `tests/unit/test_scene_readiness_api.py` or equivalent narrow test file — shared readiness service/API coverage
- Targeted UI/component tests as supported by the existing harness

## Redundancy / Removal Targets

- The local red/yellow-only `getReadiness()` helper in `ui/src/pages/SceneWorkspacePage.tsx`
- Any concern-group badges that say Draft/Approved without actually feeding the workspace summary
- Any duplicated review-toggle logic if a shared concern-group review seam replaces panel-specific copies
- Any UI path that hides `user_approved` in the exact place the workspace needs to surface review truth

## Notes

- This is intentionally a continuation of the original Scene Workspace line, not a new story shell. The original Story 099 explicitly shipped with green readiness deferred; the current repo now has enough substrate that deferral is the clearest remaining workspace honesty gap.
- The existence of `compute_scene_readiness()` plus the existing Character & Performance review toggle is the proof that this is now buildable. The missing work is not "invent a readiness model"; it is "stop bypassing the one we already have."
- If implementation proves that a dedicated readiness endpoint is unnecessary and the same typed contract can be surfaced through another narrow existing API without bloating it, that is acceptable. What is not acceptable is leaving readiness ownership inside `SceneWorkspacePage.tsx`.

## Plan

### Repo-Fit / Optimality Evidence

- The canonical readiness computation already exists and is well-tested. Reusing it is simpler and more honest than inventing a second readiness heuristic in the UI.
- The current generic artifact-group summary is intentionally thin (`artifact_type`, `entity_id`, `latest_version`, health). It is the wrong owner for payload-derived scene readiness unless the contract is deliberately extended.
- Character & Performance already demonstrates the correct mutation pattern: immutable artifact edit, immediate cache invalidation, and visible Draft/Reviewed state. That is the behavior to generalize, not replace.
- Story World and the generic concern-group panels are the current mismatch points: they expose some state but cannot complete the same review loop that Character & Performance already supports.

### Structural Health Check

- `make check-size` on 2026-04-10 flagged the main risk files for this work:
  - `ui/src/pages/SceneWorkspacePage.tsx` — `890`
  - `ui/src/components/StoryWorldPanel.tsx` — `598`
  - `ui/src/components/CharacterPerformancePanel.tsx` — `458`
  - `ui/src/lib/types.ts` — `750`
  - `src/cine_forge/api/models.py` — `644`
  - `src/cine_forge/api/service.py` — `1302`
  - `src/cine_forge/api/app.py` — `732`
- Plan implication: extract a narrow backend readiness seam and a small reusable review-control UI seam instead of piling more branching into the current page and panels.

### Implementation Order

1. **Shared readiness owner**
   - Add the narrowest typed backend owner for scene readiness.
   - Reuse `compute_scene_readiness()` and latest concern-group artifacts as the only source of truth.

2. **Typed API + frontend hook**
   - Expose the readiness contract through a focused API route and query hook.
   - Keep generic artifact-group summaries generic unless there is a strong reason to merge surfaces.

3. **Reusable review controls**
   - Extract or add a small reusable concern-group review control.
   - Generalize the Character & Performance reviewed/draft behavior instead of duplicating ad hoc toggles.

4. **Workspace wiring**
   - Replace the local red/yellow helper in `SceneWorkspacePage.tsx`.
   - Feed the shared readiness state into the summary bar and tab indicators.

5. **Verification**
   - Add focused backend coverage for readiness loading and API output.
   - Add the narrowest UI regression coverage available.
   - Browser-verify both desktop and mobile Scene Workspace on a representative project state.

## Work Log

20260227 — Story created per ADR-003 propagation. Scene Workspace concept came from the two-view architecture plus the new concern-group model.

20260301 — Phase 1/2 exploration + plan. Original implementation intentionally deferred green readiness because the workspace had no shared approval signal and no summary contract for `user_approved`.

20260301 — Phase 3 implementation complete for the first shipped slice. Scene Workspace landed with five concern-group tabs, generation actions, and red/yellow readiness, while green readiness remained explicitly deferred.

20260302 — Post-ship UI polish completed for the initial workspace slice. No change to the deferred readiness truth.

20260410-1059 — triage follow-up: reopened Done -> Pending instead of minting a new story ID. Evidence: `src/cine_forge/schemas/readiness.py` already supports green readiness; `ui/src/pages/SceneWorkspacePage.tsx` still computes red/yellow only from artifact existence; `ui/src/components/CharacterPerformancePanel.tsx` already toggles Draft/Reviewed; `ui/src/components/StoryWorldPanel.tsx` still lacks that toggle; and `ui/src/components/DirectionAnnotation.tsx` hides `user_approved`. Next step: build the shared scene-readiness surface and unify review controls across the five concern groups.

20260410-1110 — exploration: confirmed the narrowest implementation path is a dedicated scene-readiness API plus a reusable review-control seam, not an expansion of generic artifact-group summaries. Evidence: `ArtifactGroupSummary` only carries type/entity/version/health, `compute_scene_readiness()` already exists and is tested, `CharacterPerformancePanel` already persists reviewed/draft state via immutable edits, and `SceneWorkspacePage` currently bypasses the canonical model with a local red/yellow helper. Files to change: scene-readiness backend route/service seam, frontend readiness hook/types, `SceneWorkspacePage`, and shared review-control UI. Main file-size risks remain `api/service.py`, `api/app.py`, `SceneWorkspacePage.tsx`, `StoryWorldPanel.tsx`, and `ui/src/lib/types.ts`. Next step: implement the readiness route and shared review control before wiring the page.

20260410-1138 — implementation: added `src/cine_forge/services/scene_readiness.py`, `src/cine_forge/api/routers/readiness.py`, `ui/src/components/ArtifactReviewControls.tsx`, frontend readiness types/API/hooks, and Scene Workspace wiring. Evidence: `/api/projects/{project_id}/scenes/{scene_id}/readiness` now returns canonical red/yellow/green states; concern-group tabs consume the typed readiness contract; approval toggles now invalidate `scene-readiness` queries immediately instead of requiring a reload. Next step: run static verification and browser smoke.

20260410-1201 — regression fix: widened the canonical Story World yellow detector after browser smoke on a temp copy of `/Users/cam/Documents/Projects/cine-forge/output/the-mariner-50` surfaced a false-red `story_world` state even though `narrative_rhythm_notes` existed. Evidence: `src/cine_forge/schemas/readiness.py` now treats current Story World note/baseline/motif fields as meaningful draft content, and `tests/unit/test_readiness.py` adds `test_yellow_story_world_with_rhythm_notes`. Next step: rerun readiness tests, full unit suite, and browser verification.

20260410-1232 — verification: static checks passed with the final patch set. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` => `692 passed, 157 deselected`; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` clean; `pnpm --dir ui run lint` completed with 6 pre-existing warnings outside touched files (`AppShell.tsx`, `StatusBadge.tsx`, `ui/badge.tsx`, `ui/button.tsx`, `ui/tabs.tsx`, `right-panel.tsx`); `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed. Next step: record browser results and hand off for `/validate`.

20260410-1238 — browser smoke: desktop + mobile Scene Workspace verification passed functionally on a temp copy of a real pipeline-produced project, with one narrow seeded scene-scoped Character & Performance artifact added only because no available sample project had that shape yet. Evidence: Playwright toggled Look & Feel yellow -> green -> yellow, Story World yellow -> green, and Character & Performance yellow -> green; screenshots saved to `/tmp/story099-scene-workspace-desktop.png` and `/tmp/story099-scene-workspace-mobile.png`; readiness API reflected each transition immediately. Known console blockers: stale historical run-state 404s and one copied-project `/api/projects/the-mariner-50/artifacts` lookup from old project-id references, unrelated to readiness wiring. Next step: human review and `/validate`.

20260410-1152 — validation: reran the full validation suite in a fresh pass. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` => `692 passed, 157 deselected`; targeted readiness tests passed; Ruff passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed; browser smoke reran on desktop and mobile with screenshots re-inspected. Validation outcome: implementation is strong, but Story 099 should remain open because the final browser/coverage acceptance surface is still partial — desktop console still logs known stale-run / old-project-id 404s, and Character & Performance verification still needs a narrow seeded smoke fixture because no representative pipeline-produced sample project currently contains the scene-scoped artifact shape the spec requires. Recommended next step: either fix or formally re-home the console-noise issue and produce a representative scene-scoped Character & Performance sample, then rerun `/validate`.

20260410-1215 — follow-up fix: eliminated stale historical progress-card polling and copied-project artifact lookups from the Scene Workspace path. Evidence: `ui/src/lib/api/core.ts` now preserves HTTP status on API errors, `ui/src/lib/hooks/runs.ts` stops retry/refetch for missing run-state 404s and no longer treats them as active runs, `ui/src/components/RunProgressCard.tsx` resolves progress cards against the currently opened project and shows a stable unavailable fallback for missing historical runs, and `ui/src/components/chat/ChatMessageItem.tsx` passes the live project id through instead of trusting copied message payload ids. Next step: rerun browser verification on the stale project repro surface without any console-error whitelist.

20260410-1221 — representative verification fix: a normal `creative_direction` single-stage run for `character_and_performance` on `scene_001` surfaced another canonical false-red case because scenes with no on-screen characters produce a valid empty `entries` list. Evidence: `src/cine_forge/schemas/readiness.py` now treats a scene-scoped Character & Performance artifact itself as meaningful draft guidance, `tests/unit/test_readiness.py` adds the no-characters regression, targeted tests (`17 passed`) and Ruff passed, and `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` now reports `693 passed, 157 deselected`. Next step: rerun the full browser smoke on a fresh project copy using the real run-produced artifact.

20260410-1225 — browser rerun: desktop/mobile Scene Workspace verification passed on a fresh temp copy of `/Users/cam/Documents/Projects/cine-forge/output/the-mariner-50` with Character & Performance created through the normal run API instead of a seeded artifact. Evidence: readiness started yellow/yellow/yellow/yellow/yellow; Look & Feel toggled yellow -> green -> yellow; Story World toggled yellow -> green; Performance toggled yellow -> green; historical run cards in chat rendered `Historical run details are unavailable.` instead of polling missing runs; screenshots saved to `/tmp/story099-scene-workspace-desktop.png` and `/tmp/story099-scene-workspace-mobile.png`; browser capture found no console errors, page errors, or 4xx/5xx responses. Next step: rerun `/validate` on the current patch set.

20260410-1229 — validation rerun: current patch set validates cleanly. Evidence: `git diff` shows the remaining delta is still confined to Story 099 readiness work; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` => `693 passed, 157 deselected`; targeted readiness tests and Ruff passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed in this validation pass; committed smoke script `scripts/story_099_scene_workspace_smoke.py` ran successfully and re-produced the clean desktop/mobile browser verification with no console, page, or network errors. Outcome: implementation is complete and the remaining work is close-out bookkeeping via `/mark-story-done`.

20260410-1229 — completion: marked Story 099 Done after validation and closure review. Evidence: acceptance criteria and task checklist now match the shipped slice, generated planning surfaces were refreshed after the status change, and the changelog already records the original Story 099 landing plus this story artifact now captures the readiness-honesty continuation clearly. Next step: `/check-in-diff`.

20260410-1234 — post-close validation: reran the full Story 099 validation suite after closure to confirm the checked-in state still holds. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` => `693 passed, 157 deselected`; targeted readiness tests (`17 passed`) and Ruff passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check` passed in this validation pass; `python scripts/story_099_scene_workspace_smoke.py` ran under fresh API/UI servers and reproduced clean desktop/mobile verification with screenshots at `/tmp/story099-scene-workspace-desktop.png` and `/tmp/story099-scene-workspace-mobile.png`. Outcome: no new implementation gaps found; recommended next step remains `/check-in-diff`.

20260410-1304 — landing validation fix: rebased-branch browser validation exposed a narrow Playwright flake where mobile `wait_for_load_state("networkidle")` could hang even when the Scene Workspace was already interactive, and the original `get_by_role(..., name=regex)` tab wait proved brittle in the horizontally scrollable mobile tab rail despite the DOM being present. Follow-up debug on the exact desktop-then-mobile sequence showed the mobile leg was most deterministic when treated as its own representative pass with a fresh copied project and a fresh browser instance instead of inheriting the already-mutated desktop project/browser state. Evidence: `scripts/story_099_scene_workspace_smoke.py` now attempts `networkidle` first, falls back to polling a direct `[role="tab"]` text-filter locator, and exposes separate `desktop` / `mobile` modes so the review-loop transition check and the responsive-render check run as isolated representative passes. Next step: rerun the committed smoke modes under fresh API/UI servers and finish `/check-in-diff`.
