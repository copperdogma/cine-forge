---
id: "100"
title: "Story World Motif Tracking"
status: "Done"
priority: "High"
ideal_refs:
  - "R3 (continuity), R8 (production artifacts)"
spec_refs:
  - "spec:4.10.6"
  - "spec:4.10.2"
  - "spec:4.10.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "008"
  - "009"
  - "011"
  - "094"
category_refs:
  - "spec:4"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 100: Story World Motif Tracking

**Priority**: High
**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003, Decision #3
**Spec Refs**: spec:4.10.6 (Story World — motif tracking), downstream impact on spec:4.10.2 (Look & Feel) and spec:4.10.3 (Sound & Music)
**Ideal Refs**: R3 (continuity), R8 (production artifacts)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 011 (continuity), Story 094 (concern group schemas)

---

## Goal

Ship the first real **story world motif tracking** slice: a project-level `story_world` artifact that stores recurring visual/audio motifs with thematic meaning, appears as a real concern-group surface instead of a placeholder, supports manual editing plus AI-authored drafts, and feeds motif context into downstream creative-direction and shot-planning prompts.

This story is intentionally narrower than a full "motif system dashboard." The repo-fit first slice is to make motifs real, editable, and consumed by existing generators before building analytics or scene-coverage views on top.

## Why (Ideal Alignment)

ADR-003 identifies motifs as one of the missing ingredients in AI-generated continuity. Global taste, mood, and style can produce consistency, but they do not create deliberate thematic recurrence on their own. A motif is not just "blue lighting everywhere"; it is a recurring, meaningful element such as "mirrors appear whenever John lies" or "a low ship hum precedes every act of fate."

The substrate is already partly present:
- `StoryWorld`, `LookAndFeel`, and `SoundAndMusic` schemas already have motif-shaped fields.
- `intent_mood` propagation already emits a draft `story_world` group.
- `shot_plan_v1` already knows how to render motif-style prompt context.

What is missing is the shipped product path: a real `story_world` module, a recipe stage, a real UI surface, and a manual acceptance/edit loop. Closing that gap moves CineForge toward the Ideal promise that taste belongs to the user and persists through the production pipeline.

## Acceptance Criteria

- [x] `MotifAnnotation.scope` supports the scopes the story promises: `world`, `character`, `location`, `prop`, and `scene`.
- [x] The creative-direction pipeline ships a real `story_world` stage that produces a `story_world` artifact instead of leaving the concern group as a placeholder.
- [x] Scene Workspace no longer renders Story World as a placeholder warning; it renders a real project-scoped Story World panel with motif content from the latest artifact.
- [x] Users can add, edit, and remove motifs through the existing artifact-editing flow, and AI-suggested `story_world` drafts from intent propagation can be accepted into the same artifact path.
- [x] `look_and_feel`, `sound_and_music`, and shot planning receive Story World motif context in their prompt payloads so recurring motifs can influence downstream outputs.
- [x] Focused regression coverage exists for the new stage / schema scope expansion / manual edit path, and browser verification covers the changed Story World surface in desktop and mobile layouts with clean console output.

## Out of Scope

- A separate motif analytics dashboard or scene-by-scene motif coverage matrix
- Automatic screenplay-wide motif mining beyond what the new `story_world` module authors
- Shipping `character_and_performance` as a non-placeholder concern group
- Large continuity redesign work already tracked elsewhere

## Approach Evaluation

- **Simplification baseline**: today there is no shipped Story World path. `story_world` is absent from `configs/recipes/recipe-creative-direction.yaml`, `src/cine_forge/pipeline/scene_actions.py` marks it as a coming-soon placeholder, `ui/src/pages/SceneWorkspacePage.tsx` renders a placeholder card, and `src/cine_forge/modules/creative_direction/story_world_v1/` does not exist.
- **Baseline measurement**: current success is effectively `0/1` on the product goal. The first acceptance gate is mechanical: stage exists, artifact is produced, placeholder is removed, and downstream prompts include motif context. The semantic gate is artifact inspection plus focused module tests because no motif-specific promptfoo harness exists yet.
- **AI-only**: strongest fit for motif authoring. A project-level `story_world_v1` module can synthesize motifs from script/intent/style context in one pass, matching the repo's existing creative-direction module pattern.
- **Hybrid**: deterministic motif extraction plus AI curation is possible, but it adds complexity before a real surface exists. There is no evidence yet that heuristics outperform a direct authored `story_world` artifact for this first slice.
- **Pure code**: wrong fit for thematic motif generation. Code can store and route motifs, but it cannot author meaningful recurring motifs from screenplay context without the AI layer.
- **Repo-fit conclusion**: build a new AI-authored `story_world_v1` module, reuse the existing artifact-editing path for manual control, and thread the resulting motifs into existing prompt consumers. Reject a separate dashboard and reject heuristic extraction for this slice.

