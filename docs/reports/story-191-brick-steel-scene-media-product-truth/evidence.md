# Story 191 Evidence Packet - Brick & Steel Scene Media Product Truth

Captured: 2026-04-28 21:29 MDT / 2026-04-29 UTC

## Scope

Project: `brick-steel-full-retired` (`Brick & Steel: Full Retired`)

This packet captures the current production truth for the scene-media failure cluster before implementation. It supports Story 191's first implementation slice: fix the confirmed final-render prompt compiler gap, while preserving adjacent symptoms as classified evidence.

## Production State

- `GET /api/projects/brick-steel-full-retired`
  - artifact groups: `121`
  - run count: `17`
  - production format: `live_action`
  - input file: `Brick-_-Steel.pdf`
- Latest scene-media artifacts:
  - `render_prompt/scene_001/v4` - `valid`
  - `generated_video/scene_001/v4` - `needs_review`
  - `media_validation/scene_001/v4` - `needs_review`
  - `shot_plan/scene_001/v3` - `valid`
  - `storyboard/scene_001/v2` - `stale`
  - `track_manifest/project/v12` - `valid`
- Relevant runs:
  - `run-117fb7de` - first render generation, done
  - `run-61b966ee` - render generation after creative-direction work, done
  - `run-6bb6df36` - render generation, done
  - `run-1c86281e` - latest render generation, done
  - `run-6b40bd87` - render generation, failed with Google RAI media filtering
  - `run-ddec372f` - AI previz generation, failed because xAI key is not set

## Confirmed Prompt Gap

`render_prompt/scene_001/v4` includes the following summarized dialogue cues:

- `Brick asks if they're cold.`
- `Steel delivers the bear joke`

The same project's `shot_plan/scene_001/v3` contains exact dialogue lines that the isolated video model needs:

- `STEEL: Beer's ready!`
- `BRICK: Are they cold?`
- `STEEL: Does a bear crap in the woods?`
- `STEEL: To retirement.`
- `BRICK: To retirement.`
- `STEEL: Screw retirement.`
- `BRICK: Screw retirement.`

Code trace: `_shot_definition_block(plan)` in `src/cine_forge/modules/generation/render_adapter_v1/main.py` sends shot id, size, camera, movement, lens, duration, blocking, action, and edit intent into the render compiler, but does not include `shot.dialogue_lines`.

Classification: `prompt compiler gap`.

## Reference-Use Truth

`render_prompt/scene_001/v4` and `generated_video/scene_001/v4` both report one resolved direct reference input:

- `character_visual_brick_braddock`
  - kind: `character_injected_image`
  - relative path: `artifacts/bibles/character_brick_braddock/design_study_r3_img1.jpg`
  - used as: `reference_image`
  - source ref: `bible_manifest/character_brick_braddock/v3`

`bible_manifest/character_dick_steel/v2` has `visual_reference_image: null`, so Dick Steel was not a direct reference image in the latest final render. This is incomplete creatively, but the persisted `resolved_inputs` are honest about what was actually passed.

Classification: `reference transport/selection gap` for missing Dick Steel reference, not a false-disclosure bug in the current render artifact.

## Design-Study Truth

`design-study/character_brick_braddock` exists:

- selected final: `design_study_r3_img1.jpg`
- round 1: Imagen 4, 1 image, rejected
- round 2: Imagen 4, 4 images, rejected
- round 3: GPT-image, 4 images, one selected final

No persisted design-study state was found for these entity ids during production API capture:

- `character_dick`
- `character_dick_steel`
- `dick_steel`
- `character_steel`
- `character_brick`
- `brick_braddock`

The inbox's Dick Steel OpenAI moderation error is therefore not preserved in a design-study state artifact through the available production API. The raw inbox request id remains useful but is not enough for a local code fix without reproducible request context.

Classification:

- Brick Braddock bad-image quality: `model-quality miss`, with rejected Imagen rounds preserved.
- GPT-image completion needing refresh: `ambiguous` / likely `UI completion/polling gap`, because the GPT-image round persisted and the current API route is synchronous.
- Dick Steel moderation prompt disclosure: `provider-policy/provider-error` plus `ambiguous` local-code owner, because no persisted design-study state was found for that entity.

## Provider Failures

`run-6b40bd87` failed during render generation:

```text
Google video operation missing output URI ... raiMediaFilteredCount: 1 ... raiMediaFilteredReasons: ["Sorry, we can't create videos with real people's names or likenesses. Please remove the celebrity reference and try again."]
```

Classification: `provider-policy/provider-error`. It may still need better operator-facing error normalization, but the first confirmed implementation seam is the deterministic prompt compiler gap.

`run-ddec372f` failed during AI previz generation:

```text
CINE_FORGE_XAI_API_KEY (or legacy XAI_API_KEY) is not set
```

Classification: `provider-policy/provider-error` / provider readiness. This is adjacent to Story 191 but not part of the first fix.

## Manual Prompt-Builder Loop Plan

The first manual loop uses local deterministic fixtures rather than paid provider calls:

1. Capture baseline compiler input from `seed_render_project`, confirming the current shot-plan dialogue line is absent from `_shot_definition_block`.
2. Add exact dialogue-line transport to the deterministic shot-definition block.
3. Re-run the local prompt path and manually inspect the compiler input for these properties:
   - exact dialogue appears near the shot that owns it
   - dialogue is clearly marked as exact scripted dialogue
   - the prompt context still remains compact enough for the existing compiler
   - no provider call or immutable production artifact is mutated
4. Add a focused unit regression for the exact dialogue transport seam.
