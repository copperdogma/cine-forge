# UI Scout — 2026-04-10 — `open-frequency` — Local Validation

**Scenario:** `FP1`
**Date:** 2026-04-10
**Operator:** Codex
**Story:** 158
**Trigger:** Story 158 validation rerun after the `/events` bootstrap fix and fresh-import chat bootstrap normalization landed
**Fixture:** `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
**Project:** `open-frequency-3` created fresh through the normal `/new` flow (`open-frequency` and `open-frequency-2` already existed locally, so the slug deduped automatically)
**Environment:** local backend on `http://127.0.0.1:8000`, local UI on `http://127.0.0.1:5174`
**Git:** `codex/story-158-fresh-run-event-polling-stops-racing-missing-event-logs` at `bde2457`
**Overall result:** Pass
**Functional reach:** Pass
**UX / trust:** Pass

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
| Home / Script | `/open-frequency-3` | Pass. Project loaded with screenplay visible. |
| Intake CTA | `Break Down Script` from Home chat | Pass. `mvp_ingest` started from the surfaced CTA with no console/page/response noise. |
| Post-intake Home | `/open-frequency-3` after ingest | Pass. Script progress/state remained clear from Home without requiring Run Details. |
| Deeper CTA | `Deep Breakdown` from Home chat | Pass. `world_building` started from the surfaced CTA with no startup `/events` response noise. |
| Mobile Home | `/open-frequency-3` | Pass. Surface remained usable on mobile with the same chat truth. |
| Mobile Render | `/open-frequency-3/scenes/scene_001?tab=render` | Pass. Representative downstream mobile surface remained usable. |

## Honest Current Boundary

The current shipped full-pipeline UI boundary for the canonical fixture remains
the scene workspace plus the surfaced `Shots`, `Storyboards`, and `Production`
tabs on `scene_001`. This rerun verified the fresh-run startup contract on the
way into that boundary and confirmed the representative mobile render route
stays reachable through normal surfaced navigation.

## Findings

### 1. Fresh-run startup polling is now technically clean

- Type: Functional
- What happened:
  Starting `Break Down Script` and `Deep Breakdown` from the surfaced Home chat
  on a freshly created canonical-fixture project produced no browser
  `console_errors`, `page_errors`, or `response_errors`.
- Why it matters:
  This closes the exact Story 158 defect and satisfies the clean technical-path
  requirement in `spec:5.6`.
- Follow-up:
  None. Story 158 is verified by this rerun.

### 2. Fresh-import Home chat is honest again

- Type: Trust
- What happened:
  The fresh imported project surfaced `Break Down Script` immediately instead of
  regressing to the stale `Upload Screenplay` placeholder path.
- Why it matters:
  The canonical FP1 path depends on Home/chat being the honest default control
  surface, per ADR-002 and the UI design decisions.
- Follow-up:
  None.

### 3. Representative desktop and mobile surfaced routes remain usable

- Type: Functional
- What happened:
  The normal desktop creation/import flow, the two Home CTA launches, and the
  required mobile Home + Render spot-check all remained reachable without
  route-hunting or power-user detours.
- Why it matters:
  This confirms the fix did not merely silence errors while breaking the
  surfaced workflow.
- Follow-up:
  None.

## Evidence Summary

- Screenshots:
  `/tmp/story158-validate2-desktop-home.png`,
  `/tmp/story158-validate2-desktop-mid.png`,
  `/tmp/story158-validate2-mobile-home.png`,
  `/tmp/story158-validate2-mobile-render.png`
- Console / page errors:
  `console_errors=[]`, `page_errors=[]`, `response_errors=[]`
- Notes:
  Fresh API reads during validation confirmed that both run ids on
  `open-frequency-3` served `/api/runs/{id}/events` with HTTP `200` and
  non-empty event arrays.

## Next Action

- Return `FP1` to normal freshness monitoring; Story 158 can close