## Tasks

- [x] T1: Tighten schema support for motif scope by expanding `MotifAnnotation.scope` and updating any dependent validation/tests.
- [x] T2: Create `story_world_v1` as a real creative-direction module and register its output in the existing recipe/module flow.
- [x] T3: Remove the Story World placeholder path from pipeline actions and Scene Workspace by shipping a real project-level Story World panel/viewer.
- [x] T4: Reuse the generic artifact-editing API/hooks so users can manually add, edit, and remove Story World motifs without inventing a parallel persistence path.
- [x] T5: Feed Story World motif context into downstream `look_and_feel`, `sound_and_music`, and shot-planning prompt compilation where it is currently missing or incomplete.
- [x] T6: Add focused regression coverage for schema scope expansion, the new module/stage, and the chosen UI/edit seam.
- [x] T7: Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=python`
  - [x] Backend lint: `python -m ruff check src/ tests/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] T8: Browser-verify the Story World surface on a representative project state in desktop and mobile views, capture screenshots or equivalent evidence, and confirm clean console output.
- [x] T9: Search all docs and update any affected by the shipped Story World surface or recipe/stage changes.
- [x] T10: Verify adherence to Central Tenets (0-5):
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

- **Primary ownership**: `src/cine_forge/modules/creative_direction/story_world_v1/` should own motif authoring. `src/cine_forge/schemas/concern_groups.py` should remain the schema source of truth. Scene Workspace should render Story World through a focused component instead of adding more logic directly to `ui/src/pages/SceneWorkspacePage.tsx`.
- **Existing seams to reuse**: `src/cine_forge/services/intent_mood.py` and `src/cine_forge/api/routers/intent_mood.py` already propagate draft `story_world` groups. `src/cine_forge/api/artifact_editing.py` plus the UI artifact hook pattern already support manual JSON-backed edits. `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` already has motif-friendly prompt rendering.
- **No new public API needed**: reuse existing artifact read/edit endpoints unless exploration during implementation proves a missing contract. If a new cross-layer contract becomes necessary, add the Pydantic schema first.
- **Large-file risks**: `ui/src/pages/SceneWorkspacePage.tsx` is 869 lines, `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` is 1206 lines, `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` is 658 lines, `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` is 628 lines, and `src/cine_forge/pipeline/scene_actions.py` is 517 lines. The plan should avoid piling new logic into these files; use extraction helpers/components where needed.
- **Decision context**: ADR-003 is the primary design driver here. No stronger competing ADR was found for Story World surfacing, so the story should follow the existing concern-group and artifact-editing patterns rather than inventing a new motif-specific architecture.

## Files to Modify

- `docs/stories/story-100-motif-tracking.md` — tighten scope, plan, and work log
- `src/cine_forge/schemas/concern_groups.py` — expand motif scope support
- `src/cine_forge/modules/creative_direction/story_world_v1/main.py` — NEW, Story World authoring module
- `src/cine_forge/modules/creative_direction/story_world_v1/module.yaml` — NEW, module manifest
- `configs/recipes/recipe-creative-direction.yaml` — add real `story_world` stage
- `src/cine_forge/pipeline/scene_actions.py` — remove Story World coming-soon placeholder handling
- `ui/src/pages/SceneWorkspacePage.tsx` — replace placeholder rendering with a real Story World surface, preferably via extraction
- `ui/src/components/StoryWorldPanel.tsx` or equivalent — NEW, focused Story World viewer/editor component
- `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` — ensure Story World motifs flow into prompt context
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — ensure Story World motifs flow into prompt context
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — ensure scene planning consumes the Story World motif context
- `src/cine_forge/artifacts/store.py` — fix numeric version ordering so manual edits become the API-visible latest artifact
- `tests/unit/test_concern_group_schemas.py` — motif scope regression coverage
- `tests/unit/test_story_world_module.py` or equivalent — NEW, focused module/stage tests
- `tests/unit/test_artifact_store.py` — manual-edit regression coverage for double-digit artifact versions
- `ui/src/lib/hooks/artifacts.ts` — invalidate active artifact queries after Story World edits
- `tests/unit/test_readiness.py` and/or targeted UI/API tests as needed for the chosen seam

