---
id: "152"
title: "Previz AI Regenerate Reuse Path"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:8.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "149"
  - "151"
  - "171"
  - "175"
  - "176"
category_refs:
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
roadmap_tags:
  - "previz"
  - "runtime"
  - "substrate"
legacy_system: ""
---

# Story 152 — Previz AI Regenerate Reuse Path

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:7.1, spec:8.2, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 149, Story 151, Story 171, Story 175, Story 176

## Goal

Reopen the AI-previz iteration line around the current shipped xAI one-pass lane. Story 152 originally proved that regenerating from an existing healthy shot plan should reuse `start_from=ai_previz` instead of silently rerunning `timeline`, `tracks`, and `shot_planning`. Story 176 then changed the shipped lane to `xai_grok_imagine_video` on the honest one-pass route, but the maintained runtime/adoption surface still reports only the first-pass one-pass latency (`65514 ms`) and the panel shows that number even when preflight is about to reuse the current shot plan. This story exists to extend the maintained runtime detector with the warmed regenerate loop, re-measure the shipped xAI reuse path, and surface distinct regenerate truth in the operator-facing previz panel if that loop is materially faster than the first-pass one-pass baseline.

## Acceptance Criteria

- [x] The maintained `real-ai-previz-runtime` harness can measure the shipped xAI same-scene regenerate loop on honest existing-clip state, not just the first-pass one-pass route. Required recorded outputs: full-regenerate control versus `start_from=ai_previz` reuse on the same shipped xAI lane, with `time_to_first_playable_ms`, isolated `ai_previz` runtime, post-playable overhead, full completion time, and result paths persisted.
- [x] `docs/evals/registry.yaml` is updated in the same story with the fresh regenerate result paths, `git_sha`, date, and mismatch classification (`model-wrong`, `golden-wrong`, `ambiguous`, plus `runtime-blocking` vs `non-runtime-blocking`) for the reopened Story 152 slice.
- [x] If the measured shipped xAI regenerate loop differs materially from the first-pass one-pass lane, the shared adoption/schema/UI contract surfaces that distinction in the Scene Workspace previz panel when preflight is reusing the current shot plan. Operators should be able to tell the difference between “first clip on this scene” and “regenerate from current plan” without reading story prose or benchmark markdown.
- [x] Focused regression coverage exists for the runtime support summary, the previz adoption service/schema, and any UI typing/rendering touched by the new regenerate truth.

## Out of Scope

- Another provider-floor comparison or fixed-pack prompt race for AI previz
- Reworking first-pass one-pass prerequisite strategy from Story 175
- Relaxing health/staleness rules to reuse stale or missing planning
- Final-render or reference-conditioned render follow-up work

## Approach Evaluation

