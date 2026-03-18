# Story 137 — Previz Fidelity Upgrade

**Priority**: Low
**Status**: Draft
**Ideal Refs**: R8 (professional-grade motion assets), R10 (playable assembly at every stage), R17 (partial workflows and real-world asset support)
**Spec Refs**: spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:6.4 (Keyframes), spec:10.3 (Always-Playable Rule), spec:7.1 (Render Adapter Layer — candidate shared substrate)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / concern-group inputs)
**Depends On**: Story 027 (current previz baseline), plus Story 028 and Story 030 if the chosen path reuses video-generation or media-QA substrate

## Goal

Story 027 proves that CineForge can generate and review animatics end to end, but its current output is deliberately symbolic: stills, simple motion, and temp audio. That satisfies the capability gap, but it may not be useful enough for real blocking, camera study, or future AI-generation handoff. This story upgrades previz from "exists" to "usefully informative" by evaluating and, if justified, implementing a richer previz mode that still behaves like previz: lower-detail, advisory, and focused on motion, camera placement, actor blocking, and pacing rather than surface polish. The key open question is not "how do we make previz prettier?" but "what mode produces meaningfully better human review value without collapsing previz into final render?"

## Acceptance Criteria

- [ ] A documented eval compares the current Story 027 symbolic animatic baseline against at least two richer previz candidates on the same fixed scene set, using a rubric focused on camera placement, blocking clarity, motion readability, and pacing usefulness.
- [ ] If a richer previz mode is adopted, it is available through the same end-to-end operator path as existing animatics: recipe/module output, Scene Workspace review, Artifact Detail viewing, and timeline track resolution all stay coherent.
- [ ] The chosen previz mode persists explicit provenance for `mode`, `fidelity_intent`, upstream inputs, and cost/latency so operators can tell whether they are looking at symbolic animatic, richer previz, or final render.
- [ ] Richer previz remains advisory and optional: it is not required to proceed downstream, is not silently substituted for final render, and does not erase the cheap symbolic fallback unless the replacement is clearly superior and intentionally adopted.
- [ ] If the chosen path uses AI video generation, the story adds or updates a previz usefulness eval and records results in `docs/evals/registry.yaml`; if no existing eval substrate fits, the story creates one.

## Out of Scope

- Replacing Story 027's symbolic animatics immediately; that baseline remains valid unless this story lands measured evidence for a different default.
- Making previz mandatory before render or export.
- Building a general-purpose 3D editor, DCC workflow, or full NLE inside CineForge.
- Solving final generated-video QA or multimodal media validation end to end; this should coordinate with Story 030 and the inbox item on agentic video/audio validation.
- Assuming AI video models will accept reference video as an input. Human review value is the primary bar; downstream AI-conditioning value is optional.

## Approach Evaluation

- **Simplification baseline**: A single SOTA video-generation call may already be good enough if prompted for low-detail blocking rather than polish. This is untested. The first build task should measure whether one model call, using current shot plans/keyframes/reference assets, already produces previz that a human would actually use.
- **AI-only**: Reuse the same video-generation substrate as final render but prompt for "blocking-first" output: accurate camera path, actor placement, motion, and pacing with deliberately reduced surface detail. Pros: semantically rich output and likely best chance of actual usefulness. Cons: may cost nearly as much as final render and may blur the operator's mental model of what previz is for.
- **Hybrid**: Code compiles a structured previz package from shot plan, keyframes, concern-group context, and real-world reference assets; the backend can target either a low-detail video-generation mode or a constrained scene-blocking generator. Pros: preserves provenance and allows multiple backends. Cons: more orchestration complexity and potentially more UI surface area.
- **Pure code**: Build a richer deterministic 2.5D/3D blocking engine with symbolic actors, sets, and explicit camera rigs. Pros: clear control, potentially lower run cost once built, and possibly strong value for filmmakers focused on staging. Cons: the repo has no 3D substrate today, and this risks turning CineForge into a half-built DCC tool.
- **Repo constraints / ADRs**: ADR-003 says previz belongs in Scene Workspace and consumes concern-group and real-asset context, not isolated prompt hacks. ADR-002 says downstream actions need visible diagnostics and preflight, not hidden backend magic. Story 027 already established the user-facing previz loop. Story 028 likely becomes the correct owner if the winning path shares video-generation logic. `src/cine_forge/modules/visualization/animatic_v1/support.py` is already oversized at 563 lines, while `ui/src/pages/SceneWorkspacePage.tsx` and `ui/src/pages/ArtifactDetail.tsx` are already large, so the eventual build should bias toward new focused modules/components instead of stuffing more logic into the existing files.
- **Existing patterns to reuse**: Story 027 animatic/keyframe/previz schemas and review surfaces, Story 029 user asset injection, Story 028 render adapter once landed, Story 030 media QA, the track-manifest/always-playable system, project-relative asset serving, and the existing Scene Workspace / Artifact Detail visualization pattern.
- **Eval**: No current eval entry exists in `docs/evals/registry.yaml` for previz usefulness or AI-generated video usefulness. The winning approach should be selected by comparing the same scenes across (a) current symbolic animatic, (b) shared video-generation low-detail mode, and (c) any 3D/blocking prototype, then scoring for blocking clarity, camera readability, pacing usefulness, controllability, and cost/latency. Raw visual impressiveness is not enough.

## Tasks

- [ ] Establish the simplification baseline: measure whether a single SOTA video-generation call already produces human-useful low-detail previz from current shot plans, keyframes, and reference assets.
- [ ] Prototype at least two richer previz candidates on the same fixed scene set:
  - [ ] shared render-pipeline low-detail mode
  - [ ] one non-final-render alternative such as structured 3D/blocking or equivalent
