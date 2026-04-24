---
id: "181"
title: "Post-Deep-Breakdown Next-Step Guidance"
status: "Done"
priority: "High"
ideal_refs:
  - "R5 (full spectrum of human involvement)"
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5.3"
  - "spec:5.4"
  - "spec:5.6"
  - "spec:6.1"
  - "spec:7.1"
adr_refs:
  - "ADR-002"
depends_on:
  - "156"
  - "157"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "ux"
  - "chat"
  - "next-step-guidance"
  - "onboarding"
  - "default-path"
legacy_system: ""
---

# Story 181 — Post-Deep-Breakdown Next-Step Guidance

**Priority**: High
**Status**: Done
**Ideal Refs**: R5 (full spectrum of human involvement), R7 (generate -> react -> refine), R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5.3, spec:5.4, spec:5.6, spec:6.1, spec:7.1
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md`. No separate ADR was found for post-ingest goal selection.
**Depends On**: Story 156 (canonical UI walkthrough) and Story 157 (completed-path CTA honesty)

## Goal

Lead the user somewhere concrete after Deep Breakdown instead of ending the guided flow at the exact moment CineForge should become most useful. Current UI behavior walks users through `Break Down Script` and `Deep Breakdown`, then falls back to generic "your story world is built" copy without a strong next move. Manual QA showed that this creates a dead end even though the operator console and scene pipeline visibly imply that `Shots`, `Storyboards`, and `Production` are next. This story adds an honest default next-step recommendation for the current script-to-film path while preserving room for a future, broader "what are you here to do?" chooser.

## Acceptance Criteria

- [x] After `world_building` completes, the surfaced chat/progress experience presents a concrete next-step CTA or short choice set instead of generic completion copy with no obvious direction.
- [x] The default recommendation reflects the current product truth: assume the user wants to continue toward scene planning / generation unless they choose otherwise.
- [x] The guidance remains honest about current progress and does not re-advertise already-completed `Break Down Script` or `Deep Breakdown` actions.
- [x] The chosen copy and CTA path work on both Home and scene routes for a representative project created through the normal workflow.
- [x] Once the user enters Scene Workspace, the surfaced UI continues teaching the default scene-to-render path instead of stopping at the first concern-group artifact. At minimum, the next step stays obvious through Shot Planning, Storyboard, and Render.
- [x] Focused regression coverage exists for the completion-state message selection, and browser verification covers desktop and mobile with clean console output.

## Out of Scope

- A full user-intent taxonomy or multi-workflow chooser immediately after import
- Rebuilding the entire chat journal or suggestion model
- Scene Workspace entry-clarity fixes; that belongs in Story 180
- Runtime optimization or performance investigation for Deep Breakdown; that belongs in Story 183

## Approach Evaluation

- **Simplification baseline**: The repo already knows when `world_building` completes and already injects post-run CTAs after `mvp_ingest`. The first baseline is therefore deterministic: extend the current state-based guidance so Deep Breakdown completion has an equally concrete next action.
- **AI-only**: Wrong fit for the initial fix. A model could propose personalized next steps later, but the current problem is missing deterministic product guidance for the default path.
- **Hybrid**: Plausible as a future upgrade if CineForge later asks users to declare goals and routes those goals conversationally. That is not required to fix the current dead end.
- **Pure code**: Best fit. The product already has enough state to say "you are ready for scene work; start with shot planning" or present a short set of downstream options.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` both require the operator console to help users know what to do next. `docs/design/decisions.md` explicitly calls dead-end screens failures. Story 157 already cleaned up stale completed-path CTAs; this story should build on that honesty rule rather than override it.
- **Existing patterns to reuse**: Reuse `ui/src/lib/use-run-progress.ts` post-run CTA injection, `ui/src/lib/chat-messages.ts` state-derived assistant messaging, and existing action-button rendering instead of creating a parallel suggestion system.
- **Eval**: The discriminator is a representative post-Deep-Breakdown walkthrough where the next move is obvious on both Home and scene routes, with no stale breakdown CTAs and no need for operator improvisation.

## Tasks

