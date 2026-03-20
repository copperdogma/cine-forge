# Story 121 — Design Study Composition UX

**Priority**: Medium
**Status**: Done
**Spec Refs**: spec:2.6 (Two-Lane Architecture / Film Lane), spec:4.10.2 (Look & Feel), spec:6.2 (Storyboards), spec:6.3 (Animatics / Previz Video)
**Depends On**: Story 056 (Design Study — Done), Story 120 (Production Format Setting), Story 119 (Design Study Prompt Compiler + Visual Reference Propagation)
**Updated**: 2026-03-14 — backlog cleanup clarified that this story builds on the format and prompt-compiler work first.

## Goal

The current design study UX is a one-shot affair: generate images, look at them, maybe select one. There's no way to tell the next generation what you liked or didn't like without typing the same guidance from scratch every time. This story introduces a **composition bar** — a sticky "next generation" panel where the user can attach positive reference images (✓), negative reference images (✗), and a text directive, then fire the next round. It also adds **contact sheet history**: previous rounds collapse to a thumbnail strip, preserving the creative archaeology without burying the current round. A "Regenerate from here" action on any historical round pre-seeds the composition bar from that round's context, enabling creative branching. Inspired by Grok Imagine's fluid, scroll-and-heart generation model — adapted for our latency constraints (5–60s per generation).

**Backlog sequencing note:** Build this after Story 120 settles the project-wide `production_format` model and Story 119 establishes the shared prompt compiler. Otherwise the iteration UX risks rework around the wrong prompt pipeline.

## Acceptance Criteria

- [x] `DesignStudyRound` gains `positive_refs: list[str]` and `negative_refs: list[str]` (filenames of images from previous rounds used as composition references)
- [x] `DesignStudyRound` gains `directive: str | None` (free-text composition instruction for this round)
- [x] Composition bar visible below the current round's images — shows: positive ref chips (green ✓), negative ref chips (red ✗), directive text input, model picker, image count, Generate button
- [x] Clicking a generated image's ✓ button adds it as a positive reference in the composition bar; clicking ✗ adds it as a negative reference
- [x] Composition bar chips are removable (click × on chip)
- [x] When Generate fires, `positive_refs`, `negative_refs`, and `directive` are sent to the backend and stored on the new `DesignStudyRound`
- [x] Previous rounds display as collapsed thumbnail strips (80–100px height) with decision overlays (heart/check/× visible at thumbnail size); clicking a round expands it to full view
- [x] Current round is always expanded; navigating to a historical round collapses the current one
- [x] "Regenerate from here" action on any historical round pre-fills the composition bar with that round's `directive` and seeds the model from that round
- [x] Prompt provenance stays transparent: composition inputs are recorded in `sources_used`, and the sources panel shows the directive plus any positive/negative reference filenames used for that round
- [x] All existing design study integration tests pass

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

