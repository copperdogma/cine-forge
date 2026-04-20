---
id: "177"
title: "OpenTimelineIO Narrative Interchange Export"
status: "Done"
priority: "High"
ideal_refs:
  - "R8 (professional-grade production artifacts)"
  - "R9 (export to professional formats)"
  - "R12 (transparency & control)"
  - "vision-level preference: Export-first, not edit"
spec_refs:
  - "spec:6.1.4"
  - "spec:7"
  - "spec:10"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "130"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "export"
  - "interchange"
  - "otio"
  - "narrative-metadata"
  - "follow-up-from-130"
legacy_system: ""
---

# Story 177 — OpenTimelineIO Narrative Interchange Export

**Priority**: High
**Status**: Done
**Ideal Refs**: R8 (professional-grade production artifacts), R9 (export to professional formats), R12 (transparency & control), vision-level preference: Export-first, not edit
**Spec Refs**: spec:6.1.4, spec:7, spec:10
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 130

## Goal

Story 130 proved the first narrative-aware interchange path by shipping shared
`NarrativeInterchangeExport` payloads plus an `FCPXML` carrier. The remaining
export-fidelity gap is not “another XML tweak”; it is adding an
OpenTimelineIO-backed carrier so CineForge can hand off the same narrative
timeline truth to OTIO-native tools and Resolve-oriented workflows without
forking metadata assembly or falling back to UI-only export logic. This story is
the next honest continuation of the export line because Story 130 explicitly
deferred OTIO until the shared payload was stable, and that payload now exists.

## Acceptance Criteria

- [x] CineForge can export an `.otio` timeline through the headless backend path
      (CLI + API, with UI as a thin client) using the existing shared
      `NarrativeInterchangeExport` payload rather than a second carrier-specific
      metadata builder.
- [x] The emitted OTIO timeline preserves the current narrative annotation
      surface from Story 130 at the carrier boundary: scene boundaries, beat /
      emotional annotations, character entrance / exit notes, and upstream refs
      or equivalent clip/marker metadata survive deterministic round-trip
      validation through the OTIO library.
- [x] `FCPXML` and `OTIO` stay in parity on the shared payload surface: if OTIO
      needs a new field, that field is added to the canonical export schema and
      both carriers consume it. No emitter-specific duplicate metadata assembly
      remains.
- [x] The export surfaces stay honest: Export Modal, API, and CLI expose OTIO
      through the same backend-owned flow, disable it when timeline substrate is
      missing, and browser verification covers desktop + mobile export-modal
      behavior with clean console output.
- [x] Focused regression coverage exists for OTIO serialization, OTIO
      round-trip parsing, shared-payload parity, and route / CLI / UI wiring,
      and Story 130’s existing `FCPXML` coverage stays green after the new
      carrier lands.

## Out of Scope

- Reworking call-sheet formatting or adding the production-logistics metadata
  follow-up Story 130 explicitly left out
- Adding `AAF` and `EDL` in the same slice
- Building timeline editing, trim UI, or any NLE-like in-app workflow
- Replacing `FCPXML`; this story adds a second carrier, not a migration away
  from the first one
- AI eval work, prompt tuning, or runtime media-validation changes unrelated to
  interchange export

## Approach Evaluation

- **Simplification baseline**: First prove the current
  `NarrativeInterchangeExport` payload is already rich enough for OTIO with only
  a thin carrier adapter. If that baseline holds, the story should avoid
  widening schema surface just because a new dependency is involved.
- **AI-only**: Wrong fit. Interchange emission, round-trip parsing, and carrier
  compatibility are deterministic trust surfaces, not a reasoning task.
- **Hybrid**: Possible only for optional human-readable note phrasing layered on
  top of deterministic metadata. That is not the first need here.
