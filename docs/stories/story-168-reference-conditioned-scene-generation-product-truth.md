---
id: "168"
title: "Reference-Conditioned Scene Generation Product Truth"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:4.10.7"
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:7.2"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "029"
  - "056"
  - "119"
  - "141"
  - "164"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "render"
  - "references"
  - "product-truth"
  - "feature-completeness"
legacy_system: ""
---

# Story 168 — Reference-Conditioned Scene Generation Product Truth

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:4.10.7, spec:5.3, spec:5.5, spec:6.1, spec:7.1, spec:7.2
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 029, Story 056, Story 119, Story 141, Story 164

## Goal

Make the normal Scene Workspace render path prove that operator-selected references
actually matter. CineForge already has origin-agnostic asset injection, canonical
design-study winners, transparent creative-brief compilation, and a representative
scene-render route, but the product is still not feature complete if a user cannot
attach or select references through the surfaced UI/API path and then see which
references became provider inputs, which were downgraded to prompt-only context,
and why. This story closes that product-truth gap on the shipped scene-generation
route instead of leaving reference conditioning as a backend-only assumption.

## Acceptance Criteria

- [x] A fresh representative project can use the normal surfaced reference flows
  (project references, injected scene/entity assets, and canonical design-study
  selections where available) and then reach a real scene-scoped `render_prompt`
  and `generated_video` artifact from the Scene Workspace `Render` tab without
  hand-seeded impossible state. The resulting artifacts record the actual
  resolved inputs used for that render. Verified on fresh project
  `story-168-reference-render-verify-patched-102817` through surfaced API asset
  flows plus Scene Workspace render, culminating in `run-880869ab`.
- [x] The render route stays honest about provider limits and selection policy:
  when engine-pack caps, unsupported media, or duration rules prevent full
  reference usage, the surfaced operator path and artifact viewers make clear
  which inputs were used as `input_reference` / `reference_image`, which were
  downgraded to `prompt_context`, which were marked `unsupported`, and why,
  without requiring raw JSON inspection. The final render surfaced the scene
  reference as `Input Reference`, kept project `mood_board.png` and
  `style_reference.png` as `Prompt Context`, and disclosed both demotions as
  image-slot cap fallout instead of hiding them in raw JSON.
- [x] Headless behavior matches the UI path: the same representative
  reference-conditioned scene route remains reproducible through the normal
  API/driver pipeline, and focused integration coverage proves canonical
  design-study images, injected asset lock priority, and project creative-brief
  references survive into the render artifacts. The verification project was
  created and driven through `/api/projects/new`, `/inputs/upload`, upstream
  ingest/world-building runs, and normal asset APIs before UI inspection.
- [x] Focused regression coverage exists for reference priority and disclosure
  decisions, including engine-pack image caps, lock strength, and the canonical
  `visual_reference_image` handoff from design-study selection. Targeted module,
  integration, and video-client tests now cover those seams with raster-backed
  canonical refs and representative project taste assets.
- [x] Browser verification covers the changed reference-conditioned render flow
  in both desktop and mobile views on representative project state with clean
  console output. Desktop/mobile Scene Workspace and Artifact Detail checks
  passed with screenshots and `browser_console_messages(level="error",
  all=false) == 0`.

## Out of Scope

- New video-generation providers, new engine-pack benchmarking, or model-default
  selection work beyond the narrow pack behavior already required by the shipped
  render route. If pack assumptions must change, record that explicitly rather
  than turning this into a benchmarking story.
- Redesigning the Design Study, Reference Library, or Intent pages beyond the
  smallest changes needed to make the render route honest.
- Broad final-output reference UX. Project-level assembly only belongs in scope
  if representative verification uncovers a tightly coupled blocker after the
  scene-render path succeeds.
- Pure output-quality tuning unrelated to whether references are carried
  through, selected correctly, and disclosed honestly.

## Approach Evaluation

- **Simplification baseline**: The repo already proves most backend capability.
  `tests/integration/test_render_adapter_integration.py` persists
  `creative_brief_preview` plus `resolved_inputs`, and the render viewers
  already parse those fields. The missing question is product truth on the
  representative surfaced route, not whether an LLM can technically compile a
  prompt with references. The first task should therefore replay the real
  reference-conditioned path before inventing more substrate.
