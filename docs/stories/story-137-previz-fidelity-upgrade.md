---
id: "137"
title: "Previz Fidelity Upgrade"
status: "Done"
priority: "Low"
ideal_refs:
  - "R8 (professional-grade motion assets), R10 (playable assembly at every stage), R17 (partial workflows and real-world asset support)"
spec_refs:
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.3"
  - "spec:6.4"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "027"
  - "028"
  - "030"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 137 — Previz Fidelity Upgrade

**Priority**: Low
**Status**: Done
**Ideal Refs**: R8 (professional-grade motion assets), R10 (playable assembly at every stage), R17 (partial workflows and real-world asset support)
**Spec Refs**: spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:6.4 (Keyframes), spec:10.3 (Always-Playable Rule), spec:7.1 (Render Adapter Layer — candidate shared substrate)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / concern-group inputs)
**Depends On**: Story 027 (current previz baseline), Story 028 (landed render substrate), Story 030 (landed video-QA / eval substrate)

## Goal

Story 027 proves that CineForge can generate and review animatics end to end, but its current output is deliberately symbolic: stills, simple motion, and temp audio. That satisfies the capability gap, but it may not be useful enough for real blocking, camera study, or future AI-generation handoff. This story upgrades previz from "exists" to "usefully informative" by evaluating and, if justified, implementing a richer previz mode that still behaves like previz: lower-detail, advisory, and focused on motion, camera placement, actor blocking, and pacing rather than surface polish. The key open question is not "how do we make previz prettier?" but "what mode produces meaningfully better human review value without collapsing previz into final render?"

## Acceptance Criteria

- [x] A documented eval compares the current Story 027 symbolic animatic baseline against at least two richer previz candidates on the same fixed scene set, including the landed shared-render low-detail path and one repo-fit non-final alternative, using a rubric focused on camera placement, blocking clarity, motion readability, and pacing usefulness.
- [x] If a richer previz mode is adopted, it is available through the same end-to-end operator path as existing animatics: recipe/module output, Scene Workspace review, Artifact Detail viewing, and timeline track resolution all stay coherent.
- [x] The chosen previz mode persists explicit provenance for `mode`, `fidelity_intent`, upstream inputs, and cost/latency so operators can tell whether they are looking at symbolic animatic, richer previz, or final render.
- [x] Richer previz remains advisory and optional: it is not required to proceed downstream, is not silently substituted for final render, and does not erase the cheap symbolic fallback unless the replacement is clearly superior and intentionally adopted.
- [x] If the chosen path uses AI video generation, the story adds or updates a previz usefulness eval and records results in `docs/evals/registry.yaml`; if no existing eval substrate fits, the story creates one.

## Out of Scope

- Replacing Story 027's symbolic animatics immediately; that baseline remains valid unless this story lands measured evidence for a different default.
- Making previz mandatory before render or export.
- Building a general-purpose 3D editor, DCC workflow, or full NLE inside CineForge.
- Solving final generated-video QA or multimodal media validation end to end; this should coordinate with Story 030 and the inbox item on agentic video/audio validation.
- Assuming AI video models will accept reference video as an input. Human review value is the primary bar; downstream AI-conditioning value is optional.

## Approach Evaluation

