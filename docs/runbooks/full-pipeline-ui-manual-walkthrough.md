# Full-Pipeline UI Manual Walkthrough

Short recurring product-truth check for the full surfaced CineForge UI path.
This runbook exists because browser smoke and targeted screenshots are not the
same thing as "can a real person take a fresh project through the pipeline, and
does the UI still feel polished and obvious while they do it?"

Companion requirement: `docs/spec.md#spec56--full-pipeline-manual-acceptance`
Companion story: `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md`
Companion history lane: `docs/ui-scout.md` and `docs/ui-scout/`

This lane is intentionally separate from `docs/scout/`, which is reserved for
external-source research.

## Canonical Fixture

- Use `tests/fixtures/ingest_inputs/open_frequency_short.fountain`
- Always start from a fresh project
- Keep this fixture short on purpose: it should exercise the path, not become a
  cost or latency benchmark

## What This Run Must Prove

- **Works**: the normal UI can carry a fresh project from intake through the
  current honest downstream boundary without route hunting, dev-only shortcuts,
  contradictory state, or dead ends
- **Feels excellent**: next actions are obvious, status is honest, copy and
  layout feel calm and elegant, and the user still feels like they are working
  with their story rather than administering a pipeline

## Rules

- Use the normal surfaced UI only
- Do **not** start from raw artifact pages, `/run`, or manual pipeline controls
  unless the normal UI itself deliberately routes you there
- Run the full walkthrough on desktop
- Reuse the same project for a mobile spot-check of Home plus one representative
  scene/downstream surface
- Every run must produce a dated report in `docs/ui-scout/` and update
  `docs/ui-scout.md`
- Every run must also update `docs/methodology/state.yaml` `ui_scout` so
  compile-time freshness stays honest
- If the honest shipped boundary changes, update this runbook and the canonical
  fixture in the same diff

## Exact Surfaced Path To Walk Today

Run this sequence exactly unless the shipped UI changes in the same diff.

1. Start at `/`, then go to `/new`.
   Pass if the New Project flow feels like the obvious first move rather than a
   developer-only intake screen.
2. Create a fresh project from `open_frequency_short.fountain`.
   Expected result: project route resolves to `/open-frequency`, the screenplay
   is visible immediately, and the first chat CTA is `Break Down Script`.
3. From `/open-frequency`, click `Break Down Script`.
   Pass if the UI can carry the whole `mvp_ingest` path without requiring
   recipe/module reasoning or a detour into raw run details.
4. Stay on `/open-frequency` until the script pass finishes.
   Expected result: surfaced script progress updates make sense from Home,
   "Run Details" stays optional, and the project is ready to continue into the
   surfaced scene routes without requiring a deeper world-building detour first.
5. Visit the surfaced desktop routes in this order:
   `/open-frequency`
   `/open-frequency/intent`
   `/open-frequency/scenes`
   `/open-frequency/characters`
   `/open-frequency/locations`
   `/open-frequency/inbox`
6. From `/open-frequency/scenes`, open `scene_001` and verify the scene
   workspace plus the current downstream tabs:
   `/open-frequency/scenes/scene_001`
   `/open-frequency/scenes/scene_001?tab=shots`
   `/open-frequency/scenes/scene_001?tab=storyboard`
   `/open-frequency/scenes/scene_001?tab=render`
   From the surfaced Render panel, run `Run Render for Current Scene`.
   Pass if the scene workspace remains usable, the downstream tabs are reachable
   through surfaced navigation, the Render tab stays honest about warnings vs.
   blockers while auto-building minimal prerequisites when appropriate, and the
   same panel then exposes `Prompt Detail`, `Video Detail`, and
   `Validation Detail` for the resulting scene render.
7. Spot-check the same project on mobile at minimum on:
   `/open-frequency`
   `/open-frequency/scenes/scene_001?tab=render`
8. Record the run in `docs/ui-scout/<date>-<project>-<env>.md`, update
    `docs/ui-scout.md`, update `docs/methodology/state.yaml` `ui_scout`, and
    rerun `pnpm methodology:compile`.
    If the honest boundary changes, update this runbook in the same diff as the
    report.

## Pass / Fail Questions

- Could a first-time filmmaker tell what to do next at each step?
- Did any screen feel like pipeline administration instead of story work?
- Did any readiness or status indicator lie, hide a blocker, or create
  self-inflicted attention debt?
- Were there dead ends, forced route hunting, or raw-artifact detours?
- Did the UI remain polished and calm rather than cluttered or confusing?
- Did browser console or page errors appear on the walked path?

## Record The Result

- Save screenshots or equivalent evidence for the start surface, a
  mid-pipeline surface, and the furthest downstream surface reached
- Write down the exact blocker or quality failure, including whether it is
  primarily functional or polish/trust
- Record the result in `docs/ui-scout/` and update `docs/ui-scout.md`
- If a product defect is discovered, create or link the focused follow-up story
  from the report instead of hiding the issue inside Story 156