- **Pure code**: Strong default. The likely work is dependency-backed emitter
  plumbing, deterministic round-trip validation, and thin route / CLI / UI
  wiring.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced export behavior
  instead of hidden fallback. ADR-003 keeps timeline / film artifacts
  story-derived and headless-first. Story 130 already landed the shared payload
  plus `FCPXML`, and explicitly called OTIO the credible next carrier once the
  metadata model stabilized. The repo currently has no `OpenTimelineIO`
  dependency, so this story introduces a real new dependency / consumer seam
  rather than a cosmetic same-carrier tweak.
- **Existing patterns to reuse**: Story 130, `src/cine_forge/schemas/export_interchange.py`,
  `src/cine_forge/export/interchange_fcpxml.py`,
  `src/cine_forge/api/routers/export.py`, `src/cine_forge/cli.py`,
  `ui/src/lib/api/exports.ts`, `ui/src/components/ExportModal.tsx`, and
  `tests/unit/test_export_interchange.py`.
- **Eval**: No model eval by default. The distinguishing evidence is
  deterministic OTIO round-trip coverage on seeded fixtures plus API / CLI /
  browser export smoke. If OTIO parity reveals a schema gap, the acceptance
  test is shared-payload parity across both carriers, not a raw “file exists”
  check.

## Tasks

- [x] Measure the simplification baseline by proving whether the current
      `NarrativeInterchangeExport` payload can feed an OTIO carrier without
      schema changes; record any missing fields before touching emitters.
- [x] Add the OTIO dependency and a focused OTIO emitter / loader path that
      consumes the shared payload instead of assembling OTIO metadata directly
      from timeline artifacts.
- [x] Extend API, CLI, and Export Modal wiring so OTIO uses the same backend
      export path and honest timeline-presence gating as `FCPXML`.
- [x] Add focused regression coverage for OTIO serialization, OTIO round-trip
      parsing, shared-payload parity with `FCPXML`, and route / CLI / UI export
      wiring.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: not expected; no agent-tooling changes planned
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: not expected; no AI eval or golden change is planned unless OTIO validation exposes a missing deterministic export benchmark
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: Export logic should stay in `src/cine_forge/export/`
  with a new focused `interchange_otio.py` sibling to
  `interchange_fcpxml.py`. API / CLI / UI should remain thin wrappers over that
  backend export path instead of adding carrier logic inline.
- **Data contracts**: `src/cine_forge/schemas/export_interchange.py` is already
  the canonical carrier-independent narrative export model. If OTIO needs a new
  field, add it there first and keep both carriers in parity; do not introduce a
  second OTIO-specific metadata DTO unless the baseline proves the shared model
  fundamentally insufficient.
