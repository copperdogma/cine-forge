---
id: "149"
title: "Fast Previz Lane and Latency Budget"
status: "Blocked"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "R17 (real-world and partial-workflow inputs)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.3"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "028"
  - "143"
  - "144"
  - "148"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "previz"
  - "latency"
  - "quick-path"
legacy_system: ""
---

# Story 149 — Fast Previz Lane and Latency Budget

**Priority**: High
**Status**: Blocked
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators), spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:7.1 (Render Adapter Layer), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 028 (Render Adapter), Story 143 (AI-Generated Low-Fidelity Previz), Story 144 (AI Previz Adoption Gate and Trust Guardrails), Story 148 (Scene-Scoped Planning and Honest Downstream Generation)

## Goal

Make previz feel iterative again. Today the best current AI-previz lane is useful but slow enough to break the generate-react-refine loop: Story 143's latest validated measurements put `Veo 3.1 Lite Previz` at about 39.3 seconds, `Veo 3.1 Fast Previz` at about 32.4 seconds, and `Sora 2 Previz` at about 106.7 seconds on the fixed fixture pack. That is acceptable for an explicit slow lane, not for the main “show me motion now” operator experience. This story should define and ship an honest fast previz path with a measured latency budget in the low single-digit seconds when possible, explicit fidelity tradeoffs, and a clean separation between “quick planning preview” and slower full AI previz. The implemented shape is now clear: deterministic annotated animatic is the measured fast default, and AI previz is the slower richer upgrade.

## Acceptance Criteria

- [x] Scene Workspace exposes an explicit fast previz path distinct from the slower full AI-previz lane, with honest copy about expected latency, fidelity, and intended use. The UI must not imply that the fast lane is final render quality.
- [x] The project has a measured previz latency budget with fixture-backed evidence. Current target: a first playable scene-level previz artifact within `<= 6000 ms` median on the fixed comparison pack for the fast lane. If that target proves impossible with current substrate, the story must record a named blocker or revised budget with provider evidence instead of pretending success.
- [x] The chosen fast path remains scene-scoped, reuses or incrementally builds only the minimum required planning substrate for the selected scene, and never silently fans out to project-wide generation.
- [x] If the fast lane is not itself the best-looking AI-video result, the product still supports an explicit upgrade path to the slower full AI-previz lane without blocking quick review. The relationship between the two lanes is visible in run metadata and artifact detail.
- [x] The eval/benchmark surface records both usefulness and latency tradeoffs for the fast lane, and `docs/evals/registry.yaml` is updated with verified numbers and an explicit recommendation/default policy.
- [x] Browser verification covers the changed previz workflow in both desktop and mobile views, including lane selection, latency/fidelity disclosure, and any quick-to-full upgrade affordance, with clean browser console output.

## Out of Scope

- Making final-render-quality video generation fast
- Pretending the current provider-backed AI-video call will hit a few seconds without measurement
- Film-level assembly/export optimization
- Hidden quality degradation or unlabeled placeholder motion
- Training custom video models, LoRAs, or heavyweight identity infrastructure

## Approach Evaluation

- **Simplification baseline**: The current deterministic animatic lane is effectively instant and already useful for timing/blocking review. The first question is whether the user’s “few seconds” need is actually solved by packaging that deterministic lane as the explicit fast default and reserving AI-video for a slower refinement step.
- **AI-only**: Try the fastest current provider / lowest-resolution / shortest-duration AI-video configuration the repo can honestly support. This is appealing if a live model inventory reveals a new lane that can actually clear the latency target. Current evidence argues against assuming this will work: the latest validated Story 143 numbers are still ~32-39 seconds for the useful Google lanes and ~106 seconds for Sora 2.
- **Hybrid**: Strong candidate. Show an immediate deterministic or lightweight proxy previz first, then optionally promote or replace it with a slower AI-video clip when the user wants richer motion. Caching, incremental clip reuse, and “quick first / full later” UI are the likely winning pattern if no provider can clear the target directly.
- **Pure code**: Also plausible. If the real product need is “show me a playable planning artifact in a few seconds,” then deterministic animatic synthesis, incremental invalidation, and better packaging/review UI may solve it without any AI-video call in the critical path.
- **Repo constraints / ADRs**: ADR-002 requires warn/proceed behavior and honest preflight rather than hidden backend magic. ADR-003 requires previz to stay a planning surface in Scene Workspace, not collapse into final-render semantics. Story 143 already measured the current AI-video lanes and proved that usefulness and speed are in tension; Story 148 already made scene-scoped downstream actions honest. Any future story here must preserve that honesty rather than silently downgrading quality or broadening scope.
- **Existing patterns to reuse**: Story 137's deterministic annotated animatic control arm, Story 143's AI-previz lane and `previz-usefulness` eval, Story 148's scene-scoped action and preflight substrate, `animatic_v1`, `render_adapter_v1`, `PrevizPanel`, and the eval registry. Reuse these before inventing a second unrelated preview framework.
- **Eval**: The repo has a quality eval (`previz-usefulness`) but not a strong operator-facing time-to-first-playable benchmark. This story should add or extend a latency-aware previz eval/harness that compares deterministic, AI-only, and hybrid candidates on the same fixture scenes, then records both usefulness and latency in `docs/evals/registry.yaml`.

