---
id: "173"
title: "Stale Coverage Graph Node Removal"
status: "Done"
priority: "Medium"
ideal_refs:
  - "Execution Ideal"
  - "R12 (transparency & control)"
  - "R15 (changes propagate through the dependency graph)"
spec_refs:
  - "spec:6.1"
  - "spec:6.1.1"
  - "spec:6.1.4"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "025"
category_refs:
  - "spec:6"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
roadmap_tags:
  - "architecture"
  - "cleanup"
  - "pipeline-graph"
  - "shot-planning"
legacy_system: ""
---

# Story 173 — Stale Coverage Graph Node Removal

**Priority**: Medium
**Status**: Done
**Ideal Refs**: Execution Ideal; R12 (transparency & control); R15 (changes propagate through the dependency graph)
**Spec Refs**: spec:6.1; spec:6.1.1; spec:6.1.4
**ADR Refs**: ADR-002 (Goal-Oriented Navigation); ADR-003 (Film Elements / Shot Planning consumes concern groups directly)
**Depends On**: Story 025 (Shot Planning)

## Goal

Remove the stale `coverage` / `coverage_report` node from the surfaced pipeline
graph so CineForge's operator-visible dependency map matches the actual shipped
shot-planning contract. Story 025 explicitly kept coverage adequacy inside
`CoverageStrategy` on `shot_plan` and rejected a separate coverage artifact, but
`src/cine_forge/pipeline/graph.py` still exposes `coverage` as a second home in
the `shots` phase and the UI renders that graph directly. This story closes that
truth gap without reopening shot-planning behavior, export formatting, or a
broader graph redesign.

## Acceptance Criteria

- [x] `src/cine_forge/pipeline/graph.py` no longer defines a separate
      `coverage` node or `coverage_report` artifact on the shipped `shots`
      path, and the `shots` phase remains honestly represented by the
      `shot_planning` capability alone unless implementation proves a real
      separate runtime owner still exists.
- [x] No surfaced graph consumer continues teaching the obsolete split:
      representative API output and the normal pipeline bar route both show the
      `shots` phase without a parallel `Coverage Analysis` node, and
      `shot_planning` remains available/completed using the same real artifact
      signals as before.
- [x] Focused regression coverage locks the contract from Story 025:
      tests fail if a parallel `coverage` / `coverage_report` node is
      reintroduced without an explicit story/ADR-level justification.
- [x] The implementation stays surgical inside already-large owners (`graph.py`,
      `test_pipeline_graph.py`, optional surfaced-path consumers), and if code
      inspection reveals a live runtime consumer of `coverage_report` beyond the
      graph decoration, the story stops and records that blocker instead of
      deleting only the visible symptom.

## Out of Scope

- Reopening `shot_plan` schema design, coverage-adequacy logic, or export
  formatting
- Any new `coverage_report` artifact, new pipeline stage, or broader capability
  graph redesign
- Storyboard, render, previz, or final-output behavior changes
- Persona/template work in the pipeline bar beyond what is strictly required to
  stop surfacing the stale node

## Approach Evaluation

- **Simplification baseline**: A single LLM call cannot solve this story. The
  problem is deterministic architecture drift: Story 025 rejected a parallel
  coverage artifact, but the shipped graph still surfaces one.
- **AI-only**: Wrong fit. An LLM can help spot the mismatch, but the fix is a
  code/documentation cleanup in the canonical capability graph and its tests.
- **Hybrid**: Reasonable only in the verification sense. Use code for the graph
  cleanup and repo-native tests/browser verification to prove the surfaced path
  is honest.
- **Pure code**: Strong default. This is graph ownership and UI/API truth, not
  creative reasoning.
- **Repo constraints / ADRs**: ADR-002 makes the capability graph the single
  source of truth for both AI guidance and UI progress. Story 025 and
  `spec:6.1.1` keep coverage adequacy inside `CoverageStrategy`, while
  `spec:6.1.4` says export formatting is a presentation concern, not a pipeline
  stage. ADR-003 keeps shot planning as the concern-group consumer; nothing
  newer reintroduces a separate coverage stage.
- **Existing patterns to reuse**: Story 172's methodology-truth cleanup
  discipline, the existing `compute_pipeline_graph()` / `PipelineBar` dynamic
  path, and focused unit assertions in `tests/unit/test_pipeline_graph.py`
  rather than a second manual graph registry.
- **Eval**: Repo-native proof only. The discriminating checks are focused graph
  tests, targeted API/browser verification of the surfaced pipeline bar, and
  `make check-size` to ensure the cleanup stays surgical.

## Tasks

