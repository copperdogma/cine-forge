# Full-Pipeline UI Acceptance — 2026-04-10 — `open-frequency` — Local

**Date:** 2026-04-10
**Operator:** Codex
**Story:** 156
**Fixture:** `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
**Project:** `open-frequency` created fresh through the normal `/new` flow
**Environment:** local backend on `http://127.0.0.1:8000`, local UI on `http://127.0.0.1:5174`
**Git:** detached HEAD at `d241da5`
**Overall result:** Fail
**Functional reach:** Pass to the current honest downstream boundary
**UX / trust:** Fail due stale chat suggestions advertising already-completed paths

## Environment Checks

- API health: `GET /api/health` returned `{"status":"ok","version":"2026.04.10-06"}`
- UI shell: `GET /` on port `5174` returned HTTP `200`
- Walkthrough used only the surfaced UI; no `/run`, raw artifact pages, or
  manual substrate seeding were needed

## Exact Path Walked

| Surface | Route / action | Result |
|---|---|---|
| Landing | `/` | Pass. Normal entrypoint to project creation. |
| New Project | `/new` | Pass. Fixture upload/create flow was reachable and understandable. |
| Home / Script | `/open-frequency` | Pass. Project loaded with screenplay visible. |
| Intake CTA | `Break Down Script` from Home chat | Pass. `mvp_ingest` started from the surfaced CTA. |
| Post-intake Home | `/open-frequency` after ingest | Pass. Script progress/state became visible from Home without needing Run Details. |
| Deeper CTA | `Deep Breakdown` from Home chat | Pass functionally. `world_building` started from the surfaced CTA. |
| Post-world Home | `/open-frequency` after world building | Mixed. Home showed `Script 5/5`, `World 6/6`, and `All 67 artifacts are current`, but chat still advertised stale next-step CTAs. |
| Intent | `/open-frequency/intent` | Pass. Surfaced route was reachable and stable. |
| Scenes | `/open-frequency/scenes` | Pass. Scene list was reachable and usable. |
| Characters | `/open-frequency/characters` | Pass. Character surface loaded through normal nav. |
| Locations | `/open-frequency/locations` | Pass. Location surface loaded through normal nav. |
| Inbox | `/open-frequency/inbox` | Pass. Inbox surface loaded through normal nav. |
| Scene workspace | `/open-frequency/scenes/scene_001` | Pass. Representative scene route was reachable through surfaced navigation. |
| Shots | `/open-frequency/scenes/scene_001?tab=shots` | Pass. Tab stayed honest about missing work and offered `Run Shot Planning for Current Scene`. |
| Storyboards | `/open-frequency/scenes/scene_001?tab=storyboard` | Pass. Tab stayed honest about missing prerequisites and offered `Run Storyboard for Current Scene`. |
| Production / Render | `/open-frequency/scenes/scene_001?tab=render` | Pass. Furthest stable downstream surface reached in this run; tab honestly warned about missing prerequisites and offered `Run Render for Current Scene`. |
| Mobile Home | `/open-frequency` | Pass. Surface remained usable on mobile. |
| Mobile Render | `/open-frequency/scenes/scene_001?tab=render` | Pass. Representative downstream mobile surface remained usable. |

## Honest Current Boundary

The current shipped full-pipeline UI boundary for the canonical fixture is the
scene workspace plus the surfaced `Shots`, `Storyboards`, and `Production`
tabs on `scene_001`. The furthest stable downstream surface reached through the
normal UI in this run was the Production / Render tab.

That boundary is functionally reachable today. It is also still honest about
missing prerequisites: the scene tabs warned about missing concern-group or
render-prep inputs instead of pretending the project was ready for later media
output.

## Findings

### 1. State-honesty failure in the chat panel

- Home showed `Script 5/5`, `World 6/6`, and `All 67 artifacts are current`
  after the world-building pass finished.
- Despite that, the chat panel still surfaced stale `Break Down Script` /
  `Deep Breakdown` suggestions on the already-built project. The captured Home
  screenshot explicitly showed `Deep Breakdown` still presented as a live CTA.
- This is not a route-reachability bug; it is a trust/polish bug. The UI had
  already moved on, but the chat surface still advertised earlier-path work as
  if it were current.
- Follow-up: `docs/stories/story-157-chat-suggestions-stop-advertising-completed-paths.md`

### 2. No console or page-error noise on the walked path

- Desktop route probe: `consoleErrors=[]`, `pageErrors=[]`
- Scene-tab probe: `consoleErrors=[]`, `pageErrors=[]`
- Mobile probe: `consoleErrors=[]`, `pageErrors=[]`

### 3. No functional dead ends on the surfaced route sequence

- The run never needed dev-only escape hatches
- The main nav and scene-tab bar were enough to reach the honest current
  boundary
- Current downstream tabs surfaced real prerequisites instead of stranding the
  operator behind a blank or contradictory screen

## Evidence Summary

- Desktop capture set covered Home, Intent, Scenes, Characters, Locations,
  Inbox, Scene Workspace, Shots, Storyboards, and Production / Render
- Mobile capture set covered Home and Production / Render
- The most important screenshot outcome was the Home capture showing a stale
  `Deep Breakdown` CTA beside `All 67 artifacts are current`

## Next Action

- Keep Story 156 focused on the standing walkthrough/reporting lane
- Build Story 157 to remove stale completed-path CTAs from the chat surface