- **File sizes**: `make check-size` flags `src/cine_forge/api/routers/export.py`
  (`440`) and `tests/unit/test_export_interchange.py` (`438`) as large enough
  to require narrow edits. Other likely touch points are `pyproject.toml` (`57`),
  `src/cine_forge/cli.py` (`188`), `ui/src/components/ExportModal.tsx` (`381`),
  `ui/src/lib/api/exports.ts` (`226`),
  `src/cine_forge/export/interchange_fcpxml.py` (`310`), and
  `src/cine_forge/schemas/export_interchange.py` (`75`). Prefer a new focused
  emitter file over widening the already-large router or test harness with
  carrier-specific branching.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`,
  `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`,
  `docs/build-map.md`, ADR-002, ADR-003, Story 130, the current export router /
  CLI / UI, `src/cine_forge/export/interchange_fcpxml.py`, and
  `src/cine_forge/schemas/export_interchange.py`. No more specific ADR governs
  OTIO carrier choice after search.

## Files to Modify

- `docs/stories/story-177-otio-narrative-interchange-export.md` — story scope,
  build handoff, and evidence log
- `pyproject.toml` — add the OTIO dependency if the simplification baseline
  confirms a dependency-backed emitter is the honest path (`57`)
- `src/cine_forge/export/interchange_otio.py` — new focused OTIO emitter /
  round-trip helper (new)
- `src/cine_forge/export/interchange_fcpxml.py` — only if shared helper
  extraction or carrier-parity fixes are needed (`310`)
- `src/cine_forge/schemas/export_interchange.py` — extend the canonical payload
  only if OTIO exposes a real schema gap (`75`)
- `src/cine_forge/api/routers/export.py` — add the OTIO export route while
  keeping carrier logic thin (`440`)
- `src/cine_forge/cli.py` — expose `otio` as a headless export format (`188`)
- `ui/src/lib/api/exports.ts` — OTIO URL / filename mapping and download helper
  parity (`226`)
- `ui/src/components/ExportModal.tsx` — surface OTIO honestly in the existing
  export UI (`381`)
- `tests/unit/test_export_interchange.py` — OTIO serialization, round-trip, and
  shared-payload parity coverage (`438`)

## Redundancy / Removal Targets

- Any carrier-specific narrative metadata assembly duplicated outside the shared
  `NarrativeInterchangeExport` payload
- Any user-facing export copy that implies `FCPXML` is the only narrative-aware
  interchange path once OTIO lands
- Any ad hoc OTIO round-trip helper logic duplicated between tests and the new
  emitter module

## Notes

- Anti-fragmentation check: Story 130 is the correct parent line and was
  reviewed before minting a new ID. A fresh story is still justified here
  because OTIO adds a new dependency and a different consumer-validation seam,
  not just another small same-carrier polish pass.
- Story 130 explicitly recorded OTIO as the credible next carrier once the
  shared metadata model stabilized. This story picks up that deferred line
  rather than reopening call-sheet or first-carrier work that is already done.
- The literal Ideal quality bar names OpenTimelineIO and DaVinci Resolve import.
  This story does not promise a full Resolve automation path up front, but it
  should leave the repo with a real OTIO artifact plus a deterministic round-trip
  proof that future Resolve validation can build on.

## Plan

1. Baseline the current shared payload against OTIO expectations before adding
   any schema surface.
   Done looks like: the build can say whether OTIO is only a carrier adapter or
   whether the canonical payload is still missing real export facts.

2. Add a focused OTIO emitter and round-trip proof through the backend export
   path.
   Done looks like: API and CLI can emit a valid `.otio` file that parses back
   through the OTIO library with CineForge narrative markers / metadata intact.

3. Surface OTIO in the existing export UI without forking behavior from the
   backend path.
   Done looks like: Export Modal uses the same gating and download semantics as
   `FCPXML`, with honest disabled states when timeline substrate is missing.

4. Lock parity and cleanup.
   Done looks like: shared-payload parity tests cover both carriers, and any
   duplicate carrier-specific metadata assembly is removed or recorded as a
   concrete follow-up.

## Work Log

20260419-1531 — story-created: triage follow-through packaged the next honest
`spec:6` / `spec:7` export-fidelity continuation after checking Story 130, Story
166, Story 167, Story 170, ADR-002, ADR-003, `docs/ideal.md`, `docs/spec.md`,
`docs/methodology/state.yaml`, `docs/build-map.md`, and the current export /
validation substrate. Anti-fragmentation result: this remains the same export
line as Story 130, but a new story is justified because OTIO adds a new
dependency-backed carrier and consumer-validation seam rather than just another
same-carrier polish pass. Evidence: Story 130 explicitly deferred OTIO until
the shared `NarrativeInterchangeExport` model existed; current repo now has that
model plus `FCPXML`, but still no OTIO dependency or carrier. Next step:
`/build-story 177`.

20260419-1622 — exploration-notes: moved Story 177 to `In Progress` after
rechecking the current implementation seams. Files expected to change:
`pyproject.toml`, a new `src/cine_forge/export/interchange_otio.py`, thin OTIO
wiring in `src/cine_forge/api/routers/export.py`, `src/cine_forge/cli.py`,
`ui/src/lib/api/exports.ts`, `ui/src/components/ExportModal.tsx`, and focused
coverage in `tests/unit/test_export_interchange.py`. Risk surfaces: export route
copy can drift from CLI/UI, and the existing router / test file are already
large enough that edits must stay narrow. ADR check: ADR-002 and ADR-003 still
support backend-owned, headless-first export; no newer ADR narrowed OTIO
ownership. Baseline result: the current `NarrativeInterchangeExport` payload
already carries scene boundaries, beat/emotional annotations, character
entrance/exit notes, timeline refs, and deterministic timing, so OTIO should
land as a carrier adapter rather than a second metadata builder unless the
library itself exposes a concrete schema gap. Evidence: current repo has
`FCPXML` on the shared payload path, no `opentimelineio` dependency in
`pyproject.toml`, and `.venv` confirms `importlib.util.find_spec('opentimelineio')`
returns `None`. Next step: add the dependency and implement the OTIO emitter /
round-trip path on top of the existing payload.

20260419-1758 — implementation: added `opentimelineio>=0.18.1` to
`pyproject.toml`, introduced `src/cine_forge/export/interchange_otio.py` as a
focused OTIO carrier on top of the existing `NarrativeInterchangeExport`
payload, and kept parity work narrow by wiring the new format through the
existing backend/UI seams instead of creating a second metadata builder. The
new carrier serializes scene segments to OTIO clips, stores canonical
scene/annotation payloads in OTIO metadata, preserves the narrative annotation
surface as OTIO markers, and adds a small parse helper so route/CLI/runtime
proofs use the same library-backed round-trip path. API / CLI / UI result:
`/export/otio`, `cine_forge export --format otio`, and Export Modal project
data now expose OTIO alongside `FCPXML`, while no-timeline projects still block
the interchange buttons honestly. Redundancy result: no new duplicate
carrier-specific metadata assembly was introduced; router duplication shrank via
one shared interchange-payload loader helper. Environment note: the first OTIO
install failed because active `CONDA_*` variables pulled CMake toward a stale
`pybind11` include path under `/Users/cam/miniconda3`; reinstalling with
`CONDA_*` unset and CMake rooted at the project `.venv` succeeded. Next step:
run full verification and record runtime/browser evidence.

20260419-1819 — verification: focused OTIO coverage passed first
(`PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_export_interchange.py -q`),
then the required repo checks stayed green:
`make test-unit PYTHON=.venv/bin/python` (`762 passed, 173 deselected, 1
pre-existing pytest mark warning`), `.venv/bin/python -m ruff check src/
tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run
build`, and `pnpm methodology:check` (warning only: existing
`api_service_and_operator_console` audit debt; outputs current). Runtime smoke:
`curl -sf http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\"...}`;
`curl -sf http://127.0.0.1:8000/api/projects/story-132-shot-plan-ui-clean/export/otio`
produced an OTIO file that parsed back through `parse_otio()` as a single-track
timeline with expected markers (`Entrance: MARA`, `Scene 1`, `Emotion: tense`,
etc.); `curl` against `liberty-and-church-4/export/otio` returned the expected
honest `404 Timeline not found for project export`. Browser evidence via
Playwright on the normal local app path: desktop project export on
`/story-132-shot-plan-ui-clean` showed OTIO + `FCPXML` in the Project Data tab,
saved screenshot `story-177-export-modal-desktop.png`, and OTIO download
completed as `story-132-shot-plan-ui-clean-timeline.otio` with clean console
(`0` errors / `0` warnings). Mobile verification on the same project saved
`story-177-export-modal-mobile-enabled.png` with the interchange buttons
visible and clean console (`0` errors / `0` warnings). Honest disabled-state
verification on `/liberty-and-church-4` saved
`story-177-export-modal-mobile-disabled.png` and showed both OTIO and `FCPXML`
disabled behind the “Run timeline generation first...” copy. One unrelated
warning appeared on that no-timeline mobile page (`Unknown highlighting tag
transition` from the screenplay viewer); it did not occur on the timeline-backed
mobile export path and was not introduced by the OTIO work. Next step:
handoff for `/validate 177`.

