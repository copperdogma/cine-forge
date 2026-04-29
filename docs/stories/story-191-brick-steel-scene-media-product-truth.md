---
id: "191"
title: "Brick & Steel Final-Render Prompt Truth"
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
  - "spec:6.2"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "168"
  - "169"
  - "190"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "brick-steel"
  - "scene-generation"
  - "image-generation"
  - "final-render"
  - "references"
  - "product-truth"
legacy_system: ""
---

# Story 191 - Brick & Steel Final-Render Prompt Truth

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:4.10.7, spec:5.3, spec:5.5, spec:6.1, spec:6.2, spec:6.3, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 168, Story 169, Story 190

## Goal

Turn the current `Brick & Steel: Full Retired` final-render prompt failure into inspectable product truth, then fix the confirmed shipped seam. The scene-media capture found several related failures, but the local-code owner proved by current artifacts was narrower: final-render prompts were hand-waving dialogue instead of carrying exact script lines into isolated video generation. This story preserves the broader classification evidence, fixes the final-render prompt compiler gap, and explicitly hands the remaining GPT-image completion/error lifecycle work to Story 192.

Reopened 2026-04-28 after production prompt review showed the first fix was too blunt: exact dialogue was present once in the compiled prose and then appended a second time by the deterministic fallback, while the prompt still invited rushed back-to-back delivery in an 8-second clip.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R17 require generated images, storyboards, and final renders to be good enough for creative reaction and refinement, with user-provided or generated references treated as real inputs instead of vibes.
- **Parent evals / truth surfaces**: Story 168 proved reference-conditioned scene generation could carry resolved inputs through the normal route. Story 169 chose the reference-conditioned final-render provider floor. Story 190 kept `storyboard-generation-quality` below the usefulness floor and rejected a reference-anchor prompt candidate after a bounded subset.
- **Latest failure evidence**: `docs/inbox.md` now has current `Brick & Steel` notes that are more specific than the maintained evals: bad character/reference images, stalled GPT-image completion detection, moderation errors, final-render reference uncertainty, and missing exact dialogue in final-render prompts.
- **Measured failure mode**: not yet measured in a fresh story artifact. The first build task is capture/classification, not prompt or provider tuning by assumption.
- **Child story boundary**: this story advances the next unresolved node by producing a representative artifact packet and fixing the confirmed final-render prompt compiler gap on the named project path. Story 192 owns the separate design-study GPT-image completion/error lifecycle and browser-verification residual.

## Acceptance Criteria

- [x] A fresh evidence packet captures the current `Brick & Steel` scene-media path through normal project/API/UI surfaces, including generated character/reference images, storyboard or image-generation attempts if relevant, final-render prompt artifacts, generated-video artifacts, resolved inputs, run state/events, and provider error payloads.
- [x] Every current inbox symptom in the scene-media cluster is classified as one of: stale production data, provider-policy/provider-error, prompt compiler gap, reference transport/selection gap, UI completion/polling gap, model-quality miss, or ambiguous. The classification cites concrete artifacts or browser/API evidence.
- [x] Final-render prompt truth is verified or fixed so isolated video-generation prompts include exact script dialogue where the provider needs it. If prompt length or provider constraints prevent full dialogue inclusion, the artifact must disclose what was omitted and why.
- [x] Reference-use truth is verified or fixed so generated character/reference images and final renders expose which character/location/scene references were direct provider inputs, prompt-only context, unsupported, or ignored by provider behavior.
- [x] GPT-image completion and failure handling is preserved as classified follow-up work in Story 192 rather than claimed fixed by this final-render prompt slice.
- [x] At least one focused regression test or harness covers any local-code seam changed by the story. If the story closes with no local code change, it must preserve the evidence packet and record the provider/model blocker plus a concrete retry trigger.
- [x] Browser verification for the remaining design-study media-generation flow is moved to Story 192; no UI files changed in this final-render prompt slice.
- [x] Reopened prompt compiler no longer appends a duplicate exact-dialogue block when the compiler already included every shot-plan line with speaker labels and extra quote wrappers.
- [x] Reopened prompt compiler gives dialogue-heavy short clips explicit cadence/timing guidance so exact lines are not encouraged to run back-to-back without breaths or reaction beats.
- [x] Current AI video prompt best-practice research is preserved in the story evidence packet and reflected in the compiler rules.

