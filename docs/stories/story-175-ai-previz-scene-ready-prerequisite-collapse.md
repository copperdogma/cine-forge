---
id: "175"
title: "AI Previz Scene-Ready Prerequisite Collapse"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:4.10.6"
  - "spec:4.10.7"
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "151"
  - "171"
  - "174"
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
  - "prerequisites"
  - "scene-ready"
  - "iteration-loop"
legacy_system: ""
---

# Story 175 — AI Previz Scene-Ready Prerequisite Collapse

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:4.10.6, spec:4.10.7, spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 151, Story 171, Story 174

## Goal

Story 171 proved that once healthy planning already exists, the honest current-scene AI-previz route reaches first playable at roughly `44237 ms` and only hides about `4s` after the clip exists. Story 174 then proved that same-shape fixed-pack prompt tweaks are effectively exhausted on the maintained `scene_ready` boundary: the best current case still lands at `186659 ms` to first playable, with `133291 ms` spent before `ai_previz` even starts and only `53368 ms` inside `ai_previz` itself. The dominant bounded hotspots are upstream prerequisites, especially the `creative_direction` run (`81188 ms` elapsed, with `story_world` the longest single-stage hotspot at `45492 ms`) plus `shot_planning` (`28102 ms`). This story exists to collapse that prerequisite cost on the honest scene-ready previz path without inventing a fake fast lane or falling back into another same-shape provider race.

## Acceptance Criteria

- [x] A measured simplification baseline exists for the maintained scene-ready previz boundary: test whether one bounded AI previz-prep pass can replace or subsume the current `creative_direction + shot_planning` prerequisite chain, and record the result files even if that approach is rejected.
- [x] The chosen implementation keeps previz product truth honest: preflight, run metadata, and prompt provenance explicitly show which prerequisite artifacts were reused, compacted, replaced by a one-pass prep artifact, or still auto-built. No silent fallback to the old full chain once a narrower route is claimed.
- [x] On an equivalent scene-ready runtime comparison, the shipped route reduces `prerequisite_elapsed_ms` by at least `20%` versus Story 174's `133291 ms` baseline, or the story records explicit blocker truth and leaves the shipped route unchanged.
- [x] If the prerequisite collapse materially changes compiled previz inputs or the prompt contract, refreshed `previz-usefulness` results stay at or above the validated Annotated Animatic floor of `0.803`; otherwise the story records why a usefulness rerun was unnecessary.
- [x] Focused regression coverage exists for the chosen prerequisite path (stage selection/reuse, upstream artifact health checks, prompt/provenance contract, and any new schema fields), and the maintained runtime surface in `docs/evals/registry.yaml` is updated with date, `git_sha`, result paths, and mismatch classification.
- [x] If operator-facing preflight, adoption, or previz provenance copy changes, desktop and mobile browser verification cover Scene Workspace previz plus any changed artifact-detail route with clean console output.

## Out of Scope

- Another fixed-pack provider-floor rerun without a new prerequisite-side hypothesis
- New video-provider transport or engine-pack integrations
- Final-render, breadth-first scene-generation, or project-cut work already closed by Stories 164-170
- Broad long-form screenplay throughput or methodology-tooling work
- Deterministic placeholder motion, impossible seeded substrate, or any fake "fast previz solved" claim

## Approach Evaluation

- **Simplification baseline**: Before adding more stage-specific optimization, test whether one bounded AI authoring call can already produce a previz-ready planning packet from the current scene plus existing project context. If that one-pass baseline beats the current prerequisite chain honestly, it is the simplest answer and should be measured first rather than argued about abstractly.
- **AI-only**: A single previz-prep call could replace `creative_direction` plus `shot_planning` for this route. That is attractive on orchestration cost, but risky for transparency, reusable concern-group artifacts, and ADR-003's compiled-prompt model if it degenerates into an opaque shortcut.
- **Hybrid**: Likely the best default. Reuse healthy project-level artifacts, collapse only the slowest scene-ready prerequisites, and keep prompt compilation/provenance explicit. This preserves the existing concern-group architecture while avoiding duplicated work on the previz path.
- **Pure code**: Only the right answer if measured time is mostly wasted on duplicated auto-builds, stale health checks, or overbroad preflight requirements. Latest evidence still shows real AI-stage cost in `story_world` and `shot_planning`, so pure code alone is unlikely to win without a stronger reuse story.
- **Repo constraints / ADRs**: ADR-002 requires honest warn/proceed behavior and explicit surfaced truth; ADR-003 keeps previz as a planning surface with concern groups upstream and prompts as read-only compiled artifacts. `spec:6.3.5` explicitly says slow AI previz must be stated honestly, not faked away. No newer ADR was found that narrows this line more specifically.
- **Existing patterns to reuse**: Story 151's compact shot-planning follow-on seam, Story 152's `start_from=ai_previz` reuse path, Story 171's first-playable truth, Story 174's runtime/usefulness harness, `scene_actions.py` preflight warnings, `scene_readiness.py`, `story_world_v1`, `shot_plan_v1`, and `render_adapter_v1/previz_prompting.py`.
- **Eval**: `real-ai-previz-runtime` remains the primary detector. If the chosen slice materially changes compiled previz inputs or prompt contract, rerun `previz-usefulness` too. If the one-pass baseline is tested, record it inside the maintained runtime/usefulness surfaces or a narrow sibling report rather than inventing a third orphan detector.