- **Simplification baseline**: A single shared-video generation call may already be good enough if prompted for low-detail blocking rather than polish. The first build task should measure whether the landed render path, using current shot plans/keyframes/reference assets, already produces previz that a human would actually use before adding new substrate.
- **AI-only**: Reuse the same video-generation substrate as final render but prompt for "blocking-first" output: accurate camera path, actor placement, motion, and pacing with deliberately reduced surface detail. Pros: semantically rich output and likely best chance of actual usefulness. Cons: may cost nearly as much as final render and may blur the operator's mental model of what previz is for.
- **Hybrid**: Code compiles a structured previz package from shot plan, keyframes, concern-group context, and real-world reference assets; the backend can target either a low-detail video-generation mode or a constrained scene-blocking generator. Pros: preserves provenance and allows multiple backends. Cons: more orchestration complexity and potentially more UI surface area.
- **Pure code**: Build a richer deterministic previz variant that stays inside the existing visualization lane: better timing, camera-path signaling, blocking overlays, or slightly richer composition metadata without introducing a new 3D toolchain. Pros: preserves cheap fallback semantics, fits the current repo, and gives a real non-video comparison branch. Cons: may still lose on motion readability versus generated video.
- **Repo constraints / ADRs**: ADR-003 says previz belongs in Scene Workspace and consumes concern-group and real-asset context, not isolated prompt hacks. ADR-002 says downstream actions need visible diagnostics and preflight, not hidden backend magic. Story 027 already established the user-facing previz loop. Story 028 already landed the correct shared-video substrate if that path wins. `src/cine_forge/modules/visualization/animatic_v1/support.py` is already oversized at 563 lines, while `ui/src/pages/SceneWorkspacePage.tsx` and `ui/src/pages/ArtifactDetail.tsx` are already large, so the eventual build should bias toward new focused modules/components instead of stuffing more logic into the existing files.
- **Existing patterns to reuse**: Story 027 animatic/keyframe/previz schemas and review surfaces, Story 029 user asset injection, Story 028 render adapter and engine packs, Story 030 media QA plus the current `video-understanding` benchmark substrate, the track-manifest/always-playable system, project-relative asset serving, and the existing Scene Workspace / Artifact Detail visualization pattern.
- **Eval**: No current eval entry exists in `docs/evals/registry.yaml` for previz usefulness. The winning approach should be selected by comparing the same scenes across (a) current symbolic animatic, (b) the shared video-generation low-detail mode, ideally including the cheapest credible current fast-video tier, and (c) one repo-fit richer deterministic previz variant, then scoring for blocking clarity, camera readability, pacing usefulness, controllability, and cost/latency. Raw visual impressiveness is not enough.

## Tasks

- [x] Establish the simplification baseline: measure whether the landed shared-video generation path already produces human-useful low-detail previz from current shot plans, keyframes, and reference assets.
- [x] Prototype at least two richer previz candidates on the same fixed scene set:
  - [x] shared render-pipeline low-detail mode
  - [x] one repo-fit non-final-render alternative inside the existing visualization lane