## Out of Scope

- Reopening generic storyboard identity work without a new realistic-reference fixture or materially new model strategy.
- Rerunning the full final-render provider-floor benchmark unless capture proves provider selection itself is the current failure.
- Fixing Brick / Brick Braddock entity resolution or AI artifact editing. That is a separate world-model/editing cluster from the same inbox batch.
- Fixing GPT-image completion polling, provider error surfacing, or design-study browser verification; Story 192 owns that UI/provider lifecycle follow-up.
- Reworking Project Home hierarchy, UI-scout cadence, or the already-closed long-running black-screen request-storm fix from Story 139.
- Adding a new image or video provider transport unless current shipped providers are proven unusable and the user approves scope expansion.
- Scrubbing `docs/inbox.md` items before the matching symptom is verified fixed or proven stale.

## Approach Evaluation

- **Simplification baseline**: First inspect current artifacts and rerun only the smallest representative path. If the resolved inputs, prompts, and error payloads already prove the issue is stale or external, no new implementation should land. A single LLM call is not a valid baseline for polling, provider errors, reference transport, or immutable artifact provenance.
- **AI-only**: A frontier model can help judge whether an image/video follows the script and references, and may help classify prompt quality. It cannot guarantee exact dialogue transport, provider input slots, completion polling, or transparent error surfacing.
- **Hybrid**: Likely strongest. Use deterministic code for source-of-truth extraction, exact dialogue/reference transport, provider-limit disclosure, and polling/error lifecycle; use AI or multimodal judging only where semantic output quality must be assessed.
- **Pure code**: Correct for completion detection, provider error normalization, artifact provenance, and prompt assembly invariants. Insufficient for deciding whether a generated image or video actually preserves identity/style/reference quality.
- **Repo constraints / ADRs**: ADR-002 requires surfaced workflow truth and no hidden dead ends. ADR-003 makes prompts read-only compiled artifacts and references first-class inputs. `docs/design/decisions.md` says the script is the source of truth for names, structure, and dialogue, so render prompts cannot replace script lines with vague summaries when the provider lacks the source script.
- **Existing patterns to reuse**: Story 168's reference-conditioned render route and disclosure path, Story 169's final-render provider-floor harness shape, Story 190's storyboard-quality runtime/reporting pattern, `render_adapter_v1` `resolved_inputs`, `src/cine_forge/ai/image.py`, `src/cine_forge/ai/video.py`, `ProviderCapabilitySmokeService`, `RenderInputUsageCard`, `RenderPromptViewer`, `GeneratedVideoViewer`, and existing reference-library/entity-reference surfaces.
- **Eval**: No existing eval directly covers this exact `Brick & Steel` product-truth cluster. The discriminating evidence is a representative capture/classification packet plus focused unit/integration/browser checks. If the fix changes model quality expectations, update or create the appropriate eval follow-up rather than treating anecdotal improvement as durable truth.

## Tasks

- [x] Capture current production and local truth for the named `Brick & Steel` project route before changing code. Preserve relevant artifact paths, run ids, prompt snippets, resolved input summaries, browser screenshots, and provider error payloads.
- [x] Build the classification matrix for the current inbox scene-media cluster: character/reference image quality, GPT-image completion detection, moderation/error disclosure, final-render reference use, exact dialogue grounding, and keyframe affordance if it still appears in the same surfaced flow.
- [x] Re-run live provider/model discovery before making any model-selection claim or adopting a new image/video model. No model-selection claim or adoption was made in this shipped slice, so discovery was not required.
- [x] Select the smallest confirmed implementation seam after classification. Candidate seams include prompt assembly/exact dialogue transport, reference-selection/disclosure, GPT-image completion invalidation, provider error normalization, or artifact viewer truth.
- [x] Implement only the chosen seam and preserve existing artifact contracts, immutable versions, and prompt/source lineage.
- [x] Add focused tests for any changed prompt-building, reference selection, image-provider error handling, completion polling, run invalidation, or artifact-viewer behavior.
- [x] If an eval or benchmark is run, classify all significant mismatches as `model-wrong`, `golden-wrong`, or `ambiguous`, and record whether remaining failures are runtime-blocking or non-runtime-blocking. No eval or benchmark was run for this deterministic prompt-transport slice.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b` passed during validation; no UI files changed, so `pnpm --dir ui run build` was not required.
- [x] If agent tooling or project instructions are touched: `make skills-check`. No agent tooling or project instructions were touched.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`. No evals or goldens changed.
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker. No UI files changed; Story 192 owns browser verification for the design-study residual.
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