## Tasks

- [x] Run `/discover-models` and establish the live baseline for current previz latency and quality, including a route-level “click to first playable artifact” measurement for the current Scene Workspace flow.
- [x] Define the product contract for a fast previz lane: naming, intended use, latency/fidelity disclosure, and how it relates to the slower full AI-previz lane.
- [x] Prototype and compare at least three repo-fit approaches against the same fixture pack:
  - [x] deterministic fast lane built from existing animatic/storyboard substrate
  - [x] AI-only fastest-lane candidate from the current model inventory
  - [x] hybrid quick proxy now plus slower AI refinement / replacement
- [x] Add or extend eval coverage so the chosen fast path is judged on both usefulness and latency, then update `docs/evals/registry.yaml` with verified scores, latency, cost, and recommendation/default policy.
- [x] Implement the winning approach end to end only if it materially improves the operator loop; otherwise mark the story blocked with measured evidence instead of shipping placebo speedups.
- [x] Keep final render and full AI previz semantics separate from the fast lane so the product does not regress into one ambiguous “generate video” button.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
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
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

Representative previz verification is honest again, and Story 153 now has a tighter provider-floor answer: once the fresh validation pass is folded into the earlier shared-substrate runs, Fast 4 becomes the current pure runtime leader at `164799 ms` total / `52196 ms` isolated AI-previz, while Lite 4 remains the usefulness leader at `0.828` vs `0.778` and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. Story 149 still stays blocked because no dominant AI-previz winner is proven, the overall path remains far outside the intended generate -> react -> refine loop, and provider jitter still reshuffles pack ordering. The current product truth is therefore “Lite 4 is the provisional shipped slow lane, but the runtime blocker is not solved.”

## Blocker Evidence

