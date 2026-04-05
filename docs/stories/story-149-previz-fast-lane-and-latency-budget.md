---
id: "149"
title: "Fast Previz Lane and Latency Budget"
status: "Draft"
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
**Status**: Draft
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators), spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:7.1 (Render Adapter Layer), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 028 (Render Adapter), Story 143 (AI-Generated Low-Fidelity Previz), Story 144 (AI Previz Adoption Gate and Trust Guardrails), Story 148 (Scene-Scoped Planning and Honest Downstream Generation)

## Goal

Make previz feel iterative again. Today the best current AI-previz lane is useful but slow enough to break the generate-react-refine loop: Story 143's latest validated measurements put `Veo 3.1 Lite Previz` at about 39.3 seconds, `Veo 3.1 Fast Previz` at about 32.4 seconds, and `Sora 2 Previz` at about 106.7 seconds on the fixed fixture pack. That is acceptable for an explicit slow lane, not for the main “show me motion now” operator experience. This story should define and ship an honest fast previz path with a measured latency budget in the low single-digit seconds when possible, explicit fidelity tradeoffs, and a clean separation between “quick planning preview” and slower full AI previz. It is intentionally `Draft` because a few-second target may require a different lane, not wishful optimization of the existing provider-backed video call.

## Acceptance Criteria

- [ ] Scene Workspace exposes an explicit fast previz path distinct from the slower full AI-previz lane, with honest copy about expected latency, fidelity, and intended use. The UI must not imply that the fast lane is final render quality.
- [ ] The project has a measured previz latency budget with fixture-backed evidence. Current target: a first playable scene-level previz artifact within `<= 6000 ms` median on the fixed comparison pack for the fast lane. If that target proves impossible with current substrate, the story must record a named blocker or revised budget with provider evidence instead of pretending success.
- [ ] The chosen fast path remains scene-scoped, reuses or incrementally builds only the minimum required planning substrate for the selected scene, and never silently fans out to project-wide generation.
- [ ] If the fast lane is not itself the best-looking AI-video result, the product still supports an explicit upgrade path to the slower full AI-previz lane without blocking quick review. The relationship between the two lanes is visible in run metadata and artifact detail.
- [ ] The eval/benchmark surface records both usefulness and latency tradeoffs for the fast lane, and `docs/evals/registry.yaml` is updated with verified numbers and an explicit recommendation/default policy.
- [ ] Browser verification covers the changed previz workflow in both desktop and mobile views, including lane selection, latency/fidelity disclosure, and any quick-to-full upgrade affordance, with clean browser console output.

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

- [ ] Run `/discover-models` and establish the live baseline for current previz latency and quality, including a route-level “click to first playable artifact” measurement for the current Scene Workspace flow.
- [ ] Define the product contract for a fast previz lane: naming, intended use, latency/fidelity disclosure, and how it relates to the slower full AI-previz lane.
- [ ] Prototype and compare at least three repo-fit approaches against the same fixture pack:
  - [ ] deterministic fast lane built from existing animatic/storyboard substrate
  - [ ] AI-only fastest-lane candidate from the current model inventory
  - [ ] hybrid quick proxy now plus slower AI refinement / replacement
