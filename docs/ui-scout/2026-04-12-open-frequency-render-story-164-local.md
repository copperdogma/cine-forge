# UI Scout — 2026-04-12 — `open-frequency-render-story-164` — Local

**Scenario:** `FP1`
**Date:** 2026-04-12
**Operator:** Codex
**Story:** 164
**Trigger:** Story 164 implementation validation after the Scene Workspace render path was promoted from “reachable” to “actually produces a scene render”
**Fixture:** `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
**Project:** `open-frequency-render-story-164` created fresh through the normal `/new` flow
**Environment:** local backend on `http://127.0.0.1:8000`, local UI on `http://127.0.0.1:4173`
**Git:** `codex/story-164-real-scene-generation-product-truth` at `993629f`
**Overall result:** Pass
**Functional reach:** Pass
**UX / trust:** Pass

## Environment Checks

- API health: `GET /api/health` returned `{"status":"ok","version":"2026.04.12-01"}`
- UI shell: `GET /` on port `4173` returned HTTP `200`
- Walkthrough used only the surfaced UI plus surfaced artifact-detail links; no `/run`, raw recipe controls, or hand-seeded substrate was needed

## Exact Path Walked

| Surface | Route / action | Result |
|---|---|---|
| Landing | `/` | Pass. Normal entrypoint to project creation. |
| New Project | `/new` | Pass. Fixture upload/create flow remained the obvious first move. |
| Home / Script | `/open-frequency-render-story-164` | Pass. Fresh project loaded with screenplay visible and the surfaced `Break Down Script` CTA. |
| Intake CTA | `Break Down Script` from Home chat | Pass. `mvp_ingest` completed without needing raw run controls. |
| Desktop surfaced routes | `/open-frequency-render-story-164`, `/intent`, `/scenes`, `/characters`, `/locations`, `/inbox` | Pass. The normal surfaced route set remained reachable without route hunting. |
| Scene Workspace | `/open-frequency-render-story-164/scenes/scene_001?tab=render` | Pass. Render tab stayed honest about warnings and auto-built prerequisites instead of demanding deeper setup first. |
| Representative render | `Run Render for Current Scene` | Pass. `run-43fbbd79` completed `timeline`, `tracks`, `shot_planning`, `render`, and `validate_media`, producing a real scene video plus trust artifacts. |
| Artifact detail trust links | `Prompt Detail`, `Video Detail`, `Validation Detail` | Pass. Each surfaced control navigated to the corresponding Artifact Detail route: `/artifacts/render_prompt/scene_001/2`, `/artifacts/generated_video/scene_001/2`, and `/artifacts/media_validation/scene_001/2`. |
| Mobile Home | `/open-frequency-render-story-164` | Pass. Home stayed usable and readable on mobile. |
| Mobile Render | `/open-frequency-render-story-164/scenes/scene_001?tab=render` | Pass. Representative downstream mobile surface remained usable after the real scene render landed. |

## Honest Current Boundary

The honest FP1 downstream boundary is no longer merely “the Render tab is
reachable.” On the canonical short screenplay, a fresh project can now reach a
real scene render from the surfaced Scene Workspace route after the initial
`Break Down Script` pass. The key trust surface is:

- the preflight summary on `scene_001?tab=render`
- the resulting `render_prompt`, `generated_video`, and `media_validation`
  detail links on the same Render panel
- the corresponding Artifact Detail pages those links open

## Findings

### 1. Scene render is now a real surfaced product path

- Type: Functional
- What happened:
  Starting from a fresh project, the Scene Workspace `Render` tab launched a
  representative scene-scoped run and auto-built `timeline`, `tracks`, and
  `shot_planning` before producing `render_prompt`, `generated_video`, and
  `media_validation` artifacts for `scene_001`.
- Why it matters:
  This closes the feature-completeness gap that made the app feel unfinished:
  the surfaced route now reaches an actual scene video instead of stopping at a
  reachable-but-nonproductive tab.
- Follow-up:
  None for FP1. Deeper scene-quality tuning remains separate from this route
  becoming real.

### 2. Warning-level preflight gaps now stay honest instead of turning into a hidden render failure

- Type: Trust
- What happened:
  The render preflight still reported warning-level missing direction/context
  (continuity, look & feel, sound & music, rhythm & flow, keyframes), but the
  render path no longer contradicted that promise by hard-failing on the same
  warning set. The resulting media validation also stayed honest: it marked the
  output `needs_review` because sampled frames did not prove the requested wide
  master.
- Why it matters:
  ADR-002 and ADR-003 both depend on CineForge distinguishing “can proceed with
  tradeoffs” from “meaningless request.” The surfaced route now matches that
  contract instead of trapping the operator after saying it can continue.
- Follow-up:
  None. The output-quality caveat is visible in the validation artifact rather
  than hidden in runtime failure.

### 3. Active render polling stayed clean after the atomic run-state fix

- Type: Functional / Trust
- What happened:
  The first successful render (`run-43fbbd79`) exposed a transient
  `/api/runs/run-43fbbd79/state` HTTP `500` while the UI was polling. Story 164
  fixed that by making `run_state.json` writes atomic in the driver. A refresh
  render (`run-7cacec1f`) then completed with zero new browser console errors
  during active polling.
- Why it matters:
  A “successful render” still feels broken if the surfaced route throws errors
  while the operator waits. This fix makes the normal long-running render path
  technically clean enough to trust.
- Follow-up:
  None.

## Evidence Summary

- Render runs:
  `run-43fbbd79` (first successful representative scene render),
  `run-7cacec1f` (post-fix refresh render proving clean polling)
- Artifacts:
  `output/open-frequency-render-story-164/artifacts/render_prompt/scene_001/v1.json`,
  `output/open-frequency-render-story-164/artifacts/generated_video/scene_001/v1.json`,
  `output/open-frequency-render-story-164/artifacts/media_validation/scene_001/v1.json`
- Screenshots:
  `story-164-home-desktop.png`,
  `story-164-scenes-desktop.png`,
  `render-desktop-story-164-clean.png`,
  `story-164-home-mobile.png`,
  `render-mobile-story-164-clean.png`
- Console / page errors:
  `browser_console_messages(level=\"error\", all=false)` returned `0` after the
  atomic run-state fix and final rerun
- Notes:
  `media_validation` stayed intentionally non-green: `recommended_health =
  needs_review` because the sampled frames did not confirm the requested wide
  establishing shot. That is correct product behavior, not a runtime defect.

## Next Action

- Keep FP1 on the new “real scene render through the surfaced route” boundary
  and let `/validate 164` do the independent acceptance pass