## Redundancy / Removal Targets

- Story World placeholder messaging in `SceneWorkspacePage.tsx`
- The `story_world` coming-soon soft block in `src/cine_forge/pipeline/scene_actions.py`
- Any motif-specific one-off edit path that duplicates the existing artifact-editing API
- Any prompt-context duplication discovered once Story World becomes the canonical source of motif annotations

## Notes

The story is now intentionally framed as a shipped first slice instead of an open-ended "motif dashboard" project. The key repo-specific finding is that motifs are already partially modeled but not yet owned by a real module/surface. That makes a direct Story World shipment much higher leverage than inventing analytics or a second motif-specific persistence layer.

## Plan

### Exploration Notes

**Files that will change:**
- `src/cine_forge/schemas/concern_groups.py` — `MotifAnnotation.scope` is currently narrower than the story promises.
- `src/cine_forge/modules/creative_direction/story_world_v1/main.py` and `module.yaml` — new module needed; directory is currently missing.
- `configs/recipes/recipe-creative-direction.yaml` — currently stops at `sound_and_music`; Story World stage is absent.
- `src/cine_forge/pipeline/scene_actions.py` — currently treats Story World as a coming-soon placeholder.
- `ui/src/pages/SceneWorkspacePage.tsx` — currently renders Story World as placeholder-only.
- `ui/src/components/StoryWorldPanel.tsx` or equivalent — extracted viewer/editor to avoid growing `SceneWorkspacePage.tsx`.
- `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py`, `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py`, and possibly `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — downstream prompt context plumbing.
- Focused test files for schema/module/UI seam coverage.

**Files at risk of breaking:**
- Recipe execution and stage readiness around `story_world`
- Any UI state assumptions in Scene Workspace that still expect placeholder concern groups
- Creative-direction prompt formatting if Story World context is injected inconsistently
- Existing propagated draft acceptance flows if the Story World artifact type diverges from current artifact-editing expectations

**ADRs / decision docs consulted:**
- `docs/decisions/adr-003-film-elements/adr.md`
- `docs/ideal.md`
- `docs/spec.md`
- `docs/methodology/state.yaml`

**Patterns to follow:**
- Creative-direction module structure in `look_and_feel_v1` and `sound_and_music_v1`
- Generic artifact-editing flow already used by existing artifact viewers/editors
- Concern-group rendering pattern in Scene Workspace, but with extraction instead of adding more page-level branching

**Potential redundant code / cleanup targets:**
- Story World placeholder UI copy and pipeline placeholder exemptions
- Any duplicated motif formatting code that can collapse onto Story World as the single source of truth

**Surprises / risks:**
- Story 100 originally promised a broader dashboard than the repo can honestly ship in one coherent slice.
- The downstream consumers already know about motif-like lists, which lowers risk for prompt-context wiring.
- Large-file pressure is real; this story should extract UI/components rather than deepen existing oversized files.

### Eval / Success Gate

- **Initial eval for this story**: focused unit coverage plus representative artifact inspection. There is no motif-specific promptfoo harness yet, so the first correctness gate is: can the recipe produce a valid `story_world` artifact, can the UI render/edit it, and do downstream prompt payloads include the motifs?
- **Baseline**: unshipped. `story_world_v1` is missing, recipe stage is missing, Scene Workspace is placeholder-only, and pipeline actions explicitly label Story World as coming soon.
- **Semantic validation**: inspect generated Story World artifacts on a representative project run and confirm motif content is meaningful enough to be usable. If outputs are structurally valid but semantically thin, record that as an AI-quality gap and classify it during validation rather than hiding behind schema success.
- **Promptfoo follow-up**: if this story exposes clear semantic instability, create a dedicated eval story instead of forcing a large benchmark harness into this implementation slice.

### Implementation Order

1. **Schema-first tightening**
   - Update `MotifAnnotation.scope` to include `prop` and `scene`.
   - Adjust or add unit coverage in `tests/unit/test_concern_group_schemas.py`.
   - Done when motif annotations validate across all promised scopes without widening unrelated concern-group semantics.

2. **Ship Story World authoring**
   - Create `story_world_v1` using the existing creative-direction module pattern.
   - Add the stage to `configs/recipes/recipe-creative-direction.yaml`.
   - Ensure module inputs use current upstream artifacts instead of inventing a new lineage path.
   - Done when recipe execution produces a `story_world` artifact through the normal driver/API path.

3. **Replace placeholder product surface**
   - Remove Story World's placeholder treatment in `src/cine_forge/pipeline/scene_actions.py`.
   - Extract a focused Story World UI component instead of growing `ui/src/pages/SceneWorkspacePage.tsx`.
   - Render the latest Story World artifact in Scene Workspace and wire it to the generic artifact-editing flow for manual motif edits.
   - Done when Story World behaves like a real concern-group surface and manual edits persist through the existing artifact API.

4. **Thread motif context downstream**
   - Pass Story World motif annotations into `look_and_feel`, `sound_and_music`, and shot-planning prompt compilation where absent.
   - Keep changes narrow inside the large prompt-building files; prefer helper extraction if any touched method is already oversized.
   - Done when prompt payload inspection shows Story World motifs reaching the downstream modules in a stable, readable form.

5. **Verification and cleanup**
   - Run backend/unit/lint checks plus UI lint/type/build.
   - Browser-verify Scene Workspace in desktop and mobile on a representative project path, inspect console, and capture evidence.
   - Remove placeholder-only code paths made obsolete by the shipped Story World surface.
   - Done when all acceptance criteria are evidenced in tests, artifact inspection, and browser verification.

### Repo-Fit / Optimality Evidence

- ADR-003 already says motifs belong in Story World and should influence other concern groups; this story implements that missing ownership directly instead of building a parallel dashboard concept first.
- The repo already has `StoryWorld` schema support, intent propagation, and motif-friendly prompt rendering, so a direct `story_world_v1` shipment reuses existing substrate rather than introducing new abstractions.
- Reusing the generic artifact-editing API is better here than a motif-specific persistence path because it keeps Story World aligned with the rest of the artifact system and avoids duplicate edit/write logic.
- Rejecting deterministic motif extraction is repo-fit: there is no evidence the project needs heuristics before it even has a first-class Story World artifact.

### Structural Health Check

- `src/cine_forge/schemas/concern_groups.py` is 474 lines. Safe to touch, but keep the schema delta narrow.
- `src/cine_forge/pipeline/scene_actions.py` is 517 lines. Avoid adding more branching than necessary; delete placeholder logic instead of layering on more conditions.
- `ui/src/pages/SceneWorkspacePage.tsx` is 869 lines. Treat it as oversized; extract Story World rendering into a focused component before adding significant logic.
- `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` is 658 lines and `sound_and_music_v1/main.py` is 628 lines. Prefer helper-level changes or narrow prompt-context seams.
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` is 1206 lines. Do not deepen large inline prompt builders unless inspection proves the context seam is already isolated.
- No new event type is expected. No new public API is expected. If a new cross-layer contract appears during implementation, add the schema first.

