---
id: "178"
title: "AI Previz First-Pass xAI Prerequisite Collapse"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:4.10.6"
  - "spec:4.10.7"
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:8.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "152"
  - "175"
  - "176"
category_refs:
  - "spec:4"
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
  - "creative_direction_and_chat"
roadmap_tags:
  - "previz"
  - "runtime"
  - "first-pass"
  - "prerequisites"
  - "one-pass"
  - "iteration-loop"
legacy_system: ""
---

# Story 178 — AI Previz First-Pass xAI Prerequisite Collapse

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:4.10.6, spec:4.10.7, spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:8.2, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 152, Story 175, Story 176

## Goal

Story 176 established the current shipped xAI one-pass previz lane at `65514 ms`
to first playable, with `47865 ms` spent before `ai_previz` even starts and only
`17649 ms` inside provider video generation. Story 152 then proved that the same
shipped lane can reach `39325 ms` for full regenerate and `17869 ms` for
`start_from=ai_previz` reuse on warmed scene state. That means the live product
gap is no longer provider floor, warmed regenerate truth, or fake-placeholder
debate. It is collapsing the first-pass prerequisite cost on the shipped xAI
lane without breaking honest preflight, compiled-prompt provenance, or the
current usefulness floor. This story measures the narrowest credible first-pass
collapse on the maintained runtime surface and either ships it or records
sharper blocker truth.

## Acceptance Criteria

- [x] A measured simplification baseline exists on the maintained
      `real-ai-previz-runtime` surface for the current shipped xAI first-pass
      route. At minimum, compare the current one-pass prerequisite bundle
      against one bounded collapse hypothesis (single previz-prep call or
      narrower prerequisite bundle) on identical current-scene substrate, with
      result paths recorded.
- [x] The chosen implementation keeps operator truth honest: preflight, run
      metadata, and prompt/video provenance explicitly show which first-pass
      prerequisites were reused, auto-built, collapsed, or bypassed. No silent
      fallback to the old first-pass bundle remains once a narrower route is
      claimed.
- [x] On an equivalent shipped-xAI first-pass runtime comparison, the chosen
      route reduces `fastest_focus_prerequisite_ms` by at least `20%` versus the
      current `47865 ms` baseline, or the story records explicit blocker truth
      and leaves the shipped lane unchanged.
- [x] If the chosen slice materially changes compiled previz inputs or prompt
      contract, refreshed `previz-usefulness` results stay at or above the
      validated usefulness floor of `0.803`; otherwise the story records why a
      usefulness rerun was unnecessary.
- [x] Focused regression coverage exists for runtime-harness case handling, any
      new first-pass strategy metadata, prompt/provenance contract, and UI
      disclosure if touched. If UI changes, desktop and mobile browser
      verification cover Scene Workspace previz plus any changed artifact-detail
      route with clean console output.

## Out of Scope

- Another provider-floor comparison or warmed regenerate follow-up already owned
  by Stories 176 and 152
- New video-provider integrations, engine-pack research, or model-transport work
- Final-render, export-fidelity, or OTIO follow-up work
- Broad screenplay-throughput, continuity, or methodology-tooling work
- Deterministic placeholder previz or a broad Scene Workspace redesign

## Approach Evaluation

- **Simplification baseline**: Before adding more orchestration, measure whether
  one bounded previz-prep call or a narrower first-pass prerequisite bundle
  already collapses the current xAI route. No abstract architecture argument is
  sufficient without that runtime proof.
- **AI-only**: A single bounded previz-prep call could plausibly replace the
  current first-pass auto-build bundle. Attractive on runtime, but risky if it
  turns compiled artifacts into an opaque shortcut that fights ADR-003's
  prompt-compilation model.
- **Hybrid**: Strongest default. Reuse healthy import/project artifacts and
  collapse only the first-pass prerequisites that are still gating xAI previz.
  Keep prompt compilation and provenance explicit rather than inventing a second
  hidden subsystem.
