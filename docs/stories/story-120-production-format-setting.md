---
id: "120"
title: "Production Format Setting"
status: "Done"
priority: "Medium"
ideal_refs: []
spec_refs:
  - "spec:2.4"
  - "spec:2.6"
  - "spec:6.2"
  - "spec:6.3"
adr_refs: []
depends_on:
  - "056"
category_refs:
  - "spec:2"
  - "spec:6"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 120 — Production Format Setting

**Priority**: Medium
**Status**: Done
**Spec Refs**: spec:2.4 (Project Configuration), spec:2.6 (Two-Lane Architecture / Film Lane), spec:6.2 (Storyboards), spec:6.3 (Animatics / Previz Video)
**Depends On**: Story 056 (Design Study — Done)
**Updated**: 2026-03-14 — backlog cleanup clarified that this story should land before the later design-study prompt/iteration follow-ons.

## Goal

When a user first generates a visual (character/location/prop image), CineForge needs to know the project's base visual medium: live action, anime, 2D animation, graphic novel, and so on. That choice is not the whole style system. It is the broad image archetype that later taste signals such as directors, films, mood boards, and written direction can build on. The first-run threshold should still live inside image generation, but the durable home for editing belongs in Intent & Mood, where users already shape the project's creative direction. Script should only show a small breadcrumb pill once the medium is set, so users can jump back to Intent without turning Script into production setup.

## Acceptance Criteria

