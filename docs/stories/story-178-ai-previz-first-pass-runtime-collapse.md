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

Story 178 was reopened after the April 19, 2026 runtime rerun corrected the
focus route. The live operator path is no longer the raw-input one-pass lane at
`65514 ms`; it is the imported-project first clip on the shipped xAI route at
`37186 ms` to first playable, with `19161 ms` still spent in the remaining
`shot_planning` prerequisite and `18025 ms` inside `ai_previz`. That means the
next bounded climb is not another provider-floor pass or another truth-surface
cleanup. It is shrinking the imported-project first-pass shot-planning cost on
the shipped xAI lane without breaking honest preflight, compiled-prompt
provenance, the persisted `shot_plan` contract, or the current usefulness
floor. This reopened scope should either ship a materially cheaper first-pass
route on the same artifact boundary or record precise blocker truth.

## Acceptance Criteria

- [x] A fresh imported-project first-pass baseline exists for the current code
      on the maintained `real-ai-previz-runtime` surface, and the benchmark can
      compare the new shipped route against an explicit old-behavior control on
      identical imported-project substrate rather than relying on prose memory.
- [x] The chosen implementation reduces
      `fastest_imported_project_first_pass_prerequisite_ms` by at least `25%`
      versus the current `19161 ms` baseline, or the story records blocker
      truth and leaves the shipped lane unchanged.
- [x] The shipped route keeps the current `shot_plan`-backed previz contract
      intact: no prompt-only first-pass shortcut ships, and prompt/video
      provenance stays honest about the same prerequisite strategy.
- [x] Refreshed `previz-usefulness` results for the shipped xAI lane stay at or
      above the validated usefulness floor of `0.803`, and every significant
      mismatch is classified as `model-wrong`, `golden-wrong`, or `ambiguous`
      with runtime impact.
- [x] Focused regression coverage exists for any new runtime-case override
      schema, shot-planning/recipe behavior, and provenance or preflight
      contract touched by the implementation.

## Out of Scope

- Another provider-floor comparison or warmed regenerate follow-up already owned
  by Stories 176 and 152
- New video-provider integrations, engine-pack research, or model-transport work
- Final-render, export-fidelity, or OTIO follow-up work
- Broad screenplay-throughput, continuity, or methodology-tooling work
- Deterministic placeholder previz or a broad Scene Workspace redesign

## Approach Evaluation

- **Simplification baseline**: Before widening scope, compare the current
  imported-project first-pass route against an explicit control on the same
  substrate. The story already proved the route; the reopened scope must now
  prove a cheaper variant of that same route.
- **AI-only**: Letting `render_adapter_v1` compile previz directly from scene +
  concern-group context without a persisted `shot_plan` is tempting on latency,
  but it now implies a larger schema break through `render_adapter_v1`,
  `CompiledRenderPrompt`, `GeneratedVideoArtifact`, module input contracts, and
  UI/viewer assumptions about `shot_plan_ref`. That is a much larger change
  than the current bottleneck justifies without evidence.
- **Hybrid**: Strongest default. Keep the persisted `shot_plan` seam and shrink
  the cost of producing it on the shipped previz-fast route. That preserves the
  existing prompt-compilation and provenance model while attacking the remaining
  `19161 ms` prerequisite wall directly.
- **Pure code**: `shot_plan_v1` already has a deterministic mock path, but
  current repo evidence says deterministic planning is a control/fallback
  substrate, not the product answer. `previz-usefulness` still keeps the
  strongest deterministic rows below the best AI rows, so replacing the shipped
  lane with code-only planning would be premature.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced action-boundary
  truth. ADR-003 keeps prompts as read-only compiled artifacts and treats Story
  World as persistent upstream context, not disposable runtime glue. `spec:6`
  remains in `climb` specifically because fast useful AI previz is still
  unfinished. If build introduces a new model-dependent prep call, rerun
  `/discover-models` before freezing that candidate.
