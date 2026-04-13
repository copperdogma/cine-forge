# UI Scout — 2026-04-13 — `story-168-reference-render-verify-patched-102817` — Local

**Scenario:** `FP2`
**Date:** 2026-04-13
**Operator:** Codex
**Story:** 168
**Trigger:** Story 168 implementation validation after the reference-conditioned scene-generation path was promoted from backend-only assumption to surfaced product truth
**Fixture:** `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
**Project:** `story-168-reference-render-verify-patched-102817` created fresh through the normal project/input API flow, then verified through the surfaced Scene Workspace and Artifact Detail routes
**Environment:** local backend on `http://127.0.0.1:8000`, local UI on `http://127.0.0.1:4173`
**Git:** `codex/story-168-reference-conditioned-scene-generation-product-truth` at `0dfbd6c`
**Overall result:** Pass
**Functional reach:** Pass
**UX / trust:** Pass

## Environment Checks

- API health: `GET /api/health` returned `{"status":"ok","version":"2026.04.13-01"}`
- UI shell: `GET /` on port `4173` returned HTTP `200`
- Route constraints: walkthrough used real project creation/upload APIs, real upstream runs, surfaced project/scene/entity asset flows, and surfaced Scene Workspace / Artifact Detail routes only; no raw recipe controls or hand-seeded impossible substrate was needed

## Exact Path Walked

| Surface | Route / action | Result |
|---|---|---|
| Project create | `POST /api/projects/new` + `POST /api/projects/{project_id}/inputs/upload` | Pass. Fresh representative project was created from `open_frequency_short.fountain`. |
| Upstream ingest | `mvp_ingest` (`run-1c44486f`) | Pass. Normal script-ingest route completed without special handling. |
| Upstream world building | `world_building` (`run-0da9ab73`) | Pass. Scene/character context existed through the normal pipeline before render. |
| Project taste refs | project asset APIs for `mood_board.png` and `style_reference.png` | Pass. Real project-level taste references were attached before render. |
| Scene + entity refs | scene `scene_reference.png` on `scene_001` and character `actor_photo.png` on `aria` | Pass. Surfaced asset flows created a real reference-conditioned setup. |
| Desktop Render tab | `/story-168-reference-render-verify-patched-102817/scenes/scene_001?tab=render` | Pass. `Run Render for Current Scene` completed `run-880869ab` and surfaced selection/demotion truth without raw JSON inspection. |
| Prompt detail | `/story-168-reference-render-verify-patched-102817/artifacts/render_prompt/scene_001/1` | Pass. Compiled creative brief, active project refs, and fallback-section note were visible. |
| Generated video detail | `/story-168-reference-render-verify-patched-102817/artifacts/generated_video/scene_001/1` | Pass. `Prompt Provenance` linked back to the prompt artifact and matched the Render tab truth. |
| Mobile Render tab | same scene render route on mobile viewport | Pass. The render surface remained usable and honest on mobile. |
| Mobile generated video detail | same generated-video route on mobile viewport | Pass. Prompt provenance and reference disclosure stayed available on mobile. |

## Honest Current Boundary

Starting from a fresh project built through the real API and driver path, the
stable downstream surface is now a real reference-conditioned scene render from
the Scene Workspace `Render` tab, with the selected versus demoted reference
truth visible on both Render and Artifact Detail. Project taste refs can still
be demoted to prompt-only context on packs with image-slot caps, but that
compromise is now surfaced explicitly instead of hiding behind backend-only
state.

## Findings

### 1. Reference-conditioned render is now a real surfaced product path

- Type: Functional
- What happened:
  After fresh ingest, world-building, and real project/scene/entity reference
  injection, `run-880869ab` completed from the surfaced Render tab and produced
  `render_prompt`, `generated_video`, and `media_validation` artifacts for
  `scene_001`.
- Why it matters:
  This closes the feature-completeness gap where CineForge claimed references
  mattered but only proved that truth in backend artifacts or synthetic tests.
- Follow-up:
  None inside Story 168; the next step is independent acceptance via
  `/validate 168`.

### 2. Scene Workspace and Artifact Detail now tell the same truth about selected versus demoted references

- Type: Trust
- What happened:
  The final render showed the scene reference as `Input Reference`, while
  project `mood_board.png` and `style_reference.png` stayed `Prompt Context`
  with explicit notes that `openai_sora2` ran out of image slots. Prompt detail
  also exposed the compiled creative brief and active project refs, and
  generated-video detail added `Prompt Provenance` plus a direct prompt-artifact
  link.
- Why it matters:
  The operator no longer has to inspect raw JSON or infer whether selected
  references were ignored, downgraded, or used directly by the provider.
- Follow-up:
  None. The remaining provider-limit compromise is honest and inspectable.

### 3. The representative route exposed and then closed two real blockers

- Type: Functional / Trust
- What happened:
  The first fresh project failed on OpenAI image-size validation
  (`run-5b36d21b`), and a later fresh probe failed because the compiled render
  prompt omitted `character_bible_state` despite upstream context being present
  (`run-9f6adeb9`). Story 168 fixed both with opening-frame normalization in
  `src/cine_forge/ai/video.py` and fallback prompt-section synthesis in
  `src/cine_forge/modules/generation/render_adapter_v1/main.py`.
- Why it matters:
  The route now passes on representative state instead of succeeding only on
  lab fixtures that bypass real provider/runtime constraints.
- Follow-up:
  Keep the new targeted regression coverage green so those seams do not regress.

## Evidence Summary

- Render runs:
  `run-1c44486f` (`mvp_ingest`),
  `run-0da9ab73` (`world_building`),
  `run-880869ab` (final successful representative render);
  blocker runs captured during implementation:
  `run-5b36d21b`, `run-f53ba61f`, `run-9f6adeb9`
- Artifacts:
  `output/story-168-reference-render-verify-patched-102817/artifacts/render_prompt/scene_001/v1.json`,
  `output/story-168-reference-render-verify-patched-102817/artifacts/generated_video/scene_001/v1.json`,
  `output/story-168-reference-render-verify-patched-102817/artifacts/media_validation/scene_001/v1.json`
- Screenshots:
  `story-168-render-desktop.png`,
  `story-168-render-prompt-detail-desktop.png`,
  `story-168-generated-video-detail-desktop.png`,
  `story-168-render-mobile.png`,
  `story-168-generated-video-detail-mobile.png`
- Console / page errors:
  `browser_console_messages(level="error", all=false)` returned `0` on the
  final desktop/mobile verification pass
- Notes:
  The final prompt/video surfaces also showed the adapter fallback note
  `Adapter synthesized fallback sections for: character_and_performance, injected_assets.`
  The successful render still waited real provider time (`render` stage
  `210.9888s`), which is expected for this path rather than a blocker.

## Next Action

- Run `/validate 168` for independent acceptance on the finished build