### Reopen Tasks

- [x] Research current official AI video-generation prompt guidance for structure, ordering, dialogue, audio, pacing, and short-clip complexity.
- [x] Replace the previous blunt exact-dialogue footer with normalized exact-line detection, a single dialogue timing fallback, and cadence guidance.
- [x] Add regression coverage for the quoted-speaker-line duplication case from the production Brick & Steel prompt.
- [x] Manually inspect the updated prompt-builder output against the pasted production failure shape.
- [x] Re-run focused backend validation for the changed compiler seam, then run the required broader checks before closing again.

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

- **Owning class/module**: `src/cine_forge/modules/generation/render_adapter_v1/` owns final-render prompt compilation, reference shaping, and resolved input truth. `src/cine_forge/ai/image.py` owns OpenAI/Imagen image generation dispatch and provider errors. `src/cine_forge/ai/video.py` owns video provider transport. `src/cine_forge/modules/visualization/storyboard_v1/` owns storyboard image generation. UI truth should stay in focused media/reference viewers rather than expanding `SceneWorkspacePage.tsx` unless page-level completion wiring is the confirmed bug.
- **Data contracts**: Existing render contracts live in `src/cine_forge/schemas/render.py`; provider health in `src/cine_forge/schemas/provider_health.py`; injected assets in `src/cine_forge/schemas/injected_asset.py`; media validation in `src/cine_forge/schemas/media_validation.py`. Any new cross-layer provider-error or prompt-omission field must be schema-first.
- **File sizes**: likely touch points are large: `render_adapter_v1/main.py` (`1823`), `src/cine_forge/ai/video.py` (`550`), `src/cine_forge/services/injected_assets.py` (`811`), `storyboard_v1/generation.py` (`657`), `ui/src/lib/use-run-progress.ts` (`795`), `ui/src/pages/SceneWorkspacePage.tsx` (`984`), `tests/unit/test_render_adapter_module.py` (`1001`), and `tests/integration/test_render_adapter_integration.py` (`541`). Smaller or focused owners include `storyboard_v1/grid.py` (`279`), `storyboard_v1/identity.py` (`326`), `GeneratedVideoPanel.tsx` (`385`), `RenderPromptViewer.tsx` (`445`), `GeneratedVideoViewer.tsx` (`213`), `tests/unit/test_ai_image.py`, `tests/unit/test_provider_capability_smoke.py`, and `tests/unit/test_storyboard_grid.py` (`87`). If the fix is not surgical, extract a focused helper before growing oversized files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Stories 168/169/190, and the current inbox cluster. No new ADR is needed unless classification proves a durable change to prompt-editability, provider strategy, or reference ownership.

## Files to Modify

