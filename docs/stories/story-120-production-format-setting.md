# Story 120 — Production Format Setting

**Priority**: Medium
**Status**: Draft
**Spec Refs**: Film Lane (spec §267) — visual style consistency across design studies, storyboards, animatics
**Depends On**: Story 056 (Design Study — Done)

## Goal

When a user first generates a visual (character/location/prop image), CineForge needs to know whether the project is live-action, animated, anime, etc. — because "cinematic concept art" means very different things for a Pixar-style 3D animation vs. a gritty prestige drama. The `production_format` field should be a one-time threshold moment: a brief picker modal surfaces the first time any image is generated for a project that doesn't yet have a format set. After that, every image generation silently inherits the format's style modifier. Story-only users (who never generate visuals) never see it. This moves us toward visual coherence across all design assets without making setup heavier.

## Acceptance Criteria

- [ ] `project_config` schema gains `production_format: str | None` field (enum: `live_action`, `animation_2d`, `animation_3d`, `anime`, `graphic_novel`, `concept_art`; default: `None`)
- [ ] API endpoint to update `production_format` on a project (PATCH or reuse existing project settings endpoint)
- [ ] On first image generation for a project with `production_format == None`, the UI shows a picker modal before firing the generate request
- [ ] After the user picks a format, the format is persisted to `project_config` and the generate request fires
- [ ] If the user dismisses the modal without picking, the generate request fires without a format (graceful degradation)
- [ ] Format picker remembers the choice — subsequent generations on the same project skip the modal
- [ ] Image prompt compiler incorporates a style modifier based on `production_format` (e.g. live_action → "photorealistic", animation_3d → "Pixar-style 3D render", anime → "anime cel art")
- [ ] `sources_used` includes `"production_format"` when the modifier is applied (hooks into Story 119 sources tracking)
- [ ] All existing design study integration tests pass

## Out of Scope

- Format-aware auto-detection from the screenplay (that's a future story — genre detection gives hints but shouldn't auto-decide)
- Per-entity format override (global project setting only)
- Changing the format after the first generation (can be done via project settings, but no UI for it in this story)
- Format applies only to image generation — storyboard and video previz are separate stories

## Approach Evaluation

This is pure plumbing — no AI reasoning required.

- **AI-only**: N/A — format is a user choice, not an AI inference. (Screenplay genre hints could inform a default suggestion, but that's optional and deferred.)
- **Hybrid**: Could pre-suggest a format based on detected genre (comedy → animation_2d, noir → live_action). Nice-to-have, not needed for v1.
- **Pure code**: Store an enum in `project_config`, map to style modifier string in `build_image_prompt()`, surface modal in UI on first generation. This is correct — no reasoning needed.
- **Eval**: Visual quality check (manual) — do images generated with format modifiers look more consistent with the intended style than without? No automated eval; subjective quality.

## Tasks

- [ ] Add `production_format: str | None = None` to `ProjectConfig` Pydantic schema (or equivalent project_config schema)
- [ ] Add PATCH endpoint or extend existing project settings endpoint to update `production_format`
- [ ] Add TypeScript `production_format` field to project API type; update `api.ts` fetch + mutate calls
- [ ] Write `FORMAT_STYLE_MODIFIERS` map in `image.py` — format id → style string appended to prompt
- [ ] Update `build_image_prompt()` (Story 119) to accept and apply `production_format`; add `"production_format"` to `sources_used` when applied
- [ ] Build `ProductionFormatModal` component — picker with 6 format options, short labels + 1-line descriptions, "Skip for now" escape hatch
- [ ] Wire modal into `DesignStudySection.tsx` — check `project.production_format` before generate; if unset, show modal first
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Architectural Fit

- **Owning class/module**: `project_config` schema (format field), `src/cine_forge/ai/image.py` (style modifier map + prompt injection), `ui/src/components/DesignStudySection.tsx` (modal trigger)
- **Data contracts**: `production_format` is a project-level field on `project_config` artifact. The UI reads it via the existing project API; writes via a new/extended PATCH endpoint. No new inter-layer schemas needed — this is a new field on an existing schema.
- **File sizes**: `image.py` ~284 lines (fine), `design_study.py` router ~298 lines (fine), `DesignStudySection.tsx` ~465 lines (fine)

## Files to Modify

- `src/cine_forge/schemas/project_config.py` (or wherever ProjectConfig is defined) — add `production_format: str | None = None`
- `src/cine_forge/api/routers/project.py` (or project settings route) — add PATCH for `production_format`
- `src/cine_forge/ai/image.py` — add `FORMAT_STYLE_MODIFIERS` map; update `build_image_prompt()` to accept + apply format
- `ui/src/lib/api.ts` — add `production_format` to project type + update/set endpoint
- `ui/src/components/DesignStudySection.tsx` — modal trigger logic
- `ui/src/components/ProductionFormatModal.tsx` — new component (format picker)

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
- The Story 119 `build_image_prompt()` is the natural injection point for the format modifier. Build this story after 119 (or in parallel if 119's interface is settled).

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260303-1700 — story created: User identified during Story 056 browser testing that Imagen images look like concept art drawings rather than photorealistic stills for a live-action project. Production format is a threshold moment between story-half and production-half of the product — surfaces only on first visual generation.