- [x] Reproduce the current post-Deep-Breakdown dead end on the canonical UI path and identify whether the missing guidance belongs in run-completion messaging, state-derived chat copy, or both.
- [x] Implement the smallest honest next-step rule for the default script-to-film path, reusing existing chat/progress message infrastructure.
- [x] Preserve completed-path honesty so the new recommendation does not regress Story 157 and re-advertise finished actions.
- [x] Extend the same guidance into Scene Workspace so the current scene route keeps suggesting the next surfaced action until a scene is rendered.
- [x] Upgrade scene-work completion cards (`creative_direction`, `shot_planning`, `storyboard_generation`, `render_generation`) so they point at the next surfaced step rather than stopping at the artifact that just landed.
- [x] Add focused regression coverage for the chosen completion-state messaging path.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: not touched
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: not expected
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

- **Owning class/module**: `ui/src/lib/use-run-progress.ts` already owns run-completion CTA injection and `ui/src/lib/chat-messages.ts` already owns project-state-derived assistant copy. Keep the change inside those existing chat/progress seams instead of adding another recommendation system in `AppShell` or the backend.
- **Data contracts**: No new backend schema should be necessary if the guidance stays client-side and state-derived. If a new action type or chat metadata field becomes necessary, keep it typed in the existing UI action/message models.
- **File sizes**: `ui/src/lib/use-run-progress.ts` is `592` lines and oversized, while `ui/src/lib/chat-messages.ts` is `360`, `ui/src/lib/constants.ts` is `285`, and `ui/src/components/chat/ChatMessageItem.tsx` is `287`. Favor extraction or small helper maps over piling more branching into `use-run-progress.ts`.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, ADR-002, Story 156, Story 157, and the existing chat/progress completion code paths.

## Files to Modify

- `ui/src/lib/use-run-progress.ts` — add a concrete post-`world_building` next-step CTA instead of stopping at generic completion (`592`)
- `ui/src/lib/chat-messages.ts` — align project-state completion copy with the default script-to-film path and any lightweight alternate choices (`360`)
- `ui/src/lib/constants.ts` — centralize the scene-work next-step copy and action so bootstrap and live completion paths stay in sync (`285`)
- `ui/src/lib/scene-workflow.ts` — shared scene-to-render tutorial helper so Scene Workspace and completion cards follow the same next-step rule (new)
- `ui/src/components/SceneWorkflowGuideCard.tsx` — thin UI surface for the scene tutorial on Scene Workspace routes (new)
- `ui/src/pages/SceneWorkspacePage.tsx` — place the shared tutorial card above the scene tabs without bloating the tab panels further (`967`)
- `ui/tests/chat-next-step-guidance.test.ts` — focused node-level regression coverage for the completion-state next-step rule
- `ui/tests/scene-workflow-guide.test.ts` — focused node-level regression coverage for the chained scene tutorial helper (new)
- `scripts/story_181_next_step_guidance_smoke.py` — desktop/mobile route smoke for the Home + scene CTA path on a representative completed project

## Redundancy / Removal Targets

- Generic completion copy that says the world is built but leaves the user at a dead end
- Any duplicated next-step logic split inconsistently between state-derived chat messages and run-completion CTAs
- Any downstream suggestion that remains phrased as a fresh discovery step when the intended product truth is "continue the default script-to-film path"

## Notes

- This stays deliberately narrower than the larger product question raised in QA: "what if the user only wants previz, prop management, or script work?" That broader intent-routing conversation is real, but current product truth still needs a default path for the common script-to-film case.
- `docs/design/decisions.md` already says dead-end screens are failures. The current post-Deep-Breakdown state violates that rule.
- The existing code already has a useful precedent: after `mvp_ingest`, `use-run-progress.ts` injects a concrete follow-up CTA. `world_building` should reach the same bar.

## Plan

1. Reproduce the current post-Deep-Breakdown message sequence on the canonical path and document exactly where the guidance stops.
2. Extend the state-derived guidance so `world_building` completion recommends a concrete next step on the current script-to-film path.
3. Keep the change consistent with Story 157's completed-path honesty rules so the new CTA is current, not stale or contradictory.
4. Extend the same default-path guidance into Scene Workspace with one shared scene-tutorial helper so concern-group tabs, shot planning, storyboard, and render all keep the next surfaced step obvious without inventing a second recommendation system.
5. Upgrade run-completion cards for the scene route so they point at the next surfaced step, not just the artifact that just landed.
6. Add focused regression coverage and verify in browser on desktop and mobile that the next move is obvious from both Home and scene routes.