- [x] Define the eval rubric and missing eval harness for previz usefulness; record the measured winner in `docs/evals/registry.yaml`.
- [x] Extend previz schemas/contracts to persist `mode`, `fidelity_intent`, upstream inputs, and intended use (`human review`, `AI conditioning`, or both`) before wiring any new backend path through the UI.
- [x] If a richer previz path is adopted, implement it end to end in the same story: backend generation, track integration, Scene Workspace, Artifact Detail, artifact metadata, run labels, and browser verification.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; no skill or project-instruction changes were part of Story 137 implementation)
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Architectural Fit

- **Owning class/module**: Do not keep growing `animatic_v1/support.py`. If richer previz stays in the visualization lane, it likely needs a new focused helper/module with `animatic_v1` retained as the cheap fallback. If the shared video-generation path wins, the already-landed `render_adapter_v1` is the natural owner for generation while Scene Workspace and Artifact Detail remain thin consumers.
- **Data contracts**: `src/cine_forge/schemas/animatic.py` is the current contract surface and likely needs explicit mode/fidelity/provenance fields or a sibling richer-previz schema. Any cross-layer payload must be schema-first. If prompt artifacts or generated-video contracts are shared with render, reuse typed schemas rather than ad hoc dicts.
- **File sizes**: `make check-size` currently flags `src/cine_forge/modules/generation/render_adapter_v1/main.py` at 1338 lines, `src/cine_forge/modules/visualization/animatic_v1/support.py` at 563 lines, `ui/src/pages/SceneWorkspacePage.tsx` at 758 lines, and `ui/src/pages/ArtifactDetail.tsx` at 634 lines. `benchmarks/scorers/video_understanding_scorer.py` is also already 586 lines, so benchmark work should prefer a sibling scorer/helper over further inflating it. Likely touched but smaller files today: `src/cine_forge/schemas/animatic.py` (126), `src/cine_forge/schemas/render.py` (167), `ui/src/components/AnimaticsPanel.tsx` (250), `ui/src/components/AnimaticViewer.tsx` (210), `ui/src/components/PrevizReelViewer.tsx` (106), and `ui/src/components/GeneratedVideoPanel.tsx` (305).
- **Decision context**: Reviewed `docs/ideal.md` (R8, R10, R17), `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:10.3`, `spec:7.1`), `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, and `docs/decisions/adr-003-film-elements/adr.md`. No existing previz usefulness eval currently exists in `docs/evals/registry.yaml`.

## Files to Modify

- `benchmarks/tasks/` — add a previz-usefulness task or a thin sibling to the current video-understanding task
- `benchmarks/prompts/` — add or refine the judging prompt for blocking/camera/pacing usefulness
- `benchmarks/scorers/` — add a focused scorer/helper without growing the existing 586-line video-understanding scorer unnecessarily
- `tests/animatic_fixtures.py` and `tests/render_fixtures.py` — provide fixed comparison fixtures for symbolic and shared-video candidates
- `src/cine_forge/schemas/animatic.py` — extend previz/animatic contracts with mode/fidelity/provenance fields if the winning path needs them (126 lines)
- `src/cine_forge/schemas/render.py` — extend render/video provenance fields if the shared-video path wins (167 lines)
- `src/cine_forge/modules/visualization/animatic_v1/main.py` — adapt orchestration only if the cheap fallback remains clean (434 lines)
- `src/cine_forge/modules/visualization/animatic_v1/support.py` — extraction/removal target only; do not pile more core logic into the current 563-line file
- `src/cine_forge/modules/generation/render_adapter_v1/` — likely owner if the shared video-generation path wins
- `ui/src/components/AnimaticsPanel.tsx` — expose richer previz mode, limitations, and provenance if operator-visible mode selection is needed (250 lines)
- `ui/src/components/AnimaticViewer.tsx` — show richer previz metadata and playback context (210 lines)
- `ui/src/components/GeneratedVideoPanel.tsx` — show shared-video previz provenance if this becomes part of the operator path (305 lines)
- `ui/src/components/PrevizReelViewer.tsx` — surface project-level mode labels and review affordances (106 lines)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only; avoid growing the 758-line page
- `ui/src/pages/ArtifactDetail.tsx` — thin routing only; avoid growing the 634-line page
- `docs/evals/registry.yaml` — add previz usefulness eval entry and measured results once they exist

## Redundancy / Removal Targets

- The current symbolic-only motion compositor as the implied "best" previz path if a richer mode clearly wins; either demote it to an explicit `symbolic` mode or keep it only as the cheap fallback.
- Any UI copy or artifact labels that treat all previz outputs as equivalent once multiple fidelity modes exist.
- Temporary bridges between previz and final-render logic if the chosen implementation converges on the render-adapter substrate.

## Notes

- Story 027 already solved the existence problem. This story is only worth doing if it solves the usefulness problem.
- Previz is not just "cheaper final render." Its value is lower-detail focus: blocking, motion, camera placement, pacing, and shot intent without getting distracted by finish polish. If a candidate path costs the same as final render, it still needs to justify itself by improving iteration clarity or controllability.
- Many AI video generators do not accept reference video, so AI-conditioning value is a bonus rather than the primary success condition.
- A bespoke 3D/blocking path is explicitly the wrong default for this repo today unless the benchmark disproves both the shared-video lane and a repo-fit richer deterministic alternative.
- Inbox triage on 2026-04-01 folded the "Gemini Veo 3.1 Light" idea into this story rather than creating a duplicate. The real question is not a new feature but whether the cheapest serious shared-video lane is already good enough for human-useful previz.
- Coordinate with the inbox item on agentic video/audio validation. Framegrabs alone are not enough to judge richer previz or generated motion.

## Plan

1. Benchmark the usefulness gap before changing product behavior.
   Files: `benchmarks/tasks/`, `benchmarks/prompts/`, `benchmarks/scorers/`, `tests/animatic_fixtures.py`, `tests/render_fixtures.py`, `docs/evals/registry.yaml`.
   Change: add a fixture-backed previz-usefulness eval that compares the current symbolic animatic baseline against two richer candidates on the same scenes. Reuse the landed video-understanding substrate instead of inventing a second eval framework. The candidate set should be: current symbolic animatic, shared low-detail render via the existing render adapter/engine packs, and one repo-fit richer deterministic previz variant inside the visualization lane.
   Impact / risk: benchmark logic can easily bloat `benchmarks/scorers/video_understanding_scorer.py` (586 lines) or fork eval conventions. Keep new scoring logic in a sibling scorer/helper unless a tiny extraction is enough. This task also sets the baseline number the rest of the story must beat.
   Done when: the comparison harness runs on fixed fixtures, baseline and candidate results are recorded, and `docs/evals/registry.yaml` has a fresh entry with date and git SHA for the measured eval.

2. Choose the winning path, then lock contracts before UI or orchestration changes.
   Files: `src/cine_forge/schemas/animatic.py`, `src/cine_forge/schemas/render.py`, story doc/work log.
   Change: use the benchmark to choose whether Story 137 should adopt a richer path at all. If a richer mode wins, add schema-first provenance fields for `mode`, `fidelity_intent`, `intended_use`, upstream inputs, and cost/latency before wiring any backend or UI changes. If no richer mode wins clearly, keep Story 027 as the default and close the story around the measured evidence instead of forcing a feature.
   Repo-fit evidence: this follows ADR-002 and ADR-003 by keeping the operator path explicit and debuggable, and it matches the Ideal by improving review usefulness rather than building speculative substrate. It also reuses the already-landed Story 027/028/030 stack instead of inventing a new toolchain.
   Done when: the chosen path and its typed contract are explicit, with no ad hoc dict payloads crossing engine, API, or UI boundaries.

3. Implement the thinnest end-to-end path for the winner while preserving the cheap fallback.
   Files: conditional on the winner, likely `src/cine_forge/modules/generation/render_adapter_v1/`, selected `ui/src/components/*` viewers, and thin routing in `ui/src/pages/SceneWorkspacePage.tsx` / `ui/src/pages/ArtifactDetail.tsx`.
   Change: if the shared-video path wins, thread it through the existing generation/review surfaces with explicit provenance and no silent substitution for final render. If the deterministic richer-previz path wins, keep it in a focused helper/module rather than growing `animatic_v1/support.py`. In both cases, preserve the symbolic baseline as an explicit cheap fallback unless the replacement is clearly superior and intentionally adopted.
   Structural health check: avoid adding new logic directly to `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1338 lines), `src/cine_forge/modules/visualization/animatic_v1/support.py` (563 lines), `ui/src/pages/SceneWorkspacePage.tsx` (758 lines), or `ui/src/pages/ArtifactDetail.tsx` (634 lines). No new event type is expected; if that changes, `src/cine_forge/schemas/events.py` must be updated first.
   Done when: operators can generate and review the winning previz mode through the same path as current animatics/generated video, and the artifact clearly states what mode they are looking at.

4. Verify, clean up, and leave the story ready for `/validate`.
   Files: touched tests/docs plus `docs/evals/registry.yaml`.
   Change: run `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, and the UI lint/typecheck/build trio if any `ui/` files changed. If the story touches the eval harness, run the relevant promptfoo task and classify any mismatches via `/improve-eval` before close-out. Remove redundant copy/helper paths that assume all previz outputs are symbolic-only, or record the follow-up explicitly if removal would blur validation.
   UI verification plan: use browser tools against the Scene Workspace previz flow and Artifact Detail playback view; if browser tooling blocks, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
   Done when: checks pass, browser verification evidence exists for any UI change, registry scores are fresh, and the work log records the decisions, evidence, and any follow-up.

Recommended scope adjustment before implementation: replace the original speculative 3D/blocking branch with a repo-fit richer deterministic previz comparison inside the existing visualization lane. That keeps the story at `M` scope instead of turning it into a larger new-substrate project. Secondary approval blocker: if the benchmark shows the current engine packs are the wrong shared-video candidate, I may need to add one cheaper/faster pack as a narrow follow-on inside this story (`S`).

## Work Log

20260318-1646 — story created: User reviewed the Story 027 smoke project and confirmed the feature works but the current symbolic previz may not be useful enough for real-world blocking or future AI-generation handoff. Captured the future enhancement as a separate low-priority Draft instead of silently expanding Story 027. Evidence reviewed while drafting: `docs/ideal.md` (R8/R10/R17), `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:10.3`, `spec:7.1`), ADR-002, ADR-003, the current Story 027 implementation/files, and `docs/evals/registry.yaml` (no existing previz usefulness eval entry). Candidate directions recorded: shared low-detail video-generation path and structured 3D/blocking path. Next step: promote only when someone is ready to measure usefulness against the current symbolic baseline.
20260401-1642 — inbox triage: folded the cheap-Google-video-model idea into this story instead of creating a duplicate. The immediate follow-up is to benchmark the cheapest serious shared-video candidate in the existing low-detail render branch before inventing new previz substrate. Next step: keep Draft until someone is ready to run the usefulness eval.
20260402-1830 — build-story exploration + planning: promoted the story to Pending, updated the story index, and re-scoped the plan around benchmark-first repo-fit decisions instead of speculative missing substrate. Evidence reviewed: `docs/ideal.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:10.3`, `spec:7.1`), ADR-002, ADR-003, Story 027, Story 028, Story 030, the current animatic/render schemas and recipes, Scene Workspace / Artifact Detail viewers, `benchmarks/tasks/video-understanding.yaml`, `docs/evals/registry.yaml`, `tests/animatic_fixtures.py`, and `tests/render_fixtures.py`. Key findings: the symbolic animatic lane, shared render lane, media-QA substrate, and review UI are already landed; no dedicated previz usefulness eval exists; `render_adapter_v1/main.py` (1338), `animatic_v1/support.py` (563), `SceneWorkspacePage.tsx` (758), `ArtifactDetail.tsx` (634), and `video_understanding_scorer.py` (586) are plan-risk files that should stay thin or be avoided. Patterns to follow: schema-first metadata, shared Scene Workspace / Artifact Detail path, track-manifest always-playable behavior, and promptfoo-backed eval recording in `docs/evals/registry.yaml`. Next step: human approval on the benchmark-first plan and the scope adjustment away from a bespoke 3D branch.
20260402-2358 — build-story implementation: landed the richer deterministic branch as `annotated_symbolic`, kept `symbolic` as the explicit cheap fallback, and threaded shared preview provenance through animatic, previz reel, render prompt, and generated-video contracts plus the review UI. New benchmark substrate: `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `benchmarks/tasks/previz-usefulness.yaml`, and `benchmarks/scripts/previz_usefulness_report.py`, reusing Story 030's video-understanding scorer/provider. Measured result: Annotated Animatic won at 0.853 overall vs Shared Video 0.678 and Symbolic Animatic 0.6747, so Story 137 adopts the annotated deterministic path rather than the shared-video lane. Mismatch classification: Shared Video on `quiet_bedside_vigil` was model-wrong (misread seated-vs-standing blocking), Shared Video on `radio_hold_tracking` was model-wrong (missed the obvious lateral track even on the source clip), and Symbolic Animatic on `radio_hold_tracking` was ambiguous rather than golden-wrong because the candidate itself flattens the planned move; all remaining benchmark misses are non-runtime-blocking for this story. Checks run: `.venv/bin/python -m pytest tests/unit/test_animatic_module.py tests/unit/test_render_schema.py tests/unit/test_video_understanding_benchmark.py`, `.venv/bin/python -m pytest tests/integration/test_animatic_integration.py -q`, `.venv/bin/python -m pytest tests/integration/test_render_adapter_integration.py -q`, `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `promptfoo eval -c tasks/previz-usefulness.yaml --no-cache -j 1 --output results/previz-usefulness-pilot-2026-04-02.json`. Browser verification: the MCP Playwright profile was locked by other live sessions, so I followed the runbook spirit with isolated shell-driven Chrome checks instead and saved evidence under `output/story-137-verification/`; asserted passes covered Scene Workspace `Animatics`, Animatic Detail, Previz Reel Detail, and Generated Video Detail. Follow-up / next step: leave the story `In Progress` for `/validate`; do not remove the symbolic path because the eval supports explicit fallback semantics rather than replacement.
20260403-0943 — validate: reran `./scripts/sync-agent-skills.sh --check`, `.venv/bin/python -m ruff check src/ tests/`, targeted Story 137 pytest coverage, `make test-unit PYTHON=.venv/bin/python`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, an isolated browser verification pass against the live local UI, and the previz-usefulness promptfoo task plus report generation. Fresh validation evidence stayed stable on the user-facing decision: Annotated Animatic remained the winner at 0.8503 overall vs Symbolic 0.6887 and Shared Video 0.593, and browser assertions passed for Scene Workspace `Animatics`, Animatic Detail, Previz Reel Detail, and Generated Video Detail with screenshots under `output/story-137-validation/`. Validation finding: `benchmarks/scripts/generate_previz_usefulness_dataset.py` is currently broken at the README write call, so the documented dataset regeneration step fails with `TypeError: 'str' object is not callable`; the promptfoo rerun only succeeded because the existing dataset was already present. Recommended next step: keep the story open, fix the dataset generator, rerun the documented eval flow end to end, and then run `/validate` again or proceed to `/mark-story-done` if the rerun stays clean.
20260403-1000 — validate follow-up: fixed the `generate_previz_usefulness_dataset.py` README write bug and removed the dead `previz_mode` parameter from `build_previz_reel(...)` so the validation rerun would not carry known drift. Re-ran the dataset generator from scratch, `promptfoo eval -c tasks/previz-usefulness.yaml --no-cache -j 1 --output results/previz-usefulness-validation-2026-04-03-rerun.json`, `benchmarks/scripts/previz_usefulness_report.py`, `./scripts/sync-agent-skills.sh --check`, `.venv/bin/python -m ruff check src/ tests/`, targeted Story 137 pytest coverage, `make test-unit PYTHON=.venv/bin/python`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `make check-size`, and a fresh MCP Playwright browser verification pass across Scene Workspace `Animatics`, Animatic Detail, Previz Reel Detail, and Generated Video Detail with no console warnings/errors. Final eval result still supports the same product decision on a clean rerun: Annotated Animatic won at 0.8113 overall vs Shared Video 0.7497 and Symbolic Animatic 0.6763; remaining failures are classified and non-runtime-blocking (`radio_hold_tracking`: Shared Video model-wrong, Symbolic Animatic ambiguous). Recommended next step: `/mark-story-done`.
20260403-1005 — mark-story-done: closed Story 137 after confirming build + validation gates, fresh registry entries, mismatch classification, and final browser verification evidence. Close-out bookkeeping updated this story file, `docs/stories.md`, `docs/build-map.md`, and `CHANGELOG.md`; the shipped slice is the richer deterministic `annotated_symbolic` previz default with symbolic fallback preserved and the benchmark harness rerunnable from scratch. Fresh evidence at closure: `make test-unit PYTHON=.venv/bin/python` (`643 passed, 141 deselected`), targeted Story 137 pytest (`16 passed`), `ruff`, UI lint/typecheck/build, skill sync, clean promptfoo rerun (`Annotated 0.8113`, `Shared 0.7497`, `Symbolic 0.6763`), and browser verification across Scene Workspace plus artifact-detail surfaces. Next step: `/check-in-diff`.