- [x] Replace the current round-level `guidance` field with a single `directive` concept across schema/API/UI instead of adding duplicate state; keep image-level `guidance` for per-image reject/seed notes
- [x] Add `positive_refs: list[str] = []`, `negative_refs: list[str] = []`, `directive: str | None = None` to `DesignStudyRound` schema
- [x] Update `GenerateRequest` in `design_study.py` router to accept `positive_refs`, `negative_refs`, `directive`; pass to `build_image_prompt()` (Story 119) for prompt enrichment
- [x] Update `build_image_prompt()` to incorporate directive and positive/negative ref descriptions (pull `prompt_used` from ref images' rounds for context)
- [x] Update TypeScript `DesignStudyRound` interface in `api.ts` — add `positive_refs`, `negative_refs`, `directive`
- [x] Extract focused router helpers before adding composition plumbing so `generate_design_study()` / `decide_design_study()` do not deepen the existing oversized file
- [x] Build `CompositionBar` component — sticky footer panel with ref chips, directive input, model picker, count, Generate button
- [x] Wire per-image ✓/✗ buttons in `ImageCard` — these are distinct from the decision buttons (heart/check/×); they add the image to the composition bar as a ref
- [x] Build `ContactSheetRow` component — collapsed thumbnail strip for a round, click to expand
- [x] Extract the new `CompositionBar` and `ContactSheetRow` surfaces so `DesignStudySection.tsx` does not absorb another large stateful block
- [x] Update `DesignStudySection` to render: current round expanded + `CompositionBar`; history as `ContactSheetRow` list
- [x] "Regenerate from here" action on `ContactSheetRow` — pre-fills `CompositionBar` directive from that round
- [x] Update `DesignStudySourcesPanel` to display composition provenance (directive text plus positive/negative refs) for each round
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

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `DesignStudySection.tsx` (layout/orchestration), new `CompositionBar.tsx` + `ContactSheetRow.tsx` components, `DesignStudyRound` schema
- **Data contracts**: `DesignStudyRound` gains three new optional fields (backward-compatible). `GenerateRequest` gains matching optional fields. No new inter-layer schemas needed.
- **File sizes**: `DesignStudySection.tsx` ~465 lines — composition changes may push it toward 600. Consider extracting `ImageCard` to its own file first.

## Files to Modify

- `src/cine_forge/schemas/design_study.py` — add `positive_refs`, `negative_refs`, `directive` to `DesignStudyRound` (~78 lines)
- `src/cine_forge/api/routers/design_study.py` — update `GenerateRequest` + forward fields to prompt builder (~298 lines)
- `src/cine_forge/ai/image.py` — update `build_image_prompt()` to use directive + ref context
- `ui/src/lib/api/design-study.ts` — update `DesignStudyRound` interface + `GenerateDesignStudyParams`
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

### Exploration Summary

- Story 121 is now `Pending` and passes the Ideal-alignment gate. It directly closes an `R7` gap: CineForge can generate design-study images, but the current UX does not support a fluid `generate -> react -> refine` loop without retyping context every round.
- This is phase-coherent work for `spec:6` in a `climb` category. It is not premature infrastructure and it is not optimizing a shrinking workaround from `docs/retrofit-gaps.md`; that document is archived, and the live authority is now `docs/spec.md` plus `docs/build-map.md`.
- ADR / design context consulted: `docs/ideal.md`, `docs/spec.md` (`spec:2.6`, `spec:4.10.2`, `spec:6.2`, `spec:6.3`), ADR-002, ADR-003, `docs/design/decisions.md`, Story 056, Story 119, Story 120, and the current design-study backend/frontend/test path.
- Exploration found one small scope correction that should stay inside this story: composition refs must flow through existing prompt provenance (`sources_used`) and the round source panel. Otherwise the next-round UX hides what actually shaped generation and violates the repo’s transparency bar.
- Exploration also found one design conflict that needs an explicit decision before implementation: Story 121’s new round-level `directive` is the same concept as the current round-level `guidance`. Duplicating both fields would be wrong. The plan below assumes **replace round-level `guidance` with `directive` end-to-end**, while keeping image-level `guidance` for reject/seed notes.

### Eval-First Approach Gate

- **What eval?**
  - Backend/schema eval: extend `tests/unit/test_design_study.py` to cover `directive`, `positive_refs`, and `negative_refs` on `DesignStudyRound` plus prompt-source tracking for composition refs.
  - Integration eval: extend `tests/integration/test_api_design_study.py` so a generated round persists composition refs/directive, records the expected `sources_used`, and a later fetch returns those values intact.
  - Preference-learning regression: if round-level `guidance` is renamed to `directive`, update `tests/unit/test_preferences.py` and the related integration assertions so the landed Story 131 preference signal path still records the round-level text correctly.
  - UI/runtime eval: browser verification on an entity detail route to confirm the composition bar, collapsed contact-sheet history, and provenance panel work together without console errors.
- **Baseline**
  - Existing targeted test slice is green: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` -> `21 passed`.
  - Static baseline from exploration:
    - `DesignStudyRound` currently has `guidance` + `seed_image_filename`, but no `directive`, `positive_refs`, or `negative_refs`.
    - `generate_design_study()` only accepts a single free-text `guidance` plus optional `seed_image_filename`.
    - `DesignStudySection.tsx` shows the latest round full-size and earlier rounds full-size behind a show/hide toggle; there is no composition bar or contact-sheet history.
- **Candidate approaches**
  - **Pure code**: deterministic prompt composition using stored prompt/context text from referenced images plus explicit directive text. No extra model call.
  - **Hybrid**: deterministic reference collection, then an LLM rewrites positive/negative refs + directive into a unified brief before image generation.
  - **AI-only**: hand referenced round data to an LLM and let it decide how to carry context forward each round.
- **Chosen approach**
  - Pure code is the correct fit here. Story 119 already established a deterministic prompt compiler; Story 121 is extending that compiler with more explicit user-authored context, not adding a new reasoning problem.
  - Hybrid / AI-only are rejected because they add cost and latency to every iteration, muddy source attribution, and solve a problem the repo already models as prompt compilation.

### Repo-Fit / Optimality Evidence

- `docs/ideal.md` makes iterative exploration the product (`R7`) and explicitly says users discover taste by reacting to generated variants. Story 121 is a direct product-level move toward that Ideal.
- ADR-003 positions prompt compilation as a read-only projection of upstream creative artifacts. That supports adding composition refs to the existing compiler path, not inventing a second AI summarizer.
- Story 119 already threads multiple prompt sources (`look_and_feel`, `project_config`, `intent_mood`, `learned_preferences`) through `build_image_prompt()` and `sources_used`; Story 121 should extend that exact path.
- Story 131 already treats design-study actions as durable taste signals. That argues for **keeping** existing decision buttons and preference capture intact, while adding composition refs as a separate next-round surface instead of replacing the landed preference-learning substrate.
- The current code already has a single-image seed mechanism (`seed_for_variants` + `seed_image_filename`). Multi-ref composition should layer on top of that deterministic substrate, not fork it into an unrelated workflow.

**Main alternatives rejected**

- Adding a second round-level field beside `guidance`:
  - Wrong because `directive` and round `guidance` are the same semantic slot. Duplicate state would create avoidable drift.
- Replacing the entire existing seed/preference loop:
  - Wrong because Story 131 depends on those signals already. Story 121 should add composition refs without silently deleting the landed preference-learning behavior.
- Full-size historical rounds with just more buttons:
  - Wrong because that continues the current UX problem. The story’s value is making history scan quickly and composition inputs easy to stage, not making the existing wall of cards denser.

### Structural Health Check

- `make check-size` findings relevant to this story:
  - `src/cine_forge/api/routers/design_study.py` — `528` lines, already large
  - `src/cine_forge/ai/image.py` — `516` lines, already large
  - `ui/src/components/DesignStudySection.tsx` — `408` lines, over the 400-line acknowledgement threshold
  - `ui/src/pages/EntityDetailPage.tsx` — `890` lines, at risk if this story leaks layout logic upward
  - `tests/integration/test_api_design_study.py` — `470` lines
- Methods / components that trigger the decomposition rule:
  - `generate_design_study()` in [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/api/routers/design_study.py) is already a large handler and will grow if composition lookup is added inline.
  - `decide_design_study()` in the same file is already over the 100-line method threshold and should not absorb new round-state logic without helper extraction.
  - `DesignStudySection()` in [DesignStudySection.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudySection.tsx) is already a large stateful component and needs child extraction before more UI state is added.
- Schema / contract checks:
  - New cross-layer data (`directive`, `positive_refs`, `negative_refs`) belongs in `src/cine_forge/schemas/design_study.py` first, then the router and TS types.
  - If round-level `guidance` is renamed to `directive`, the matching preference-signal contract in `src/cine_forge/schemas/preferences.py` must be updated before service code depends on it.
  - No new event type is needed.

### Task-by-Task Plan

1. **Schema-first composition contract**
   - Files:
     - [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/schemas/design_study.py)
     - [preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/schemas/preferences.py)
     - [design-study.ts](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/lib/api/design-study.ts)
     - [test_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_design_study.py)
     - [test_preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_preferences.py)
   - Change:
     - Replace round-level `guidance` with `directive`.
     - Add `positive_refs` / `negative_refs` to `DesignStudyRound` and the generate request contract.
     - Keep image-level `guidance` unchanged for reject/seed note capture.
     - Rename `round_guidance` to `round_directive` in the preference-signal schema/service path if the round field rename is approved.
   - Impact / risk:
     - This is a cross-layer contract change touching backend, API, UI, and preference aggregation.
   - Done looks like:
     - Unit tests can construct a round with directive + refs, and the TS/API contract matches the schema exactly.

2. **Backend helper extraction before feature logic**
   - Files:
     - [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/api/routers/design_study.py)
     - [image.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/ai/image.py)
   - Change:
     - Extract focused helpers for:
       - resolving reference images from filenames in existing state
       - turning referenced rounds/images into concise positive/negative prompt context
       - building / appending a new round payload
       - mutating round/image decisions without deepening `decide_design_study()`
     - Keep `build_image_prompt()` as the single compiler entry point, but pass it precomputed composition-context strings or structured ref summaries instead of doing state traversal inside `image.py`.
   - Repo-fit evidence:
     - This keeps prompt compilation deterministic and prevents the current oversized router and compiler files from taking on more unrelated responsibilities.
   - Done looks like:
     - Router handlers get smaller, and composition logic lives in named helpers that tests can target directly.

3. **Prompt composition + provenance**
   - Files:
     - [image.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/ai/image.py)
     - [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/api/routers/design_study.py)
     - [DesignStudySourcesPanel.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudySourcesPanel.tsx)
     - [test_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_design_study.py)
     - [test_api_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/integration/test_api_design_study.py)
   - Change:
     - Extend prompt-building to include:
       - the round directive
       - positive reference summaries
       - negative reference summaries
       - existing seed / learned-preference / style-context inputs
     - Record provenance in `sources_used` with explicit composition entries, and show the directive + reference filenames in the source panel.
   - Impact / risk:
     - Any change here affects Story 119 provenance guarantees and Story 131 preference-learning prompt sources.
   - Done looks like:
     - Integration tests prove that a generated round stores the expected refs, the fetched round shows the same values, and `sources_used` reflects the active composition inputs.

4. **UI extraction + composition bar**
   - Files:
     - [DesignStudySection.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudySection.tsx)
     - [DesignStudyImageCard.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudyImageCard.tsx)
     - new `ui/src/components/CompositionBar.tsx`
     - new `ui/src/components/ContactSheetRow.tsx`
     - [EntityReferenceStudio.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/assets/EntityReferenceStudio.tsx) only if the layout needs a thin integration change
   - Change:
     - Extract the new composition bar and contact-sheet row into focused child components before adding more state to `DesignStudySection`.
     - Add separate positive/negative ref controls to image cards without removing existing decision buttons.
     - Replace the current full-card history toggle with collapsed thumbnail strips, one expanded round at a time.
     - Keep the current round expanded by default.
   - Impact / risk:
     - UI density is the main risk. The image card cannot turn into a button graveyard; composition controls should be visually secondary to final/favorite/reject/seed decisions.
   - Done looks like:
     - `DesignStudySection.tsx` stays manageable, historical rounds collapse into contact-sheet rows, and the composition bar can generate a round with refs/directive/model/count from one place.

5. **Regression coverage + verification**
   - Files:
     - [test_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_design_study.py)
     - [test_api_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/integration/test_api_design_study.py)
     - [test_preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_preferences.py)
   - Change:
     - Add tests for:
       - round contract rename/additions
       - directive + refs persistence
       - prompt provenance for composition inputs
       - preference-service round-text handling if the round field is renamed
     - Then run required backend/UI checks and browser verification.
   - Done looks like:
     - Targeted design-study tests remain green, broader static checks pass, and a browser smoke confirms the new UX on an entity page with no console errors.

### Impact Analysis

- **Files that will change**
  - [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/schemas/design_study.py)
  - [preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/schemas/preferences.py)
  - [design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/api/routers/design_study.py)
  - [image.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/ai/image.py)
  - [preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/services/preferences.py)
  - [design-study.ts](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/lib/api/design-study.ts)
  - [DesignStudySection.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudySection.tsx)
  - [DesignStudyImageCard.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudyImageCard.tsx)
  - [DesignStudySourcesPanel.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/DesignStudySourcesPanel.tsx)
  - new `CompositionBar.tsx`
  - new `ContactSheetRow.tsx`
  - [test_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_design_study.py)
  - [test_api_design_study.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/integration/test_api_design_study.py)
  - [test_preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/tests/unit/test_preferences.py)
- **Files at risk of breakage even if not heavily edited**
  - [EntityDetailPage.tsx](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/pages/EntityDetailPage.tsx) due to layout growth in the reference studio area
  - [reference-library-model.ts](/Users/cam/.codex/worktrees/6a51/cine-forge/ui/src/components/assets/reference-library-model.ts) if API type changes ripple through design-study image metadata
  - [preferences.py](/Users/cam/.codex/worktrees/6a51/cine-forge/src/cine_forge/services/preferences.py) because it records round-level text today
- **Potential redundant code / cleanup targets**
  - The current `showHistory` full-card earlier-round path in `DesignStudySection.tsx`
  - Any duplicated inline composition state that should live in `CompositionBar.tsx`
  - Any duplicated prompt-source label logic outside `DesignStudySourcesPanel.tsx`

### UI Verification Plan

- Route to verify:
  - `/<projectId>/characters/<entityId>` or the equivalent location/prop entity detail route where the Reference Studio renders the design-study UI.
- Interactions:
  - Add one positive ref and one negative ref from historical/current images.
  - Enter a directive, change model/count, and generate a new round.
  - Expand a historical round from the contact sheet and use `Regenerate from here`.
  - Open the sources panel for the new round and confirm the directive + reference filenames are visible.
- Browser checks:
  - Screenshot of composition bar with ref chips
  - Screenshot of collapsed contact-sheet history with overlays
  - Console check for zero new errors
  - Optional network check that the generate request carries `directive`, `positive_refs`, and `negative_refs`
- Fallback if browser tools fail:
  - Use the browser-automation runbook and record the blocker in the work log instead of guessing.

### Human-Approval Blockers / Scope Adjustments

- **Directive vs guidance**
  - Recommendation: replace round-level `guidance` with `directive` across schema/API/UI and the preference-signal path. Do **not** add a second round-level field. Relative effort: `S`.
- **Seed flow coexistence**
  - Recommendation: keep the existing `seed_for_variants` decision path intact for now. Treat composition refs as a separate next-round staging surface rather than removing Story 131’s landed signal path inside Story 121. Relative effort if you want to also redesign/remove the seed path now: `M`.
- **Small scope expansion already folded into this story**
  - Composition provenance through `sources_used` + `DesignStudySourcesPanel`.
  - Helper extraction to keep the oversized router/component from growing in place.

### Definition Of Done

- A user can stage next-round generation from a composition bar using positive refs, negative refs, directive text, model, and count.
- Historical rounds render as contact-sheet rows instead of a wall of full-size cards.
- The new round persists the chosen directive and reference filenames, and the sources panel explains what shaped the round.
- Existing seed/favorite/final/reject behavior still works when composition refs are unused.
- Targeted tests pass, required backend/UI checks pass, and browser verification on an entity route is clean.

## Work Log

20260303-1700 — story created: User identified during Story 056 browser testing that there's no UX for iterative generation — each round starts from scratch. Inspired by Grok Imagine's fluid generation model and film contact sheet workflow. Sticky composition bar + contact sheet history is the design direction.

20260314 — Backlog cleanup: added explicit dependencies on Stories 120 and 119 so the composition UX is not built against an unstable format/prompt baseline.
20260320-1050 — status promoted to Pending and workflow gates added so `/build-story` can proceed. Next: complete exploration, structural health check, and implementation plan before any code changes.
20260320-1118 — exploration: reviewed `docs/ideal.md`, `docs/spec.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Story 056, Story 119, Story 120, `docs/build-map.md`, and the archived `docs/retrofit-gaps.md` note. Traced the live codepath through `src/cine_forge/{schemas/design_study.py,api/routers/design_study.py,ai/image.py,services/preferences.py}`, `ui/src/{lib/api/design-study.ts,components/DesignStudySection.tsx,components/DesignStudyImageCard.tsx,components/DesignStudySourcesPanel.tsx,components/assets/EntityReferenceStudio.tsx,pages/EntityDetailPage.tsx}`, and `tests/{unit/test_design_study.py,unit/test_preferences.py,integration/test_api_design_study.py}`. Baseline evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` -> `21 passed`. Key findings: `DesignStudySection.tsx` is already 408 lines, `design_study.py` is 528 lines, `image.py` is 516 lines, and `decide_design_study()` is already >100 lines, so extraction must precede feature growth; the story text is partly stale because round-level `guidance`, `seed_image_filename`, prompt provenance, and preference learning already exist; and the necessary small scope expansion is to thread composition refs through existing prompt provenance instead of hiding them. Next: human review of the plan and the `directive` vs round-`guidance` contract decision before any implementation starts.
20260320-1129 — implementation start: plan approved. Story moved to In Progress. First implementation task is the schema/API contract cleanup: replace round-level `guidance` with `directive`, add positive/negative composition refs, and update the matching preference-learning schema before feature wiring. Next: land the backend contract changes, then extract router helpers before adding composition logic.
20260320-1215 — implementation: landed the composition contract and UI extraction. `DesignStudyRound`, `GenerateRequest`, prompt building, and preference signals now use `directive` plus `positive_refs` / `negative_refs`; new router helper module `src/cine_forge/api/routers/design_study_support.py` handles decision mutation and reference summarization; and the UI now renders extracted `CompositionBar` + `ContactSheetRow` components with one expanded round at a time, composition ref toggles on image cards, historical round branching, and source-panel provenance for directive/reference filenames. Evidence: updated `tests/unit/test_design_study.py`, `tests/unit/test_preferences.py`, `tests/integration/test_api_design_study.py`, `ui/src/components/{CompositionBar.tsx,ContactSheetRow.tsx,DesignStudySection.tsx,DesignStudyImageCard.tsx,DesignStudySourcesPanel.tsx}`, and `ui/src/components/ProjectPreferenceLearningSection.tsx`. Next: run the full static/runtime verification loop and capture smoke evidence.
20260320-1231 — verification: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `600 passed, 139 deselected`; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` -> clean; `pnpm --dir ui install --frozen-lockfile` restored missing `ui/node_modules` in this worktree; `pnpm --dir ui run lint` -> 0 errors with 5 pre-existing `react-refresh/only-export-components` warnings outside this story’s files; `cd ui && npx tsc -b` -> clean; `pnpm --dir ui run build` -> clean with the existing Vite large-chunk warning. Runtime smoke: local backend on `127.0.0.1:8000` returned `{\"status\":\"ok\",\"version\":\"2026.03.20-02\"}`; local Vite route `http://localhost:5174/cineforge-story121-smoke/characters/mariner` served the app shell with title `CineForge`, and `http://localhost:5174/src/main.tsx` returned HTTP 200; a live mock-backed generate against the running server produced round 2 with directive `Push the silhouette older and harsher, with a less polished coat.`, `positive_refs=[design_study_r1_img1.jpg]`, `negative_refs=[design_study_r1_img2.jpg]`, and `sources_used` including `directive`, `positive_refs`, and `negative_refs`. Browser MCP remained blocked after profile cleanup (`bootstrap_check_in ... Permission denied`, UKM database locked, Playwright context timeout), so screenshot/console verification fell back to HTTP + live API evidence per `docs/runbooks/browser-automation-and-mcp.md`. Next: `/validate`.
20260320-1242 — validation: validation run complete. Findings: browser verification is still incomplete because Playwright MCP could not attach to the Chrome profile even after stale singleton cleanup (`bootstrap_check_in ... Permission denied`, UKM database locked, Playwright context timeout), so this UI-affecting story lacks screenshot/console evidence. Evidence checked: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_design_study.py tests/unit/test_preferences.py tests/integration/test_api_design_study.py -q` -> `25 passed`; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `600 passed, 139 deselected`; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` -> clean; `pnpm --dir ui run lint` -> 0 errors with 5 pre-existing warnings outside touched files; `cd ui && npx tsc -b` -> clean; `pnpm --dir ui run build` -> clean; live mock-backed generate on `/api/projects/cineforge-story121-smoke/design-study/character_mariner/generate` persisted the expected directive, positive refs, negative refs, and `sources_used`. No dedicated promptfoo/acceptance eval exists for this deterministic prompt-plumbing path, so no eval registry update was required. Recommended next step: `/mark-story-done` if the browser-tool environment blocker is accepted as non-story-local drift.
20260320-1400 — browser rerun: closed the missing screenshot/console gap using isolated Playwright instead of the stuck MCP Chrome profile. Added `scripts/reset_playwright_mcp.py`, updated `docs/runbooks/browser-automation-and-mcp.md`, and verified Storybook’s durable pattern was operational isolation rather than special Playwright config. For Story 121 evidence, ran `python3 .agents/skills/webapp-testing/scripts/with_server.py --timeout 90 --server "PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m uvicorn cine_forge.api.app:app --host 127.0.0.1 --port 8000" --port 8000 --server "pnpm --dir ui exec vite --host 127.0.0.1 --port 5174" --port 5174 -- bash -lc 'NODE_PATH=/tmp/cineforge-playwright-probe/node_modules node /Users/cam/.codex/worktrees/6a51/cine-forge/tmp/browser-smoke/story-121-browser-rerun.js'` against a copied smoke project. Result: route `http://127.0.0.1:5174/story121-browser-rerun/characters/mariner` rendered successfully; latest round 3 showed `Sources used` with directive + positive/negative refs; `Regenerate from here` on historical round 2 prefilled the directive `Push the silhouette older and harsher, with a less polished coat.`; expanding round 1 and clicking `Ref +` / `Ref -` staged both chips; `consoleErrors=[]`; `pageErrors=[]`. Screenshots captured at `tmp/browser-smoke/story-121-browser-latest.png` and `tmp/browser-smoke/story-121-browser-branching.png`. Next: if desired, rerun `/validate` to clear the old medium finding with current evidence.
20260320-1415 — validation rerun: reran the mandatory gates against the current diff. Evidence checked: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `600 passed, 139 deselected`; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` -> clean; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_design_study.py tests/unit/test_preferences.py tests/integration/test_api_design_study.py -q` -> clean; `pnpm --dir ui run lint` -> 0 errors with the same 5 pre-existing `react-refresh/only-export-components` warnings outside touched files; `cd ui && npx tsc -b` -> clean; `pnpm --dir ui run build` -> clean with the existing Vite chunk-size warning. Browser verification reran clean via isolated Playwright on `http://127.0.0.1:5174/story121-browser-rerun/characters/mariner`; `consoleErrors=[]`; `pageErrors=[]`; screenshots refreshed at `tmp/browser-smoke/story-121-browser-latest.png` and `tmp/browser-smoke/story-121-browser-branching.png`, and manual inspection confirmed the composition bar, historical branching, and ref chips render correctly. Residual note: the worktree still lacks `.venv/bin/python`, so validation depends on the shared repo venv path. Recommended next step: `/mark-story-done`.
20260320-1428 — completion: Story 121 closed. Status set to `Done`, workflow gates completed, and the story index / changelog were updated to reflect the landed composition-bar + contact-sheet iteration loop plus the Playwright recovery/runbook follow-on that made browser verification reproducible. Evidence remains the current validation set from `20260320-1415`, including `600 passed, 139 deselected`, clean Ruff, clean UI typecheck/build, and clean browser rerun screenshots. Next: `/check-in-diff`.
