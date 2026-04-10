# UI Scout — 2026-04-10 — `open-frequency` — Local Recheck

**Scenario:** `FP1`
**Date:** 2026-04-10
**Operator:** Codex
**Story:** 157
**Trigger:** FP1 recheck after Story 157 landed
**Fixture:** `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
**Project:** `open-frequency` created fresh through the normal `/new` flow
**Environment:** local backend on `http://127.0.0.1:8000`, local UI on `http://127.0.0.1:5174`
**Git:** detached HEAD at `bde2457`
**Overall result:** Fail
**Functional reach:** Pass to the current honest downstream boundary
**UX / trust:** Fail due desktop `/api/runs/{id}/events` 404 noise during fresh run startup

## Environment Checks

- API health: `GET /api/health` returned `{"status":"ok","version":"2026.04.10-10"}`
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
| Post-intake Home | `/open-frequency` after ingest | Pass. Script progress/state remained clear from Home without requiring Run Details. |
| Deeper CTA | `Deep Breakdown` from Home chat | Pass. `world_building` started from the surfaced CTA. |
| Post-world Home | `/open-frequency` after world building | Pass. Home showed `Script 5/5`, `World 6/6`, and `All 67 artifacts are current`, and the stale completed-path CTAs from the earlier run were no longer active. |
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

The current shipped full-pipeline UI boundary for the canonical fixture is still
the scene workspace plus the surfaced `Shots`, `Storyboards`, and `Production`
tabs on `scene_001`. The furthest stable downstream surface reached through the
normal UI in this rerun was the Production / Render tab.

That boundary remains functionally reachable today. The failed result comes from
technical cleanliness on the walked path, not from route reachability or stale
CTA honesty.

## Findings

### 1. Story 157's completed-path CTA bug is fixed

- Type: Trust
- What happened:
  After the world-building pass finished, Home still showed `Script 5/5`,
  `World 6/6`, and `All 67 artifacts are current`, but the chat surface no
  longer advertised `Break Down Script` or `Deep Breakdown` as active next-step
  buttons. Desktop and mobile both stayed honest about completed-path actions.
- Why it matters:
  This closes the exact trust defect from the first FP1 report and proves the
  recheck was necessary rather than assumed.
- Follow-up:
  None. Story 157 is verified by this rerun.

### 2. Fresh-run event polling still emits one desktop 404 per started run

- Type: Functional
- What happened:
  The rerun recorded two desktop response errors on the surfaced path:
  `http://127.0.0.1:5174/api/runs/run-20314e5e/events` and
  `http://127.0.0.1:5174/api/runs/run-a6ca1da5/events`.
  Both happened while starting the normal `Break Down Script` and `Deep Breakdown`
  runs from Home. The route later recovered, the run folders contained
  `pipeline_events.jsonl`, and direct backend requests to
  `http://127.0.0.1:8000/api/runs/<id>/events` returned `200`.
- Why it matters:
  `spec:5.6` treats clean technical behavior on the canonical path as part of
  product truth. "It recovered later" is not enough when the first surfaced run
  action throws console/network noise on the golden path.
- Follow-up:
  `docs/stories/story-158-fresh-run-event-polling-stops-racing-missing-event-logs.md`

### 3. No functional dead ends on the surfaced route sequence

- Type: Functional
- What happened:
  The full desktop route order and required mobile spot-check were still
  reachable without dev-only escape hatches, raw artifact detours, or route
  hunting.
- Why it matters:
  The recheck isolates the remaining failure to a narrow run-startup issue
  instead of reopening the whole FP1 path.
- Follow-up:
  None.

## Evidence Summary

- Screenshots:
  `/tmp/ui-scout-2026-04-10-start-desktop.png`,
  `/tmp/ui-scout-2026-04-10-mid-desktop.png`,
  `/tmp/ui-scout-2026-04-10-render-desktop.png`,
  `/tmp/ui-scout-2026-04-10-home-mobile.png`,
  `/tmp/ui-scout-2026-04-10-render-mobile.png`
- Console / page errors:
  desktop console errors were limited to two matching `404` resource failures
  for `/api/runs/{id}/events`; `pageErrors=[]`
- Notes:
  Story 157's target defect is verified fixed, but FP1 remains red until the
  fresh-run event-log startup race is removed.

## Next Action

- Build Story 158, then rerun `FP1` so `state.ui_scout` can move from
  `issues_found` to `pass`