## Tasks

- [x] Measure the simplification baseline on the maintained scene-ready boundary: can one bounded previz-prep call replace or subsume the current `creative_direction + shot_planning` chain without dropping below the existing usefulness floor?
- [x] Trace the smallest honest prerequisite collapse after measurement. Prefer reuse of healthy artifacts and narrow compaction or bypass of the slowest stage(s) (`story_world`, `shot_planning`, or specific concern-group passes) over another pack/provider comparison.
- [x] Implement the chosen slice end to end in the owning runtime seams so preflight, run-state metadata, and prompt provenance stay honest about reused vs auto-built vs replaced prerequisites.
- [x] Add or extend focused tests for stage-selection/reuse logic, any new schema/runtime metadata, and any changed previz prompt/provenance contract.
- [x] Rerun the maintained runtime detector and, if required by the chosen slice, `previz-usefulness`; classify all significant mismatches and update `docs/evals/registry.yaml`.
- [x] If operator-facing preflight, adoption, or provenance copy changes, update the UI in the same story and browser-verify the changed surfaces.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: not applicable (`none touched`)
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

- **Owning class/module**: `src/cine_forge/pipeline/scene_actions.py` owns honest preflight and auto-build truth; `src/cine_forge/modules/creative_direction/story_world_v1/main.py` and the scene-scoped concern-group modules own the expensive upstream authoring passes; `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` owns previz planning substrate; and `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` owns the compiled previz prompt shape. Do not create a parallel previz subsystem unless the measured one-pass baseline clearly wins.
- **Data contracts**: Existing cross-layer contracts already live in `src/cine_forge/schemas/concern_groups.py`, `src/cine_forge/schemas/shot_plan.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/runtime_params.py`, and `src/cine_forge/schemas/scene_scope.py`. If new previz-prep or reuse metadata crosses service/API/UI boundaries, define it schema-first instead of smuggling dicts through run state or artifact metadata.
- **File sizes**: `make check-size` and `wc -l` show the main watchpoints: `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` (`1232`, LARGE), `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` (`695`, LARGE), `src/cine_forge/pipeline/scene_actions.py` (`571`, LARGE), `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`501`, LARGE), `ui/src/pages/SceneWorkspacePage.tsx` (`951`, LARGE), `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` (`736`, LARGE), and `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` (`692`, LARGE). More targeted likely files are `src/cine_forge/modules/creative_direction/story_world_v1/main.py` (`423`), `src/cine_forge/services/scene_readiness.py` (`60`), `src/cine_forge/schemas/render.py` (`249`), `src/cine_forge/schemas/runtime_params.py` (`60`), `src/cine_forge/schemas/scene_scope.py` (`56`), `ui/src/components/PrevizPanel.tsx` (`388`), `ui/src/components/AiPrevizViewer.tsx` (`292`), `ui/src/components/preview-provenance.ts` (`118`), `tests/unit/test_shot_planning_module.py` (`829`), `tests/unit/test_previz_prompting.py` (`170`), and `tests/integration/test_render_adapter_integration.py` (`541`).
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 151 / 171 / 174, `benchmarks/results/real-ai-previz-runtime-story-174-compact-candidate-2026-04-18.md`, `docs/evals/registry.yaml`, `src/cine_forge/pipeline/scene_actions.py`, and `docs/runbooks/promptfoo.md`. No newer ADR or design doc changed previz ownership beyond ADR-002 / ADR-003.

## Files to Modify

- `docs/stories/story-175-ai-previz-scene-ready-prerequisite-collapse.md` — keep the story current during build, validation, and close-out
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — add explicit prerequisite-strategy cases for the one-pass baseline and any shipped narrowed route (`11` cases today)
- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — measure the simplification baseline and the maintained scene-ready prerequisite split (`501`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — persist any added prerequisite-breakout or candidate metadata (`303`)
- `configs/recipes/recipe-ai-previz-generation.yaml` — adjust the shipped scene-ready prerequisite contract only if the measured winner changes the route (`80`)
- `configs/recipes/recipe-creative-direction.yaml` — fallback-only if the honest shipped scene-ready route still needs a narrower concern-group subset rather than a new prep artifact (`53`)
- `src/cine_forge/pipeline/scene_actions.py` — keep preflight and auto-build truth aligned with the chosen prerequisite collapse (`571`)
- `src/cine_forge/services/scene_readiness.py` — likely home for reusable scene-ready health checks if collapse logic needs a shared helper (`60`)
- `src/cine_forge/modules/creative_direction/story_world_v1/main.py` — likely hotspot owner for the current scene-ready chain (`423`)
- `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` — fallback-only touchpoint if the winning collapse narrows this pass (`736`)
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — fallback-only touchpoint if sound pass cost is part of the winning slice (`692`)
- `src/cine_forge/modules/creative_direction/character_and_performance_v1/main.py` — fallback-only touchpoint if character/performance prep becomes part of the narrowed previz path (`498`)
- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — current planning hotspot and Story 151 follow-on seam (`1232`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — wire any new prerequisite-truth metadata into prompt/video artifacts (`1658`)
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` — keep compiled previz prompt contract and provenance aligned with the chosen prep path (`695`)
- `src/cine_forge/schemas/preview.py` — schema-first home for operator-facing prerequisite provenance on previz artifacts (`61`)
- `src/cine_forge/schemas/render.py` — schema-first home for any new previz-prep or reuse metadata (`249`)
- `src/cine_forge/schemas/runtime_params.py` — if run metadata needs new fields for reused/replaced prerequisites (`60`)
- `src/cine_forge/schemas/scene_scope.py` — if scope or preflight semantics change (`56`)
- `tests/unit/test_real_ai_previz_runtime_support.py` — fixture/schema coverage for prerequisite-strategy expansion and summary math (`247`)
- `tests/unit/test_scene_actions.py` — preflight truth coverage for reused vs auto-built vs replaced prerequisites (`307`)
- `tests/unit/test_shot_planning_module.py` — stage-compaction and reuse coverage (`829`)
- `tests/unit/test_previz_prompting.py` — prompt/provenance contract coverage (`170`)
- `tests/unit/test_render_adapter_module.py` — fallback-only touchpoint if render adapter consumes new metadata (`918`)
- `tests/unit/test_render_schema.py` — schema-first coverage if preview/render provenance fields change (`204`)
- `tests/integration/test_render_adapter_integration.py` — honest scene-ready route regression coverage (`541`)
- `ui/src/components/PrevizPanel.tsx` — fallback-only if preflight/adoption copy changes (`388`)
- `ui/src/components/AiPrevizViewer.tsx` — fallback-only if prompt/provenance disclosure changes (`292`)
- `ui/src/components/RenderPromptViewer.tsx` — fallback-only if prompt detail needs to surface prerequisite-strategy truth (`363`)
- `ui/src/components/preview-provenance.ts` — fallback-only if candidate/provenance wording changes (`118`)
- `ui/src/pages/SceneWorkspacePage.tsx` — fallback-only if changed run/preflight truth cannot stay in smaller surfaces (`951`)
- `src/cine_forge/services/previz_adoption.py` — fallback-only if the shipped-lane recommendation or blocker wording changes (`324`)
- `docs/evals/registry.yaml` — record refreshed runtime/usefulness evidence, `git_sha`, result paths, and mismatch classification (`2551`)