- Fresh representative project: `story-149-real-ui-rerun`, created via `/api/projects/new` with the same single-scene screenplay uploaded through `/api/projects/{id}/inputs/upload`.
- Honest prerequisite chain completed on the fresh project: `mvp_ingest` finished in `17.9s` (`run-b68ec8ca`) and `creative_direction` finished in `101.9s` (`run-219959ad`).
- Fresh scene-scoped AI-previz run: `run-6305b0b5` completed successfully through the normal API path for `scene_001`. Measured breakdown: `shot_planning=230.3s` on `claude-haiku-4-5-20251001`, `ai_previz=63.3s`, `validate_media=5.2s`, `total=299.0s`, `total_cost_usd=0.0643432`.
- The previz recipe routing fix materially improved the upstream planner cost but did not solve the product gap: the earlier honest baseline `story149-real-animatic` spent `455.2s` in `shot_planning`, so the Haiku-pinned rerun cut that stage roughly in half while still leaving the path too slow for interactive use.
- The animatic failure itself is fixed: retry run `story149-real-animatic-retry-ccad` completed through the normal failed-stage path in `62.5s` total (`animatics=61.7s`, `keyframes=0.8s`) and wrote a valid `animatic` artifact whose `audio_refs` list is now empty instead of containing a bogus descriptive filesystem path.
- Story 150's first runtime pilot (`benchmarks/results/real-ai-previz-runtime-story-150-pilot-2026-04-08.json`) reinforced the blocker instead of clearing it: the best honest scene-ready AI-previz case was the shipped Lite 8-second lane at `270922 ms` total, the 4-second Fast scene-ready variant was worse at `353687 ms`, and even the ingest-only Fast control still needed `124929 ms`.
- Story 151's compact shot-planning rerun (`benchmarks/results/real-ai-previz-runtime-story-151-compact-pilot-2026-04-08.json`) materially improved the substrate without unblocking the product: shipped Lite scene-ready fell to `153528 ms`, Fast 4 scene-ready fell to `182138 ms`, and shipped Lite `shot_planning` itself fell from `109.3s` to `25.4s`. That is a real gain, but it still leaves the path far outside the intended quick-loop budget.
- Story 153's build-time provider-floor matrix (`benchmarks/results/real-ai-previz-runtime-story-153-provider-floor-2026-04-08.json`) favored Lite 4 scene-ready at `146281 ms` total, beating the pre-change shipped Lite 8 baseline (`184926 ms`) and Fast 4 (`182737 ms`) while reusing the existing 4-second Veo Lite usefulness evidence.
- Story 153's fresh validation rerun (`benchmarks/results/real-ai-previz-runtime-story-153-validation-2026-04-08.json`) did not confirm that winner as stable: `veo31_4_scene_ready` became the fastest scene-ready case at `166188 ms`, `fast_4_scene_ready` had the quickest scene-ready `ai_previz` segment at `95434 ms`, and Lite 4 still beat both Lite 8 control cases. The AI lane therefore improved but has not converged on a reproducible winner, and the whole comparison remains runtime-blocking for the fast-previz detector.
- Story 153 then tightened the comparison boundary itself and reran the `scene_ready` pack race from identical precomputed `shot_planning` substrate across three passes (`benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-summary-2026-04-08.json`). Median result: shipped Lite 4 is currently best at `142634 ms` total / `50320 ms` isolated AI-previz, ahead of Fast 4 at `145285 ms` / `57186 ms`, ahead of full Veo 4 at `150847 ms` / `57623 ms`, and ahead of the old Lite 8 control at `155501 ms` / `60857 ms`. That keeps Lite 4 as the honest shipped slow lane, while the overall detector remains runtime-blocking.
- Fresh `/validate` then reran that tighter shared-substrate comparison once more (`benchmarks/results/real-ai-previz-runtime-story-153-validation-shared-scene-ready-2026-04-08.json`) and the single pass flipped back to `fast_4_scene_ready` at `184313 ms` total / `47207 ms` isolated AI-previz, while shipped Lite 4 landed at `199380 ms` / `62274 ms`. That does not beat the repeated median/usefulness case for Lite 4, but it confirms pack ordering is still unstable enough that the shipped slow-lane choice should remain provisional.
- Story 153's combined decision summary (`benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-decision-2026-04-08.json`) then folded that fresh validation pass into the earlier three shared-substrate runs. Combined result: `fast_4_scene_ready` is the current median runtime leader at `164799 ms` total / `52196 ms` isolated AI-previz, but `shipped_lite_4_scene_ready` remains the usefulness leader at `0.828` vs `0.778` and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. The decision is therefore not “Fast 4 wins” or “Lite 4 wins”; it is “no dominant winner is proven, keep Lite 4 provisional, and keep the detector runtime-blocking.”

## Unblock Condition

Unblock this story only when one of these is true:

- a fastest-real-AI-previz eval identifies a materially faster reachable lane, settings profile, or caching strategy that lowers time to first `ai_previz_video` enough to support interactive review, or
- a provider or substrate change materially beats the current repeated shared-substrate median of `142634 ms` scene-ready total / `50320 ms` isolated AI-previz time while remaining reproducible across reruns, or
- the shared previz substrate is redesigned so `shot_planning` no longer dominates the critical path for scene-scoped previz runs.

Representative browser verification can now use the honest API-driven project routes, but the story should not return to `In Progress` until the runtime blocker above has a credible fix path.

## Architectural Fit

- **Owning class/module**: The winning shape did not need a new module. Deterministic fast-lane semantics now live in the shared policy contract (`src/cine_forge/schemas/render.py`, `src/cine_forge/services/previz_adoption.py`), while `animatic_v1` remains the producer for the fast lane and `render_adapter_v1` remains the slower AI-upgrade producer. UI framing stays in the existing previz surfaces (`PrevizPanel`, `AnimaticViewer`, `AiPrevizViewer`) instead of creating a third preview subsystem.
- **Data contracts**: The fast-lane contract is schema-first. `PrevizLaneStatus` now carries latency class, intended use, fidelity disclosure, latency budget, and explicit upgrade metadata, and the shared policy response exposes both lanes plus a policy summary for the UI.
- **File sizes**: The implementation deliberately avoided widening the oversized backend generation modules and kept route-level churn low. The largest touched UI file remains `ui/src/components/PrevizPanel.tsx`, so the copy and lane-selection changes were kept localized there and in the artifact viewers instead of adding more logic to `SceneWorkspacePage.tsx`.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 143’s measured AI-previz results, Story 148’s scoped-previz work, the relevant previz sections of `docs/spec.md`, the eval registry entry for `previz-usefulness`, and the new deterministic measurements (`606 ms` average / `635 ms` median for annotated fast previz on the fixed fixture pack).