- **AI-only**: Wrong fit for the main gap. A single LLM call can help compile a
  reference-aware prompt, but it cannot by itself guarantee canonical reference
  selection, lock-aware priority, engine-pack cap handling, or surfaced
  disclosure that remains reproducible across runs.
- **Hybrid**: Likely repo-fit. Keep the existing AI prompt compiler, but use
  deterministic code for reference collection, priority, capability shaping, and
  omission disclosure. If a prompt section needs clearer reference language,
  make that a small companion change rather than a new architecture.
- **Pure code**: Plausible only if the route already works and the remaining gap
  is disclosure or selection policy. If the only missing truth is in how the UI
  surfaces already-persisted data, the story should stay that small.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced next steps
  instead of hidden backend magic. ADR-003 requires prompts to stay read-only
  compiled artifacts and real-world assets to remain first-class, origin-agnostic
  inputs. Story 029 explicitly deferred render wiring, Story 056 explicitly
  deferred design-study consumption by render, Story 119 writes the canonical
  `visual_reference_image` back to bible state, Story 141 compiles project taste
  references into the creative brief, and Story 164 proved the scene-render path
  can succeed without requiring optional references.
- **Existing patterns to reuse**: `render_adapter_v1` `resolved_inputs`,
  `RenderInputUsageCard`, `injected_assets.py` reference collection,
  `tests/render_fixtures.py`, Story 164's representative route validation, and
  the existing Render / Artifact Detail viewers. Do not invent a parallel
  reference-debug path if the current render artifacts already carry the right
  truth.
- **Eval**: No direct promptfoo or registry-backed eval currently measures
  reference-conditioned render truth. The discriminating evidence is a
  representative surfaced render walkthrough plus deterministic assertions on
  prompt/video artifact `resolved_inputs` and omission notes under engine-pack
  limits. If implementation changes AI behavior beyond those deterministic seams,
  record whether a new eval follow-up is warranted.

## Tasks

- [x] (in progress) Walk the normal reference-conditioned route on a fresh representative
  project and capture the exact blocker or disclosure gap before changing code.
  Use surfaced reference flows where possible instead of hand-seeded impossible
  substrate. Fresh surfaced runs captured two real blockers before the final
  success path: OpenAI rejected mismatched opening-frame dimensions on
  `run-5b36d21b`, and the adapter hard-failed on omitted
  `character_bible_state` prompt sections on `run-9f6adeb9`.
- [x] Fix the smallest end-to-end seam that prevents reference-conditioned scene
  generation from being representative and inspectable. Prefer existing render,
  injected-asset, and viewer seams over new infrastructure. Landed surgical
  fixes in the existing owners: OpenAI input-reference normalization in
  `src/cine_forge/ai/video.py`, fallback prompt-section synthesis and stable
  reference priority in `render_adapter_v1`, and existing render viewers for UI
  disclosure.
- [x] Keep reference truth honest on the shipped route: selected references,
  lock strength, engine-pack image caps, and demotions to `prompt_context` or
  `unsupported` should be visible in Scene Workspace and Artifact Detail and
  persisted in the render artifacts themselves. Scene Workspace, prompt detail,
  and generated-video detail now surface the same disclosure truth and reuse
  `prompt_ref` / creative-brief viewer seams instead of adding a new debug path.
- [x] Add focused regression coverage for canonical design-study selection,
  injected asset priority, project creative-brief reference carry-through, and
  engine-pack reference-image caps. Added focused unit/integration coverage plus
  video-client resizing tests and upgraded representative fixtures to raster
  canonical refs plus real project mood/style assets.
- [x] If implementation changes provider or engine-pack assumptions, run
  `scripts/discover-models.py --check-new` and record the result before
  finalizing the change. Not required; this story changed input shaping and
  disclosure on existing packs, not model or engine-pack availability
  assumptions.