## Redundancy / Removal Targets

- Duplicate previz-specific prerequisite work that recomputes full scene-ready context when healthy project-level artifacts already exist
- Any second home for scene-ready reuse truth split between `scene_actions.py`, runtime reports, and previz provenance once one schema-backed path wins
- Stale product or work-log framing that still treats fixed-pack provider churn as the primary next move after prerequisite collapse becomes the active owner

## Notes

- This is a new story rather than a reopen of Story 174 because the success surface changed. Story 174 closed the fixed-pack compare line and proved the next blocker is upstream prerequisite cost, not another prompt/provider tweak on the same pack race. That is the same product lane, but a different validation boundary.
- Story 171 proved the healthy-planning current-scene route can reach first playable in about `44.2s`, so the route-level surfacing seam is already solved once planning exists.
- Story 174 proved fixed-pack prompt compaction is effectively exhausted on the scene-ready boundary: compact Lite beat shipped Lite by only `605 ms`, while prerequisites still cost `133291 ms` before `ai_previz`.
- Current measured scene-ready hotspots are concrete: `creative_direction` took `81188 ms` elapsed, `story_world` was the longest single-stage hotspot at `45492 ms`, and `shot_planning` added `28102 ms` on the fastest current case.
- Recent architecture audits for `generation_and_visualization` and `api_service_and_operator_console` are clean, so this story should start as product/runtime work rather than a structural cleanup detour.
- If a one-call previz-prep baseline wins, that is simplification toward the Ideal, not a regression from ADR-003, as long as prompts remain compiled artifacts and provenance stays explicit.