- `docs/stories/story-191-brick-steel-scene-media-product-truth.md` - keep story truth and work log current
- `docs/methodology/state.yaml` - update active generation-lane planning truth now that Story 191 owns the next follow-up
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` - only if final-render prompt/reference shaping is confirmed (`1823`, LARGE)
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` - only if prompt text assembly needs focused exact-dialogue or reference wording changes
- `src/cine_forge/ai/image.py` - only if GPT-image request/response/error behavior is confirmed (`550`, LARGE)
- `src/cine_forge/ai/video.py` - only if video provider request/error behavior is confirmed (`550`, LARGE)
- `src/cine_forge/services/injected_assets.py` - only if reference collection/priority is confirmed (`811`, LARGE)
- `src/cine_forge/modules/visualization/storyboard_v1/` - only if the confirmed failure is storyboard/image-generation owned
- `ui/src/components/RenderPromptViewer.tsx`, `ui/src/components/GeneratedVideoViewer.tsx`, `ui/src/components/GeneratedVideoPanel.tsx`, or reference-library/entity-reference components - only if surfaced truth or completion state is confirmed UI-owned
- `tests/unit/test_ai_image.py`, `tests/unit/test_render_adapter_module.py`, `tests/integration/test_render_adapter_integration.py`, `tests/unit/test_storyboard_module.py`, or focused new tests - add regression coverage for the confirmed seam
- `docs/evals/registry.yaml` - only if an eval or benchmark rerun updates maintained scores
- `docs/ui-scout.md` / `docs/ui-scout/` - only if browser verification is best recorded as a UI-scout product-truth run

## Redundancy / Removal Targets

- Any prompt path that summarizes dialogue when the isolated downstream model needs exact script lines.
- Any duplicated provider-error string handling that can be centralized in existing provider failure/error-normalization seams.
- Any image-generation completion polling or invalidation logic that relies on manual refresh to reveal completed artifacts.
- Any reference-debug UI that duplicates persisted `resolved_inputs` instead of rendering the existing artifact truth.

## Notes

- `docs/inbox.md` remains the live queue until the matching symptoms are verified fixed or stale. Do not delete the cluster just because this story exists.
- The missing prod xAI key is adjacent provider-health work, not this story, unless capture proves the default shipped scene-media route cannot honestly surface that provider readiness.
- The long-running black-screen report is likely handled by Story 139 and the 2026-04-29 deploy. Treat it as stale unless it reproduces after that fix.
- The Brick / Brick Braddock duplicate-character and AI artifact-editing notes are important but should be a separate world-model/editing story if current repro confirms them.

## Plan

Proceed in one capture-first implementation slice. The confirmed local-code owner is the final-render prompt compiler dropping shot-plan `dialogue_lines` before the LLM compiler sees them. The broader image-generation and provider-error symptoms stay in the evidence matrix unless capture proves a same-slice fix is needed.

1. Create a story evidence packet under `docs/reports/story-191-brick-steel-scene-media-product-truth/`.
   - Capture production artifact IDs and summaries for `brick-steel-full-retired`: `render_prompt/scene_001/v4`, `generated_video/scene_001/v4`, `media_validation/scene_001/v4`, `shot_plan/scene_001/v3`, `storyboard/scene_001/v2`, runs `run-117fb7de`, `run-61b966ee`, `run-6bb6df36`, `run-1c86281e`, `run-6b40bd87`, and `run-ddec372f`.
   - Record the classification matrix for the current inbox cluster. Current baseline: final-render dialogue grounding is a prompt compiler gap; Brick reference transport is partially honest but incomplete because only `character_brick_braddock` has `visual_reference_image`; Dick Steel image generation has no persisted design-study state found; `run-6b40bd87` is a provider-policy/provider-error case from Google RAI filtering; `run-ddec372f` is missing xAI key provider readiness.
   - Preserve prompt excerpts, resolved input summaries, and the current provider failure text. Do not store secrets or raw API keys.
2. Fix the prompt compiler seam in `src/cine_forge/modules/generation/render_adapter_v1/main.py`.
   - Add exact per-shot dialogue lines to `_shot_definition_block(plan)` next to each shot's action/blocking/edit intent.
   - Add a compact instruction in the compiler context if needed so isolated video prompts must preserve exact quoted dialogue instead of replacing it with summaries like "Steel delivers the bear joke."
   - Keep this surgical inside the existing helper. `main.py` is 1823 lines, so avoid growing unrelated logic or adding another responsibility to the module.