- **Existing patterns to reuse**: Story 151's compact shot-planning profile,
  Story 175's prerequisite-strategy compare, Story 176's shipped xAI one-pass
  route, Story 178's imported-project first-pass detector, `recipe-ai-previz-generation.yaml`,
  `shot_plan_v1`, `scene_actions.py`, and the existing preview-provenance
  surfaces.
- **Eval**: `real-ai-previz-runtime` remains the primary detector. Because this
  reopened scope changes shot-planning behavior on the shipped lane, rerun
  `previz-usefulness` even if the downstream previz prompt contract text stays
  nominally the same.

## Tasks

- [x] Extend the maintained `real-ai-previz-runtime` case schema only as much as
      needed so the benchmark can compare the reopened shipped lane against an
      old-behavior imported-project control on identical substrate.
- [x] Implement the smallest honest imported-project first-pass optimization on
      the shipped xAI route. Default expectation: keep the same persisted
      `shot_plan` seam and reduce the cost of producing it for previz-fast,
      rather than inventing a prompt-only shortcut.
- [x] Keep preflight, runtime summary, and preview provenance aligned with the
      same prerequisite strategy. No UI wording should claim a new strategy if
      the route still behaves as one-pass previz prep.
- [x] Add or extend focused regression coverage for the runtime harness,
      shot-planning behavior, and any provenance contract touched by the
      implementation.
- [x] Rerun `real-ai-previz-runtime` on the imported-project first-pass subset
      plus the matched control, rerun `previz-usefulness` for the shipped xAI
      lane, classify all significant mismatches, and update
      `docs/evals/registry.yaml`.
- [x] Check whether the chosen implementation makes any old recipe knobs,
      benchmark assumptions, or docs redundant; remove them or create a
      concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
  - [x] UI validation: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
  - [x] Browser verification not required; no UI files changed
- [x] Methodology surfaces refreshed with `pnpm methodology:compile` after the eval registry changed
- [x] If evals are changed: classify all mismatches and update `docs/evals/registry.yaml`
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

- Historical context: Story 178 originally split out from Stories 175 / 176 /
  152 because the success surface changed from provider-floor selection to the
  first-pass prerequisite wall on the shipped xAI lane. The current work keeps
  that same story open because the subsystem and detector are still the same.
- Reopened baseline from `docs/evals/registry.yaml` before this implementation:
  shipped xAI imported-project first pass was `37186 ms` to first playable with
  `19161 ms` of prerequisites, `18025 ms` inside `ai_previz`, and `40198 ms`
  full completion on the April 19, 2026 rerun.
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

### Task 1 — Add a true before/after comparison on the imported-project first-pass route