## Plan

The implementation order is intentionally measurement-first. Story 174 already proved that another fixed-pack compare is a dead end here, so this story must first decide whether the honest route should become a schema-backed one-pass `previz prep` lane or a narrower hybrid reuse lane.

**Task 1 — Expand the maintained runtime detector so it can compare prerequisite strategies, not just engine packs**

- Files: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, `tests/unit/test_real_ai_previz_runtime_support.py`
- Change: widen the runtime-harness case schema beyond the current `scene_ready` vs `mvp_ingest_only` split so one-pass prep and any shipped narrowed route can run through the same detector. Persist which prerequisite strategy ran, the per-stage prerequisite breakdown, and which artifacts were reused or replaced.
- Repo-fit evidence: the current harness already measures the right boundary by splitting shared prerequisites from `start_from=ai_previz`; it just cannot yet compare a one-pass prep candidate. Reusing this harness keeps Story 175 on the maintained `real-ai-previz-runtime` surface instead of creating a third orphan detector.
- Risk / impact: this touches a `501`-line script, so keep the change local to case-schema parsing, prerequisite-plan materialization, and summary rendering rather than widening unrelated harness code.
- Done means: one result file can show Story 174’s current scene-ready baseline alongside a one-pass or narrowed prerequisite candidate, with no ambiguity about what the prerequisite bundle was.

**Task 2 — Measure the simplest route first: a one-pass previz-prep baseline**

- Files: likely `benchmarks/...` from Task 1 plus the smallest new runtime seam required to materialize the candidate; if a new cross-layer artifact is needed, define it schema-first in `src/cine_forge/schemas/preview.py` and/or `src/cine_forge/schemas/render.py` before code uses it.
- Change: implement only enough code to let the harness run one bounded AI prep pass that can replace or subsume the current `creative_direction + shot_planning` prerequisite chain for current-scene AI previz. Keep the artifact explicit and inspectable; do not smuggle opaque dicts through run state.
- Repo-fit evidence: this directly follows the story goal, the build-story eval-first rule, and AGENTS guidance to test the simplest AI answer before building more orchestration. ADR-003 still allows it as long as prompts remain read-only compiled artifacts and provenance stays explicit.
- Decision gate after measurement:
  - Ship AI-only only if it honestly clears the `20%` prerequisite reduction bar and does not require hidden fallback.
  - If AI-only beats runtime but misses usefulness or provenance clarity, keep it as measured evidence only and ship the narrower hybrid instead.
  - Reject another provider/pack sweep unless the prerequisite-side measurement changes the boundary materially.
- Done means: the story contains a recorded baseline result for the one-pass candidate, even if the candidate is rejected.

**Task 3 — Ship the smallest honest prerequisite collapse that fits this repo**