- [x] Re-read Story 025, ADR-002, ADR-003, and the current pipeline graph/API/UI
      path to confirm `coverage` is only a stale surfaced second home and not a
      real runtime owner.
- [x] Remove the `coverage` / `coverage_report` node from
      `src/cine_forge/pipeline/graph.py`, including any coupled phase membership
      or status logic, while keeping `shot_planning` as the single shipped
      shots-path capability.
- [x] Add or update focused regression coverage in
      `tests/unit/test_pipeline_graph.py` so the `shots` phase contract
      explicitly excludes a parallel `coverage` node and still preserves real
      `shot_planning` status behavior.
- [x] Run `make check-size` before finalizing to keep edits narrow inside the
      already-large graph/test owners and record any remaining watchpoints
      honestly.
- [x] Verify the surfaced pipeline path end to end on a representative project
      state: API graph response plus desktop/mobile pipeline bar rendering. If a
      narrow UI or API guard is required, keep it in the same story.
- [x] Check whether the chosen implementation makes any existing code, helper
      paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): not applicable; no UI source files changed in this story
- [x] If agent tooling or project instructions are touched: not applicable by
      default; run `make skills-check` only if that scope changes
- [x] If story metadata, ADR metadata, or methodology state changes:
      `pnpm methodology:compile`
- [x] If evals or goldens are changed: not expected; if they are, run
      `/improve-eval` or equivalent mismatch investigation, classify all
      mismatches, and update `docs/evals/registry.yaml`
- [x] If UI is touched: verify the changed flow with browser tools in desktop
      and mobile views when possible (screenshots + console check); if blocked,
      follow `docs/runbooks/browser-automation-and-mcp.md` and record the
      blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first
        preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session
        understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will
        handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human
      summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

> If this story is `Blocked`, replace the `N/A` values below with concrete
> blocker truth and rewrite `## Plan` around the unblock path or blocker
> reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `src/cine_forge/pipeline/graph.py` owns the shipped
  capability graph definition. This story should delete the stale `coverage`
  second home there rather than layering exceptions into
  `src/cine_forge/api/service.py` or the UI.
- **Data contracts**: The existing graph response shape
  (`compute_pipeline_graph()` on the backend and `PipelineGraphNode` /
  `PipelineGraphPhase` / `PipelineGraphResponse` in `ui/src/lib/types.ts`) stays
  stable. No new cross-layer schema is expected; this story changes node
  membership/truth, not payload structure.
- **File sizes**: `src/cine_forge/pipeline/graph.py` is `717` lines and
  `tests/unit/test_pipeline_graph.py` is `664` lines, so edits must stay
  surgical. Fallback consumers are also large:
  `src/cine_forge/api/service.py` is `1302` lines and
  `ui/src/components/AppShell.tsx` is `838` lines. Avoid growing those files
  unless verification proves a narrow coupled fix is required.
- **Decision context**: Reviewed `docs/spec.md` (`spec:6.1`, `spec:6.1.1`,
  `spec:6.1.4`), `docs/methodology/state.yaml` architecture-audit state, Story
  025, ADR-002, and ADR-003. No newer CineForge-local ADR was found that
  re-justifies a separate coverage capability.

## Files to Modify

- `docs/stories/story-173-stale-coverage-graph-node-removal.md` — planning
  artifact, execution log, and validation evidence
- `src/cine_forge/pipeline/graph.py` — remove the stale `coverage` node and the
  `shots` phase reference while keeping `shot_planning` as the sole shipped
  shots capability (`717`)
- `tests/unit/test_pipeline_graph.py` — add or adjust focused assertions so the
  graph contract fails if a parallel `coverage` node returns without explicit
  justification (`664`)
- `docs/stories.md` — generated output after `pnpm methodology:compile`
- `docs/build-map.md` — generated output after `pnpm methodology:compile`
- `docs/methodology/graph.json` — generated output after
  `pnpm methodology:compile`
- `src/cine_forge/api/service.py` — fallback-only touchpoint if representative
  API verification proves the graph route has stale node-specific logic (`1302`)
- `ui/src/components/PipelineBar.tsx` or `ui/src/components/AppShell.tsx` —
  fallback-only touchpoints if desktop/mobile verification proves the UI assumes
  a two-node `shots` phase instead of rendering dynamically (`379`, `838`)

## Redundancy / Removal Targets

- The obsolete `coverage` node and `coverage_report` artifact type on the
  surfaced pipeline graph
- Any focused tests or docs that still teach a separate `Coverage Analysis`
  stage on the shipped shots path