- Files: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`,
  `benchmarks/scripts/real_ai_previz_runtime_support.py`,
  `benchmarks/scripts/real_ai_previz_runtime_eval.py`,
  `tests/unit/test_real_ai_previz_runtime_support.py`
- Change: extend the runtime-case schema just enough to patch the
  `shot_planning` stage as well as `ai_previz`, then add an imported-project
  control case that preserves the old shipped shot-planning behavior beside the
  reopened shipped route.
- Repo-fit evidence: the maintained runtime harness already owns this line, and
  the codebase has no other detector that can compare two imported-project
  first-pass variants honestly on the same substrate.
- Structural health check: `real_ai_previz_runtime_eval.py` is `633` lines and
  `real_ai_previz_runtime_support.py` is `467`, so new override logic should
  stay in the support model + small recipe materialization helper rather than
  bloating the runner.
- Done means: one rerun can say whether the new shipped route is actually
  faster than the old behavior on the same imported-project first-pass seam.

### Task 2 — Reduce first-pass shot-planning cost without deleting the shot-plan seam

- Files: `configs/recipes/recipe-ai-previz-generation.yaml`,
  `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`,
  `tests/unit/test_shot_planning_module.py`
- Change: make the shipped previz-fast shot-planning path cheaper in place.
  Default expected slice: skip the extra QA pass on the AI-previz recipe's
  compact shot-planning stage, while keeping the same persisted `shot_plan`
  artifact boundary and current prompt-compilation model.
- Repo-fit evidence: `render_adapter_v1` and the render schemas still require a
  real `shot_plan_ref`; bypassing that would spill into `CompiledRenderPrompt`,
  `GeneratedVideoArtifact`, module input contracts, and UI viewers. The shot
  planner already exposes `skip_qa` and `previz_fast`, so this route reuses an
  existing bounded control point instead of inventing a second planning system.
- Alternatives rejected:
  - AI-only no-shot-plan first pass: larger schema/product refactor with no
    evidence yet that it is needed.
  - Pure code/mock shot plan: deterministic planning remains a control/fallback
    substrate, and current usefulness evidence keeps deterministic rows below
    the best AI rows.
- Structural health check: `shot_plan_v1/main.py` is `1232` lines, so keep the
  code change surgical and favor recipe-level wiring plus a small focused test.
- Done means: the shipped imported-project first-pass route still emits a real
  `shot_plan`, but it no longer pays for an avoidable QA pass before xAI previz.

### Task 3 — Re-measure the shipped lane and update the repo truth surfaces

- Files: `docs/evals/registry.yaml`, `docs/stories/story-178-ai-previz-first-pass-runtime-collapse.md`,
  fallback-only methodology outputs after compile
- Change: rerun the imported-project runtime subset plus the shipped xAI
  usefulness lane, classify any mismatches, and update the registry/work log
  with the new first-pass numbers and blocker truth.
- Repo-fit evidence: `real-ai-previz-runtime` and `previz-usefulness` are the
  canonical detectors for this line; using anything else would produce drift.
- Done means: the story, registry, and generated planning surfaces all reflect
  the new shipped first-pass cost and whether the reopened climb actually moved
  the user-facing loop.

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
20260420-0858 — implementation: kept the shipped imported-project first-pass
route on the same persisted `shot_plan` seam and removed only the extra QA pass
from the previz-fast shot-planning recipe. Evidence: set `skip_qa: true` on
`configs/recipes/recipe-ai-previz-generation.yaml`; extended the maintained
runtime harness with a bounded `shot_planning` override model in
`benchmarks/scripts/real_ai_previz_runtime_support.py` and recipe
materialization support in `benchmarks/scripts/real_ai_previz_runtime_eval.py`;
added the explicit old-behavior imported-project control to
`benchmarks/fixtures/real_ai_previz_runtime_cases.json`; and added regression
coverage in `tests/unit/test_real_ai_previz_runtime_support.py`. Fresh runtime
artifact `benchmarks/results/real-ai-previz-runtime-story-178-shot-planning-qa-collapse-2026-04-20.{json,md}`
shows the shipped route at `31369 ms` first playable (`13194 ms` prerequisites
+ `18175 ms` isolated `ai_previz`; `35639 ms` full completion) versus the
matched old-behavior control at `41675 ms` (`23844 ms` prerequisites +
`17831 ms` isolated `ai_previz`; `45959 ms` full completion). That is a
`31.1%` prerequisite reduction versus the prior imported-project baseline
(`19161 ms`) and a `44.7%` prerequisite reduction versus the matched control.
Practical product read: the first imported-project clip is still too slow, but
the wait dropped by about ten seconds without inventing a second planning
system or weakening provenance truth. Next step: rerun usefulness, refresh the
registry, and run full checks.
20260420-0919 — evals-and-validation: reran the shipped xAI usefulness slice,
classified the remaining mismatches, updated the registry, and completed the
required backend checks. Evidence: `benchmarks/results/previz-usefulness-story-178-shot-planning-qa-collapse-2026-04-20-report.{json,md}`
keeps `Grok Imagine Previz` above the usefulness floor at `0.8380` overall with
`17549 ms` generation latency; `Annotated Animatic` lands at `0.8180` /
`601 ms`; `Symbolic Animatic` lands at `0.6847` / `480 ms`. Significant
mismatch classification: no model-wrong or golden-wrong mismatches remained;
`radio_hold_tracking` stayed ambiguous and non-runtime-blocking for all three
rerun providers. For xAI specifically, the only miss is a python-only
ambiguity where the strict scorer still penalizes tone/emotion tag drift
(`urgent`/`resolve` vs `tense|detached` / `suspicion|hesitation`) plus the
missing `navy` color tag while the Opus rubric passes the row at `0.78` for
blocking, camera, motion, and continuity. Required checks passed:
`make test-unit PYTHON=.venv/bin/python` (`765 passed, 173 deselected,
1 warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`,
and targeted pytest for the touched runtime/shot-planning coverage. No browser
or API smoke pass was needed because this slice changed recipe/eval surfaces,
not UI or service behavior. `docs/evals/registry.yaml` now records the fresh
runtime compare and the xAI/control usefulness rerun with current `git_sha`
`e3c1d39`. Next step: `/validate 178`.
20260420-0926 — methodology-refresh: recompiled the generated planning surfaces
after the eval registry changed so future triage does not read stale derived
views. Evidence: `pnpm methodology:compile` rewrote
`docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md` with
only the pre-existing `api_service_and_operator_console` architecture-audit
warning. Next step: `/validate 178`.
20260420-1613 — validation: reran the full required validation suite plus both
paid Story 178 detectors and confirmed the implementation is ready for close-out.
Fresh evidence from this validation pass: `make test-unit PYTHON=.venv/bin/python`
passed (`765 passed, 173 deselected, 1 warning`); `.venv/bin/python -m ruff
check src/ tests/ benchmarks/scripts/` passed clean; targeted pytest
`tests/unit/test_real_ai_previz_runtime_support.py
tests/unit/test_shot_planning_module.py -q` passed (`16 passed`); `pnpm --dir ui
run lint` passed; `cd ui && npx tsc -b` passed with only the pre-existing npm
`min-release-age` warning; `pnpm methodology:check` initially failed because the
generated surfaces were stale, then passed after `pnpm methodology:compile`
with only the pre-existing `api_service_and_operator_console` architecture-audit
warning. Fresh runtime artifact
`benchmarks/results/real-ai-previz-runtime-story-178-shot-planning-qa-collapse-validation-2026-04-20.{json,md}`
holds the shipped imported-project first pass at `32130 ms` first playable
(`14103 ms` prerequisites + `18027 ms` isolated `ai_previz`; `36258 ms` full
completion) versus `40507 ms` (`22967 ms` prerequisites + `17540 ms`
isolated `ai_previz`; `44928 ms` full completion) for the matched QA control,
which still clears the story bar at `26.4%` prerequisite reduction versus the
`19161 ms` baseline and `38.6%` versus the matched control. Fresh usefulness
artifact
`benchmarks/results/previz-usefulness-story-178-shot-planning-qa-collapse-validation-2026-04-20-report.{json,md}`
keeps `Grok Imagine Previz` at `0.8997` overall / `17935 ms`, `Annotated
Animatic` at `0.8380` / `618 ms`, and `Symbolic Animatic` at `0.6647` / `445
ms`. Significant mismatch classification from this validation rerun: no
model-wrong or golden-wrong mismatches remained; xAI and Annotated passed
clean; `Symbolic Animatic / quiet_bedside_vigil` and
`Symbolic Animatic / radio_hold_tracking` remain ambiguous and
non-runtime-blocking deterministic-control failures. Practical product read:
the first imported-project clip is still far from the Ideal, but the shipped
xAI lane now reaches a first playable clip about eight seconds sooner than the
validated old-behavior control without dropping below the usefulness floor or
weakening the persisted `shot_plan` seam. Next step: `/mark-story-done 178`.
20260420-1626 — story-done: closed Story 178 after the clean validation rerun
and final close-out audit. Evidence: story status is now `Done`; workflow gates
are fully checked; `pnpm methodology:compile` refreshed
`docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`; and
the existing `CHANGELOG.md` Story 178 entry was updated to reflect the shipped
QA-skip collapse outcome rather than the earlier narrower first-pass truth-only
reopen note. Close-out judgment: no implementation work remained, registry
scores and mismatch classifications were current, and the still-red runtime
detector remained explicitly classified as `runtime-blocking` rather than being
misrepresented as unfinished story work. Next step: `/check-in-diff`.