## Files to Modify

- `src/cine_forge/schemas/render.py` — typed fast-lane contract, latency budget fields, and upgrade metadata
- `src/cine_forge/schemas/__init__.py` — export the new previz schema surface
- `src/cine_forge/services/previz_adoption.py` — shared two-lane policy (`Fast Previz` default plus `AI Previz` upgrade)
- `tests/unit/test_previz_adoption_service.py` — lock the two-lane policy and default-selection behavior
- `ui/src/lib/types.ts` — frontend typing for the expanded previz policy response
- `ui/src/components/PrevizPanel.tsx` — Scene Workspace fast-lane framing, disclosures, and upgrade affordance
- `ui/src/components/AnimaticViewer.tsx` — fast-lane detail copy and AI-upgrade relationship
- `ui/src/components/AiPrevizViewer.tsx` — slower-upgrade copy and lane relationship
- `ui/src/components/preview-provenance.ts` — lane/provenance wording alignment
- `ui/src/lib/constants.ts` — shared labels and explanatory copy
- `ui/src/lib/chat-messages.ts` — align assistant-facing lane wording
- `benchmarks/scripts/generate_previz_usefulness_dataset.py` — measured deterministic latency capture and temporary output-dir support
- `benchmarks/scripts/previz_usefulness_report.py` — fast-lane recommendation logic and dataset-root support
- `benchmarks/tasks/previz-usefulness.yaml` — task metadata alignment for the fast-lane policy
- `tests/unit/test_previz_usefulness_report.py` — report expectations for the new policy fields
- `docs/evals/registry.yaml` — verified fast-lane latency, updated target budget, and the default-policy note

## Redundancy / Removal Targets

- Any UX copy that implies slow AI previz is the only meaningful motion-preview path
- Any hidden spinner-only wait state that withholds a usable quick preview while a slower lane runs
- Any code path that recomputes full AI previz when a deterministic fast artifact or cached partial output would satisfy the operator’s immediate need
- Any ambiguous “generate video” wording that blurs quick previz, full AI previz, and final render into one action

## Notes

- Current validated Story 143 numbers are the main reason this is a separate story: `Veo 3.1 Lite Previz` is useful but ~39.3 seconds, `Veo 3.1 Fast Previz` is ~32.4 seconds, and `Sora 2 Previz` is ~106.7 seconds on the fixed fixture pack as of 2026-04-03. That is too slow for the core creative loop the user just described.
- The likely right answer is not “optimize Veo a bit harder.” It is probably a two-lane product: something fast and always available for planning, plus something slower and richer when the user wants more motion fidelity.
- This story should push back on fake speed wins. A cheaper prompt, a shorter timeout, or a loading-state polish pass is not success if the operator still waits tens of seconds for the first usable result.
- `previz-usefulness` now carries the fast-lane policy directly: keep Fast Previz as the default quick loop unless an AI lane can match the usefulness win *and* fit inside the same `<= 6000 ms` budget.
- If no credible path can clear a few-second budget while staying useful, the correct outcome is a measured blocker or a redefined “quick previz” lane, not quietly accepting current latency as “good enough.”
- Follow-up runtime discovery is now tracked explicitly in Story 150 (`docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md`) so the unblock path is named in the methodology artifacts instead of living only in chat history.
- User feedback on 2026-04-08 clarified that deterministic animatic output is placeholder substrate, not the intended shipped fast-previz experience. That means the current Story 149 implementation is still useful as measurement/policy work, but it does **not** settle the product direction. The next decision should be driven by a fastest-real-AI-previz eval, not by promoting deterministic shapes/stills into the final lane.

## Plan

### Buildability

Exploration proved this Draft is now honestly buildable and should be promoted
to `Pending` before implementation starts. The story is no longer about
inventing a previz surface from scratch. Stories 143, 144, and 148 already
landed:

- a dedicated `ai_previz_generation` recipe path
- scene-scoped execution and preflight wiring
- media-validation trust for `ai_previz_video`
- a shared previz adoption service and API route
- a side-by-side `Previz` workspace surface for deterministic and AI lanes

The remaining gap is narrower and more product-specific: turn the current
deterministic lane into an explicit **fast previz** lane with a measured latency
budget, keep AI previz as the slower richer lane, and make the upgrade
relationship between them explicit in policy, UI copy, and artifact detail.

### Baseline / Eval Gate

- Existing quality baseline:
  - `docs/evals/registry.yaml` currently records `Annotated Animatic` at `0.803`
    overall and `Veo 3.1 Lite Previz` at `0.828` overall on
    `previz-usefulness`, but the AI lane still takes about `39.3s` and remains
    outside the core rapid-iteration loop.
- Existing product baseline:
  - `ui/src/components/PrevizPanel.tsx` already exposes two lanes, but they are
    framed as `Annotated Animatic` and `AI Previz`, not as an explicit
    `fast now` lane plus `slower richer` upgrade lane.
  - `src/cine_forge/services/previz_adoption.py` only models AI-lane adoption.
    It does not model a first-class fast lane or a <= `6000 ms` budget.
  - `benchmarks/tasks/previz-usefulness.yaml` and the report pipeline record AI
    candidate generation latency, but they do not record measured deterministic
    lane latency beyond a placeholder `0`.
- Success measure for this story:
  - record fixture-backed deterministic fast-lane latency
  - make the fast lane explicit in shared policy and UI
  - show an explicit upgrade path from fast lane to AI previz
  - keep the current always-playable deterministic lane as the default unless a
    future AI lane can honestly replace it

### Candidate Approaches

- **AI-only**: try to find a new model fast enough to make AI previz itself the
  fast lane. Rejected for this slice. Current measured evidence is still tens of
  seconds, and the repo already has a deterministic lane that satisfies the
  planning purpose much better.
- **Hybrid**: treat the deterministic annotated animatic as the fast lane and AI
  previz as the slower richer upgrade path, with policy and UI making that
  distinction explicit. This is the strongest fit for the current repo.
- **Pure code**: rename labels only and skip measurement/policy work. Rejected.
  That would be cosmetic churn and would keep the latency story ungrounded.

### Repo-Fit / Optimality Evidence

- ADR-002 requires honest warn/proceed behavior and clear operator guidance
  rather than hidden backend magic. An explicit fast-lane/default policy fits
  that decision directly.
- ADR-003 says previz is a planning surface inside Scene Workspace, not a final
  render seam. The right product shape is `fast planning preview now` plus an
  optional richer AI motion pass, not one ambiguous "generate video" action.
- The current repo already has the deterministic substrate in
  `animatic_v1` and the slower AI lane in `render_adapter_v1`. Adding a third
  preview subsystem would be wrong because it would fragment ownership and blur
  the same success surface across more files.
- The best repo-fit move is therefore to:
  - reuse the existing deterministic lane as `Fast Previz`
  - keep the existing AI lane as `AI Previz`
  - extend the shared policy object to describe both lanes and the upgrade link
  - add real latency evidence for the deterministic lane instead of pretending
    the placeholder `0 ms` value is meaningful

### Structural Health Check