- [x] Run `make check-size` and keep any new logic out of the already-oversized
  files unless the change is truly surgical or extracted into a focused helper.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up. Reused `CreativeBriefPreviewCard` and `prompt_ref` instead of creating a second render-reference truth surface; no extra cleanup path emerged beyond the existing pre-story `ingest_and_world_building` methodology warning.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`. Not required; no agent tooling or project instruction files changed.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`. Already completed earlier in the story when Story 168 moved to `In Progress` and methodology state was refreshed; no additional metadata change was needed after implementation.
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`. Not required; this story changed representative fixtures/tests and shipped product surfaces, not eval or golden assets.
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker. Verified on representative project state with desktop/mobile screenshots and zero final console errors; see `docs/ui-scout/2026-04-13-story-168-reference-conditioned-render-local.md`.
- [x] Search all docs and update any related to what we touched. Updated this story with final evidence and added a dedicated UI scout note for the representative local walkthrough.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No destructive data-path changes; the story only improves reference shaping/disclosure and leaves capture-first flows intact.
  - [x] **T1 — AI-Coded:** New logic stays in existing owners with schema-backed artifact truth, explicit tests, and a verbose work log.
  - [x] **T2 — Architect for 100x:** Reused current render/prompt provenance seams instead of inventing a new debug subsystem AI agents would later delete.
  - [x] **T3 — Fewer Files:** Touched oversized owners surgically, added one focused scout doc, and kept contracts in existing schema/viewer surfaces.
  - [x] **T4 — Verbose Artifacts:** Story log, scout note, render artifacts, and screenshots now preserve the representative blocker/fix trail.
  - [x] **T5 — Ideal vs Today:** The surfaced route now gets closer to the ideal promise that operator references actually matter and that any provider-limit compromise is honest.

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

- **Owning class/module**: `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  is the current owner for resolved render inputs and engine-pack shaping, while
  `src/cine_forge/services/injected_assets.py` owns reference collection and
  canonical design-study lookups. UI truth should stay in focused render
  viewers/panels rather than expanding `SceneWorkspacePage.tsx` into another
  policy layer.
- **Data contracts**: The current cross-layer contracts already exist in
  `src/cine_forge/schemas/render.py`: `RenderResolvedInput`,
  `CompiledRenderPrompt`, and `GeneratedVideoArtifact`. The story may also touch
  `VisualCreativeBrief` and injected-asset manifest payloads if current fields do
  not expose enough provenance. If new omission or selection fields cross the
  backend/UI boundary, add them schema-first instead of smuggling them through
  viewer-only logic.
- **File sizes**: `render_adapter_v1/main.py` is `1554` lines,
  `render_adapter_v1/prompting.py` is `306`, `services/injected_assets.py` is
  `811`, `schemas/render.py` is `247`, `GeneratedVideoPanel.tsx` is `374`,
  `RenderPromptViewer.tsx` is `355`, `GeneratedVideoViewer.tsx` is `182`,
  `SceneWorkspacePage.tsx` is `951`, `ArtifactDetail.tsx` is `647`,
  `tests/unit/test_render_adapter_module.py` is `501`,
  `tests/integration/test_render_adapter_integration.py` is `351`, and
  `tests/render_fixtures.py` is `471`. The main risk files are
  `render_adapter_v1/main.py`, `services/injected_assets.py`,
  `SceneWorkspacePage.tsx`, and `ArtifactDetail.tsx`; if the fix is not
  surgical, extract a focused helper rather than widening those files further.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`
  (`spec:4.10.7`, `spec:5.3`, `spec:5.5`, `spec:6.1`, `spec:7.1`, `spec:7.2`),
  `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003,
  Story 029, Story 056, Story 119, Story 141, Story 148, and Story 164. No
  newer ADR was found that narrows render-reference ownership more specifically.

## Files to Modify

- `docs/stories/story-168-reference-conditioned-scene-generation-product-truth.md` -
  keep scope, evidence, and work log current
- `tests/storyboard_fixtures.py` -
  replace the current SVG-only `visual_reference_image` seeds with uploadable
  raster fixtures for the render-truth path so canonical entity references can
  honestly reach provider-input status when the engine pack allows it (`471`)