3. Add focused regression coverage.
   - Add or extend a unit test in `tests/unit/test_render_adapter_module.py` proving the compiler prompt includes exact `shot.dialogue_lines`, using existing `seed_render_project` fixture data.
   - If the prompt text can be verified without a live provider call, assert the generated compiler input includes `We can still stop this.` or a Brick-and-Steel-style exact line and does not depend on vague action text alone.
   - No live image/video provider call is required for this first fix because the bug is deterministic prompt-context loss before provider transport.
4. Verify the changed seam.
   - Run the targeted render-adapter unit test first.
   - Run `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`.
   - Because the planned code change is backend prompt compilation only, browser verification is not required for acceptance of this seam. If later implementation touches UI completion/error surfacing, add desktop and mobile browser verification before handoff.
   - Run `pnpm methodology:compile` and `pnpm methodology:check` after updating the story artifact.
5. Defer larger adjacent fixes unless the evidence packet contradicts the current classification.
   - GPT-image completion may be a long request/client lifecycle issue in `DesignStudySection` or API timeout behavior, but production state showed Brick's GPT-image round persisted and the design-study route is synchronous. Treat this as a follow-up unless it reproduces during implementation without broadening the slice.
   - OpenAI moderation prompt disclosure should become a provider-error/design-study follow-up if the error can be reproduced or a state artifact exists. No persisted Dick Steel design-study state was found in production during exploration.
   - Reference-use quality for final render should be a follow-up unless exact-dialogue prompt repair also changes reference selection. Current `resolved_inputs` honestly reports one direct Brick reference image; it does not pretend Dick Steel has a direct reference.

Impact and risk:

- The main behavioral improvement is that the isolated final-render video prompt will get the exact scripted lines already present in the shot plan, reducing model hand-waving in the generated scene.
- The main technical risk is touching `render_adapter_v1/main.py`, a large file. The mitigation is a tiny helper-level edit and a focused regression test.
- This plan does not claim the visual image-quality problems are fixed. It makes them inspectable in the evidence packet and fixes the code-owned prompt truth bug already proven by production artifacts.

Anti-fragmentation check: this remains a new story instead of a Story 190 reopen because Story 190 was limited to storyboard identity/reference eval work and rejected a specific non-default candidate, while this story's first confirmed fix is final-render prompt grounding plus current production scene-media classification.

### Reopen Plan

1. Preserve a small source-backed research artifact for AI video prompt structure and ordering. Bias toward official provider guidance and translate it into compiler rules, not generic prompt folklore.
2. Change the final-render compiler to use a single dialogue timing contract:
   - The shot-definition context should point to one dialogue timing section instead of burying exact lines inline in each shot row.
   - The postprocessor should normalize quotes and punctuation around exact dialogue before deciding a line is missing.
   - The deterministic fallback should append one `Dialogue timing / exact lines` section only when exact lines are actually absent.
3. Add cadence pressure handling for dialogue-dense short clips. The prompt and artifact notes should state when the requested duration is tight for the line count, then ask for terse but distinct delivery with breaths/reaction beats.
4. Validate with a regression modeled on the production failure: shot-plan lines like `STEEL: Beer's ready!` must not be considered missing when the compiler writes `STEEL: "Beer's ready!"`.

## Work Log