- **Simplification baseline**: Keep the existing shipped xAI lane and current `Avg 65.5s` badge untouched. That is wrong if regenerate-from-current-plan is materially faster, because ADR-002 requires the surfaced route to explain what will happen when the operator clicks now, not just the slowest honest first-pass lane.
- **AI-only**: Wrong fit. This is runtime measurement, schema truth, and UI disclosure, not a reasoning-quality problem.
- **Hybrid**: Best fit. Keep the product/runtime measurement deterministic via the maintained `real-ai-previz-runtime` harness, then use the shared adoption/preflight contract to surface the operator-facing distinction only when the measured regenerate loop is actually different.
- **Pure code**: Insufficient by itself. We could add a second badge or copy branch immediately, but without a fresh measured xAI regenerate baseline we would just be moving story prose into UI chrome.
- **Repo constraints / ADRs**: ADR-002 rejects hidden pipeline differences and expects warn/proceed guidance at the action boundary. ADR-003 keeps previz as a readable planning surface, so “reuse current shot plan” is not enough if the panel still advertises only first-pass latency. The maintained `real-ai-previz-runtime` surface already owns honest current-lane timing, so this story should extend that surface instead of inventing a third detector.
- **Existing patterns to reuse**: Reuse Story 152's `start_from=ai_previz` loop, Story 171's first-playable truth framing, Story 175's one-pass route distinction, Story 176's shipped xAI provider floor, `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `PrevizAdoptionService`, `PrevizPanel.tsx`, and the existing preflight reuse disclosure rather than adding a new subsystem.
- **Eval**: Extend the maintained `real-ai-previz-runtime` harness so it can seed an existing-clip state and compare full regeneration versus reuse on the shipped xAI lane. If the regenerate delta is small, keep the UI unchanged and record why. If the delta is material, use that measured number in the shared adoption/UI truth.

## Tasks

- [x] Extend `real_ai_previz_runtime` case/schema support so the harness can seed existing-clip state and compare full-regenerate versus `start_from=ai_previz` reuse on the shipped xAI lane.
- [x] Add the shipped xAI regenerate cases to the runtime manifest, rerun the regenerate benchmark on honest current-scene state, and update `docs/evals/registry.yaml`.
- [x] Thread measured regenerate latency through the shared previz adoption/schema surface and update the Scene Workspace previz panel so reuse-path latency is surfaced distinctly when preflight is reusing the current shot plan.
- [x] Add focused regression coverage for runtime support summaries, previz adoption parsing, and UI typing/rendering.
- [x] Check whether the reopened implementation makes any prior helper paths or copy redundant; remove them or record a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: classify all mismatches and update `docs/evals/registry.yaml`
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

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: The regenerate measurement belongs first in the maintained benchmark seam (`benchmarks/scripts/real_ai_previz_runtime_eval.py` and `real_ai_previz_runtime_support.py`), while the operator-facing distinction belongs in the shared previz adoption contract (`schemas/render.py`, `services/previz_adoption.py`) and the existing `PrevizPanel.tsx` consumer. No new standalone previz policy surface is justified.
- **Data contracts**: This story likely adds a small schema-first cross-layer contract so the backend can expose a distinct regenerate latency/readout without forcing the UI to infer it from raw registry notes. Add the field in `PrevizLaneStatus` before wiring service/UI consumers.
- **File sizes**: `make check-size` currently flags likely owners at: `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`560`), `ui/src/lib/types.ts` (`768`), and `ui/src/components/PrevizPanel.tsx` (`419`). `real_ai_previz_runtime_support.py` (`359`), `render.py` (`249`), `previz_adoption.py` (`342`), `tests/unit/test_real_ai_previz_runtime_support.py` (`314`), and `tests/unit/test_previz_adoption_service.py` (`326`) are still tractable. Keep changes concentrated in these seams and avoid widening `render_adapter_v1/main.py` unless the benchmark reveals a real runtime defect there.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 152 / 171 / 175 / 176, `docs/evals/registry.yaml`, `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `scene_actions.py`, `PrevizPanel.tsx`, `PrevizAdoptionService`, and the current shipped recipe/engine-pack defaults.

## Files to Modify

- `docs/stories/story-152-previz-ai-regenerate-reuse-path.md` — reopen the story, track the new xAI regenerate scope, and record fresh evidence (`190`)
- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — extend the maintained harness to seed existing-clip state and compare regenerate modes (`560`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — add regenerate-case metadata and summary fields without bloating the main eval script (`359`)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — add shipped xAI regenerate control/reuse cases on honest current-scene state (`169`)
- `src/cine_forge/schemas/render.py` — add schema-first regenerate-latency fields to the shared previz adoption response if the measured delta is material (`249`)
- `src/cine_forge/services/previz_adoption.py` — read the new runtime metrics from the registry and populate the shared operator-facing status (`342`)
- `ui/src/lib/types.ts` — keep the frontend contract aligned with the shared regenerate-latency fields (`768`)
- `ui/src/components/PrevizPanel.tsx` — surface first-pass versus regenerate truth when preflight is reusing the current shot plan (`419`)
- `tests/unit/test_real_ai_previz_runtime_support.py` — cover new summary fields and focus behavior for regenerate cases (`314`)
- `tests/unit/test_previz_adoption_service.py` — cover the new regenerate-latency parsing and shipped xAI disclosure (`326`)
- `docs/evals/registry.yaml` — record fresh regenerate evidence and classifier truth for the reopened Story 152 slice
- `docs/methodology/state.yaml` — refresh the current execution summary after the story is reopened and the latest lane truth is known

## Redundancy / Removal Targets

- Any remaining panel copy that implies the first-pass one-pass latency is the same thing as the reuse/regenerate loop
- Story/state prose that still treats Story 152 as a closed historical artifact rather than the active owner for iteration-loop truth on the shipped xAI lane

## Notes

- Historical Story 152 benchmark on the old Fast 4 / one-pass substrate proved the structural reuse seam but is no longer current shipped truth:
  - full regen (`story152-regen-full-baseline`): `81545 ms`
  - reuse regen (`story152-regen-start-baseline`): `75337 ms`
  - delta: `6208 ms`, with `validate_media` noise masking the removed `shot_planning=20964 ms`
- Current shipped first-pass one-pass baseline after Story 176 is materially different:
  - `real-ai-previz-runtime` now records shipped xAI one-pass first playable at `65514 ms`
  - isolated `ai_previz` on that route is `17649 ms`
  - this story now adds paired same-scene regenerate truth: `39325 ms` first playable for full regenerate versus `17869 ms` for `start_from=ai_previz` reuse on the same warmed substrate
- Answered question: the warmed current-scene regenerate loop does deserve a distinct operator-facing latency readout. The shipped xAI reuse path is materially faster than rerunning from recipe start, while the underlying provider video segment is effectively the same.

## Plan

### Exploration Notes

- **Files likely to change**: `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `real_ai_previz_runtime_cases.json`, `render.py`, `previz_adoption.py`, `PrevizPanel.tsx`, `ui/src/lib/types.ts`, runtime/adoption tests, the story, the eval registry, and likely `state.yaml`.
- **Files at risk of breakage**: oversized benchmark script `real_ai_previz_runtime_eval.py` (`560`), oversized UI contract `ui/src/lib/types.ts` (`768`), and the panel consumer `PrevizPanel.tsx` (`419`). Keep new logic out of `render_adapter_v1/main.py` unless the fresh regenerate measurement proves a real runtime defect there.
- **ADRs / decision docs consulted**: `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 152 / 171 / 175 / 176, `docs/evals/registry.yaml`.
- **Patterns to follow**: maintained benchmark surfaces over orphan detectors, schema-first backend↔UI changes, preflight-driven UI disclosure, and explicit first-playable versus full-completion truth.
- **Potential redundant code / cleanup targets**: lane-level latency copy that ignores regenerate-path truth, and stale methodology summary text that still stops at Story 175.

### Baseline / Eval Gate

- **Primary eval**: extend the maintained `real-ai-previz-runtime` harness so it can seed an existing-clip project state and compare:
  - shipped xAI full regeneration from recipe start on current scene
  - shipped xAI regenerate reuse via `start_from=ai_previz`
- **Baseline to record**:
  - current shipped first-pass one-pass truth from Story 176: `65514 ms` first playable, `17649 ms` isolated `ai_previz`
  - current historical reuse truth from old Story 152: `81545 ms` full regen vs `75337 ms` reuse on pre-xAI substrate
- **Candidate approaches**:
  - AI-only: rejected
  - Hybrid: extend maintained runtime measurement + surface operator truth from shared backend contract
  - Pure code: only if the fresh regenerate measurement says the current panel is already honest enough or exposes a tiny non-measured fix

### Repo-Fit / Optimality Evidence

- Story 176 already answered the provider-floor question on the honest one-pass lane. Repeating that line would violate the current state bias and the anti-fragmentation rule.
- ADR-002 requires the action boundary to explain what will happen now. The current panel already tells the user when CineForge will reuse the current shot plan, so the missing piece is measured latency truth for that exact branch.
- The repo already has one maintained runtime detector (`real-ai-previz-runtime`) and one shared operator-facing policy contract (`PrevizAdoptionService` / `PrevizLaneStatus`). Extending those is lower-risk and more honest than adding a story-local benchmark or UI-only heuristic.

### Structural Health Check

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — `560` lines, already large. Keep new behavior in helpers or small branches rather than widening one long control path.
- `ui/src/lib/types.ts` — `768` lines, already large. Add only the minimal new fields needed for the shared contract.
- `ui/src/components/PrevizPanel.tsx` — `419` lines, large but still locally owned. Keep disclosure changes small and reuse existing preflight/adoption badges instead of adding another panel.
- `benchmarks/scripts/real_ai_previz_runtime_support.py` (`359`), `src/cine_forge/services/previz_adoption.py` (`342`), `tests/unit/test_real_ai_previz_runtime_support.py` (`314`), and `tests/unit/test_previz_adoption_service.py` (`326`) are the preferred homes for most of the new logic.

### Implementation Order

1. Extend the runtime support schema and summary to represent regenerate cases and report a distinct regenerate winner.
   Done looks like: the support layer can summarize full-regenerate versus reuse cases without overloading the existing first-pass one-pass fields.

2. Extend the runtime eval harness and manifest to seed existing-clip state on the shipped xAI lane and rerun the current-scene regenerate comparison.
   Done looks like: a fresh runtime artifact records the shipped xAI regenerate loop with concrete full-regenerate versus reuse numbers on honest project state.

3. If the regenerate delta is material, add schema-first shared adoption fields and surface them in the panel only when preflight is reusing the current shot plan.
   Done looks like: the panel can distinguish first-pass lane truth from regenerate truth without inferring anything UI-side from raw registry prose.

4. Update the eval registry, story, and methodology truth with the fresh measured result and classifier status.
   Done looks like: `docs/evals/registry.yaml`, this story, and `docs/methodology/state.yaml` all agree on the active iteration-loop truth.

### UI Verification Plan

- Exercise the normal Scene Workspace route on a project where the current scene already has a healthy shot plan and at least one AI previz clip.
- Verify desktop and mobile:
  - the previz panel shows the shipped xAI lane
  - the reuse-path disclosure appears when preflight chooses `start_from=ai_previz`
  - any new regenerate-latency badge/copy only appears on the reuse branch and does not replace the broader lane truth elsewhere
- Confirm clean console output and capture screenshots of the reuse-path state.

### Human-Approval Blockers

- None. This is a bounded continuation of the existing Story 152 / 176 line and does not introduce a new public API family or architectural decision.

## Work Log

20260419-2046 — validation-rerun: reran the full required validation suite after closure rather than relying on the earlier close-out note. Fresh evidence from this validation pass only: `git status --short`, `git diff --stat`, `git diff`, and `git ls-files --others --exclude-standard` re-collected the local delta; `make test-unit PYTHON=.venv/bin/python` (`759 passed, 173 deselected, 1 warning`); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (clean); `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_previz_adoption_service.py -q` (`10 passed`); `pnpm --dir ui run lint` (clean); `cd ui && npx tsc -b` (clean); `pnpm --dir ui run build` (clean except the pre-existing chunk-size warning); `pnpm methodology:check` (current, with the pre-existing `api_service_and_operator_console` audit warning); `PYTHONPATH=src .venv/bin/python benchmarks/scripts/real_ai_previz_runtime_eval.py --fixture-manifest benchmarks/fixtures/real_ai_previz_runtime_cases.json --filter-case shipped_xai_4_480p_regenerate_full --filter-case shipped_xai_4_480p_regenerate_reuse --output-prefix benchmarks/results/real-ai-previz-runtime-story-152-xai-regenerate-2026-04-19 --repeat-count 1` (successful runtime rerun); and a fresh desktop/mobile browser pass on `http://127.0.0.1:5188/eval-real-ai-previz-shared-mvp_ingest_only-1-6e2703/scenes/scene_001?tab=previz` with `consoleErrors=[]` / `pageErrors=[]` plus updated screenshots at `output/browser-verification/story152-previz-desktop-2026-04-19.png` and `output/browser-verification/story152-previz-mobile-2026-04-19.png`. Fresh runtime truth: `shipped_xai_4_480p_regenerate_full` reached `39325 ms` first playable (`21363 ms` pre-`ai_previz` + `17962 ms` isolated `ai_previz`; `43952 ms` full completion), while `shipped_xai_4_480p_regenerate_reuse` reached `17869 ms` first playable / `20976 ms` full completion. Classification: no `model-wrong`, `golden-wrong`, or `ambiguous` mismatches remained; the detector is still explicitly `runtime-blocking` against the Ideal `<=6000 ms` target, but the implementation result still holds because the reuse path remains materially faster than full regenerate and the UI surfaces that distinction honestly. Next step: `/check-in-diff`.