- `tests/render_fixtures.py` -
  seed representative render cases that include canonical entity visual refs
  plus project taste references with `mood_board` / `style_reference` purposes,
  not only generic `reference_image` uploads (`471`)
- `tests/unit/test_render_adapter_module.py` -
  pin reference priority, project creative-brief carry-through, engine-pack cap
  demotions, and raster design-study-style inputs (`501`)
- `tests/integration/test_render_adapter_integration.py` -
  prove the representative reference-conditioned render path end to end with
  persisted `creative_brief_preview` and `resolved_inputs` truth (`351`)
- `ui/src/components/RenderPromptViewer.tsx` -
  surface the already-persisted `creative_brief_preview` and active project
  taste references instead of hiding that truth in raw JSON (`355`)
- `ui/src/components/GeneratedVideoViewer.tsx` -
  expose prompt provenance on the resulting render path, likely by reusing the
  existing `prompt_ref` rather than duplicating prompt truth into a second
  artifact unless the walkthrough proves that is insufficient (`182`)
- `ui/src/components/GeneratedVideoPanel.tsx` -
  correct the Render-tab copy so it promises honest reference handling rather
  than implying every approved reference always becomes a provider input (`374`)
- `ui/src/components/intent/CreativeBriefPreviewCard.tsx` -
  reuse or lightly generalize the existing brief card instead of inventing a
  second render-only creative-brief surface (`89`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` -
  only if the new deterministic coverage or representative walkthrough proves a
  real selection-policy or disclosure bug beyond fixture/viewer truth (`1554`)

## Redundancy / Removal Targets

- Any render-surface copy that implies "approved references" are always used
  without caveat once engine-pack limits or unsupported inputs force demotion.
- Any duplicated reference-priority heuristic split across the render adapter
  and injected-asset service once the representative route is made truthful.
- Hand-seeded test assumptions that only prove reference support through backend
  fixture surgery once the same behavior is covered on a representative route.

## Notes

- Story 029 and Story 056 both intentionally stopped short of proving render
  consumption of references. That deferral is the point of this story, not an
  excuse to assume the shipped route already satisfies `spec:7.2`.
- Story 164 deliberately proved the render route can succeed without optional
  direction or reference substrate. This story is the next non-terminal owner:
  prove that references matter when they are present.
- The existing render integration tests already suggest the backend may be close
  to correct. This story can close on representative proof plus small disclosure
  fixes if the surfaced route already behaves honestly. It should not invent a
  larger subsystem just because the campaign needs a new owner.
- Final-output verification belongs here only as fallout if representative
  reference-conditioned scene generation uncovers a coupled downstream blocker.

## Plan

### Eval / Baseline Gate

- This is product-truth, provenance, and representative-fixture work over
  already-landed substrate, not a new generation-capability or model-selection
  story.
- Current repo evidence before implementation:
  - `make check-size` confirms the likely backend owners are already oversized:
    `render_adapter_v1/main.py` (`1554`), `services/injected_assets.py` (`811`),
    `SceneWorkspacePage.tsx` (`951`), and `ArtifactDetail.tsx` (`647`). The plan
    should therefore prefer fixture/test/viewer work over widening those files.
  - Targeted render baseline is green:
    `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py -q`
    currently passes `7/7`.
  - The render backend already persists the key truth surfaces:
    `render_prompt` stores both `creative_brief_preview` and `resolved_inputs`,
    and `generated_video` stores `resolved_inputs` plus `prompt_ref`.
  - A one-off local probe with representative `mood_board` /
    `style_reference` project refs showed that those refs already land in
    `creative_brief_preview.active_project_references` for both
    `openai_sora2` and `google_veo31`; the main surfaced gap is that
    `RenderPromptViewer.tsx` does not display that persisted field today.
  - The same probe exposed a representative-fixture gap: the seeded
    `visual_reference_image` files in `tests/storyboard_fixtures.py` are SVGs,
    so canonical entity references can only ever be `prompt_context` in current
    tests because the render adapter only uploads raster images (`jpeg/png/webp`)
    as provider inputs. That means current coverage does **not** honestly prove
    design-study-style entity references on the provider-input path.
- Success measures:
  - deterministic coverage proves three seams explicitly:
    1. canonical entity visual references reach provider-input status when the
       underlying file is uploadable and engine-pack capacity exists
    2. project `mood_board` / `style_reference` refs survive into
       `creative_brief_preview`
    3. engine-pack caps and unsupported media demotions remain visible in
       `resolved_inputs` and completeness notes
  - a representative surfaced route proves the same truth in Scene Workspace and
    Artifact Detail without raw JSON inspection
  - no new registry-backed eval is required unless implementation changes AI
    semantics rather than truth surfacing / deterministic shaping

### Approach Choice

- **Verification-only close**: no longer sufficient. Exploration found two real
  gaps: the current render viewers hide `creative_brief_preview`, and the
  representative fixture for canonical entity refs is non-representative because
  it seeds non-uploadable SVGs.
- **Small hybrid fix**: repo-fit answer. Keep the existing AI prompt compiler
  and deterministic request-shaping path, upgrade the representative fixtures,
  add the missing deterministic assertions, and surface the already-persisted
  creative-brief truth in the render viewers.
- **Backend policy rewrite**: reject unless the new deterministic tests or the
  surfaced walkthrough proves a real bug in selection ordering, lock semantics,
  or omission notes. Current evidence says the adapter already carries most of
  the right truth.
- **New reference-debug subsystem**: reject. The repo already has the right
  seams (`creative_brief_preview`, `resolved_inputs`, completeness notes, and
  `prompt_ref`). Reuse them instead of inventing a parallel transparency path.

### Repo-Fit / Optimality Evidence

- ADR-002 says surfaced generation actions need honest explanation rather than
  hidden backend state.
- ADR-003 says real-world assets are first-class inputs and prompts are a
  read-only window into upstream decisions.
- Story 119 already established the canonical `visual_reference_image` handoff,
  Story 141 already established the project creative-brief seam, and Story 164
  already established the representative scene-render route. The smallest honest
  next move is to connect those truths end to end rather than invent a separate
  "reference debug" workflow.
- Existing repo patterns already support the smallest path:
  - `ui/src/components/intent/CreativeBriefPreviewCard.tsx` is the established
    operator-facing surface for `creative_brief_preview` and should be reused in
    render viewers.
  - `RenderInputUsageCard` plus completeness notes already expose `used_as`,
    lock status, and demotion reasons, so disclosure work should tighten those
    surfaces rather than replacing them.
  - `GeneratedVideoArtifact.prompt_ref` already exists, so the generated-video
    route can point back to prompt truth without automatically forcing a schema
    duplication into `generated_video`.
- Alternatives rejected:
  - Duplicating `creative_brief_preview` into `generated_video` immediately:
    possible, but not justified before testing whether `prompt_ref` plus a
    clearer prompt viewer already solves the operator truth gap.
  - Reworking `InjectedAssetService` reference collection now: exploration did
    not show duplicate collection bugs; the more urgent gap is representative
    proof and surfaced disclosure.

### Structural Health Check

- `render_adapter_v1/main.py` (`1554`) and `services/injected_assets.py` (`811`)
  are already oversized. Do not widen them casually.
- `SceneWorkspacePage.tsx` (`951`) and `ArtifactDetail.tsx` (`647`) should stay
  thin routing surfaces. Prefer focused viewer/panel changes instead of page
  growth.
- `tests/unit/test_render_adapter_module.py` (`501`) is slightly oversized but
  still the correct local owner for deterministic render-adapter behavior until
  the file itself becomes the next pain point. Add tightly scoped cases only.
- No new cross-layer schema is required for the current likely plan because
  `creative_brief_preview`, `resolved_inputs`, and `prompt_ref` already exist.
  If the generated-video detail view truly needs self-contained creative-brief
  data after the walkthrough, add that schema-first as a deliberate branch, not
  as a casual inline expansion.
- If the representative gap turns out to be a selection-policy bug rather than a
  viewer/fixture bug, add or extract one focused helper close to the owning
  module instead of spreading reference logic across UI and service layers.

### Scope Adjustment Folded In

- Small inline scope expansion approved by exploration: the story now includes
  upgrading render fixtures from SVG-only entity visual refs to raster refs and
  seeding project taste references with the actual `mood_board` /
  `style_reference` purposes. Without that, the tests cannot honestly prove the
  shipped route against `spec:7.2`.

### Implementation Order

1. Put the story `In Progress`, then upgrade the representative fixtures first.
   Files:
   `tests/storyboard_fixtures.py`, `tests/render_fixtures.py`
   Work:
   seed uploadable raster `visual_reference_image` files for canonical entity
   refs and add explicit project `mood_board` / `style_reference` assets to the
   render fixture.
   Done looks like:
   the fixture can exercise both provider-input and prompt-only demotion paths
   honestly instead of proving entity refs only through SVG fallbacks.
2. Add deterministic regression coverage before changing surfaced UI.
   Files:
   `tests/unit/test_render_adapter_module.py`,
   `tests/integration/test_render_adapter_integration.py`
   Work:
   add one unit path for `openai_sora2` prompt-only demotions, one unit/integration
   path for `google_veo31` capacity behavior, and explicit assertions that
   `creative_brief_preview.active_project_references` contains the project taste
   refs while canonical entity refs appear in `resolved_inputs`.
   Impact / break risk:
   these tests will fail if reference priority, lock handling, or creative-brief
   compilation drifts.
   Done looks like:
   reference-conditioned truth is pinned in deterministic tests, not implied by
   broad happy-path coverage.
3. Surface the already-persisted creative-brief truth in the render UI and fix
   any misleading copy.
   Files:
   `ui/src/components/RenderPromptViewer.tsx`,
   `ui/src/components/GeneratedVideoViewer.tsx`,
   `ui/src/components/GeneratedVideoPanel.tsx`,
   `ui/src/components/intent/CreativeBriefPreviewCard.tsx`
   Work:
   reuse the existing creative-brief card in the prompt viewer; expose prompt
   provenance from the generated-video route via existing `prompt_ref`; correct
   Render-tab copy so it says references may become provider inputs, prompt-only
   context, or unsupported items depending on engine-pack limits.
   Impact / break risk:
   low backend risk, moderate UI polish risk if the reuse feels too Intent-page
   specific and needs a small generalization.
   Done looks like:
   an operator can inspect project taste refs, canonical entity refs, and
   demotion reasons from the normal render surfaces without opening raw JSON.
4. Only if tests or the surfaced walkthrough expose a real adapter bug, patch
   the smallest backend seam.
   Files:
   `src/cine_forge/modules/generation/render_adapter_v1/main.py` only if needed
   Work:
   tighten selection/disclosure behavior, preferably via one focused helper or
   small note/label fix rather than a broad rewrite.
   Human-approval blocker:
   if this branch requires a new persisted field on `generated_video`, call that
   out before widening the schema.
   Done looks like:
   the backend truth matches the newly representative tests instead of the UI
   papering over a real mismatch.
5. Verify headless and browser paths on representative state.
   Headless:
   rerun the targeted render tests plus any new focused cases with the shared
   repo venv path above.
   UI:
   use browser tools on the normal Scene Workspace `Render` tab for a fresh
   project route, then inspect the matching `render_prompt` and
   `generated_video` Artifact Detail pages on both desktop and mobile.
   Browser plan:
   use Playwright/MCP first; if tooling is blocked, follow
   `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the
   work log.
6. Run close-out checks for touched scope.
   Backend:
   `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
   and
   `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
   UI:
   `pnpm --dir ui run lint`,
   `cd ui && npx tsc -b`,
   `pnpm --dir ui run build`
   Methodology:
   rerun `pnpm methodology:compile` only if story metadata changes again.

### Impact / Risk Notes

- The main risk is falsely implying a reference was honored when it was only
  included as prompt context, or vice versa.
- A secondary risk is adding yet another reference-priority implementation in a
  second place. This story should converge on one inspectable source of truth.
- If the smallest honest fix is only a disclosure fix, do not pad the story by
  rewriting working backend logic.
- The newly discovered representative-fixture risk is concrete: if SVG
  `visual_reference_image` seeds remain in the render fixture, the tests will
  continue proving a non-representative prompt-only path for canonical entity
  refs and may hide real provider-input regressions.
- The other concrete risk is over-fixing generated-video detail by duplicating
  prompt truth into a second artifact when a prompt link or reused prompt viewer
  would have solved the operator problem more simply.

## Work Log

20260413-0852 — story-created: packaged the next `scene-generation-completion`
follow-up after triage confirmed Stories 164-167 closed route existence and
trust but still left `spec:7.2` under-owned on the shipped scene-generation
path. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`,
`docs/build-map.md`, ADR-002, ADR-003, Stories 029/056/119/141/148/164, current
render schemas/viewers/tests, and the active campaign notes. Conclusion: this
is a new `Pending` story rather than a reopen because the subsystem is
continuous but the success surface changed from "render route exists" to
"reference-conditioned render route is representative and honest." Next step:
`pnpm methodology:compile` so the active campaign has a live owner.

20260413-1006 — exploration-and-plan: finished the `/build-story` exploration
and planning pass without implementation writes. Evidence: re-read
`docs/ideal.md`, the cited spec refs, ADR-002, ADR-003, Stories
029/056/119/141/164, the active `scene-generation-completion` lane in
`docs/methodology/state.yaml`, and the current render/reference call path in
`render_adapter_v1`, `services/creative_brief.py`, `GeneratedVideoPanel`,
`RenderPromptViewer`, `GeneratedVideoViewer`, and the render fixtures/tests.
Ran `make check-size` and confirmed the relevant backend/page owners are already
oversized. Ran the current targeted render baseline with the shared repo venv:
`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py -q`
and it passed `7/7`. A focused local probe with `mood_board` /
`style_reference` project refs showed that the backend already persists project
taste references in `creative_brief_preview.active_project_references`, but the
render viewers do not surface that field today. The same probe exposed the
current representative-fixture gap: seeded entity `visual_reference_image`
files are SVGs, so canonical entity refs can only prove prompt-only carry-through
in tests because the adapter only uploads raster images. Files most likely to
change: `tests/storyboard_fixtures.py`, `tests/render_fixtures.py`,
`tests/unit/test_render_adapter_module.py`,
`tests/integration/test_render_adapter_integration.py`,
`ui/src/components/RenderPromptViewer.tsx`,
`ui/src/components/GeneratedVideoViewer.tsx`,
`ui/src/components/GeneratedVideoPanel.tsx`, and possibly
`ui/src/components/intent/CreativeBriefPreviewCard.tsx`. Redundancy target:
avoid inventing a second render-reference debug surface or duplicating prompt
truth into `generated_video` unless the walkthrough proves the existing
`prompt_ref` is insufficient. Next step: human approval on this plan before
implementation.

20260413-1014 — implementation-started: moved Story 168 to `In Progress` after
user approval so methodology truth matches execution. Next step: compile the
planning surfaces, then land the representative fixture and regression coverage
before touching the render UI.

20260413-1108 — representative-fixtures-and-surfaced-truth: upgraded the
reference-conditioned fixture substrate so the story could prove provider-input
conditioning honestly instead of only prompt-only carry-through. Changed
`tests/storyboard_fixtures.py` to seed raster JPEG canonical entity refs, added
real project `mood_board` / `style_reference` assets in
`tests/render_fixtures.py`, expanded focused render/video tests, and reused the
existing render viewers by surfacing `creative_brief_preview` in
`RenderPromptViewer`, `prompt_ref` provenance in `GeneratedVideoViewer`, and
honest Render-tab copy in `GeneratedVideoPanel`. Evidence: targeted checks
passed for the touched UI stack earlier in the story (`pnpm --dir ui run lint`,
`cd ui && npx tsc -b`, `pnpm --dir ui run build`), and focused backend tests now
cover project taste refs, soft-lock priority, cap/demotion behavior, fallback
prompt sections, and OpenAI input-resize behavior. Operator impact: the normal
render route now has a surfaced explanation of which references mattered,
instead of hiding the truth in raw artifacts. Next step: drive a fresh
representative project through the normal API/driver path to find the first real
runtime seam.

20260413-1216 — representative-runtime-seams-closed: a fresh surfaced project
exposed two real blockers that tests alone did not prove away. First,
`run-5b36d21b` failed on OpenAI with `HTTP 400: Inpaint image must match the
requested width and height`, so `src/cine_forge/ai/video.py` now normalizes
opening-frame uploads to the requested render dimensions before multipart
submission. Second, `run-f53ba61f` and the fresh patched-project probe
`run-9f6adeb9` failed because the compiled prompt omitted required
`character_bible_state` context even though the upstream data existed, so
`render_adapter_v1/main.py` now synthesizes fallback prompt sections from the
already-available context blocks instead of hard-failing the surfaced route.
Evidence: added regression coverage in `tests/unit/test_video_client.py` and
`tests/unit/test_render_adapter_module.py`, plus integration coverage in
`tests/integration/test_render_adapter_integration.py`. Operator impact: the
reference-conditioned render path now survives real provider input validation
and prompt completeness drift instead of only working on idealized fixtures.
Next step: rerun the full representative route and verify the surfaced truth on
desktop and mobile.

20260413-1312 — representative-route-passed-and-documented: the fresh patched
project `story-168-reference-render-verify-patched-102817` completed
`mvp_ingest` (`run-1c44486f`), `world_building` (`run-0da9ab73`), and the
surfaced Scene Workspace render (`run-880869ab`) using real project, scene, and
entity reference assets. The resulting `render_prompt`, `generated_video`, and
`media_validation` artifacts landed at
`output/story-168-reference-render-verify-patched-102817/artifacts/.../v1.json`.
Desktop and mobile browser checks passed on the Render tab plus prompt/video
artifact detail pages, with screenshots captured and
`browser_console_messages(level="error", all=false)` returning `0` for the final
verification pass. Surfaced truth matched the artifact truth: the scene
reference became `Input Reference`, project `mood_board.png` and
`style_reference.png` stayed `Prompt Context` with explicit image-slot-cap
demotion notes, and the prompt/video detail pages exposed the compiled creative
brief, active project refs, fallback section note, and prompt provenance link.
Final checks also passed: focused render/video tests (`20 passed`), backend
minimum (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`:
`746 passed, 164 deselected, 1 pre-existing warning`), backend lint
(`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`),
and `make check-size`. Added the scout note at
`docs/ui-scout/2026-04-13-story-168-reference-conditioned-render-local.md`.
Operator impact: the shipped route now proves "my references mattered" on a real
project instead of asking the operator to trust backend-only plumbing. Next
step: independent acceptance via `/validate 168`.

