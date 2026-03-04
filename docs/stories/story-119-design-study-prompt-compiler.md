# Story 119 — Design Study Prompt Compiler + Visual Reference Propagation

**Priority**: Medium
**Status**: Draft
**Spec Refs**: Film Lane (spec §267) — visual references flow forward into shot planning, storyboards, animatics
**Depends On**: Story 056 (Design Study — Done), Story 120 (Production Format Setting — for `production_format` field in prompt compiler)

## Goal

The current design study prompt is thin: it only reads the entity bible. A real prompt compiler should gather everything that influences how the entity looks — genre, period, visual style direction, emotional tone — and synthesize a richer, more coherent image prompt. Additionally, when the user marks an image as `selected_final`, that filename should be written back to the entity's bible manifest as a `visual_reference_image` field so downstream stages (storyboard generator, video previz) can find the canonical character/location/prop image without manual wiring.

Two deliverables:
1. **Prompt compiler** — At generation time, load project_config (genre, period, tone), look_and_feel creative direction, and intent_mood creative direction. Weave relevant context into the synthesized prompt. Record which sources were actually used in the `DesignStudyRound` so the UI can show them.
2. **Downstream propagation** — When `selected_final` is set (via the decide endpoint), update the entity's bible manifest `visual_reference_image` field. When deselected, clear it.

## Acceptance Criteria

- [ ] Generating an image with an existing look_and_feel artifact incorporates visual style language into the prompt (visible in `prompt_used` field)
- [ ] Generating an image with project_config available incorporates genre/period context into the prompt
- [ ] `DesignStudyRound.sources_used` lists which context sources contributed (e.g. `["bible", "look_and_feel", "project_config"]`)
- [ ] Sources panel in `DesignStudySection.tsx` lists what inputs were used for each round
- [ ] Setting `selected_final` on an image updates the entity's bible manifest with `visual_reference_image: filename`
- [ ] Deselecting (toggle off) clears `visual_reference_image` from the bible manifest
- [ ] All existing design study integration tests pass
- [ ] New integration test: generate with mock look_and_feel → verify prompt contains style language

## Out of Scope

- Actual storyboard generation (separate story)
- Video previz generation
- Image model selection beyond what Story 056 provides (model picker UI already exists)
- Prompt compiler UI for manual editing of the synthesized prompt
- Seed image conditioning via API (Imagen 4 doesn't support image-to-image in the current API)

## Approach Evaluation

This is pure plumbing — no AI reasoning needed for the prompt compiler itself. The synthesis is deterministic: gather fields, concatenate with priority ordering, truncate if needed.

- **Pure code**: Read artifact store for look_and_feel + project_config + intent_mood, extract relevant fields (visual style, genre, period, tone keywords), append to bible-derived prompt. Simple string operations, no LLM call. This is almost certainly the right approach.
- **AI-assisted synthesis**: LLM takes the raw context objects and writes a unified visual brief. Higher quality but adds latency and cost to every generation call. Not justified when the downstream call (Imagen 4) is already ~15s.
- **Eval**: Manual inspection of generated images with/without context enrichment — does the enriched version look more consistent with the intended film style? No automated eval needed at this stage; visual quality is subjective. Document examples in the work log.

**Decision gate**: Start with pure code. If after 10+ real generations the prompts feel generic/inconsistent with the film direction, revisit AI-assisted synthesis.

## Tasks

- [ ] Add `sources_used: list[str]` to `DesignStudyRound` schema (e.g. `["bible", "project_config", "look_and_feel"]`)
- [ ] Write `build_image_prompt()` in `src/cine_forge/ai/image.py` — replaces `synthesize_image_prompt()`, accepts `bible_data` + optional `project_config_data`, `look_and_feel_data`, `intent_mood_data`
- [ ] Update generate router to load project_config, look_and_feel, intent_mood from artifact store before calling prompt builder; populate `sources_used` on the round
- [ ] Update `DesignStudyRound` TypeScript interface in `ui/src/lib/api.ts` — add `sources_used: string[]`
- [ ] Add "Sources used" display in `DesignStudySection.tsx` (collapse toggle under generate controls — show what context was available for the last round)
- [ ] Update decide router: when decision becomes `selected_final`, write `visual_reference_image` to bible manifest; when deselected, clear it
- [ ] Add integration test: generate with mock look_and_feel → verify prompt contains style language
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

- **Owning class/module**: `src/cine_forge/ai/image.py` (prompt synthesis), `src/cine_forge/api/routers/design_study.py` (context loading + propagation)
- **Data contracts**: `DesignStudyRound.sources_used: list[str]` (new field, backward-compatible default `[]`). Bible manifest gains `visual_reference_image: str | None` — needs to be added to `BibleManifest` schema or stored as a sidecar key.
- **File sizes**: `image.py` ~188 lines (fine), `design_study.py` router ~298 lines (fine), `design_study.py` schema ~78 lines (fine)

## Files to Modify

- `src/cine_forge/schemas/design_study.py` — add `sources_used: list[str] = []` to `DesignStudyRound` (78 lines)
- `src/cine_forge/ai/image.py` — refactor/extend `synthesize_image_prompt` into `build_image_prompt` accepting multi-source context (188 lines)
- `src/cine_forge/api/routers/design_study.py` — load context before generation; update decide endpoint to propagate to bible manifest (298 lines)
- `ui/src/lib/api.ts` — add `sources_used: string[]` to `DesignStudyRound` interface
- `ui/src/components/DesignStudySection.tsx` — add Sources display in generate area (465 lines)
- `tests/integration/test_api_design_study.py` — add context-enrichment test (232 lines)

## Notes

- `look_and_feel` and `intent_mood` artifacts may not exist for a project — gracefully degrade, just use bible + project_config
- The `sources_used` field on `DesignStudyRound` is display-only — it doesn't affect generation logic, only shows the user what fed the prompt
- For `visual_reference_image` propagation: check whether bible manifest schema already has a slot for this or needs a new optional field. If the schema doesn't have it, adding it is a small non-breaking change (optional field with `None` default).
- Priority ordering for prompt assembly: specific entity description (bible) > visual style (look_and_feel) > genre/period (project_config) > emotional tone (intent_mood). More specific = higher priority = earlier in prompt.
- This is the foundation for storyboard generation consistency: the storyboard module will load `visual_reference_image` to use as a face/design reference when available.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260303-1600 — story created: Design discussion with user during Story 056 browser testing — user wants prompt compiler (gather genre/style/mood context) and downstream propagation (selected_final → bible manifest). This is a Draft; needs design review before building.