20260428-2113 - story-created: created Story 191 from unscoped `/triage` after neutral story, inbox, eval, architecture, and health lanes agreed that the current `Brick & Steel` scene-media cluster is the highest-value active `spec:6` / `spec:7` follow-up. Evidence: `docs/inbox.md` reports bad character/reference images, GPT-image completion uncertainty, moderation errors, final-render reference uncertainty, and missing exact script lines; Story 139 likely handled the black-screen item; Story 190 is done and waiting for a realistic-reference fixture trigger rather than another prompt tweak. Next step: run `/build-story 191` to capture and classify the current artifact truth before coding.
20260428-2129 - exploration-notes: completed `/build-story 191` exploration and plan gate without implementation code. Consulted `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/build-map.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Stories 168/169/190, current `docs/inbox.md`, production project API, and render/design-study code paths. Production baseline: `brick-steel-full-retired` has 121 artifact groups and 17 runs; latest scene media includes `render_prompt/scene_001/v4`, `generated_video/scene_001/v4`, `media_validation/scene_001/v4`, `shot_plan/scene_001/v3`, and stale `storyboard/scene_001/v2`. The latest render prompt still says "Brick asks if they're cold" and "Steel delivers the bear joke" even though `shot_plan/scene_001/v3` has exact dialogue lines (`STEEL: Beer's ready!`, `BRICK: Are they cold?`, `STEEL: Does a bear crap in the woods?`, `STEEL: To retirement.`, `BRICK: To retirement.`, `STEEL: Screw retirement.`, `BRICK: Screw retirement.`). Code trace found `_shot_definition_block` in `src/cine_forge/modules/generation/render_adapter_v1/main.py` sends shot size, camera, blocking, action, and edit intent to `compile_render_prompt` but omits `shot.dialogue_lines`, making this a deterministic prompt compiler gap. `render_prompt/scene_001/v4` reports one direct reference image for `character_brick_braddock`; `character_dick_steel` has no `visual_reference_image`, so the final render reference-use truth is partial but honest. Design-study state exists for `character_brick_braddock` with a GPT-image round selected as final; no design-study state was found for `character_dick`, `character_dick_steel`, `dick_steel`, `character_steel`, or `character_brick`. Provider failures are separately classified: `run-6b40bd87` failed with Google RAI media filtering about real people's names/likenesses, and `run-ddec372f` failed because the xAI key is not set. Structural check: `make check-size` passed but flagged large files; likely touched files are `render_adapter_v1/main.py` (1823 lines), `render_adapter_v1/prompting.py` (315), and `tests/unit/test_render_adapter_module.py` (1001). Plan: create an evidence packet, fix the shot-definition dialogue transport seam, add a focused regression test, run backend/unit/lint/methodology checks, and defer GPT-image completion/UI/error-disclosure work unless implementation evidence proves it belongs in the same slice.
20260428-2138 - implementation: preserved the evidence and classification matrix in `docs/reports/story-191-brick-steel-scene-media-product-truth/evidence.md`, then fixed the confirmed final-render prompt truth seam. `_shot_definition_block` now carries per-shot `exact_scripted_dialogue` from `shot.dialogue_lines` into the compiler context, and final render prompts are guarded by deterministic post-processing that appends an `Exact scripted dialogue to preserve verbatim` block if the LLM compiler still omits any exact lines. Added prompt-builder guidance in `render_adapter_v1/prompting.py` so the compiler is instructed not to turn exact dialogue into summaries. Manual loop evidence: local fixture prompt inspection first exposed a double-period note issue, which was fixed; production `shot_plan/scene_001/v3` inspection then showed exact Brick & Steel lines attached to shots 002/003/005 and appended to the final prompt tail when the simulated compiler output summarized the scene. Focused regression now asserts the compiler input, persisted prompt artifact, and video request all include `We can still stop this.` from the shot plan. Checks: targeted unit passed, targeted Ruff passed, full `make test-unit PYTHON=.venv/bin/python` passed (`818 passed, 179 deselected, 1 warning`), and full `.venv/bin/python -m ruff check src/ tests/` passed. Remaining residuals: GPT-image completion/failure handling is classified but not locally fixed in this slice; no UI files were touched, so browser verification remains a follow-up before story closure if validation requires it.
20260428-2154 - validation: ran `/validate` fresh against the Story 191 diff. Checks passed: `make test-unit PYTHON=.venv/bin/python` (`818 passed, 179 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/`, `.venv/bin/python -m pytest -m unit tests/unit/test_render_adapter_module.py::test_run_module_generates_prompt_video_and_track_entries`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm methodology:check`, and `git diff --check`. The implemented exact-dialogue prompt transport is clean and aligned with ADR-002/ADR-003; no compatibility shim, duplicate owner, dead wrapper, or widened contract drift was found. No promptfoo eval or registry update was run because this slice changed deterministic prompt assembly rather than a maintained scored model-quality eval. Closure is not clean as written: GPT-image completion/failure handling and desktop/mobile browser verification remain unchecked original acceptance criteria. Recommendation: rescope those UI/provider lifecycle criteria into a follow-up story, then run `/mark-story-done 191`; otherwise keep Story 191 open and fix the residual completion/error/browser path before closure.
20260428-2158 - rescope-closeout: created Story 192, `Brick & Steel GPT-Image Completion and Error Truth`, as the explicit owner for the design-study GPT-image completion/failure handling and desktop/mobile browser-verification residual. Narrowed Story 191's title, goal, acceptance criteria, tasks, and out-of-scope list to the shipped final-render prompt-truth slice. Evidence remains the Story 191 capture packet plus validation pass; no UI/provider lifecycle fix is claimed here. Next step: `/mark-story-done 191`.
20260428-2201 - completion: marked Story 191 Done via `/mark-story-done` after the rescope made all acceptance criteria and tasks truthful for the shipped final-render prompt-truth slice. Fresh close-out checks passed: `make test-unit PYTHON=.venv/bin/python` (`818 passed, 179 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm methodology:check`, and `git diff --check`. Story 192 now owns the separate design-study GPT-image completion/error/browser follow-up, so Story 191 closes without claiming that residual is fixed. Recommended next step: `/check-in-diff`.
20260428-2252 - reopened: production prompt review for `brick-steel-full-retired/scene_001` showed the first exact-dialogue fallback created a new artifact-quality problem. The compiled prompt already contained the exact Brick/Steel lines in prose with quote wrappers, but deterministic missing-line detection treated `STEEL: "Beer's ready!"` as missing relative to `STEEL: Beer's ready!` and appended a second exact-dialogue block. The same prompt still gave only broad rhythm language for seven lines plus a long silence inside an 8-second clip, which invites rapid-fire delivery. Reopened Story 191 rather than creating a separate story because the bug is directly inside the prior prompt compiler seam.
20260428-2300 - implementation: researched official Sora, Veo, and Runway prompt guidance and captured the compiler implications in `docs/reports/story-191-brick-steel-scene-media-product-truth/video-prompting-research.md`. Updated the render adapter so `_shot_definition_block` exposes one `Dialogue timing / exact lines` contract instead of duplicating exact lines inside shot rows, and replaced the blunt footer with normalized exact-line matching plus a single timing fallback. The postprocessor now normalizes quote wrappers and curly quotes before deciding a line is missing, so `STEEL: "Beer's ready!"` no longer triggers a duplicate exact-dialogue block. Added cadence guidance and a density note when the exact line count is tight for the requested duration. Focused regression now covers both missing-dialogue fallback and the quoted Brick/Steel-style duplicate case; targeted unit check passed (`2 passed`).
20260428-2311 - validation: manually exercised a Brick/Steel-shaped sample through `_shot_definition_block` and `_ensure_dialogue_prompt_contract`; the shot block contained one `Dialogue timing / exact lines` contract, the quoted exact-dialogue prompt did not get a fallback timing block appended, `Beer's ready!` appeared once, and the dense 8-second cadence guidance was added. Checks passed: targeted Story 191 regression tests (`2 passed`), targeted Ruff for the touched files, `make test-unit PYTHON=.venv/bin/python` (`819 passed, 179 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm methodology:compile`, `pnpm methodology:check`, and `git diff --check`. Methodology check reports pre-existing warnings for `api_service_and_operator_console` architecture audit attention and stale UI-scout freshness; no UI files were touched, so browser verification is not part of this compiler-only reopen.
20260428-2351 - reclose-scope-boundary: re-closed Story 191 as the prompt-compiler truth repair only. The shipped slice fixes duplicate exact-dialogue fallback behavior, preserves exact lines once, and adds cadence guidance for dialogue-heavy clips. It intentionally does not claim to solve the larger provider-duration mismatch where a roughly 30-second scene is forced into a single 8-second render; Story 193 now owns the prerequisite `render_clip_plan` artifact and Story 194 drafts the dependent multi-clip render execution path. Recommended next step: `/check-in-diff`.