20260413-1459 — validation-passed-close-now: reran the validation suite against
the current local delta instead of relying on build-time evidence. Fresh checks
passed: targeted Story 168 tests
(`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py -q`),
backend lint
(`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`),
backend minimum
(`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`:
`746 passed, 164 deselected, 1 pre-existing warning`),
UI lint (`pnpm --dir ui run lint`), UI types (`cd ui && npx tsc -b`), UI build
(`pnpm --dir ui run build`), and desktop/mobile browser verification on the
representative render and generated-video routes with zero console errors.
Validation also rechecked methodology alignment: `pnpm methodology:check`
initially failed because the generated graph lagged the latest story updates, so
the next step is to refresh the generated methodology surfaces and confirm the
check is green. Assessment: implementation is complete, the approach matches
ADR-002 / ADR-003 and the active `spec:6` / `spec:7` lane, and no remaining gap
belongs to this subsystem beyond close-out bookkeeping. Recommended next step:
close the story once the regenerated methodology views are confirmed clean.

20260413-1514 — completion-marked-done: closed Story 168 after confirming the
fresh validation pass, workflow gates, and story evidence all matched the
shipped slice. Completion evidence remained green from the latest reruns:
targeted Story 168 tests, backend lint, backend minimum, UI lint/types/build,
desktop/mobile browser verification on the representative project, and
`pnpm methodology:check` after refreshing generated planning surfaces. Updated
story status to `Done`, checked the close-out gate, and prepared the changelog
entry for landing. Operator impact: CineForge's surfaced scene-render route now
proves reference conditioning on a real project and explains any provider-limit
demotions honestly. Next step: `/check-in-diff`.