### UI Verification Plan

- Start the normal app/backend flow and reach Scene Workspace through the existing project pipeline, not a hand-seeded impossible state.
- Desktop path: open the project's Scene Workspace, load the Story World concern group, inspect motif rendering, perform a manual motif edit, save, and confirm the latest artifact reflects the change.
- Mobile path: resize to a mobile viewport, reopen the same Story World surface, confirm the panel remains usable and the edit path still works.
- Inspect browser console and network behavior during both passes. If browser tooling is blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

### Human-Approval / Scope Notes

- This plan intentionally tightens the story from "motif dashboard" to "shipped Story World slice." That is a small, necessary scope correction rather than a deferral.
- A separate dashboard or coverage matrix should only become a follow-up after Story World is a real artifact and surface.
- If implementation confirms that downstream prompt consumers already receive sufficient motif context from the Story World artifact without extra code, reduce that subtask instead of forcing redundant plumbing.

## Work Log

20260227 — Story created per ADR-003 propagation. Motifs elevated from "just consistency" to explicit thematic tracking per ADR-003 Discussion #3.

20260409-1748 — Explored Story 100 against current substrate and tightened it into a buildable first slice. Evidence: `story_world` schema fields and intent propagation already exist, but `src/cine_forge/modules/creative_direction/story_world_v1/` is missing, `configs/recipes/recipe-creative-direction.yaml` has no Story World stage, `src/cine_forge/pipeline/scene_actions.py` marks Story World as a coming-soon placeholder, and `ui/src/pages/SceneWorkspacePage.tsx` still renders a placeholder card. Also confirmed structural risks: `SceneWorkspacePage.tsx` is 869 lines, `shot_plan_v1/main.py` is 1206, `look_and_feel_v1/main.py` is 658, and `sound_and_music_v1/main.py` is 628, so the plan now requires extraction-oriented changes instead of adding more page-level branching. Next step: user approval on this tightened plan, then promote to `Pending`/`In Progress` on implementation start.