## Work Log

20260420-0001 — story-created: split the post-Deep-Breakdown dead end into its own `Pending` story so it can be solved as chat/progress guidance rather than mixed with Scene Workspace layout fixes. Evidence: `docs/inbox.md` QA notes, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/chat-messages.ts`, `docs/design/decisions.md`, Story 156, and Story 157. Next step: `/build-story 181`.
20260420-1053 — exploration: traced the current post-Deep-Breakdown guidance through bootstrap welcome messages, persisted chat rendering, and run-completion CTA injection before implementation. Evidence: `ui/src/lib/chat-messages.ts` still falls back to generic complete-state "Explore Scenes" / `artifacts` messaging, while `ui/src/lib/use-run-progress.ts` only injects a next-step CTA for `mvp_ingest` and stops after a generic `world_building` completion message. Files changing: `ui/src/lib/chat-messages.ts`, `ui/src/lib/use-run-progress.ts`, a small shared copy helper in `ui/src/lib/constants.ts`, plus focused UI regression coverage and a browser smoke script. Files at risk: `ui/src/lib/use-run-progress.ts` is currently `592` lines and should stay on the narrowest possible diff; `ChatPanel` / `ChatMessageItem` look unnecessary because Story 157 already owns completed-path archival. Decision docs consulted: ADR-002, `docs/design/decisions.md`, Story 156, Story 157, and Story 180. Repo-fit decision: route the new default CTA to `scenes` so the operator lands in real scene work instead of the generic artifact archive, while keeping `Browse Results` / `Run Details` available from the existing completion surfaces. Next step: implement the shared scene-work next-step copy and wire it into both complete-state bootstrap messaging and `world_building` completion.
20260420-1118 — implementation: wired a single scene-work recommendation through both completion seams instead of inventing a new suggestion system. `ui/src/lib/constants.ts` now owns the shared `Start Scene Work` CTA and the "pick a scene and start with shot planning" copy; `ui/src/lib/chat-messages.ts` now uses that shared helper for the `complete` bootstrap state and drops the stale `Explore Scenes` / inbox/world-model suggestion set; and `ui/src/lib/use-run-progress.ts` now injects the same CTA immediately after successful `world_building` runs while preserving the existing `Browse Results` / `Run Details` completion affordances. Added `ui/tests/chat-next-step-guidance.test.ts` to pin the copy/action contract and `scripts/story_181_next_step_guidance_smoke.py` for route-level desktop/mobile verification. Redundancy removed: duplicated next-step wording split across bootstrap vs live-completion paths.
20260420-1146 — static-verification: reran the touched-scope checks and kept the work inside the intended UX slice. Evidence: `node --test ui/tests/chat-next-step-guidance.test.ts` passed; `python -m py_compile scripts/story_181_next_step_guidance_smoke.py` passed; `pnpm methodology:compile` regenerated `docs/methodology/graph.json`, `docs/build-map.md`, and `docs/stories.md`; `pnpm methodology:check` passed with only the pre-existing architecture-audit warning for `api_service_and_operator_console`; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_181_next_step_guidance_smoke.py` passed; `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`771 passed, 176 deselected, 1 pre-existing pytest mark warning`). Environment note: this worktree had no local `.venv` or `ui/node_modules`, so verification used the shared repo venv and a temporary `ui/node_modules` symlink to the primary checkout.
20260420-1208 — runtime-check: attempted to verify the full fresh UI flow by creating project `story-181-smoke-1776747360`, uploading `tests/fixtures/ingest_inputs/open_frequency_short.fountain`, and triggering `Break Down Script` through the live local API/UI stack. Result: the normal workflow did not reach Deep Breakdown because the backend failed during `script_bible` with provider error `API key not valid. Please pass a valid API key.` from the Gemini path. This is an environment blocker, not a Story 181 regression, so I kept the implementation scope intact and recorded the blocker instead of broadening the story into model/runtime repair.
20260420-1229 — browser-verification: verified the shipped CTA on a representative completed-project substrate using a disposable copy of `/Users/cam/Documents/Projects/cine-forge/output/the-mariner-36` with its old `chat.jsonl` removed so the current complete-state bootstrap could render fresh. Opened the copy through `/api/projects/open` as `story181-complete-smoke`, then ran `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/story_181_next_step_guidance_smoke.py --project-id story181-complete-smoke --mode both`. Result: desktop Home, desktop `scenes/scene_001?tab=render`, mobile Home, and mobile `scenes/scene_001?tab=render` all showed `Start Scene Work`, clicking the CTA routed to `/<project_id>/scenes`, stale labels `Review Inbox` / `Refine World Model` were absent, and the smoke script reported `console_errors=[]`, `page_errors=[]`, and `response_errors=[]`. Screenshots saved to `/tmp/story181-next-step-home-desktop.png`, `/tmp/story181-next-step-scene-desktop.png`, `/tmp/story181-next-step-home-mobile.png`, and `/tmp/story181-next-step-scene-mobile.png`. Next step: `/mark-story-done 181`.
20260421-2305 — scope-expansion exploration: manual QA on `brick-steel-full-retired-3` showed Story 181's original fix only solved the first handoff. After a concern-group run, the UI still stopped at "Open Look & Feel in Scene Workspace" with no explicit next surfaced step, which violates ADR-002, `docs/design/decisions.md`, and the manual-walkthrough rule that a first-time operator should know what to do next at each stage. Evidence: reread ADR-002, ADR-003, `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, `ui/src/lib/use-run-progress.ts`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/components/SceneWorkspaceFocusBanner.tsx`, `ui/src/components/ShotPlanningPanel.tsx`, `ui/src/components/StoryboardPanel.tsx`, `ui/src/components/PrevizPanel.tsx`, and `ui/src/components/GeneratedVideoPanel.tsx`. Scope decision: keep this in Story 181 instead of splitting a new story because the remaining gap is the same default-path tutorial seam, just one step downstream. Owner/size note: `SceneWorkspacePage.tsx` (`967`) and `use-run-progress.ts` (`608`) are already oversized, so the implementation should add a shared helper/component instead of more inline branching. Next step: implement a shared scene-tutorial card plus chained completion guidance through Shot Planning, Storyboard, and Render.
20260421-2342 — implementation: extended Story 181 from a one-step post-Deep-Breakdown fix into a shared scene tutorial without inventing another recommendation subsystem. Added `ui/src/lib/scene-workflow.ts` as the scene-to-render decision helper, `ui/src/components/SceneWorkflowGuideCard.tsx` as the thin surfaced card, wired `ui/src/pages/SceneWorkspacePage.tsx` to render that card above the scene tabs on every scene route, and upgraded `ui/src/lib/use-run-progress.ts` so concern-group, shot-planning, storyboard, and render completion cards point at the next surfaced step instead of stopping at the artifact that just landed. Documentation follow-through: updated `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` so the recurring UI truth check now explicitly expects Scene Workspace to keep the path obvious through Shot Planning, Storyboard, and Render. Redundancy outcome: the next-step rule now lives in one helper instead of being split across ad hoc tab prose and run-completion one-offs. Next step: rerun static checks and browser-verify the chained tutorial states on representative scene routes.
20260421-2356 — verification: reran the required checks and validated the chained tutorial on real project states. Static evidence: `node --test ui/tests/chat-next-step-guidance.test.ts ui/tests/scene-workflow-guide.test.ts` passed, `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b` passed, `pnpm --dir ui run build` passed, `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ ui/tests/ scripts/story_181_next_step_guidance_smoke.py` passed, `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`776 passed, 177 deselected, 1 pre-existing pytest mark warning`), `pnpm methodology:compile` refreshed the generated views, `pnpm methodology:check` passed with the same existing architecture-audit warning, and `git diff --check` passed. Browser evidence: desktop screenshots at `/tmp/story181-scene-guide-look-and-feel-desktop.png`, `/tmp/story181-scene-guide-shots-desktop.png`, `/tmp/story181-scene-guide-storyboard-desktop.png`, and `/tmp/story181-scene-guide-render-desktop.png` proved the guide stepping through `Open Shots` on `brick-steel-full-retired-3`, `Open Storyboard` on `story-132-shot-plan-ui-clean`, `Open Render` on `story-143-ui-check`, and the terminal rendered-scene state on `render-demo`; mobile spot-check screenshots at `/tmp/story181-scene-guide-look-and-feel-mobile.png` and `/tmp/story181-scene-guide-render-mobile.png` confirmed the first and terminal states on small viewports. All browser probes completed with `console_errors=[]`, `page_errors=[]`, and `response_errors=[]`. Runtime note: a fresh API-triggered `shot_planning` attempt on `brick-steel-full-retired-3` (`run-99976328`) stayed in-stage with no failure event during this pass, so I did not use it as acceptance proof for Story 181; the actual UI verification instead used representative real projects whose states were already produced through normal pipeline runs. Next step: `/validate 181` or `/mark-story-done 181` depending on whether you want a separate validation pass.
20260422-1826 — storyboard-refresh-reuse: operator testing surfaced a real depth-first workflow bug on the tutorial path. Evidence: `run-22f25866` on `brick-steel-full-retired-6` showed `stage_order=["timeline","tracks","shot_planning","storyboards"]`, and [ui/src/components/StoryboardPanel.tsx](/Users/cam/.codex/worktrees/400e/cine-forge/ui/src/components/StoryboardPanel.tsx) was starting `storyboard_generation` without passing any `start_from`, so `Refresh Storyboard for Current Scene` really did recompute timeline, tracks, and shot planning even when `track_manifest` and `shot_plan` were already healthy. Change: [src/cine_forge/pipeline/scene_actions.py](/Users/cam/.codex/worktrees/400e/cine-forge/src/cine_forge/pipeline/scene_actions.py) now recommends `start_from="storyboards"` for `storyboard_generation` when healthy `track_manifest` and scoped `shot_plan` artifacts exist, prunes the fake auto-build items, and the storyboard panel now passes that start stage through to `/api/runs/start`. Verification: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_scene_actions.py -q` (pass), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/cine_forge/pipeline/scene_actions.py tests/unit/test_scene_actions.py` (pass), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`781 passed, 179 deselected, 1 warning`), `pnpm --dir ui run lint` (pass), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass). Live backend proof: `POST /api/projects/brick-steel-full-retired-6/scene-actions/preflight` now returns `start_from:"storyboards"` with no `timeline` / `track_manifest` / `shot_plan` auto-build items. Browser proof on desktop and mobile at `http://127.0.0.1:5174/brick-steel-full-retired-6/scenes/scene_001?tab=storyboard` intercepted the refresh button request with `start_from:"storyboards"` and clean console/page output; screenshots: `/tmp/storyboard-reuse-verify-clean/desktop.png` and `/tmp/storyboard-reuse-verify-clean/mobile.png`. Next step: keep current-scene storyboard refresh depth-first by default unless prerequisites are actually stale, instead of burning upstream recompute time on healthy substrate.
20260424-0010 — close-out: marked Story 181 done during `/finish-and-push` after confirming the tutorial path now continues from post-Deep-Breakdown into Scene Workspace, through shot planning/storyboards/render, and current-scene storyboard refresh no longer recomputes healthy timeline/tracks/shot-plan prerequisites. Evidence remains the focused UI tests, desktop/mobile browser verification recorded above, full backend/unit/UI validation from the branch validation pass, and refreshed methodology surfaces. Where to verify: open a project scene route such as `/<project>/scenes/scene_001?tab=storyboard` and confirm the guide points to the next scene-to-render step while storyboard refresh submits `start_from:"storyboards"` when prerequisites are complete. Next step: `/check-in-diff`.
20260424-0025 — finish-and-push validation: full branch validation stayed green after close-out edits. Evidence: full unit suite `808 passed, 179 deselected`; Ruff passed on `src/`, `tests/`, touched scripts, and storyboard benchmark files; UI lint, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed; `pnpm methodology:check` passed with only the existing `api_service_and_operator_console` architecture-audit warning; `git diff --check` passed.
