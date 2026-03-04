# Story 121 — Design Study Composition UX

**Priority**: Medium
**Status**: Draft
**Spec Refs**: Film Lane (spec §267) — iterative visual development, round-by-round creative direction
**Depends On**: Story 056 (Design Study — Done)

## Goal

The current design study UX is a one-shot affair: generate images, look at them, maybe select one. There's no way to tell the next generation what you liked or didn't like without typing the same guidance from scratch every time. This story introduces a **composition bar** — a sticky "next generation" panel where the user can attach positive reference images (✓), negative reference images (✗), and a text directive, then fire the next round. It also adds **contact sheet history**: previous rounds collapse to a thumbnail strip, preserving the creative archaeology without burying the current round. A "Regenerate from here" action on any historical round pre-seeds the composition bar from that round's context, enabling creative branching. Inspired by Grok Imagine's fluid, scroll-and-heart generation model — adapted for our latency constraints (5–60s per generation).

## Acceptance Criteria

- [ ] `DesignStudyRound` gains `positive_refs: list[str]` and `negative_refs: list[str]` (filenames of images from previous rounds used as composition references)
- [ ] `DesignStudyRound` gains `directive: str | None` (free-text composition instruction for this round)
- [ ] Composition bar visible below the current round's images — shows: positive ref chips (green ✓), negative ref chips (red ✗), directive text input, model picker, image count, Generate button
- [ ] Clicking a generated image's ✓ button adds it as a positive reference in the composition bar; clicking ✗ adds it as a negative reference
- [ ] Composition bar chips are removable (click × on chip)
- [ ] When Generate fires, `positive_refs`, `negative_refs`, and `directive` are sent to the backend and stored on the new `DesignStudyRound`
- [ ] Previous rounds display as collapsed thumbnail strips (80–100px height) with decision overlays (heart/check/× visible at thumbnail size); clicking a round expands it to full view
- [ ] Current round is always expanded; navigating to a historical round collapses the current one
- [ ] "Regenerate from here" action on any historical round pre-fills the composition bar with that round's `directive` and seeds the model from that round
- [ ] All existing design study integration tests pass

## Out of Scope

- Actual image-to-image conditioning (Imagen 4 and gpt-image-1 don't support seed images via current API) — positive/negative refs inform the *text prompt* only (Story 122+)
- Auto-generating new images as user scrolls (Grok-style continuous generation) — latency is 5–60s; UX design for continuous gen is a separate story
- Multi-entity composition (mixing refs from different characters) — single-entity only
- Keyboard navigation of the contact sheet
- Drag-and-drop ref ordering

## Approach Evaluation

Pure UI + data plumbing — no AI reasoning.

- **AI-only**: N/A — composition is user-directed, not AI-inferred. (AI could *suggest* which images to use as refs based on diversity/similarity, but that's future work.)
- **Hybrid**: N/A for core feature. Optional enhancement: LLM synthesizes a unified directive from positive/negative refs + text into a richer prompt. This is Story 119's domain (prompt compiler) — compose there, not here.
- **Pure code**: Extend `DesignStudyRound` schema with ref fields + directive; pass through to `build_image_prompt()`; build composition bar as React component; collapse/expand round history in UI. All deterministic.
- **Eval**: Manual visual check — do rounds with composition context produce images that reflect the stated direction better than rounds without? No automated eval; subjective.

## Tasks

- [ ] Add `positive_refs: list[str] = []`, `negative_refs: list[str] = []`, `directive: str | None = None` to `DesignStudyRound` schema
- [ ] Update `GenerateRequest` in `design_study.py` router to accept `positive_refs`, `negative_refs`, `directive`; pass to `build_image_prompt()` (Story 119) for prompt enrichment
- [ ] Update `build_image_prompt()` to incorporate directive and positive/negative ref descriptions (pull `prompt_used` from ref images' rounds for context)
- [ ] Update TypeScript `DesignStudyRound` interface in `api.ts` — add `positive_refs`, `negative_refs`, `directive`
- [ ] Build `CompositionBar` component — sticky footer panel with ref chips, directive input, model picker, count, Generate button
- [ ] Wire per-image ✓/✗ buttons in `ImageCard` — these are distinct from the decision buttons (heart/check/×); they add the image to the composition bar as a ref
- [ ] Build `ContactSheetRow` component — collapsed thumbnail strip for a round, click to expand
- [ ] Update `DesignStudySection` to render: current round expanded + `CompositionBar`; history as `ContactSheetRow` list
- [ ] "Regenerate from here" action on `ContactSheetRow` — pre-fills `CompositionBar` directive from that round
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

- **Owning class/module**: `DesignStudySection.tsx` (layout/orchestration), new `CompositionBar.tsx` + `ContactSheetRow.tsx` components, `DesignStudyRound` schema
- **Data contracts**: `DesignStudyRound` gains three new optional fields (backward-compatible). `GenerateRequest` gains matching optional fields. No new inter-layer schemas needed.
- **File sizes**: `DesignStudySection.tsx` ~465 lines — composition changes may push it toward 600. Consider extracting `ImageCard` to its own file first.

## Files to Modify

- `src/cine_forge/schemas/design_study.py` — add `positive_refs`, `negative_refs`, `directive` to `DesignStudyRound` (~78 lines)
- `src/cine_forge/api/routers/design_study.py` — update `GenerateRequest` + forward fields to prompt builder (~298 lines)
- `src/cine_forge/ai/image.py` — update `build_image_prompt()` to use directive + ref context
- `ui/src/lib/api.ts` — update `DesignStudyRound` interface + `GenerateDesignStudyParams`
- `ui/src/components/DesignStudySection.tsx` — layout refactor; wire CompositionBar + ContactSheetRow (~465 lines → may need split)
- `ui/src/components/CompositionBar.tsx` — new component (sticky next-gen bar)
- `ui/src/components/ContactSheetRow.tsx` — new component (collapsed thumbnail strip per round)

## Notes

- **Composition bar design**: Sticky bottom panel on the design study page. Left side: chip row (green ✓ chips for positive refs, red ✗ chips for negative refs, each with an × dismiss). Center: text input for directive ("Make it darker, more weathered"). Right: model picker + image count + Generate button.
- **Thumbnail size**: 80–100px height per image, aspect-ratio preserved. Decision overlays (heart/check/× icons) must be legible at this size — use colored backgrounds (green/red), not just icons.
- **"Regenerate from here"**: This pre-fills the composition bar from a historical round's directive. It does NOT copy the round's positive/negative refs (those are session-specific user choices). It's a creative branching point, not a replay.
- **Positive/negative refs inform prompt text only**: Since image-to-image conditioning isn't available, the `build_image_prompt()` function should look up the `prompt_used` from each ref image's round and incorporate phrases from it. E.g. positive refs → "Incorporate elements like: [summary of ref prompts]"; negative refs → "Avoid: [summary of ref prompts]". This is imprecise but directionally useful.
- **Grok Imagine inspiration**: Their model is fluid — generate many, heart as you go, the stream continues. We can't match their latency, but we can match the creative intent: composition bar is always ready, history is always accessible, no page reloads between rounds.
- **Contact sheet inspiration**: Film contact sheets — tiny thumbnails of every frame, laid out in rows. Directors mark keepers with a grease pencil. Same concept applied to AI generations.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260303-1700 — story created: User identified during Story 056 browser testing that there's no UX for iterative generation — each round starts from scratch. Inspired by Grok Imagine's fluid generation model and film contact sheet workflow. Sticky composition bar + contact sheet history is the design direction.