- [ ] Define the eval rubric and missing eval harness for previz usefulness; record the measured winner in `docs/evals/registry.yaml`.
- [ ] Extend previz schemas/contracts to persist `mode`, `fidelity_intent`, upstream inputs, and intended use (`human review`, `AI conditioning`, or both`) before wiring any new backend path through the UI.
- [ ] If a richer previz path is adopted, implement it end to end in the same story: backend generation, track integration, Scene Workspace, Artifact Detail, artifact metadata, run labels, and browser verification.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: Do not keep growing `animatic_v1/support.py`. If richer previz stays in the visualization lane, it likely needs a new focused module (`previz_generation_v1` or similar) with `animatic_v1` retained as the cheap fallback. If the shared video-generation path wins, `render_adapter_v1` becomes the natural owner once Story 028 lands. Scene Workspace and Artifact Detail should remain thin consumers.
- **Data contracts**: `src/cine_forge/schemas/animatic.py` is the current contract surface and likely needs explicit mode/fidelity/provenance fields or a sibling richer-previz schema. Any cross-layer payload must be schema-first. If prompt artifacts or generated-video contracts are shared with render, reuse typed schemas rather than ad hoc dicts.
- **File sizes**: `make check-size` currently flags `src/cine_forge/modules/visualization/animatic_v1/support.py` at 563 lines, `src/cine_forge/modules/visualization/animatic_v1/main.py` at 434 lines, `ui/src/pages/SceneWorkspacePage.tsx` at 734 lines, and `ui/src/pages/ArtifactDetail.tsx` at 617 lines. Likely touched but smaller files today: `src/cine_forge/modules/visualization/keyframe_v1/main.py` (332), `src/cine_forge/schemas/animatic.py` (126), `ui/src/components/AnimaticsPanel.tsx` (250), `ui/src/components/AnimaticViewer.tsx` (210), `ui/src/components/PrevizReelViewer.tsx` (106), and `ui/src/components/KeyframeViewer.tsx` (220).
- **Decision context**: Reviewed `docs/ideal.md` (R8, R10, R17), `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:10.3`, `spec:7.1`), `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, and `docs/decisions/adr-003-film-elements/adr.md`. No existing previz usefulness eval currently exists in `docs/evals/registry.yaml`.

## Files to Modify

- `src/cine_forge/schemas/animatic.py` — extend previz/animatic contracts with mode/fidelity/provenance fields (126 lines)
- `src/cine_forge/modules/visualization/animatic_v1/main.py` — adapt orchestration only if the cheap fallback remains clean (434 lines)
- `src/cine_forge/modules/visualization/animatic_v1/support.py` — likely extraction/removal target; do not pile more core logic into the current 563-line file
- `src/cine_forge/modules/visualization/keyframe_v1/main.py` — propagate richer previz/keyframe linkage if needed (332 lines)
- `src/cine_forge/modules/generation/render_adapter_v1/` — likely owner if the shared video-generation path wins (not yet landed; Story 028 dependency)
- `ui/src/components/AnimaticsPanel.tsx` — expose richer previz mode, limitations, and provenance (250 lines)
- `ui/src/components/AnimaticViewer.tsx` — show richer previz metadata and playback context (210 lines)
- `ui/src/components/PrevizReelViewer.tsx` — surface project-level mode labels and review affordances (106 lines)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only; avoid growing the 734-line page
- `ui/src/pages/ArtifactDetail.tsx` — thin routing only; avoid growing the 617-line page
- `docs/evals/registry.yaml` — add previz usefulness eval entry and measured results once they exist

## Redundancy / Removal Targets

- The current symbolic-only motion compositor as the implied "best" previz path if a richer mode clearly wins; either demote it to an explicit `symbolic` mode or keep it only as the cheap fallback.
- Any UI copy or artifact labels that treat all previz outputs as equivalent once multiple fidelity modes exist.
- Temporary bridges between previz and final-render logic if the chosen implementation converges on the render-adapter substrate.

## Notes

- Story 027 already solved the existence problem. This story is only worth doing if it solves the usefulness problem.
- Previz is not just "cheaper final render." Its value is lower-detail focus: blocking, motion, camera placement, pacing, and shot intent without getting distracted by finish polish. If a candidate path costs the same as final render, it still needs to justify itself by improving iteration clarity or controllability.
- Many AI video generators do not accept reference video, so AI-conditioning value is a bonus rather than the primary success condition.
- A 3D/blocking path is plausible, but only if it meaningfully improves staging/camera reasoning without dragging CineForge into a bespoke animation toolchain.
- Coordinate with the inbox item on agentic video/audio validation. Framegrabs alone are not enough to judge richer previz or generated motion.
- Promotion guidance: keep this Draft until either Story 028 lands or someone is ready to run a focused prototype/eval pass that can choose between the shared-video and structured-blocking branches.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260318-1646 — story created: User reviewed the Story 027 smoke project and confirmed the feature works but the current symbolic previz may not be useful enough for real-world blocking or future AI-generation handoff. Captured the future enhancement as a separate low-priority Draft instead of silently expanding Story 027. Evidence reviewed while drafting: `docs/ideal.md` (R8/R10/R17), `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:10.3`, `spec:7.1`), ADR-002, ADR-003, the current Story 027 implementation/files, and `docs/evals/registry.yaml` (no existing previz usefulness eval entry). Candidate directions recorded: shared low-detail video-generation path and structured 3D/blocking path. Next step: promote only when someone is ready to measure usefulness against the current symbolic baseline.