- [ ] Add or extend eval coverage so the chosen fast path is judged on both usefulness and latency, then update `docs/evals/registry.yaml` with verified scores, latency, cost, and recommendation/default policy.
- [ ] Implement the winning approach end to end only if it materially improves the operator loop; otherwise mark the story blocked with measured evidence instead of shipping placebo speedups.
- [ ] Keep final render and full AI previz semantics separate from the fast lane so the product does not regress into one ambiguous “generate video” button.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `animatic_v1` is the strongest current home for a deterministic fast lane; `render_adapter_v1` remains relevant only if a true AI-video fast path survives measurement. The Scene Workspace previz surface should own the UX, but this story should avoid adding more packed logic to already-oversized route/components and likely needs a focused helper or dedicated `fast_previz` module if the hybrid path wins.
- **Data contracts**: Any fast-lane contract should be schema-first: typed previz mode, latency class / expected budget, and upgrade relationship to the slower AI lane should cross API/runtime/UI boundaries as explicit schema fields rather than ad hoc flags in run metadata.
- **File sizes**: `src/cine_forge/modules/generation/render_adapter_v1/main.py` is already `1538` lines, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` is `522`, `src/cine_forge/modules/visualization/animatic_v1/main.py` is `526`, `ui/src/components/PrevizPanel.tsx` is `600`, and `ui/src/pages/SceneWorkspacePage.tsx` is `879`. Any implementation plan that adds logic directly to those files without extraction is suspect.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 143’s measured AI-previz results, Story 148’s scoped-previz work, the relevant previz sections of `docs/spec.md`, and the eval registry entry for `previz-usefulness`.

## Files to Modify

- `benchmarks/tasks/previz-usefulness.yaml` — extend or split the benchmark so it can distinguish fast-lane latency and usefulness (`129`)
- `benchmarks/scripts/generate_previz_usefulness_dataset.py` — fixture generation / measurement support for fast-lane comparisons (`595`)
- `docs/evals/registry.yaml` — add the latency-budget policy and verified results (`1778`)
- `src/cine_forge/modules/visualization/animatic_v1/main.py` — candidate deterministic fast-lane substrate; extract before adding more branching if needed (`526`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — only touch if a measured AI-video fast path remains viable; otherwise keep this file out of the critical path (`1538`)
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` — fast-lane prompt/fidelity profiles if AI-video remains in contention (`522`)
- `src/cine_forge/ai/video.py` — provider request shaping only if live measurement justifies it (`411`)
- `ui/src/components/PrevizPanel.tsx` — expose fast vs full previz affordances and honest latency/fidelity copy (`600`)
- `ui/src/components/GeneratedVideoPanel.tsx` — keep render semantics separate if any upgrade affordance crosses lanes (`316`)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only; do not add more packed logic here (`879`)
- `src/cine_forge/schemas/render.py` or a new focused previz schema file — typed fast-lane contract and upgrade metadata (`new or existing`)
- `src/cine_forge/modules/visualization/fast_previz_v1/main.py` — likely new focused module if the winning path deserves its own execution surface (`new`)

## Redundancy / Removal Targets

- Any UX copy that implies slow AI previz is the only meaningful motion-preview path
- Any hidden spinner-only wait state that withholds a usable quick preview while a slower lane runs
- Any code path that recomputes full AI previz when a deterministic fast artifact or cached partial output would satisfy the operator’s immediate need
- Any ambiguous “generate video” wording that blurs quick previz, full AI previz, and final render into one action

## Notes

- Current validated Story 143 numbers are the main reason this is a separate story: `Veo 3.1 Lite Previz` is useful but ~39.3 seconds, `Veo 3.1 Fast Previz` is ~32.4 seconds, and `Sora 2 Previz` is ~106.7 seconds on the fixed fixture pack as of 2026-04-03. That is too slow for the core creative loop the user just described.
- The likely right answer is not “optimize Veo a bit harder.” It is probably a two-lane product: something fast and always available for planning, plus something slower and richer when the user wants more motion fidelity.
- This story should push back on fake speed wins. A cheaper prompt, a shorter timeout, or a loading-state polish pass is not success if the operator still waits tens of seconds for the first usable result.
- `previz-usefulness` already gives this story a quality baseline, but it currently tolerates long latencies (`latency_ms_max: 180000`) because it was built to choose AI lanes, not to enforce an interactive UX budget.
- If no credible path can clear a few-second budget while staying useful, the correct outcome is a measured blocker or a redefined “quick previz” lane, not quietly accepting current latency as “good enough.”

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260404-2245 — story creation: captured the new previz-speed gap as a separate `Draft` story instead of reopening Story 148, because the subsystem is still previz but the success surface changed from scoped execution / honest prerequisites to operator-loop latency. Evidence: the user’s live workflow report said AI previz “took a LONG time,” and Story 143’s validated registry entry still shows the useful AI lanes at roughly 32-39 seconds with Sora much slower. Drafted this as a fast-lane / latency-budget story rather than a vague “make rendering faster” note, because a few-second target likely requires a separate quick-previz path or hybrid strategy instead of minor tuning to the existing provider-backed call. Next step: compile methodology surfaces so the new story appears in generated planning views.