20260419-1837 — validation: reran the required validation-pass checks instead
of relying on the build handoff: `make test-unit PYTHON=.venv/bin/python`
(`762 passed, 173 deselected, 1 pre-existing pytest acceptance-mark warning`),
`.venv/bin/python -m ruff check src/ tests/`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_export_interchange.py -q`,
`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
all passed again. Fresh browser evidence: `/story-132-shot-plan-ui-clean`
showed the Export Modal Project Data flow on desktop and mobile with OTIO +
`FCPXML` enabled and clean console (`0` errors / `0` warnings), and OTIO
download was re-exercised in this validation pass; `/liberty-and-church-4`
showed the honest disabled state with both interchange buttons blocked behind
the “Run timeline generation first…” copy. One console warning remained on that
no-timeline route (`Unknown highlighting tag transition` from the screenplay
 viewer); it is pre-existing and did not reproduce on the timeline-backed export
 route. Validation note: `pnpm methodology:check` initially failed because this
 story edit made `docs/methodology/graph.json` stale; next step is rerun
 `pnpm methodology:compile` and confirm `pnpm methodology:check` goes green
 before `/mark-story-done 177`.

20260419-1849 — validation-rerun: reran the full validation pass again after
the previous report to keep closure evidence fresh. Checks rerun and green in
this pass: `make test-unit PYTHON=.venv/bin/python`
(`762 passed, 173 deselected, 1 pre-existing pytest acceptance-mark warning`),
`.venv/bin/python -m ruff check src/ tests/`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_export_interchange.py -q`,
`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`,
and `pnpm methodology:check` (warning only: existing
`api_service_and_operator_console` audit debt; generated outputs were current
before this log entry). Fresh browser evidence stayed consistent: desktop and
mobile `/story-132-shot-plan-ui-clean` both showed OTIO + `FCPXML` enabled in
Export Modal → Project Data with clean console (`0` errors / `0` warnings), and
OTIO download completed again as `story-132-shot-plan-ui-clean-timeline.otio`.
Fresh no-timeline verification on `/liberty-and-church-4` again showed both
interchange buttons disabled behind the “Run timeline generation first…” copy.
One warning remained on that route only (`Unknown highlighting tag transition`
from the screenplay viewer); it stayed absent on the timeline-backed export
 path and does not appear introduced by Story 177. Fresh API smoke also stayed
 honest: `/api/projects/story-132-shot-plan-ui-clean/export/otio` returned `200`
 and parsed through `parse_otio()` with expected markers (`Entrance: MARA`,
 `Entrance: OWEN`, `Scene 1`, `Emotion: tense`), while
 `/api/projects/liberty-and-church-4/export/otio` returned the expected `404
 Timeline not found for project export`. Next step: rerun
 `pnpm methodology:compile` + `pnpm methodology:check` after this story-log edit,
 then proceed to `/mark-story-done 177`.

20260419-1904 — story-done: closed Story 177 after the fresh validation rerun
confirmed the OTIO carrier, shared-payload parity, API/CLI/UI wiring, and
honest disabled-state behavior all still match the story contract. Completion
evidence for close-out: `make test-unit PYTHON=.venv/bin/python`
(`762 passed, 173 deselected, 1 pre-existing pytest acceptance-mark warning`),
`.venv/bin/python -m ruff check src/ tests/`,
`PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_export_interchange.py -q`,
`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`,
fresh desktop/mobile Playwright verification on
`/story-132-shot-plan-ui-clean`, and API smoke for both the `200` timeline-backed
OTIO path and the honest `404` no-timeline path. One pre-existing screenplay
viewer warning remained isolated to `/liberty-and-church-4` and did not
reproduce on the timeline-backed export flow. Next step: `/check-in-diff`.