- `make check-size` on 2026-04-07 confirmed the main risk files for this story:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1538`
  - `src/cine_forge/driver/engine.py` — `1367`
  - `src/cine_forge/api/service.py` — `1145`
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — `1108`
  - `src/cine_forge/api/app.py` — `730`
  - `src/cine_forge/pipeline/graph.py` — `722`
  - `src/cine_forge/api/models.py` — `510`
  - `src/cine_forge/modules/visualization/animatic_v1/support.py` — `563`
  - `src/cine_forge/api/artifact_manager.py` — `531`
  - `src/cine_forge/modules/visualization/animatic_v1/main.py` — `526`
  - `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` — `522`
  - `ui/src/pages/SceneWorkspacePage.tsx` — `879`
  - `ui/src/lib/types.ts` — `671`
  - `ui/src/pages/ArtifactDetail.tsx` — `645`
  - `ui/src/pages/RunDetail.tsx` — `629`
  - `ui/src/components/PrevizPanel.tsx` — `600`
- Plan consequence:
  - keep `render_adapter_v1/main.py`, `SceneWorkspacePage.tsx`, and
    `ArtifactDetail.tsx` as thin integration points only
  - put new cross-layer lane semantics in schema/service files first
  - prefer small helper extraction in benchmark/report code instead of widening
    oversized modules

### Scope Refinement

- Folded into this story:
  - typed fast-lane semantics in shared previz policy
  - deterministic-lane latency measurement in the benchmark/report surface
  - explicit fast-lane vs AI-upgrade copy and affordances in Scene Workspace and
    Artifact Detail
- Explicitly not folded into this story:
  - a new AI-video provider sweep
  - replacing the existing AI previz quality gate
  - new render-adapter orchestration
  - a new preview module or third lane

### Implementation Order

#### Task 1 — Extend shared previz policy to describe both lanes

- Files:
  - `src/cine_forge/schemas/render.py`
  - `src/cine_forge/schemas/__init__.py`
  - `src/cine_forge/services/previz_adoption.py`
  - `tests/unit/test_previz_adoption_service.py`
  - `ui/src/lib/types.ts`
- Change:
  - extend the shared previz status contract so it can describe:
    - deterministic fast lane metadata
    - AI previz metadata
    - explicit default lane and explicit upgrade target
    - latency budget and measured latency where available
  - keep artifact types unchanged; this is a product-policy change, not a
    storage migration
- Could break:
  - frontend typing for the existing `/previz/adoption` API
- Done looks like:
  - the backend can tell the UI "fast lane now, slower AI upgrade here, and
    why" without hard-coded panel logic

#### Task 2 — Add deterministic fast-lane latency evidence to the benchmark surface

- Files:
  - `benchmarks/scripts/generate_previz_usefulness_dataset.py`
  - `benchmarks/scripts/previz_usefulness_report.py`
  - `benchmarks/tasks/previz-usefulness.yaml`
  - `docs/evals/registry.yaml`
- Change:
  - record measured generation latency for the deterministic baseline variants
    instead of placeholder zeroes
  - surface the deterministic lane as the fast-lane control arm in the report
  - update the registry note/policy so the default story is:
    - `Fast Previz` is the default because it clears the interaction budget
    - `AI Previz` is the slower richer optional lane until future evidence says
      otherwise
- Could break:
  - report parsing if baseline variants do not carry the new metadata uniformly
- Done looks like:
  - the repo has fixture-backed evidence for the fast lane rather than relying
    on implied "instant enough" behavior

#### Task 3 — Reframe the workspace and artifact detail around fast lane vs AI upgrade

- Files:
  - `ui/src/components/PrevizPanel.tsx`
  - `ui/src/components/AiPrevizViewer.tsx`
  - `ui/src/components/AnimaticViewer.tsx`
  - `ui/src/lib/constants.ts`
  - `ui/src/lib/artifact-meta.ts`
  - `ui/src/pages/ArtifactDetail.tsx`
  - `ui/src/lib/use-run-progress.ts`
- Change:
  - rename the deterministic lane in the UI to `Fast Previz`
  - keep the AI lane explicit as the slower richer upgrade path
  - surface measured latency / budget copy for the fast lane
  - add explicit cross-links and "upgrade to AI previz" affordances where the
    user already has a deterministic result
  - keep final render clearly separate in the `Render` tab
- Could break:
  - run labels and copy consistency across Scene Workspace, Run Detail, and
    Artifact Detail
- Done looks like:
  - the user can tell at a glance which lane is for immediate planning feedback
    and which lane is the slower richer motion pass

#### Task 4 — Verification

- Required checks after implementation:
  - backend: `make test-unit PYTHON=<python>` for touched unit tests
  - backend lint: `<python> -m ruff check src/ tests/ benchmarks/scripts/`
  - UI: `pnpm --dir ui run lint`
  - UI: `cd ui && npx tsc -b`
  - UI: `pnpm --dir ui run build`
- Browser verification plan:
  - desktop: Scene Workspace `Previz` tab for a scene with existing animatic and
    AI previz artifacts; verify default lane copy, fast-lane latency disclosure,
    and explicit AI-upgrade affordance
  - mobile: same `Previz` flow after viewport resize; verify the lane messaging
    still reads correctly and actions remain usable
  - Artifact Detail: open one `animatic` and one `ai_previz_video` artifact and
    confirm the relationship between the lanes is clear
- Eval / registry rule:
  - if the benchmark/report output changes, update `docs/evals/registry.yaml`
    with the new deterministic latency evidence and policy note

### Risks / Approval Blockers

- The environment blocker is resolved for this build: `.venv` was recreated with
  Python `3.12`, the repo was installed in editable dev mode, and the required
  benchmark / validation scripts ran successfully.
- The product risk remains real and intentional: current provider-backed AI
  previz is still far outside the fast-lane budget, so the default policy must
  stay deterministic until a future measured AI lane can clear the same budget
  without losing usefulness.

### Definition Of Done For This Build

- Story 149 is promoted from `Draft` because the substrate is already real.
- Shared previz policy exposes a real fast-lane contract and upgrade path.
- The benchmark/report surface records deterministic fast-lane latency.
- Scene Workspace and Artifact Detail clearly separate fast deterministic previz
  from slower AI previz.
- Required checks pass in a working Python/Node environment, or the exact
  environment blocker is documented in the work log.
- Browser verification covers desktop and mobile `Previz` flow with clean
  console output, unless a documented environment blocker prevents it.

## Work Log

20260404-2245 — story creation: captured the new previz-speed gap as a separate `Draft` story instead of reopening Story 148, because the subsystem is still previz but the success surface changed from scoped execution / honest prerequisites to operator-loop latency. Evidence: the user’s live workflow report said AI previz “took a LONG time,” and Story 143’s validated registry entry still shows the useful AI lanes at roughly 32-39 seconds with Sora much slower. Drafted this as a fast-lane / latency-budget story rather than a vague “make rendering faster” note, because a few-second target likely requires a separate quick-previz path or hybrid strategy instead of minor tuning to the existing provider-backed call. Next step: compile methodology surfaces so the new story appears in generated planning views.
20260407-1742 — exploration: Story 149 is substrate-verified and buildable, but narrower than the original draft now that Stories 143, 144, and 148 have already landed the `ai_previz_generation` recipe, scene-scoped previz actions, media-validation trust for `ai_previz_video`, the shared previz adoption service, and the side-by-side `Previz` workspace surface. The real remaining gap is a first-class fast-lane contract: measured deterministic-lane latency, explicit fast-vs-slower-lane semantics, and visible upgrade flow from fast deterministic previz to slower AI previz. Evidence checked: `docs/spec.md` (`spec:5.3`, `spec:5.5`, `spec:6.3`, `spec:7.1`, `spec:10.3`), ADR-002, ADR-003, Stories 143/144/148, `src/cine_forge/services/previz_adoption.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `configs/recipes/recipe-ai-previz-generation.yaml`, `benchmarks/tasks/previz-usefulness.yaml`, and `make check-size`. Risks found: `PrevizPanel.tsx` and `SceneWorkspacePage.tsx` are already large, and this worktree currently has no `.venv`, so `/discover-models`, repo-local tests, and benchmark reruns will need environment repair or an alternate project Python before implementation can be verified cleanly. Next step: use the narrowed plan above as the implementation gate and promote to `Pending` only when coding begins.
20260408-0736 — implementation: repaired the local environment first by recreating `.venv` with Python `3.12` and installing the repo in editable dev mode, then ran `.venv/bin/python scripts/discover-models.py --summary` and `.venv/bin/python scripts/check-compromises.py` to re-ground the build against the live model catalog and current compromise state. Implemented the winning two-lane policy instead of chasing placebo AI-video speedups: the shared previz contract now exposes deterministic `Fast Previz` as the default lane, `AI Previz` as the slower richer upgrade lane, a `<= 6000 ms` fast-lane budget, and explicit latency/fidelity/upgrade metadata across backend and UI. Updated the benchmark/report surface to measure deterministic lanes honestly instead of using placeholder zeroes, then generated a new report from measured deterministic data plus the latest validated AI eval result. Evidence: annotated fast previz measured `606 ms` average / `635 ms` median on the fixed fixture pack, symbolic measured `476 ms` average, and the new report recommends `keep_fast_default` because `Veo 3.1 Lite Previz` still leads AI quality at `0.828` overall but remains around `39273 ms`. Verification: `make test-unit PYTHON=.venv/bin/python` (`665 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all completed successfully; UI lint still reports existing non-blocking warnings outside the touched previz flow. Browser verification covered desktop and mobile Scene Workspace plus animatic and AI-previz artifact detail with clean console output and screenshots for the updated routes. Next step: run `/validate` against Story 149 before any `/mark-story-done` closeout.
20260408-0922 — correction: user feedback invalidated the seeded browser-fixture evidence as product verification. The fixture had manually injected artifacts and produced an impossible UI state: disabled previz actions sitting beside already-ready previz outputs. Re-ran testing through the normal API path instead: created fresh project `story-149-real-ui`, uploaded the same sample screenplay, ran `mvp_ingest`, confirmed both previz preflights moved to honest `warn` status, then ran `creative_direction` to provide real `look_and_feel` / `rhythm_and_flow` / `sound_and_music` inputs before re-testing previz. Browser verification on the real route now shows an active prerequisite run instead of fake “ready but disabled” controls. New runtime finding: scene-scoped `animatics_generation` run `story149-real-animatic` spent about `455s` in `shot_planning`, then another `110s+` in `storyboards`, and still had not reached an `animatic` artifact when this note was written; process sampling shows the backend waiting on provider SSL reads, so representative previz validation is currently blocked by live runtime latency, not by the old seeded fixture. Also updated `AGENTS.md`, `/build-story`, and `/validate` to forbid counting hand-seeded or impossible project states as UX/product evidence. Decision correction: deterministic animatic should no longer be treated as the settled shipped fast-previz lane; next falsifiable step is a fastest-real-AI-previz eval across reachable engine-pack/settings combinations, grounded in the refreshed `/discover-models` inventory and the current real runtime blocker.
20260408-0955 — unblock pass: fixed the real animatic failure by making `animatic_v1` ignore non-file `sound_and_music.reference_audio_assets` entries during muxing instead of treating descriptive strings as project-relative audio files. Added unit coverage in `tests/unit/test_animatic_module.py`, reran the animatic-specific unit suite, and retried the failed honest run through `/api/runs/{run_id}/retry-failed-stage`. Evidence: retry run `story149-real-animatic-retry-ccad` completed in `62.5s` total (`animatics=61.7s`, `keyframes=0.8s`, `total_cost_usd=0.0`), and `/output/story-149-real-ui/artifacts/animatic/scene_001/v1.json` now carries `audio_refs=[]` instead of the bogus descriptive path that previously broke FFmpeg. Next step: rerun fresh AI previz on a normal project to measure whether the upstream model-routing fix materially changes time to first real AI previz artifact.
20260408-0955 — representative rerun: created fresh project `story-149-real-ui-rerun` through the API, uploaded the screenplay normally, reran `mvp_ingest` (`17.9s`) and `creative_direction` (`101.9s`), then launched scene-scoped `ai_previz_generation` for `scene_001`. Pinned both previz recipes’ `shot_planning` stage to `claude-haiku-4-5-20251001` / `claude-haiku-4-5-20251001` / `claude-opus-4-6` so previz no longer inherits video-facing defaults for upstream planning. Evidence: fresh run `run-6305b0b5` used Haiku for `shot_planning`, improved that stage from the earlier `455.2s` honest baseline to `230.3s`, then spent `63.3s` in `ai_previz` and `5.2s` in `validate_media` for a `299.0s` end-to-end time to first real `ai_previz_video`. That is materially better than the earlier path but still far outside the intended interactive budget, so Story 149 is now honestly `Blocked` on real runtime rather than on fixture validity. Next step: create/run a fastest-real-AI-previz eval or redesign upstream previz substrate so `shot_planning` no longer dominates the path.
20260408-1136 — validation: corrected the misleading fast-vs-AI copy before closeout instead of leaving the PR to imply that AI previz is simply “better except slower.” The shared policy and UI now describe AI previz as an optional generated motion pass that trades latency, cost, and determinism for a low-fidelity clip, and the Scene Workspace action labels now say `Generate` / `Regenerate` instead of ambiguous `Run` / `Refresh`. Fresh checks rerun in this validation pass: targeted previz pytest (`tests/unit/test_previz_adoption_service.py`, `tests/unit/test_animatic_module.py`, `tests/unit/test_previz_usefulness_report.py`), `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `./scripts/sync-agent-skills.sh --check`, and `pnpm methodology:check`. Browser verification was rerun after restarting the non-reloading API process so the UI reflected the final policy text: local Chromium Playwright passed on desktop Scene Workspace previz (`story-149-real-ui`), mobile Scene Workspace previz (`story-149-real-ui-rerun`), and AI previz detail (`story-149-real-ui-rerun`) with clean console output and screenshots saved under `/tmp/story149-*-final.png`. Outcome: implementation quality is validated, but the story remains correctly `Blocked` because the named runtime blocker still stands. Next step: follow the recorded unblock condition rather than trying to mark Story 149 done.
