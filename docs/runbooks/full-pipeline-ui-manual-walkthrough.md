# Full-Pipeline UI Manual Walkthrough

Short recurring product-truth check for the full surfaced CineForge UI path.
This runbook exists because browser smoke and targeted screenshots are not the
same thing as "can a real person take a fresh project through the pipeline, and
does the UI still feel polished and obvious while they do it?"

Companion requirement: `docs/spec.md#spec56--full-pipeline-manual-acceptance`
Companion story: `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md`

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
- If the honest shipped boundary changes, update this runbook and the canonical
  fixture in the same diff

## Minimum Path To Walk

1. Create a new project from `open_frequency_short.fountain`.
   Pass if the project name is clean, the screenplay renders immediately, and
   the first obvious action is clear without developer vocabulary.
2. Start the default intake path from Home.
   Fail if you need to reason about recipes, module names, or hidden pages to
   continue the golden path.
3. Let the first pass finish.
   Pass if progress makes sense from the surfaced UI alone and "Run Details" is
   optional rather than required to understand what happened.
4. Continue via the surfaced "go deeper / next step" path.
   Pass if the UI makes the next action obvious and honest.
5. Review the primary story surfaces on the resulting project:
   `Home/Script`, `Scenes`, `Characters`, `Locations`, `World/Intent`, and
   `Inbox` if present.
6. Open one representative scene workspace.
   Pass if readiness, direction, and shot-planning surfaces are usable and the
   state is honest about what is missing vs inferred.
7. Continue to the furthest stable downstream surface the normal UI exposes
   today: storyboard, previz, generation, export, or equivalent.
   If a later stage is intentionally unavailable, the UI must say so honestly
   and point to the real prerequisite instead of stranding the user.
8. Spot-check the same project on mobile at minimum on Home and one
   representative scene/downstream surface.

## Pass / Fail Questions

- Could a first-time filmmaker tell what to do next at each step?
- Did any screen feel like pipeline administration instead of story work?
- Did any readiness or status indicator lie, hide a blocker, or create
  self-inflicted attention debt?
- Were there dead ends, forced route hunting, or raw-artifact detours?
- Did the UI remain polished and calm rather than cluttered or confusing?
- Did browser console or page errors appear on the walked path?

## Record The Result

- Save screenshots for the start surface, a mid-pipeline surface, and the
  furthest downstream surface reached
- Write down the exact blocker or quality failure, including whether it is
  primarily functional or polish/trust
- Until a dedicated reporting home exists, append the result to Story 156's work
  log or the active follow-up story that owns the discovered defect