20260409-1814 — Promoted story from Draft to Pending after substrate verification. Evidence: Story World schema exists, intent propagation already creates draft `story_world` artifacts, and the remaining gap is shipped ownership rather than missing foundations. Next step: move to In Progress and implement the first shipped slice.

20260409-1818 — Moved story to In Progress and corrected methodology state so generated planning surfaces reflect the real active lane. Evidence: `pnpm methodology:compile` initially failed because `docs/methodology/state.yaml` still listed Story 100 under the Draft lane; state and story metadata were updated together before implementation continued. Next step: land schema/module/recipe/UI changes and rerun compile plus full validation.

20260409-1912 — Shipped the Story World first slice end to end. Result: `story_world_v1` now exists and is wired into `recipe-creative-direction.yaml`; Scene Workspace renders a real `StoryWorldPanel` instead of the placeholder path; Story World preflight moved from soft-block to warning-only; downstream `look_and_feel`, `sound_and_music`, and `shot_plan_v1` prompt assembly now receive Story World context. Evidence: full unit suite `make test-unit PYTHON=python` (`684 passed, 157 deselected`), `python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (6 pre-existing warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check`. Next step: record the verification-only regressions found during browser smoke, then hand off for `/validate` or `/mark-story-done`.

20260409-1944 — Browser/runtime verification uncovered and fixed the actual manual-edit seam blockers. First bug: `useEditArtifact()` invalidated artifact groups but not the active artifact query, so Story World writes succeeded on disk but the panel stayed stale until refresh. Second bug: `ArtifactStore.list_versions()` sorted lexicographically, so `v9` incorrectly outranked `v10+`; that made `/api/projects/.../artifacts` report stale latest versions and blocked the UI from resolving the real newest Story World artifact after edits. Fixes landed in `ui/src/lib/hooks/artifacts.ts`, `src/cine_forge/artifacts/store.py`, and `tests/unit/test_artifact_store.py`. Evidence: disposable local smoke copy `story-world-smoke` created immutable Story World versions `v11` (add motif), `v12` (edit motif), and `v13` (remove motif), with the panel refreshing in-place after each write. Representative browser proof rerun on the real project route `/the-mariner-50/scenes/scene_001?tab=story_world` via a temporary Playwright spec after the fixes: desktop `1440x1200` and mobile `390x844` both passed with the Story World summary visible, zero console warnings/errors, and zero failed network requests. Screenshots saved to `/tmp/cineforge-storyworld-verify/story-world-desktop-mainrepo-final.png` and `/tmp/cineforge-storyworld-verify/story-world-mobile-mainrepo-final.png`. Residual note: the disposable copy used for destructive edit smoke emitted expected 404s for historic run IDs copied without the original `output/runs/` tree, so that copy was used only for mutation proof, not clean-console evidence. Next step: optional `/validate`, then `/mark-story-done` if no additional review findings emerge.

20260409-2108 — Validation pass completed against the implemented Story World slice. Evidence rerun in this pass only: `make test-unit PYTHON=python` passed (`684 passed, 157 deselected`), `python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` passed with only pre-existing warnings, `cd ui && npx tsc -b` passed, `pnpm --dir ui run build` passed, `pnpm methodology:check` passed, and a fresh Playwright verification on `/the-mariner-50/scenes/scene_001?tab=story_world` passed at desktop (`1440x1200`) and mobile (`390x844`) with zero console warnings/errors and zero failed requests. Operational note: this worktree does not have a local `.venv`, so the equivalent working interpreter commands were used instead of the skill's literal `.venv/bin/python` path. Next step: `/mark-story-done`.

20260410-0932 — Story closed after validating the shipped Story World slice against the actual repo surface. Result: Story 100 now ends at the right boundary: real `story_world` module + recipe stage + Scene Workspace surface + downstream motif propagation, with the two validation-discovered edit-path bugs fixed in the same slice instead of deferred. Evidence: workflow gates now reflect completed build and validation, the story metadata now cites ADR-003 consistently with the body, and generated planning surfaces were refreshed after the status flip. Next step: `/check-in-diff`.