20260419-2034 — close-out: marked Story 152 Done after the reopened shipped-xAI regenerate slice cleared its actual success surface. Evidence: `benchmarks/results/real-ai-previz-runtime-story-152-xai-regenerate-2026-04-19.{json,md}` records `35847 ms` first playable for full regenerate versus `17752 ms` for `start_from=ai_previz` reuse on honest existing-clip state; `docs/evals/registry.yaml` and `docs/methodology/state.yaml` now carry the fresh result, `git_sha`, and classifier truth; `output/browser-verification/story152-previz-desktop-2026-04-19.png` and `output/browser-verification/story152-previz-mobile-2026-04-19.png` show the reused-path disclosure plus the new `First pass` / `Full regen` truth on the real Scene Workspace route `http://127.0.0.1:5188/eval-real-ai-previz-shared-mvp_ingest_only-1-6e2703/scenes/scene_001?tab=previz` with `consoleErrors=[]` and `pageErrors=[]`; and the required local checks passed (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`, `pnpm --dir ui run lint`, `pnpm --dir ui run build`, `pnpm methodology:compile`, `pnpm methodology:check`). Classification: no `model-wrong`, `golden-wrong`, or `ambiguous` mismatches remained in the runtime harness; the remaining detector miss is explicitly `runtime-blocking` against the Ideal `<=6000 ms` target, but that blocker belongs to the broader fast-previz loop, not to this story’s success surface. Next step: `/check-in-diff`.

20260419-2026 — validation: reran the maintained runtime detector on the reopened shipped lane and verified the surfaced UI against a representative kept project. Runtime evidence: `benchmarks/results/real-ai-previz-runtime-story-152-xai-regenerate-2026-04-19.{json,md}` shows `shipped_xai_4_480p_regenerate_full` at `35847 ms` first playable (`18113 ms` pre-`ai_previz` + `17734 ms` isolated `ai_previz`; `39672 ms` full completion) and `shipped_xai_4_480p_regenerate_reuse` at `17752 ms` first playable / `21437 ms` full completion. Browser evidence: `output/browser-verification/story152-previz-desktop-2026-04-19.png` and `output/browser-verification/story152-previz-mobile-2026-04-19.png` on `eval-real-ai-previz-shared-mvp_ingest_only-1-6e2703` both show the reuse-path disclosure, measured regenerate copy, `First pass` badge, `Full regen` badge, and enabled `Regenerate AI Previz for Current Scene` button with zero console/page errors. Next step: close the story if the shared planning truth stays aligned after recompiling methodology outputs.

20260419-1956 — implementation: extended the maintained runtime harness to seed existing-clip state, thread regenerate-case metrics through the shared adoption contract, and expose distinct reuse-versus-full-regenerate truth in the Scene Workspace previz panel. Evidence: updated `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `src/cine_forge/schemas/render.py`, `src/cine_forge/services/previz_adoption.py`, `ui/src/lib/types.ts`, `ui/src/components/PrevizPanel.tsx`, and focused tests in `tests/unit/test_real_ai_previz_runtime_support.py` plus `tests/unit/test_previz_adoption_service.py`. Local seam checks passed immediately after implementation: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_previz_adoption_service.py -q` (`10 passed`), `.venv/bin/python -m ruff check src/cine_forge/services/previz_adoption.py src/cine_forge/schemas/render.py tests/unit/test_previz_adoption_service.py benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_support.py` (clean), `pnpm --dir ui run lint` (clean), and `pnpm --dir ui run build` (clean except existing chunk-size warning). Next step: run the live shipped-xAI regenerate benchmark, classify the result, and update eval/planning truth before closing.

20260419-1904 — reopened-story: reopened Story 152 after `/triage` identified the shipped xAI current-scene regenerate loop as the highest-leverage continuation of the active `spec:6` / `spec:7` lane. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 152 / 171 / 175 / 176, `docs/evals/registry.yaml`, `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `PrevizAdoptionService`, `PrevizPanel.tsx`, and current shipped xAI recipe/defaults. Key conclusion: this should be a reopen, not a new story shell, because the subsystem, operator-facing outcome, and validation boundary remain Story 152’s iteration-loop seam; the new trigger is Story 176’s shipped xAI one-pass lane plus the now-misaligned single-latency panel truth. Next step: extend the maintained runtime detector with regenerate cases, rerun the shipped xAI regenerate comparison, and surface distinct reuse-path latency only if the measured delta is material.

20260408-2018 — story-created: opened Story 152 as a distinct unblocker because the work moved from “shrink shot planning” to “avoid unnecessary replanning in the AI-previz loop.” Evidence: Story 149 is blocked on runtime, Story 150 measured the runtime envelope, and Story 151 already landed the compact planner. Next step: prove whether the current regenerate path is really rerunning `shot_planning`.

20260408-2024 — exploration: traced the current product/runtime path and found that `PrevizPanel` starts `ai_previz_generation` with `force=true` whenever an AI-previz artifact already exists, while `DriverEngine` only reuses stage cache when `force` is false. Mechanical benchmark setup on copied honest project state showed the full regen path paying `shot_planning=20.9637s` before entering provider video generation, while the sliced `start_from=ai_previz` path executes only `ai_previz` and `validate_media`. Evidence: `ui/src/components/PrevizPanel.tsx`, `src/cine_forge/driver/engine.py`, `output/runs/story152-regen-full-baseline/run_state.json`, and `output/runs/story152-regen-start-baseline/run_state.json`. Next step: implement a safe backend preflight recommendation for `start_from=ai_previz` and wire the UI to honor it.

20260408-2114 — runtime-benchmark: completed the paired regenerate benchmark on copied honest project state and recorded the result under `benchmarks/results/real-ai-previz-runtime-story-152-reuse-baseline-2026-04-08.{json,md}`. Result: `start_from=ai_previz` skipped `shot_planning` entirely and reduced wall time from `81545 ms` to `75337 ms`, but the net win was only `6208 ms` because `validate_media` was noisier on the sliced run (`21693 ms` vs `6704 ms`). Next step: finish the broader validation pass and browser-check that the real UI now sends the reuse start stage when planning is healthy.

20260408-2210 — validation: finished the honest UI verification against the live API-backed route `http://127.0.0.1:5174/story-149-real-ui-rerun/scenes/scene_001?tab=previz` using a disposable local Playwright install with system Chrome because the shared MCP browser profile was locked. Evidence: desktop and mobile screenshots at `/tmp/story152-previz-reuse-desktop.png` and `/tmp/story152-previz-reuse-mobile.png`, clean console output, visible reuse note, enabled `Regenerate AI Previz for Current Scene` button, and intercepted `/api/runs/start` payload containing `start_from: "ai_previz"` for `scene_001`. Next step: hand off Story 152 as implemented and validated, while keeping Story 149 blocked because first-time AI-previz latency is still dominated by provider generation and prerequisites.

20260408-2242 — close-out: marked Story 152 Done because the shipped slice is complete and verified. Evidence: backend and UI checks passed, honest browser validation confirmed the real Scene Workspace route sends `start_from: "ai_previz"`, and the runtime benchmark plus registry update show the iteration-loop improvement without overstating it. Remaining detector failure stayed runtime-blocking for Story 149, not for this story, because Story 152's first success surface was the regenerate reuse seam rather than first-time raw-input latency. Historical note only: Story 176 later changed the shipped lane to xAI and reopened this story on 2026-04-19 to refresh the iteration-loop truth. Next step at the time was `/check-in-diff`.