- [x] `project_config` schema gains `production_format: str | None` field (enum: `live_action`, `animation_2d`, `animation_3d`, `anime`, `graphic_novel`, `concept_art`; default: `None`)
- [x] API endpoint to update `production_format` on a project (PATCH or reuse existing project settings endpoint)
- [x] On first image generation for a project with `production_format == None`, the UI shows a picker modal before firing the generate request
- [x] After the user picks a format, the format is persisted to `project_config` and the generate request fires
- [x] If the user dismisses the modal without picking, the generate request fires without a format (graceful degradation)
- [x] Format picker remembers the choice — subsequent generations on the same project skip the modal
- [x] Intent & Mood exposes a lightweight `Visual Medium` control as part of the project's visual-direction surface; selecting a value persists it as `production_format`
- [x] Project-level visual references live on Intent & Mood instead of Script, so the screenplay view stays focused on reading
- [x] Once a project has a saved `production_format`, Script shows a small pill/chip; clicking it routes the user to Intent & Mood to edit the choice there
- [x] Projects with no saved `production_format` do not show a Script pill before first visual generation, so story-only users are not pushed into premature setup from the Script page
- [x] User-facing copy refers to this choice as `Visual Medium`, clarifying that it is the base medium rather than the project's full aesthetic style
- [x] Script Breakdown / Deep Breakdown CTAs on Intent and in chat reflect the shared active-run state so they become disabled and consistent while a run is in flight
- [x] On gated Intent states, the prerequisite/status card sits directly below `Visual Medium` and above `Project References`, so the page explains its readiness before showing supporting reference controls
- [x] Chat completion copy distinguishes `Script Breakdown` from `Deep Breakdown`, so the two pipeline phases are not conflated in the operator UI
- [x] Image prompt compiler incorporates a style modifier based on `production_format` (e.g. live_action → "photorealistic", animation_3d → "Pixar-style 3D render", anime → "anime cel art")
- [x] `sources_used` includes `"project_config"` when the format-derived project context is applied (normalized by Story 119's broader prompt provenance taxonomy)
- [x] All existing design study integration tests pass

## Out of Scope

- Format-aware auto-detection from the screenplay (that's a future story — genre detection gives hints but shouldn't auto-decide)
- Per-entity format override (global project setting only)
- An always-visible unset production-format pill on Script or Intent (that would push story-only users into production setup too early)
- A broader project settings consolidation for production controls
- The fuller Ideal-first visual-direction stack in Intent (medium + directors/films + uploaded mood boards + compiled creative brief) — capture as follow-on work rather than silently inflating this story
- Format applies only to image generation — storyboard and video previz are separate stories

## Approach Evaluation

This is pure plumbing — no AI reasoning required.

- **AI-only**: N/A — format is a user choice, not an AI inference. (Screenplay genre hints could inform a default suggestion, but that's optional and deferred.)
- **Hybrid**: Could pre-suggest a format based on detected genre (comedy → animation_2d, noir → live_action). Nice-to-have, not needed for v1.
- **Pure code**: Store an enum in `project_config`, map to style modifier string in `build_image_prompt()`, surface modal in UI on first generation. This is correct — no reasoning needed.
- **Eval**: Visual quality check (manual) — do images generated with format modifiers look more consistent with the intended style than without? No automated eval; subjective quality.

## Tasks

- [x] Add `production_format: str | None = None` to `ProjectConfig` in `src/cine_forge/schemas/models.py`
- [x] Extend the existing project settings API surface (`ProjectSettingsUpdate`, `ProjectSummary`, service persistence/sync path, and `PATCH /api/projects/{project_id}/settings`) to round-trip `production_format`
- [x] Add TypeScript `production_format` field to the project types and update project fetch + mutate calls
- [x] Write `FORMAT_STYLE_MODIFIERS` map in `image.py` — format id → style string appended to prompt
- [x] Introduce the minimal `build_image_prompt()` wrapper needed for Story 120, route design-study generation through it, and add project-config prompt provenance when the format-derived medium modifier is applied
- [x] Add `sources_used` to the design-study round schema/API/UI types so prompt provenance survives the round-trip
- [x] Build `ProductionFormatModal` component — picker with 6 format options, short labels + 1-line descriptions, "Skip for now" escape hatch
- [x] Build a reusable `ProductionFormatPill` control that can either edit the saved value in Intent or act as a Script breadcrumb back to Intent
- [x] Wire the first-run modal into `DesignStudySection.tsx` — check `project.production_format` before generate; if unset, show modal first, with a small extraction if needed to avoid further bloating the component
- [x] Add a lightweight `Visual Medium` section to Intent & Mood so the base medium sits next to presets, reference films, and written direction
- [x] Move the project-level references surface from Script into Intent & Mood
- [x] Reduce Script to a subtle breadcrumb pill that appears only after the medium has been set and routes users back to Intent to edit it
- [x] Unify Script Breakdown / Deep Breakdown CTA state around the shared active run so duplicate buttons disable and stale banners clear correctly
- [x] Reorder gated Intent states so the prerequisite/status card sits above `Project References`
- [x] Make run-completion chat copy phase-specific (`Script Breakdown complete` vs `Deep Breakdown complete`) so the state transition reads clearly
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete — implementation finished, required checks run, and build handoff shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `ProjectConfig` in `src/cine_forge/schemas/models.py` (format field), project settings API/service models (round-trip persistence), `src/cine_forge/ai/image.py` (style modifier map + prompt builder), `src/cine_forge/api/routers/design_study.py` and `src/cine_forge/schemas/design_study.py` (generation contract), `ui/src/components/ProductionFormatPill.tsx` (Intent editor + Script breadcrumb), `ui/src/components/VisualMediumCard.tsx` (Intent-owned surface), `ui/src/pages/ProjectHome.tsx` and `ui/src/pages/IntentMoodPage.tsx` (project-definition surfaces), `ui/src/components/DesignStudySection.tsx` (first-run modal trigger)
- **Data contracts**: `production_format` is a project-level field on the persisted project config and project settings response. The UI reads it via the existing project API and writes it via the existing settings PATCH path. `sources_used` must be added schema-first on the design-study round models before backend and UI code depend on it.
- **File sizes**: `src/cine_forge/ai/image.py` 283 lines (safe), `src/cine_forge/api/routers/design_study.py` 299 lines (safe), `ui/src/pages/ProjectHome.tsx` 752 lines (plan risk — prefer a small reusable header control over more inline logic), `ui/src/pages/IntentMoodPage.tsx` 611 lines (same risk), `ui/src/components/DesignStudySection.tsx` 526 lines (keep the generate gate surgical)

## Files to Modify

- `src/cine_forge/schemas/models.py` — add `production_format: str | None = None` to `ProjectConfig`
- `src/cine_forge/api/models.py` — extend project settings request/response models for `production_format`
- `src/cine_forge/api/service.py` — persist `production_format` in `project.json` and mirror it into `project_config` using the existing settings-sync pattern
- `src/cine_forge/api/app.py` — verify the existing project settings endpoint exposes the updated models (touch only if required)
- `src/cine_forge/ai/image.py` — add `FORMAT_STYLE_MODIFIERS`, introduce `build_image_prompt()`, and apply format-derived prompt modifiers
- `src/cine_forge/schemas/design_study.py` — add `sources_used` to the round artifact schema
- `src/cine_forge/api/routers/design_study.py` — route generation through the prompt builder and return `sources_used`
- `ui/src/lib/types.ts` — add `production_format` to the project summary type
- `ui/src/lib/api/projects.ts` — extend the project settings endpoint wiring for `production_format`
- `ui/src/lib/api/design-study.ts` — extend design-study round types for `sources_used`
- `ui/src/components/PageHeader.tsx` — allow an optional accessory/action slot for top-level page controls
- `ui/src/components/ProductionFormatPill.tsx` — Intent editor / Script breadcrumb surface for the saved medium
- `ui/src/components/VisualMediumCard.tsx` — Intent-owned visual-medium surface that frames the medium as the base archetype, not the whole style system
- `ui/src/pages/ProjectHome.tsx` — show the breadcrumb pill in the Script header once a format exists
- `ui/src/pages/IntentMoodPage.tsx` — host the editable visual-medium control in Intent & Mood
- `ui/src/components/DesignStudySection.tsx` — modal trigger logic
- `ui/src/components/ProductionFormatModal.tsx` — new component (format picker)
- `tests/unit/test_project_config_schema.py` — validate `production_format`
- `tests/unit/test_api.py` — cover project settings persistence / project config sync for `production_format`
- `tests/unit/test_design_study.py` — cover prompt modifier mapping and `sources_used`
- `tests/integration/test_api_design_study.py` — cover first-run prompt path and returned round provenance

## Notes

- **Format → style modifier map** (initial values, tunable):
  | Format | Style modifier appended to prompt |
  |--------|----------------------------------|
  | `live_action` | "photorealistic, film photography, cinematic lighting" |
  | `animation_2d` | "2D animation style, hand-drawn, flat color fills, Disney/Pixar influence" |
  | `animation_3d` | "3D animated film, Pixar render quality, subsurface scattering, ambient occlusion" |
  | `anime` | "anime cel art, manga influence, clean line art, vibrant flat colors" |
  | `graphic_novel` | "graphic novel illustration, ink lines, limited palette, high contrast" |
  | `concept_art` | "concept art, production design sketch, matte painting style" |
- The modal should feel lightweight — not a "setup wizard". It's a one-question interstitial, not a settings page.
- `production_format` stored in `project_config` artifact (not a separate config file) — project_config is the right home for project-wide production decisions.
- Story 120 currently needs a small slice of Story 119 to be real: a minimal prompt-builder wrapper plus `sources_used` round-tripping. Fold that narrowly into this story; keep the broader prompt-composition work in Story 119.
- UI shape should have three layers, not one: a first-run modal to capture the threshold moment inside the visual lane, an Intent-owned `Visual Medium` control that sits beside reference films and written direction, and a subtle Script breadcrumb pill that links back to Intent after the medium exists. Do not show an unset Script pill to story-only users.
- `production_format` is the base medium only. Broader taste anchors such as directors, reference films, mood boards, and uploaded imagery belong in the Intent stack, not in this field.

## Plan

1. Persist `production_format` through the existing project settings path.
   Files: `src/cine_forge/schemas/models.py`, `src/cine_forge/api/models.py`, `src/cine_forge/api/service.py`, `src/cine_forge/api/app.py`, `tests/unit/test_project_config_schema.py`, `tests/unit/test_api.py`.
   Change: add the new nullable field to `ProjectConfig`, extend `ProjectSettingsUpdate` and `ProjectSummary`, and update the existing `PATCH /api/projects/{project_id}/settings` flow to persist it in `project.json` and mirror it into `project_config` using the same service-level sync pattern already used for `human_control_mode`.
   Why this fits here: `docs/spec.md` treats format preferences as project-level context, and ADR-003 defines the project as the container for script-adjacent production decisions. Reusing the existing project settings path is better than inventing a second config endpoint or hiding the value in UI-only state.
   Done looks like: project settings payloads can read/write `production_format`, schema validation passes, and unit tests prove the persisted project summary and canonical config stay aligned.

2. Add the smallest prompt-builder slice necessary to apply format styling cleanly.
   Files: `src/cine_forge/ai/image.py`, `src/cine_forge/schemas/design_study.py`, `src/cine_forge/api/routers/design_study.py`, `tests/unit/test_design_study.py`, `tests/integration/test_api_design_study.py`, `ui/src/lib/api/design-study.ts`.
   Change: introduce `build_image_prompt()` as a thin deterministic wrapper around the existing design-study prompt synthesis, add `FORMAT_STYLE_MODIFIERS`, and record project-config prompt provenance when the modifier is applied. Extend the round schema/API/UI types so `sources_used` survives round-tripping.
   Why this fits here: Story 120 cannot honestly claim prompt provenance or format-aware generation without a prompt-builder seam. This is the minimal tightly coupled scope expansion from Story 119; the broader multi-source prompt-composition work remains deferred there.
   Done looks like: prompt-building tests cover each format mapping, unformatted projects degrade gracefully, and API tests show `sources_used` includes `project_config` only when project-level visual context is actually applied.

3. Keep the first-run modal in design study, but move the durable control into Intent and reduce Script to a breadcrumb.
   Files: `ui/src/components/ProductionFormatModal.tsx`, `ui/src/components/ProductionFormatPill.tsx`, `ui/src/components/VisualMediumCard.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/IntentMoodPage.tsx`, `ui/src/components/DesignStudySection.tsx`, `ui/src/lib/types.ts`, `ui/src/lib/api/projects.ts`.
   Change: keep the threshold-moment modal inside design-study generation, add a small Intent-owned `Visual Medium` section near the top of Intent & Mood, and convert Script's surface into a subtle pill that links back to Intent instead of editing in place. Use `Visual Medium` wording in the UI to distinguish the medium choice from the broader style/taste stack.
   Why this fits here: the Ideal and ADR-003 both make Intent/Mood the primary interaction surface for taste, references, and big creative knobs. Putting the edit control there keeps Script from feeling like production setup while still leaving a breadcrumb for quick return.
   Done looks like: users can set or edit the medium directly in Intent, Script only shows a small linked pill after the medium exists, the first generation still intercepts unset projects with the modal, and the UI language clarifies that this choice is the base medium rather than the whole aesthetic.

4. Validate, trim redundancy, and update docs/work log evidence.
   Files: story work log plus any touched docs if behavior or architecture text becomes stale.
   Change: remove any obsolete direct prompt-construction path if the new builder fully replaces it, update this story log with evidence, and run the required checks for touched backend/UI scope.
   Impact / breakage risk: project settings serialization, design-study round parsing, and the large `DesignStudySection.tsx` component are the main regression surfaces. Existing design-study integration coverage should catch API regressions; unit tests around schema and prompt building should catch format-specific failures.
   Done looks like: required checks pass, no duplicate prompt path remains, and the story log records evidence and any residual follow-up.

Repo-fit / optimality evidence:
- `docs/ideal.md` prioritizes easy, engaging creative flow; this favors a one-time interstitial over a mandatory settings step.
- `docs/ideal.md` also favors transparent creative controls; a persistent but invisible format choice would undermine that.
- `docs/ideal.md` says taste belongs to the user and should be expressed through references and examples. That makes `production_format` only one layer in a larger taste stack, not the whole visual-direction model.
- `docs/spec.md` positions production/format preferences at the project level, not per-image local state.
- ADR-003 says Intent/Mood is the primary interaction surface for reference input, vibe packages, and natural-language creative direction. That makes Intent the right durable home for the edit affordance.
- `ui/src/pages/ProjectHome.tsx` and `ui/src/pages/IntentMoodPage.tsx` are both top-level project-definition surfaces, but only Intent is explicitly about visual direction. Script should stay lighter and point people back there.

Alternatives rejected:
- Frontend-only persistence in `localStorage`: rejected because AGENTS explicitly says project-scoped preferences belong in project settings, not browser storage.
- New dedicated production-format endpoint: rejected because it duplicates the existing project settings API and would create two write paths for one project-level concern.
- Modal-only UX with no persistent visible surface: rejected because it makes a project-wide creative control effectively write-only after the first decision.
- Always-visible unset pill on Script/Intent: rejected because it violates the story goal that story-only users should not see this setup before they enter the visual lane.
- Editable Script pill as the main control: rejected because it makes Script feel like production setup and misplaces a creative-direction decision outside the Intent surface that already owns presets, references, and natural-language taste.
- ProjectSettings-only editing: rejected because it hides a creative identity choice in a generic dialog instead of placing it on the project-definition surfaces where users reason about story-to-film intent.
- Waiting for Story 119 first: rejected because the missing prompt-builder seam is a small tightly coupled delta, not a distinct story goal, and postponing it would leave Story 120 not actually buildable.

Structural health check:
- `src/cine_forge/schemas/models.py` — 142 lines
- `src/cine_forge/api/models.py` — 368 lines
- `src/cine_forge/api/app.py` — 1034 lines; touch only if request/response wiring truly requires it
- `src/cine_forge/api/service.py` — 1002 lines; use surgical edits around the existing settings sync path
- `src/cine_forge/ai/image.py` — 283 lines
- `src/cine_forge/api/routers/design_study.py` — 299 lines
- `src/cine_forge/schemas/design_study.py` — 77 lines
- `ui/src/lib/types.ts` — 304 lines
- `ui/src/lib/api/projects.ts` — 102 lines
- `ui/src/components/PageHeader.tsx` — 19 lines
- `ui/src/pages/ProjectHome.tsx` — 752 lines; prefer a reusable pill component instead of embedding new stateful logic in the page
- `ui/src/pages/IntentMoodPage.tsx` — 611 lines; same extraction pressure
- `ui/src/components/DesignStudySection.tsx` — 526 lines; do not pile more branch-heavy logic inline if a small helper/modal extraction keeps the file stable
- `tests/integration/test_api_design_study.py` — 231 lines
- `tests/unit/test_design_study.py` — 187 lines
No new event type is needed. New boundary data (`production_format`, `sources_used`) already has a schema-first plan via existing Pydantic models and TS types before consumers change.

Eval / baseline:
- This story is plumbing/UI, so the success measure is deterministic tests plus manual UI verification rather than model comparison.
- Baseline on current code: `python -m pytest tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` → `12 passed`.
- Final verification target: keep those tests green, add schema/settings coverage, then run the broader required backend/UI checks once implementation lands.

Redundancy plan:
- If `build_image_prompt()` fully subsumes the direct prompt-construction call in the design-study router, remove the old call path instead of keeping both.
- Do not leave an unused modal state branch in `DesignStudySection.tsx`; collapse the generate flow to one canonical path after the modal decision.
- Do not duplicate edit affordances across Script, Intent, and settings with different implementations; use one picker/editor surface behind the modal and header pill.

UI verification plan:
- Preferred: start backend + UI dev servers, open the design-study screen for a project with no `production_format`, trigger Generate, confirm the modal appears, pick a format, and verify the next Generate skips the modal. Then open Script and Intent and confirm Script shows only the small breadcrumb pill while Intent shows the editable `Visual Medium` control. Click the Script pill to jump into Intent and confirm the editor opens there.
- Browser tooling: use Playwright/browser tools for a screenshot of the Script breadcrumb pill, a screenshot of the Intent-side `Visual Medium` card in both set and unset states, an interaction check that Script links to Intent, an interaction check that the Intent control opens the picker, and a console-error check.
- Fallback if browser tooling is unavailable: use the webapp-testing skill/runbook and record the blocker plus a manual verification path in the work log.

Human-approval blockers:
- Small scope expansion already folded in: introduce the minimal `build_image_prompt()` seam and `sources_used` round-trip needed to satisfy the story honestly. Relative effort: `S`.
- UI scope adjustment from the earlier plan: use an Intent-owned `Visual Medium` surface plus a Script breadcrumb pill, rather than editable header pills on both pages or a generic Project Settings field. This is a cleaner fit with the story goal and keeps Script from feeling like production setup.
- Schema/API surface change: `production_format` becomes part of project settings and project summary. This is expected and low risk in this greenfield repo, but it is a real inter-layer contract change.

## Work Log

20260303-1700 — story created: User identified during Story 056 browser testing that Imagen images look like concept art drawings rather than photorealistic stills for a live-action project. Production format is a threshold moment between story-half and production-half of the product — surfaces only on first visual generation.

20260314 — Backlog cleanup: corrected the sequencing note, confirmed the story is build-shaped, and promoted it from `Draft` to `Pending`. `production_format` is the project-level prerequisite for the prompt-compiler and composition UX follow-ons, not a downstream detail of them.

20260314-1405 — exploration: read `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, ADR-003, and dependency Story 056; traced the current project settings path (`src/cine_forge/api/models.py`, `src/cine_forge/api/service.py`, `src/cine_forge/api/app.py`) plus the design-study generation path (`src/cine_forge/ai/image.py`, `src/cine_forge/api/routers/design_study.py`, `src/cine_forge/schemas/design_study.py`, `ui/src/lib/api/design-study.ts`, `ui/src/components/DesignStudySection.tsx`). Found that the story's original file map was stale (`ProjectConfig` lives in `src/cine_forge/schemas/models.py`, not `schemas/project_config.py`), `build_image_prompt()` does not exist yet, and `sources_used` is not currently in the round schema/API/UI contracts. Baseline tests: `python -m pytest tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` → `12 passed`. Structural check: `make check-size` plus targeted `wc -l` confirmed `DesignStudySection.tsx` is already 526 lines and `api/app.py` / `api/service.py` are >1000, so the implementation plan must keep edits surgical and prefer extraction over more inline branching. Next step: wait for approval, then implement via the existing project settings sync path and the minimal prompt-builder seam folded in from Story 119.

20260314-1422 — UX correction: reviewed the existing settings UI and concluded the story needs more than a first-run modal, but a generic settings-field solution is not the best fit. A modal-only approach would make `production_format` hidden state; a permanently visible unset pill would violate the story goal that story-only users should not see production setup. Updated the story so the durable edit surface is an editable pill on the Script and Intent headers that only appears once a format exists, while first capture still happens inside the first visual-generation flow.

20260314-1546 — implementation: added typed `production_format` support to `ProjectConfig`, `ProjectSummary`, and `ProjectSettingsUpdate`; synced project-setting changes into canonical `project_config` artifacts; introduced `build_image_prompt()` plus `FORMAT_STYLE_MODIFIERS`; and added `sources_used` to design-study rounds so prompt provenance survives the API/UI round-trip. Frontend work added a shared `ProductionFormatModal`, reusable `ProductionFormatPill`, Script/Intent header integration, and first-run gating in `DesignStudySection.tsx` that saves the selected format then continues generation without a second click. Evidence: targeted backend tests for schema/settings/design-study passed (`45 passed`), and the API now round-trips `production_format` while design-study responses include `sources_used`. Next step: run full static checks and runtime/browser smoke verification.

20260314-1608 — verification: installed missing `ui/node_modules` with `pnpm --dir ui install` so UI checks could run in this worktree; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`533 passed, 125 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` completed with 5 pre-existing `react-refresh/only-export-components` warnings and no new errors, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed. Playwright runtime smoke on the live dev servers verified: a saved format appears as an editable header pill on Script, changing it persisted (`Live Action` → `Anime`) and updated the Script page immediately, the same `Anime` pill appeared on Intent and reopened the shared picker there, an unset project rendered no header pill after load, the modal UI was captured in-browser with `Anime` selected, and console errors were `0`. Docs search/update result: no repo docs besides this story needed changes for the current implementation slice. Next step: hand off for `/validate`.

20260314-1718 — plan correction: revisited `docs/ideal.md` and ADR-003 after user feedback. Conclusion: `production_format` is a base visual-medium choice, not the project's whole style system. Updated the story plan so Intent & Mood owns the durable edit surface, Script drops to a breadcrumb pill, and the UI language shifts to `Visual Medium`. Captured the larger follow-on idea — an Intent-side visual-direction stack with directors, films, mood boards, and compiled creative briefs — in `docs/inbox.md` instead of silently expanding this story.

20260314-1827 — implementation correction: extracted `ui/src/components/VisualMediumCard.tsx` so the new Intent-owned medium surface did not add more inline logic to `IntentMoodPage.tsx`, updated `ProductionFormatPill.tsx` to support two modes (`edit` for Intent, `intent-link` for Script), shifted user-facing copy from `Production Format` to `Visual Medium`, and updated the design-study modal copy to point users back to Intent & Mood. This keeps Script lightweight while preserving the first-run generation gate.

20260314-1836 — verification refresh: reran `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`533 passed, 125 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (same 5 pre-existing `react-refresh/only-export-components` warnings, no errors), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass; same existing Vite chunk-size warning), and `git diff --check` (clean). Playwright smoke on the running dev servers verified: Script shows a small linked `Anime` pill that routes to `Intent & Mood`; Intent shows a `Visual Medium` card with an editable button when set; an unset project shows no Script pill but does show a `Choose visual medium` button in Intent; both set and unset Intent states open the picker; browser console errors remained `0`. Next step: hand off for `/validate`.

20260314-2148 — UX consolidation: fixed the follow-on issues from live testing by moving the large project-level references surface out of `ProjectHome.tsx` and into Intent, adding `ProjectReferencesSection.tsx` so Script stays screenplay-first, and unifying pipeline-run startup/CTA state around the shared `activeRunId` path. Added `startTrackedRun()` plus `useActiveProjectRun()` so the Intent gate button and chat action buttons now use the same run source of truth, disable while a run is active, and show the current plain-language run label. Also fixed a stale-banner bug in `useRunProgressChat`: finished runs now clear `activeRunId` even when completion messages already exist from a previous mount. Browser evidence: `format-pill-smoke` Script no longer shows `Project References`; `format-pill-smoke/intent` shows both `Visual Medium` and `Project References`; starting Deep Breakdown from Intent immediately disabled the gate CTA and showed shared banner/chat progress; `format-pill-unset/intent` now correctly offers `Run Script Breakdown` first, then disables to `Running Script Breakdown...` after click. Checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`533 passed, 125 deselected`), `pnpm --dir ui run lint` (same 5 pre-existing warnings), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `git diff --check`, Playwright console errors `0`.

20260314-2235 — state-language correction: investigated the confusing `the-mariner-2` Intent state after user feedback. Artifact evidence from `GET /api/projects/the-mariner-2/artifacts` showed only script-breakdown outputs (`canonical_script`, `scene`, `scene_index`, `script_bible`, `project_config`) and no deep-breakdown artifacts (`character_bible`, `location_bible`, `entity_graph`), so the Intent gate was correct but the operator wording was not. Updated the story plan and implementation so gated Intent states place the prerequisite/status card directly under `Visual Medium` and above `Project References`, and so run-completion chat copy now explicitly says `Script Breakdown complete!` or `Deep Breakdown complete!` instead of the misleading generic `Breakdown complete!`. This keeps the phase transition legible and aligns the page flow with the actual blocking dependency.

20260314-2258 — validation: ran the required validation suite against the worktree code using the shared repo virtualenv with `PYTHONPATH=src` because this worktree has no local `.venv`. Checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`533 passed, 125 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), targeted pytest for `tests/unit/test_project_config_schema.py tests/unit/test_api.py tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` (pass when rerun with `PYTHONPATH=src`; initial plain invocation imported the sibling main-repo package and is not a product failure), `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass; same existing chunk-size warning). Browser validation with Playwright confirmed: Script shows only the linked visual-medium pill on `format-pill-smoke`, clicking it routes to `Intent & Mood`, Intent shows `Visual Medium` plus `Project References`, and the real `the-mariner-2/intent` page now places the Deep Breakdown gate above `Project References` with `0` console errors. Residual note: previously stored chat history still shows the old generic `Breakdown complete!` wording, but fresh runs will use the corrected phase-specific completion copy. Recommended next step: `/mark-story-done`.

20260314-2310 — closure: marked Story 120 done after validation confirmed all acceptance criteria, tests, and browser checks. Story 120 now lands the project-level `production_format`/`Visual Medium` path end-to-end: persisted settings, format-aware design-study prompts with provenance, first-run capture in the visual lane, Script breadcrumb editing via Intent, Intent-owned project references, and shared Script Breakdown / Deep Breakdown run-state handling. Evidence: validation grade `A`, workflow gates complete, `docs/stories.md` updated to `Done`, and changelog entry added. Recommended next step: `/check-in-diff`.