- Any surfaced UI copy or phase summary that implies shot planning and coverage
  analysis are separate shipped capabilities

## Notes

This is a new story rather than a reopen of Story 025 because Story 025 already
made the correct product/architecture call. The remaining problem is stale
surface truth discovered by the 2026-04-18 `generation_and_visualization`
architecture audit: the operator-visible graph still teaches a second capability
that the real shot-planning contract explicitly rejected.

If implementation discovers a real runtime consumer of `coverage_report` outside
the graph decoration, stop and record that evidence instead of deleting only the
UI symptom. The story's job is to remove a stale second home, not to hide a live
one.

## Plan

### Alignment and baseline

- This is a `spec:6` simplification story. It does not add capability; it
  restores honesty to the shipped dependency graph so the operator-visible
  pipeline aligns with the actual shot-planning contract.
- Baseline evidence from the audit:
  - Story 025 says a separate `coverage_report` stage/artifact is not justified
    and adequacy belongs inside `CoverageStrategy`.
  - `src/cine_forge/pipeline/graph.py` still defines `coverage` with
    `artifact_types=["coverage_report"]` and still includes it in the `shots`
    phase.
  - `src/cine_forge/api/service.py` returns that graph and
    `ui/src/components/AppShell.tsx` renders it through `PipelineBar`, so the
    stale node is operator-visible, not dead code.
- Simplification rule: delete the stale second home if code inspection confirms
  it is only surfaced graph drift. Do not widen this into a broader capability
  graph rewrite.

### Structural health check

- Large-file watchpoints on this slice:
  - `src/cine_forge/pipeline/graph.py` — `717`
  - `tests/unit/test_pipeline_graph.py` — `664`
  - `src/cine_forge/api/service.py` — `1302`
  - `ui/src/components/AppShell.tsx` — `838`
- Guardrail: keep the implementation inside `graph.py` plus focused graph tests
  unless verification proves a narrow consumer fix is required. Do not add new
  abstraction layers or graph registries to "clean up" the cleanup story.

### Implementation order

1. Confirm the live seam:
   - Re-read Story 025 and trace `coverage` / `coverage_report` usage across
     `src/` and `ui/src/`.
   - If the only live ownership is the pipeline graph surface, proceed with
     deletion.
2. Remove the stale graph node:
   - Delete the `coverage` node definition and remove it from the `shots`
     phase.
   - Keep `shot_planning` status semantics and prerequisites unchanged unless
     tests prove the graph currently depends on the stale node in some hidden
     way.
3. Lock the contract:
   - Extend `tests/unit/test_pipeline_graph.py` with explicit assertions that
     `coverage` is absent and `shot_planning` remains the sole `shots` node.
4. Validate the surfaced path:
   - Run targeted graph tests first, then required backend checks, then
     `pnpm methodology:compile`.
   - Verify the pipeline bar on representative desktop and mobile states with
     clean console output.

### Stop condition

- If the build uncovers a real consumer or artifact flow that still depends on
  `coverage_report`, stop and convert the story into an explicit re-justification
  or broader cleanup path. Deleting the visible node while leaving a hidden
  runtime owner alive would make the graph less honest, not more.

## Work Log

20260418-2109 — story_created: created Pending follow-up from the
generation-and-visualization architecture audit, evidence is Story 025's
rejection of a parallel `coverage_report` artifact versus the still-surfaced
`coverage` node in `src/cine_forge/pipeline/graph.py`, next step is a surgical
graph/test cleanup that either deletes the stale second home or records a real
blocker if one still exists.

20260418-2124 — exploration_notes: confirmed the blast radius is still narrow.
`coverage_report` appears only in `src/cine_forge/pipeline/graph.py`, so there
is no hidden runtime artifact owner to preserve before deleting the surfaced
node. Files that will change: `docs/stories/story-173-stale-coverage-graph-node-removal.md`,
`src/cine_forge/pipeline/graph.py`, `tests/unit/test_pipeline_graph.py`, and
generated methodology outputs. Files at risk of breaking: the pipeline graph API
route in `src/cine_forge/api/service.py`, the rendered pipeline bar in
`ui/src/components/AppShell.tsx` / `ui/src/components/PipelineBar.tsx`, and any
graph assumptions locked in `tests/unit/test_pipeline_graph.py`. Decision docs
consulted: Story 025, ADR-002, ADR-003, `spec:6.1`, `spec:6.1.1`, and
`spec:6.1.4`. Pattern to follow: keep the truth fix in the canonical graph
definition plus focused graph tests rather than layering UI/service exceptions.
Risk: `graph.py` (`717`) and `test_pipeline_graph.py` (`664`) are already large,
so the change must stay surgical. Next step is to flip the story to `In Progress`,
compile methodology surfaces, then remove the stale node and lock the contract
with tests.