- Expected default: a narrower hybrid route, not a parallel previz subsystem.
- Files: `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/pipeline/scene_actions.py`, `src/cine_forge/services/scene_readiness.py`, `src/cine_forge/modules/creative_direction/story_world_v1/main.py`, `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`, schema/test files listed above
- Change: collapse only the slow prerequisite work that the current previz lane does not need to wait on. Repo-specific evidence strongly points here:
  - `recipe-ai-previz-generation.yaml` auto-builds `timeline`, `tracks`, and `shot_planning`, but it only warns on missing direction artifacts.
  - `render_adapter_v1/previz_prompting.py` compiles from `shot_plan`, `intent_mood`, `rhythm_and_flow`, `look_and_feel`, `sound_and_music`, and resolved inputs; it does not consume `story_world` directly.
  - `story_world` (`45492 ms`) and full `creative_direction` (`81188 ms`) are currently the biggest scene-ready cost centers.
- Chosen seam criteria:
  - Prefer reusing healthy project-level artifacts over regenerating them.
  - Prefer shrinking the contract around artifacts actually consumed by previz over keeping the full chain out of habit.
  - If the winning path still needs a new artifact, make it a first-class schema-backed artifact instead of a hidden shortcut.
- Structural health guardrails:
  - `shot_plan_v1/main.py` is `1232` lines, `previz_prompting.py` is `695`, and `scene_actions.py` is `571`; do not dump new branchy logic into those files without extracting a focused helper first.
  - Any new operator-facing preflight or provenance shape must be schema-first in `scene_scope.py`, `preview.py`, or `render.py` before service/UI code consumes it.
  - No new event type is expected; if that changes, add it schema-first.
- Done means: the shipped current-scene previz route has one honest prerequisite contract, and the old full-chain fallback is no longer silently implied once the narrower route is claimed.

**Task 4 — Surface prerequisite truth in preflight, run metadata, and prompt/video provenance**

- Files: `src/cine_forge/pipeline/scene_actions.py`, `src/cine_forge/schemas/scene_scope.py`, `src/cine_forge/schemas/preview.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`, `tests/unit/test_scene_actions.py`, `tests/unit/test_previz_prompting.py`, `tests/unit/test_render_adapter_module.py`, `tests/unit/test_render_schema.py`
- Change: make every operator-visible surface say which prerequisite strategy ran and which artifacts were reused, auto-built, compacted, or replaced. This includes preflight, prompt detail, and persisted previz/video provenance.
- Repo-fit evidence: ADR-002 requires warn/proceed truth instead of silent magic, and `spec:6.3.5` explicitly rejects fake speed claims. The current code already carries `preview_provenance` and compiled prompt sections, so the right move is to extend those honest surfaces rather than invent a second metadata home.
- Done means: inspecting the preflight card or prompt detail answers “what did CineForge actually wait for?” without opening run-state internals.

**Task 5 — UI copy only if the operator-facing truth changes**

- Files: `src/cine_forge/services/previz_adoption.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/RenderPromptViewer.tsx`, `ui/src/components/preview-provenance.ts`
- Change: only touch UI if the new prerequisite contract needs new labels or disclosure. Keep the change in the smaller previz components; avoid pushing story-specific logic into `SceneWorkspacePage.tsx` (`951`) unless there is no smaller seam.
- Browser verification plan if this task is touched:
  - Desktop: Scene Workspace → Previz tab → inspect preflight copy → start current-scene AI previz → open prompt detail and AI previz detail.
  - Mobile: repeat the same path in a narrow viewport and confirm badges/copy stay legible with clean console output.
  - Fallback if browser tooling is unavailable: follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.
- Done means: the operator can tell the difference between a reused-shot-plan rerun, a narrowed prerequisite run, and any one-pass prep route without reading code.

**Task 6 — Validate, classify mismatches, and update the maintained eval surface**