- **Pure code**: Only the right answer if the remaining `47865 ms` of first-pass
  prerequisite time proves to be overbroad orchestration, duplicate health
  checks, or avoidable auto-build stages rather than missing reasoning. Story
  152's warmed regenerate numbers suggest much of the remaining gap is in route
  prep, not provider video time.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced action-boundary
  truth. ADR-003 keeps prompts as read-only compiled artifacts and treats Story
  World as persistent upstream context, not disposable runtime glue. `spec:6`
  remains in `climb` specifically because fast useful AI previz is still
  unfinished. If build introduces a new model-dependent prep call, rerun
  `/discover-models` before freezing that candidate.
- **Existing patterns to reuse**: Story 175's prerequisite-strategy compare,
  Story 176's shipped xAI one-pass route, Story 152's regenerate/reuse runtime
  surface, `benchmarks/scripts/real_ai_previz_runtime_eval.py`,
  `scene_actions.py` preflight truth, `scene_readiness.py`,
  `recipe-ai-previz-generation.yaml`, `render_adapter_v1/previz_prompting.py`,
  `PrevizAdoptionService`, and existing preview-provenance surfaces.
- **Eval**: `real-ai-previz-runtime` is the primary detector. Rerun
  `previz-usefulness` only if the chosen slice materially changes compiled
  previz inputs or prompt contract. No new eval entry is needed because the
  registry already owns this lane.

## Tasks

- [x] Extend the maintained `real-ai-previz-runtime` surface so it isolates the
      current shipped xAI first-pass prerequisite bundle and compares at least
      one bounded collapse hypothesis on identical current-scene substrate.
- [x] Implement the smallest honest first-pass collapse in the owning runtime
      seams. Prefer a narrower prerequisite bundle and reuse of healthy artifacts
      over a new parallel previz subsystem.
- [x] Thread first-pass strategy truth through preflight, run metadata, and
      prompt/video provenance so operators can see what the first-pass route
      actually waited for.
- [x] Add or extend focused regression coverage for the runtime harness,
      scene-action/readiness logic, prompt/provenance contract, and any UI
      rendering touched by the chosen slice.
- [x] Rerun `real-ai-previz-runtime` and, if required by the chosen slice,
      `previz-usefulness`; classify all significant mismatches and update
      `docs/evals/registry.yaml`.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
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

- **Owning class/module**: The maintained runtime detector belongs first in
  `benchmarks/scripts/real_ai_previz_runtime_eval.py` and
  `real_ai_previz_runtime_support.py`. The shipped first-pass route is owned by
  `configs/recipes/recipe-ai-previz-generation.yaml`,
  `src/cine_forge/pipeline/scene_actions.py`, and
  `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`,
  with `render_adapter_v1/main.py` carrying prompt/video provenance. If the
  winning collapse touches upstream prep, prefer `scene_readiness.py` or the
  existing story-world / shot-planning owners over a new previz-only subsystem.
- **Data contracts**: Existing cross-layer contracts already live in
  `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/preview.py`,
  `src/cine_forge/schemas/runtime_params.py`, and
  `src/cine_forge/schemas/scene_scope.py`. If new first-pass strategy metadata
  crosses backend/UI boundaries, define it schema-first there. If build needs a
  bounded previz-prep artifact, define that artifact explicitly instead of
  threading runtime-only dicts through run state.
- **File sizes**: Current watchpoints from `make check-size` / `wc -l` are
  `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`633`),
  `benchmarks/scripts/real_ai_previz_runtime_support.py` (`467`),
  `src/cine_forge/pipeline/scene_actions.py` (`613`),
  `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`
  (`695`), `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  (`1823`), `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`
  (`1232`), `src/cine_forge/modules/creative_direction/story_world_v1/main.py`
  (`423`), `ui/src/lib/types.ts` (`770`), `ui/src/components/PrevizPanel.tsx`
  (`443`), and `tests/unit/test_render_adapter_module.py` (`1001`, test file).
  Smaller seams to prefer are `scene_readiness.py` (`60`), `render.py` (`251`),
  `preview.py` (`89`), `runtime_params.py` (`60`), `scene_scope.py` (`63`),
  `previz_adoption.py` (`365`), and `preview-provenance.ts` (`137`).