20260418-2129 — implementation: removed the stale `coverage` node from
`src/cine_forge/pipeline/graph.py`, removed the extra `shots` phase membership,
and added focused regression coverage in `tests/unit/test_pipeline_graph.py`
that locks `shots` to `["shot_planning"]` and fails if `Coverage Analysis`
reappears in computed graph output. Evidence: the only live
`coverage_report` reference before the edit was the graph definition itself, so
the cleanup deleted a surfaced second home rather than hiding a live runtime
artifact path. Next step was targeted graph tests, then full backend/runtime
verification.

20260418-2129 — verification_static: targeted and full backend checks passed.
Evidence:
- `.venv/bin/python -m pytest tests/unit/test_pipeline_graph.py -q` → pass
- `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  → 753 passed, 168 deselected, 1 pre-existing pytest mark warning
- `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  → all checks passed
- `make check-size` after implementation still flags the known large owners, but
  the touched files stayed surgical: `src/cine_forge/pipeline/graph.py` is now
  `709` lines (down from `717`), `tests/unit/test_pipeline_graph.py` is `676`
  lines, and no fallback edit was needed in `api/service.py` or the UI. Next
  step was runtime proof on the real app route.

20260418-2129 — runtime_verify: verified the shipped API and UI route with a
fresh project created through `/api/projects/new` under the normal backend
workflow. Evidence:
- `/api/health` returned `{\"status\": \"ok\", \"version\": \"2026.04.18-02\"}`
- `/api/projects/{project_id}/pipeline-graph` returned `shots.total_count == 1`,
  `shots.implemented_count == 1`, and no node with id `coverage`
- Desktop browser check on `http://127.0.0.1:5174/{project_id}` hovered the
  `Shots` phase, showed `Shot Planning`, did not show `Coverage Analysis`, and
  produced a clean console; screenshot saved at
  `/tmp/story-173-pipeline-desktop.png`
- Mobile browser check on the same route tapped the `Shots` phase sheet, showed
  `Shot Planning`, did not show `Coverage Analysis`, and produced a clean
  console; screenshot saved at `/tmp/story-173-pipeline-mobile.png`
- The temporary runtime-proof project under `output/story-173-runtime-*` was
  removed after verification so the story does not leave a new operator-facing
  project behind. Next step is to sync the story/generated methodology surfaces
  and hand off to `/validate`.

20260418-2133 — docs_sync: refreshed the generated planning surfaces after the
implementation evidence landed and cleared the now-stale
`generation_and_visualization` architecture-audit open finding in
`docs/methodology/state.yaml`. Evidence:
- `pnpm methodology:compile` rewrote `docs/stories.md`,
  `docs/build-map.md`, and `docs/methodology/graph.json`
- `pnpm methodology:check` passed once rerun sequentially after compile
- the audit state now records Story 173 in `recent_story_refs`, keeps the known
  oversized watchpoints, and no longer claims the deleted `coverage` node still
  exists. Next step is implementation handoff to `/validate 173`.

20260418-2139 — validation: reran the full validation pass on the local Story
173 delta and the implementation is ready to close. Fresh evidence:
- `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  → 753 passed, 168 deselected, 1 pre-existing pytest mark warning
- `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  → pass
- `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_pipeline_graph.py -q`
  → pass
- `pnpm --dir ui run lint` → pass (with one existing npm config warning only)
- `cd ui && npx tsc -b` → pass
- `pnpm methodology:check` → pass
- fresh browser verification on a project created through `/api/projects/new`
  confirmed the API graph and both desktop/mobile pipeline-bar surfaces show
  `Shot Planning` only, with no `Coverage Analysis`, and clean console output;
  screenshots saved at `/tmp/story-173-validate-desktop.png` and
  `/tmp/story-173-validate-mobile.png`
- local unrelated edits still exist in `docs/deploy-log.md`, `docs/inbox.md`,
  and `.codex/`; validation for this story was scoped to the Story 173 slice.
Recommended next step: `/mark-story-done 173`.

20260418-2145 — completion: marked Story 173 done after validation confirmed
the stale `coverage` / `coverage_report` second home is gone from the shipped
graph, targeted/full checks passed, and representative desktop/mobile browser
verification stayed clean on a fresh project created through the normal API
route. `docs/methodology/state.yaml` now records the
`generation_and_visualization` audit as clean with Story 173 in the recent
history. Recommended next step: `/check-in-diff`.