- Required checks:
  - Backend: `make test-unit PYTHON=.venv/bin/python`
  - Lint: `.venv/bin/python -m ruff check src/ tests/`
  - If UI changed: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`
- Evals:
  - Always rerun `real-ai-previz-runtime` on the maintained scene-ready detector.
  - Rerun `previz-usefulness` only if the shipped path materially changes compiled previz inputs or the prompt contract; otherwise record why the rerun was unnecessary.
  - Classify every significant mismatch as `model-wrong`, `golden-wrong`, or `ambiguous`, and record whether any remaining issue is `runtime-blocking` or `non-runtime-blocking`.
  - Update `docs/evals/registry.yaml` with the new date, `git_sha`, result path, and classification notes.
- Done means: Story 175 can prove either that prerequisites dropped by at least `20%` on the honest route or that the blocker truth is now tighter and should stop more same-shape retries.

**Alternatives rejected up front**

- Another provider-pack comparison: rejected because Story 174 only improved first-playable by `605 ms`, while prerequisites still cost `133291 ms`.
- Pure code-only reuse work: unlikely to win alone because the measured hotspot is dominated by real AI stage time (`story_world`, `shot_planning`), not just orchestration overhead.
- Shipping an opaque AI shortcut immediately: rejected because ADR-002 / ADR-003 and `spec:6.3.5` require visible upstream truth and compiled-prompt transparency.

**Human-approval blockers**

- No new dependency, migration, or public API blocker is expected.
- The only meaningful execution risk is scope: if the one-pass baseline clearly wins, this story may need a new schema-backed artifact/module rather than only narrowing the existing route. That is still inside Story 175, but it is the branch point to keep visible before implementation starts.

## Work Log

20260418-2349 — story-created: packaged the next previz climb after Story 174 proved fixed-pack prompt/profile tweaks are exhausted on the scene-ready boundary. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 151 / 171 / 174, `docs/evals/registry.yaml`, and `benchmarks/results/real-ai-previz-runtime-story-174-compact-candidate-2026-04-18.md`; key result was `133291 ms` of prerequisites before `53368 ms` of `ai_previz` on the fastest current case. Anti-fragmentation check: a new story is justified because Story 174 closed the fixed-pack comparison surface, while this story owns upstream prerequisite collapse. Next step: `/build-story 175`.
20260419-1059 — exploration: traced Story 175 across the maintained runtime harness, generation preflight, shot planning, previz prompt compilation, scene-readiness UI, and current eval registry before choosing an implementation seam. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `configs/recipes/recipe-ai-previz-generation.yaml`, `configs/recipes/recipe-creative-direction.yaml`, `src/cine_forge/pipeline/scene_actions.py`, `src/cine_forge/services/scene_readiness.py`, `src/cine_forge/modules/creative_direction/story_world_v1/main.py`, `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`, `src/cine_forge/schemas/preview.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/services/previz_adoption.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/RenderPromptViewer.tsx`, and ADR-002 / ADR-003. Key repo-specific finding: the shipped `ai_previz_generation` recipe already only auto-builds `timeline`, `tracks`, and `shot_planning`, while the maintained scene-ready detector still pays for full `creative_direction`; `story_world` is the single biggest hotspot even though `previz_prompting.py` does not consume it directly. Structural risk: `shot_plan_v1/main.py` (`1232`), `previz_prompting.py` (`695`), and `scene_actions.py` (`571`) are oversized watchpoints, so the likely winning path is a schema-backed prerequisite-truth helper or new prep artifact, not another branch pile inside those files. Next step: present the plan and stop at the approval gate before implementation.
20260419-1118 — implementation-started: user approved the Story 175 plan, so the story moved from `Pending` to `In Progress` before code changes. Next step: regenerate methodology surfaces, then implement the measurement/provenance seam around the existing on-demand previz prep route before deciding whether a larger prep artifact is necessary.
20260419-1308 — implementation: made prerequisite strategy a schema-backed first-class truth across the honest previz path instead of an implicit eval-only distinction. Evidence: `src/cine_forge/schemas/scene_scope.py` now records `prerequisite_strategy`, reused/auto-build/missing-optional artifact types in preflight; `src/cine_forge/schemas/preview.py` and `src/cine_forge/modules/generation/render_adapter_v1/main.py` persist the same truth into prompt/video provenance; `src/cine_forge/pipeline/scene_actions.py` prunes stale auto-build claims when the route already reuses shot planning; `benchmarks/scripts/real_ai_previz_runtime_eval.py` and `..._support.py` now compare prerequisite strategies; `src/cine_forge/services/previz_adoption.py` now prefers the maintained runtime detector over older usefulness-only latency. Regression evidence: `tests/unit/test_scene_actions.py`, `tests/unit/test_render_adapter_module.py`, `tests/unit/test_previz_adoption_service.py`, and `tests/unit/test_real_ai_previz_runtime_support.py` all passed in the focused seam run before the full suite. Operator impact: Scene Workspace and artifact detail now answer “what did CineForge actually wait for?” without forcing the operator to inspect hidden run state. Next step: run the maintained runtime compare and browser-verify the changed disclosure surfaces.
20260419-1506 — validation: Story 175 proved the one-pass previz-prep lane is the honest shipped winner and left a clean evidence trail for both runtime and UI truth. Evidence: `benchmarks/results/real-ai-previz-runtime-story-175-prereq-strategy-2026-04-19.{json,md}` measured `shipped_lite_4_mvp_ingest_only` at `99540 ms` to first playable with `45801 ms` of prerequisites versus `194199 ms` / `140342 ms` for the paired full `scene_ready` chain, which is a `65.6%` prerequisite reduction versus Story 174's `133291 ms` baseline and a `67.4%` reduction versus the same-run full-chain control. Static checks: `make test-unit PYTHON=.venv/bin/python` (`755 passed, 172 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed; the only backend noise was the pre-existing `PytestUnknownMarkWarning` for `acceptance`. Browser evidence: desktop and mobile Scene Workspace previz plus fresh `v2` artifact-detail routes were verified with clean console output using representative project `eval-real-ai-previz-shared-scene_ready-1-d09a2c`; screenshots were captured under `/tmp/story175-browser-final/` (`scene-previz-desktop.png`, `scene-previz-mobile.png`, `prompt-detail-desktop.png`, `ai-previz-detail-desktop.png`, `ai-previz-detail-mobile-strategy.png`, `scene-previz-desktop-latency-focused.png`). After `docs/evals/registry.yaml` was updated, `/api/projects/eval-real-ai-previz-shared-scene_ready-1-d09a2c/previz/adoption` returned the new `99540 ms` lane latency and the refreshed desktop Scene Workspace badge rendered as `Avg 99.5s`. Mismatch classification: no `model-wrong`, `golden-wrong`, or `ambiguous` mismatches remained; the maintained detector stays runtime-blocking only because `99540 ms` still misses the `<=6000 ms` fast-previz target. `previz-usefulness` was not rerun because the shipped compiled previz inputs and prompt contract did not change; this story only surfaced honest prerequisite/runtime truth around the existing one-pass route. Next step: hand off build-complete implementation and recommend `/validate 175`.
20260419-1649 — validation-pass: reran the full validation suite after fixing the registry lineage mismatch surfaced by `pnpm methodology:check`, and the story is now validation-complete. Fresh static evidence: `make test-unit PYTHON=.venv/bin/python` (`755 passed, 172 deselected`, same pre-existing `PytestUnknownMarkWarning` for `acceptance`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:compile`, and `pnpm methodology:check` all passed; the only remaining methodology warning is the pre-existing `api_service_and_operator_console` architecture-audit due flag. Fresh runtime evidence: `benchmarks/results/real-ai-previz-runtime-story-175-validation-2026-04-19.{json,md}` measured `shipped_lite_4_mvp_ingest_only` at `96821 ms` to first playable with `44048 ms` of prerequisites versus `209021 ms` / `156144 ms` for the paired full `scene_ready` chain, so the validation rerun preserved the same winner and improved the shipped lane slightly. Fresh browser evidence: representative project `eval-real-ai-previz-shared-scene_ready-1-d09a2c` was rechecked in desktop and mobile with clean console output after the validation registry row landed; screenshots live under `/tmp/story175-validation-browser/` (`scene-previz-desktop.png`, `scene-previz-mobile.png`, `prompt-detail-desktop.png`, `ai-previz-detail-desktop.png`, `ai-previz-detail-mobile.png`) and the Scene Workspace now renders the updated `Avg 96.8s` badge. Mismatch classification remains clean: no `model-wrong`, `golden-wrong`, or `ambiguous` mismatches; `real-ai-previz-runtime` is still runtime-blocking only because `96821 ms` misses the `<=6000 ms` target, and `previz-usefulness` still did not require a rerun because the shipped compiled previz inputs/prompt contract never changed. Next step: `/mark-story-done 175`.
20260419-1758 — completion: closed Story 175 after confirming the shipped one-pass previz-prep lane remains the honest winner and the methodology/eval surfaces already carry the latest validation truth. Evidence: the story has build + validation gates checked, `docs/evals/registry.yaml` points at `benchmarks/results/real-ai-previz-runtime-story-175-validation-2026-04-19.{json,md}`, and the latest validation rerun still shows `96821 ms` first playable / `44048 ms` prerequisites for the shipped lane versus `209021 ms` / `156144 ms` for the paired full chain, with no `model-wrong`, `golden-wrong`, or `ambiguous` mismatches. Operator impact: CineForge now tells the truth about reused vs auto-built vs missing-optional previz prerequisites while holding the faster one-pass lane as the shipped route. Next step: `/check-in-diff`.