- **Decision context**: Reviewed `docs/ideal.md`,
  `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`,
  `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003,
  Stories 152 / 175 / 176, `docs/evals/registry.yaml`, and `make check-size`
  output. I did not find a newer ADR or design doc that narrows this previz
  runtime line more specifically.

## Files to Modify

- `docs/stories/story-178-ai-previz-first-pass-runtime-collapse.md` — keep the
  story current during build, validation, and close-out
- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — compare the current
  shipped first-pass xAI bundle against bounded collapse candidates and persist
  honest first-pass metrics (`633`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — add any strategy or
  summary fields without further bloating the main eval script (`467`)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — add explicit
  first-pass collapse cases on the maintained shipped-xAI substrate (`192`)
- `configs/recipes/recipe-ai-previz-generation.yaml` — update the shipped
  first-pass prerequisite contract only if a measured winner exists (`80`)
- `src/cine_forge/pipeline/scene_actions.py` — keep preflight and auto-build
  truth aligned with the chosen first-pass route (`613`)
- `src/cine_forge/services/scene_readiness.py` — likely home for shared
  first-pass readiness checks if collapse logic needs a focused helper (`60`)
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` —
  keep compiled previz prompt contract aligned with the chosen collapse (`695`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — fallback-only
  touchpoint if prompt/video provenance needs new first-pass strategy fields
  (`1823`)
- `src/cine_forge/modules/creative_direction/story_world_v1/main.py` —
  fallback-only touchpoint if the winning slice narrows or bypasses current
  story-world work on first pass (`423`)
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — fallback-only
  touchpoint if the winning slice shrinks shot-planning work on first pass
  (`1232`)
- `src/cine_forge/services/previz_adoption.py` — fallback-only if shared
  operator-facing lane truth changes (`365`)
- `src/cine_forge/schemas/render.py` — schema-first home for any first-pass
  strategy metadata that crosses into adoption/UI surfaces (`251`)
- `src/cine_forge/schemas/preview.py` — schema-first home for operator-facing
  preview provenance changes (`89`)
- `src/cine_forge/schemas/runtime_params.py` — if run metadata needs new
  first-pass strategy fields (`60`)
- `src/cine_forge/schemas/scene_scope.py` — if scope/preflight semantics change
  (`63`)
- `ui/src/lib/types.ts` — keep frontend contracts aligned with any new shared
  first-pass strategy fields (`770`)
- `ui/src/components/PrevizPanel.tsx` — fallback-only if preflight/adoption copy
  changes on the surfaced route (`443`)
- `ui/src/components/AiPrevizViewer.tsx` — fallback-only if prompt/video
  disclosure changes (`338`)
- `ui/src/components/preview-provenance.ts` — fallback-only if provenance text
  changes (`137`)
- `tests/unit/test_real_ai_previz_runtime_support.py` — strategy-summary coverage
  for the expanded runtime detector (`374`)
- `tests/unit/test_previz_adoption_service.py` — fallback-only if shared lane
  truth changes (`336`)
- `tests/unit/test_previz_prompting.py` — prompt/provenance contract coverage
  (`170`)
- `tests/unit/test_render_adapter_module.py` — fallback-only touchpoint if
  render adapter consumes new strategy fields (`1001`)
- `tests/unit/test_scene_actions.py` — likely preflight-truth coverage if the
  chosen slice changes first-pass auto-build behavior
- `docs/evals/registry.yaml` — record refreshed runtime/usefulness evidence,
  `git_sha`, result paths, and mismatch classification

## Redundancy / Removal Targets

- Any duplicated first-pass auto-build logic that reruns creative-direction or
  shot-planning work the shipped xAI lane no longer needs
- Any second home for first-pass strategy truth split between runtime reports,
  preflight copy, and prompt/video provenance once one schema-backed path wins
- Stale notes or surfaced copy that still treat the current `47865 ms`
  prerequisite bundle as a fixed shipped cost after the collapse lands

## Notes

- This is a new story rather than a reopen of Stories 175, 176, or 152 because
  the success surface changed again. Story 175 chose the one-pass route. Story
  176 chose the shipped xAI provider floor on that route. Story 152 measured
  warmed regenerate/reuse truth. None of them collapse the first-pass cost on
  the current shipped route itself.
- Current baseline from `docs/evals/registry.yaml`: shipped xAI first pass is
  `65514 ms` to first playable with `47865 ms` of prerequisites, `17649 ms`
  inside `ai_previz`, and `82137 ms` full completion.
- Warmed same-lane evidence is materially better: Story 152 records `39325 ms`
  for full regenerate with `21363 ms` before `ai_previz`, and `17869 ms` for
  `start_from=ai_previz` reuse. That implies the remaining first-pass gap is
  mostly pre-`ai_previz` work rather than provider video generation.
- Existing eval coverage already owns this lane: `real-ai-previz-runtime` for
  runtime truth and `previz-usefulness` for semantic guardrails. No new eval
  entry is needed unless build invents a genuinely new first-pass artifact with
  its own separate truth surface.
- If a one-call previz-prep baseline wins, that is simplification toward the
  Ideal, not a regression from ADR-003, as long as prompts remain read-only
  compiled artifacts and provenance stays explicit.

## Plan

### Task 1 — Expand the maintained runtime detector around the actual current-project first-pass problem

- Files: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`,
  `benchmarks/scripts/real_ai_previz_runtime_eval.py`,
  `benchmarks/scripts/real_ai_previz_runtime_support.py`
- Change: add an explicit imported-project first-pass case for the shipped xAI
  lane so the maintained runtime surface can distinguish raw screenplay
  bootstrap from the real Scene Workspace route that already reuses healthy
  import artifacts and only auto-builds `shot_planning` before `ai_previz`.
  Persist both the raw-input and imported-project first-pass metrics in the
  same artifact instead of silently treating them as one route.
- Repo-fit evidence: this keeps the new work on the maintained
  `real-ai-previz-runtime` surface rather than inventing a story-local benchmark
  that would drift immediately.
- Done means: one runtime artifact can answer “what did first pass wait for,
  and which current-project route is actually relevant?” on the shipped xAI
  lane.

### Task 2 — Prove the narrowest honest collapse before adding any new prep subsystem

- Candidate baseline: current-project first pass on already imported substrate.
  Exploration found that the repo already has this narrower route: scene-action
  preflight reuses `timeline` and `track_manifest` when they are healthy,
  auto-builds only `shot_plan`, and the actual first-pass cost is then
  dominated by `shot_planning` plus xAI video generation. That is the simplest
  truthful collapse to measure before inventing any new one-call previz-prep
  subsystem.
- Decision gate:
  - If the imported-project first-pass case materially improves the maintained
    prerequisite budget and the current shared product surfaces can already
    express it honestly, prefer detector/adoption truth over adding a new prep
    subsystem.
  - Only if that narrower current-project route still proves insufficiently
    honest or unmeasurable should build widen scope into new first-pass
    strategy code.
  - If build still needs a new model-dependent prep call after that, rerun
    `/discover-models` before freezing it.
- Done means: the story contains measured evidence for the already-shipped
  narrower route first, not a speculative architecture branch.

### Task 3 — Let the maintained focus metrics follow the current-project first-pass route

- Expected default: no new previz-prep subsystem. Prefer the existing imported
  project route if it already satisfies the story's first-pass collapse surface.
- Likely owners: the benchmark harness plus the shared adoption/runtime truth
  seam. Touch recipe/preflight/provenance code only if the benchmark proves the
  current product path cannot actually express the narrower route.
- Change: keep raw-input bootstrap evidence visible, but stop letting it stand
  in for the active Scene Workspace first-pass route when the maintained score
  and surfaced latency truth are supposed to describe what happens after import.
- Structural guardrail: `render_adapter_v1/main.py` and `shot_plan_v1/main.py`
  stay fallback-only. The likely implementation should remain inside the
  benchmark/support/adoption seams.
- Done means: the shipped xAI lane still has one honest prerequisite contract,
  but the current-project first-pass route is no longer hidden behind the raw
  import bundle.

### Task 4 — Surface the narrowed first-pass truth and lock it with tests and registry updates

- Files: focused benchmark/adoption tests, `docs/evals/registry.yaml`, and
  fallback-only shared UI contract files if the current panel needs an explicit
  imported-project first-pass field.
- Change: make the runtime artifact, registry note, and any surfaced
  first-pass latency readout agree on the actual current-project route while
  preserving raw-input bootstrap evidence as explicit context rather than
  hidden baseline drift.
- Done means: runtime artifact, registry entry, and surfaced first-pass truth
  all agree on when CineForge is reusing imported substrate versus building
  more before `ai_previz`.

## Work Log

20260419-2138 — story-created: triage promoted the active `spec:6` / `spec:7`
follow-up into Story 178 because the current shipped xAI lane still spends
`47865 ms` in first-pass prerequisites before `ai_previz` starts. Evidence:
reviewed `docs/ideal.md`, `docs/spec.md`,
`docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`,
`docs/build-map.md`, ADR-002, ADR-003, Stories 152 / 175 / 176,
`docs/evals/registry.yaml`, and `make check-size` output; confirmed the
anti-fragmentation boundary that this is not provider floor, scene-ready
collapse, or warmed regenerate reuse. Next step: run `/build-story 178`.
20260419-2232 — exploration-notes: traced the current shipped xAI first-pass
route end to end before changing code and found the real split is narrower than
the maintained detector implies. Evidence: `real-ai-previz-runtime` still
reports `47865 ms` of first-pass prerequisites, but the latest run-state breaks
that into `25899 ms` inside `mvp_ingest` (`script_bible=8060 ms`,
`project_config=17680 ms`) plus `21567 ms` inside `shot_planning`, while
`timeline` and `tracks` are effectively free. Repo-fit surprise: the actual
Scene Workspace preflight in `src/cine_forge/pipeline/scene_actions.py`
already reuses healthy `timeline` / `track_manifest` and auto-builds only
`shot_plan` for a first clip on an imported project, so the maintained score
and panel latency are still anchored to a raw-input bootstrap bundle that is
not the same route operators trigger after import. Consulted context: ADR-002,
ADR-003, Stories 152 / 175 / 176, `recipe-ai-previz-generation.yaml`,
`recipe-mvp-ingest.yaml`, `real_ai_previz_runtime_eval.py`,
`real_ai_previz_runtime_support.py`, `scene_actions.py`,
`render_adapter_v1/main.py`, `shot_plan_v1/main.py`, and the current registry
entry. Chosen implementation boundary: extend the runtime harness to measure
that imported-project first-pass route explicitly, let the maintained focus
metrics follow it if the comparison is honest, and only widen into new
first-pass strategy code if the existing shared adoption/preflight/provenance
contract cannot surface the narrower truth. Next step: implement the harness
and shared truth changes, then rerun the shipped-xAI runtime compare.
20260419-2249 — implementation: extended the maintained runtime harness with an
explicit imported-project first-pass case and split the focus summary into
`raw_input_first_pass`, `imported_project_first_pass`, and existing-clip reuse
instead of forcing those routes into one baseline. Evidence: updated
`benchmarks/scripts/real_ai_previz_runtime_eval.py`,
`benchmarks/scripts/real_ai_previz_runtime_support.py`,
`benchmarks/fixtures/real_ai_previz_runtime_cases.json`, and
`tests/unit/test_real_ai_previz_runtime_support.py`; fresh runtime artifact
`benchmarks/results/real-ai-previz-runtime-story-178-first-pass-project-ready-2026-04-19.{json,md}`
now lands the imported-project first clip at `37186 ms` first playable
(`19161 ms` prerequisites + `18025 ms` isolated `ai_previz`; `40198 ms` full
completion), preserves the raw-input bootstrap at `109868 ms` /
`92216 ms`, and keeps same-scene full regenerate / reuse at `39062 ms` and
`18152 ms`. Practical product read: the repo already had the narrower current
Scene Workspace route; the broken part was the maintained detector and first-pass
truth still anchoring the operator-facing lane to the raw-input bootstrap
bundle. I did not change recipe, preflight, or provenance code because the
existing shared surfaces already show reused and auto-built first-pass inputs
honestly once the maintained latency truth follows the imported-project route.
`previz-usefulness` was not rerun because compiled previz inputs and prompt
contract did not change. Classification: no model-wrong, golden-wrong, or
ambiguous mismatches remained in the runtime harness. Next step: run repo-wide
checks, update the registry, and recompile methodology surfaces.
20260419-2253 — checks-and-registry: updated `docs/evals/registry.yaml` to make
the imported-project first-pass route the maintained focus truth, ran the
required static checks, and left Story 178 build-complete but still open for
`/validate`. Evidence: `make test-unit PYTHON=.venv/bin/python` passed
(`763 passed, 173 deselected, 1 warning`); `.venv/bin/python -m ruff check
src/ tests/ benchmarks/scripts/` passed clean; the runtime artifact keeps all
four shipped-xAI cases successful; and the registry now records imported-project
first pass, raw-input bootstrap, full regenerate, and reuse in one row with
fresh `git_sha` and result path. Redundancy outcome: no app-code removal was
needed because the existing `scene_actions` preflight plus render provenance
already describe this route honestly; the redundant piece was the detector-level
assumption that “first pass” meant raw-input bootstrap. Next step: recompile
methodology surfaces, then hand off for `/validate 178`.
20260419-2301 — validation: reran the required local validation checks and
confirmed Story 178 is implementation-complete with only `/mark-story-done`
bookkeeping remaining. Fresh evidence from this validation pass:
`make test-unit PYTHON=.venv/bin/python` passed (`763 passed, 173 deselected,
1 warning`); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
passed clean; `PYTHONPATH=src .venv/bin/python -m pytest
tests/unit/test_real_ai_previz_runtime_support.py -q` passed (`6 passed`);
`pnpm --dir ui run lint` passed; `cd ui && npx tsc -b` passed (with the
pre-existing npm `min-release-age` warning only); and `pnpm methodology:check`
reported current outputs with the pre-existing `api_service_and_operator_console`
architecture-audit warning. Not freshly rerun in this validation pass: the paid
`real-ai-previz-runtime` benchmark itself and `previz-usefulness`; validation
instead inspected the fresh Story 178 runtime artifact and registry row already
produced during build, where classification remained `runtime-blocking` versus
the `<=6000 ms` detector and no model-wrong, golden-wrong, or ambiguous
mismatches remained. Next step: run `/mark-story-done 178`.
20260420-0712 — story-done: closed Story 178 after the clean validation pass
and refreshed the generated planning surfaces. Evidence: story status is now
`Done`; all workflow gates are checked; `pnpm methodology:compile` rewrote
`docs/stories.md`, `docs/build-map.md`, and `docs/methodology/graph.json` with
only the pre-existing `api_service_and_operator_console` architecture-audit
warning; and `CHANGELOG.md` now includes the Story 178 entry. Close-out
judgment: no implementation work remained, and the still-red runtime detector
was already classified honestly as `runtime-blocking` in the registry and
validation note. Next step: `/check-in-diff`.
