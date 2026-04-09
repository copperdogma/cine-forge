---
id: "149"
title: "Fast AI Previz and Latency Budget"
status: "Done"
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
  - "spec:6.3.5"
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

# Story 149 — Fast AI Previz and Latency Budget

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3 (Stage Progression), spec:5.5 (Readiness Indicators), spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:6.3.5 (Product Truth), spec:7.1 (Render Adapter Layer), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 028 (Render Adapter), Story 143 (AI-Generated Low-Fidelity Previz), Story 144 (AI Previz Adoption Gate and Trust Guardrails), Story 148 (Scene-Scoped Planning and Honest Downstream Generation)

## Goal

Make previz feel iterative again. Today the best current AI-previz lane is useful but slow enough to break the generate-react-refine loop: Story 143's latest validated measurements put `Veo 3.1 Lite Previz` at about 39.3 seconds, `Veo 3.1 Fast Previz` at about 32.4 seconds, and `Sora 2 Previz` at about 106.7 seconds on the fixed fixture pack. That is acceptable for an explicit slow lane, not for the main “show me motion now” operator experience. This story now exists to keep the product truth honest: operator-facing previz should mean AI-generated motion, with a measured latency budget in the low single-digit seconds when possible, and the old deterministic annotated-animatic placeholder should be removed from the shipped previz product path rather than preserved as a visible fallback. The `<= 6000 ms` target remains a climb goal for this line, not a blocker for continuing the real AI-previz product path.

## Acceptance Criteria

- [x] Scene Workspace exposes AI previz as the only shipped operator-facing previz lane, with honest copy about expected latency, fidelity, and intended use. No deterministic animatic card, CTA, or ready-viewer remains in the previz surface.
- [x] The project has a measured fast-AI-previz latency budget with fixture-backed evidence. Current target: a first playable scene-level AI-previz artifact within `<= 6000 ms` median on the fixed comparison pack. That target is tracked as a climb goal for future quality/runtime work, not as a blocker for shipping or improving the real AI-previz lane.
- [x] Operator-facing previz no longer creates, recommends, or links to the programmatically created deterministic video. The deterministic generation lane, viewer affordances, and adoption-policy framing are removed from the shipped previz UX and normal operator workflow.
- [x] Any remaining animatic or keyframe substrate is either deleted outright or re-homed away from previz semantics with a concrete surviving consumer. AI-previz generation and review do not depend on animatic artifacts to run.
- [x] AI-previz run metadata and artifact detail no longer depend on `previz_baseline_ref` or other deterministic-baseline cross-links that imply a live two-lane product.
- [x] The eval/benchmark surface records the current usefulness and latency evidence for the AI lane, and may retain deterministic comparison data only as historical evidence rather than as an active shipped control arm.
- [x] Browser verification covers the changed previz workflow in both desktop and mobile views, including AI-only lane positioning, latency/fidelity disclosure, and absence of deterministic-placeholder affordances, with clean browser console output.

> Historical note: sections below retain the earlier deterministic-default exploration as implementation history, but that product conclusion is superseded. Current story direction is AI-only shipped previz, with deterministic placeholder removal now part of the active build.

## Out of Scope

- Making final-render-quality video generation fast
- Pretending the current provider-backed AI-video call will hit a few seconds without measurement
- Film-level assembly/export optimization
- Hidden quality degradation or unlabeled placeholder motion
- Training custom video models, LoRAs, or heavyweight identity infrastructure

## Approach Evaluation

- **Simplification baseline**: The current deterministic animatic lane is no longer useful enough to justify shipped or semi-shipped complexity. Historical measurements can remain as evidence, but the live lane itself is now a removal target.
- **AI-only**: Try the fastest current provider / lowest-resolution / shortest-duration AI-video configuration the repo can honestly support. This is appealing if a live model inventory reveals a new lane that can actually clear the latency target. Current evidence argues against assuming this will work: the latest validated Story 143 numbers are still ~32-39 seconds for the useful Google lanes and ~106 seconds for Sora 2.
- **Hybrid**: Rejected for shipped product semantics. Keeping a visible deterministic fallback would preserve a lane the product no longer believes in.
- **Pure code**: Rejected. Deterministic synthesis cannot be the answer to “proper previz,” and it now also fails the bar for continued product exposure.
- **Repo constraints / ADRs**: ADR-002 requires honest warn/proceed behavior and honest preflight rather than hidden backend magic. ADR-003 requires previz to stay a planning surface in Scene Workspace, not collapse into final-render semantics. Removing a fake placeholder lane is more aligned with that truth than preserving it as a comfort blanket.
- **Existing patterns to reuse**: Story 143's AI-previz lane and `previz-usefulness` eval, Story 148's scene-scoped action and preflight substrate, `render_adapter_v1`, `PrevizPanel`, and the eval registry. `animatic_v1` is now primarily a dependency-audit/removal target, not a product pattern to preserve by default.
- **Eval**: The repo already has the evidence needed to justify this product decision. Existing deterministic comparisons can remain in the registry as historical evidence, but no new product decision here depends on maintaining the live deterministic lane.

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
- [x] Remove the programmatically created deterministic previz video from the shipped previz product path instead of merely re-homing it.
- [x] Make the operator-facing previz generate/review path default to an actual AI-generated clip, with the `<= 6000 ms` budget tracked as climb evidence rather than a stop-ship gate.
- [x] Delete deterministic-baseline UI lanes, artifact-detail affordances, and adoption-policy contract fields from the normal previz workflow.
- [x] Audit and remove stale backend/runtime assumptions that a deterministic previz lane still exists (`previz_baseline_ref`, deterministic lane status, upgrade copy, scene actions, and any related types/tests), unless a surviving non-previz consumer proves they still belong.
- [x] Decide whether `animatic_v1` and any dependent keyframe behavior still earn their keep once detached from previz. Delete dead substrate instead of leaving a renamed placeholder.
- [x] Re-run required checks and representative browser verification after deterministic-lane deletion.
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
- [x] Story marked done via `/mark-story-done`

## Current State

Representative previz verification is honest again, and Story 153 now supplies the provider-floor measurement slice: once the fresh validation pass is folded into the earlier shared-substrate runs, Fast 4 becomes the current pure runtime leader at `164799 ms` total / `52196 ms` isolated AI-previz, while Lite 4 remains the usefulness leader at `0.828` vs `0.778` and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. That evidence does not block this story anymore. It defines the climb reality: AI-generated previz is the real product lane, Lite 4 is the current provisional shipped slow lane, the `<= 6000 ms` detector stays red as a climb signal, and the next product move is to delete the programmatic deterministic placeholder from the shipped previz path and remove any dead contract/substrate it leaves behind.

## Current Evidence

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

## Next Step

Build the next product slice against the current measured AI lane instead of waiting for the detector to go green. Concretely:

- make actual AI-generated previz the only operator-facing previz path,
- delete the deterministic/programmatic placeholder from shipped previz surfaces and contracts,
- audit whether any remaining animatic/keyframe substrate still has a concrete non-previz consumer, and
- keep using the runtime detector as climb evidence while improving pack choice, planning cost, and time-to-first-clip.

## Architectural Fit

- **Owning class/module**: No new module is justified. This removal spans the existing previz surface and contract: `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/schemas/render.py`, and `src/cine_forge/modules/generation/render_adapter_v1/main.py`. `AnimaticViewer` / `animatic_v1` stay in scope only if they survive with a concrete non-previz owner.
- **Data contracts**: The current schema-first contract is now too wide because it encodes a live two-lane product. Prefer deleting dead `deterministic_previz` / baseline-link fields rather than preserving them as optional ghosts.
- **Route ownership**: `/api/projects/{project_id}/previz/adoption` may remain if it still adds value after shrinking to AI-only truth; otherwise simplify it rather than keeping a compatibility shell.
- **Decision context**: Reviewed ADR-002, ADR-003, Stories 028/143/144/148/153, the spec refs above, `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/api/routers/previz.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/visualization/animatic_v1/main.py`, `src/cine_forge/modules/visualization/keyframe_v1/main.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/previz-panel-support.ts`, `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and `src/cine_forge/pipeline/scene_actions.py`.

## Files to Modify

- `ui/src/components/PrevizPanel.tsx` — remove deterministic-baseline lane affordances so AI previz is the only shipped previz generate/review path
- `ui/src/components/AiPrevizViewer.tsx` — remove deterministic cross-links and baseline framing that imply a live two-lane product
- `ui/src/components/AnimaticViewer.tsx` — delete the previz-specific animatic viewer role or re-home it outside previz semantics if the artifact survives
- `ui/src/components/previz-panel-support.ts` — centralize lane wording so the panel copy stays consistent
- `ui/src/components/preview-provenance.ts` — remove deterministic-previz provenance language from shipped previz surfaces and re-home any surviving animatic labels outside previz semantics
- `ui/src/lib/constants.ts` — align recipe/run labels and start/complete copy with AI-only shipped previz truth
- `ui/src/lib/chat-messages.ts` — remove deterministic-previz stage language from the normal previz workflow
- `src/cine_forge/pipeline/scene_actions.py` — remove deterministic-previz scene actions from the normal previz workflow if they still exist
- `src/cine_forge/services/previz_adoption.py` — shrink the adoption policy to AI-only shipped truth
- `src/cine_forge/schemas/render.py` — remove dead deterministic-lane and baseline-link contract fields
- `ui/src/lib/types.ts` — mirror the contract shrink
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — remove `previz_baseline_ref` if it no longer communicates anything useful
- `src/cine_forge/modules/visualization/animatic_v1/main.py` — delete or re-home deterministic animatic generation if no concrete non-previz consumer remains
- `src/cine_forge/modules/visualization/keyframe_v1/main.py` — audit any surviving animatic dependency and remove dead lineage/consumer assumptions
- `tests/unit/test_previz_adoption_service.py` — lock the backend policy deletion
- `tests/unit/test_render_adapter_module.py` — lock any `previz_baseline_ref` removal

## Redundancy / Removal Targets

- Any surviving deterministic lane card, CTA, viewer, or artifact-detail cross-link inside previz surfaces
- Any run/stage copy that announces deterministic output as if it satisfied the real previz promise
- Any `deterministic_previz` lane contract, upgrade copy, or baseline-link field that survives only because the old product model expected two lanes
- Any orphaned animatic/keyframe substrate kept alive without a concrete non-previz owner

## Notes

- This build is no longer a model-selection or benchmark-design story. Story 153 already did the provider-floor measurement slice, and the current runtime evidence is sufficient to say “AI primary, slow today.”
- The remaining gap is no longer just operator-surface honesty. It is deletion of a placeholder lane the product no longer wants.
- The previous caution against deleting deterministic baseline is superseded by direct user direction and by the fact that the AI-previz path does not require animatic artifacts to run.
- If animatic or keyframe artifacts still matter, they need a concrete non-previz justification in this story rather than passive survival.
- Follow-up runtime/provider work remains separate. This story should not silently absorb Story 150/153-style benchmarking again unless implementation exposes a narrowly coupled blocker.

## Plan

### Buildability

Story 149 remains honestly buildable, but the required slice is now broader than the prior UI-only correction.

- `ai_previz_generation` already exists and is scene-scoped.
- The deterministic lane is not a hard prerequisite for AI-previz generation; the current recipe does not consume animatic artifacts to run.
- The main risk is dead contract residue: `/previz/adoption`, `PrevizPanel`, viewer cross-links, `previz_baseline_ref`, and any animatic/keyframe substrate still labeled as previz.

The missing work is no longer “demote the placeholder.” It is “delete the placeholder lane cleanly without breaking the real AI-previz path.”

### Baseline / Eval Gate

- This is still primarily UI/policy/plumbing/removal work, not a new reasoning or model-choice problem. No new benchmark is required before implementation.
- Current evidence already supports the deletion decision:
  - `spec:6.3.5` says deterministic assemblies do not satisfy the previz-video requirement.
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` stores `previz_baseline_ref` only as a backlink on AI-previz artifacts rather than as a required input.
  - `src/cine_forge/modules/visualization/keyframe_v1/main.py` can optionally consume animatics, so that module needs an explicit keep-or-delete audit instead of automatic preservation.
- Success will be measured by:
  - no operator-facing deterministic previz lane
  - AI-previz path still functioning end to end
  - no dead schema/UI contract pretending a removed lane still exists
  - required static checks plus browser verification on the normal Scene Workspace / Artifact Detail flow

### Candidate Approaches

- **Hard removal from product + contract**: Preferred. Remove deterministic previz from Scene Workspace, artifact-detail hierarchy, adoption policy, and normal previz workflow.
- **UI hide only**: Rejected. Hiding the lane while keeping the contract and generation path alive would leave dead architecture and invite relapse.
- **Internal-only quarantine**: Acceptable only if the implementation audit finds a concrete non-previz consumer. If not, delete the substrate instead of renaming it.
- **Historical-evidence only**: Existing eval results and work-log history can remain as historical comparison evidence. They do not justify keeping the live lane.

### Repo-Fit / Optimality Evidence

- `docs/spec.md` already says deterministic assemblies are baseline/control only and do not satisfy the previz-video requirement.
- The current `PrevizAdoptionStatus` shape encodes a live two-lane product that no longer matches the desired product truth and should be shrunk, not preserved.
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` stores `previz_baseline_ref` only as a backlink on AI-previz artifacts, which makes it a good removal target rather than a blocker.
- `src/cine_forge/modules/visualization/keyframe_v1/main.py` can derive value from animatic input, but that is not enough by itself to preserve the deterministic previz lane unless the story explicitly re-homes those artifacts outside previz semantics.

### Structural Health Check

- `make check-size` / direct file-size check on 2026-04-09 flagged the likely touch points:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1538` lines
  - `src/cine_forge/modules/visualization/animatic_v1/main.py` — `526` lines
  - `src/cine_forge/services/previz_adoption.py` — `423` lines
  - `ui/src/components/PrevizPanel.tsx` — `619` lines
  - `ui/src/lib/types.ts` — `680` lines
- The removal should delete or shrink logic, not add more branching to these files.
- If `animatic_v1` or `render_adapter_v1` need substantive behavioral changes, extract helpers before widening them further.

### Scope Refinement

- Folded into this story:
  - delete deterministic-baseline product surfaces and CTAs
  - shrink the previz adoption contract to AI-only truth
  - remove deterministic cross-links from AI artifact detail/run metadata where they no longer serve a real purpose
  - audit `animatic_v1` / `keyframe_v1` / `previz_baseline_ref` for real remaining consumers
- Explicitly not folded into this story:
  - new provider sweeps or model discovery work beyond the evidence already gathered
  - recipe/runtime optimization for `shot_planning` or `ai_previz`
  - broader non-previz storyboard/keyframe redesign beyond what deletion forces
  - “keep it just in case” substrate preservation without a concrete consumer

### Implementation Order

#### Task 1 — Delete the deterministic previz lane from operator surfaces

- Files:
  - `ui/src/components/PrevizPanel.tsx`
  - `ui/src/components/AiPrevizViewer.tsx`
  - `ui/src/components/AnimaticViewer.tsx`
  - `ui/src/components/previz-panel-support.ts`
  - `ui/src/components/preview-provenance.ts`
  - `ui/src/lib/constants.ts`
  - `ui/src/lib/chat-messages.ts`
  - `src/cine_forge/pipeline/scene_actions.py`
- Change:
  - remove deterministic-baseline cards, CTAs, ready-viewer ordering, and artifact-detail cross-links from previz flows
  - keep only the AI-previz generate/review path in Scene Workspace
  - if animatic artifacts survive, stop presenting them as previz
- Could break:
  - CTA enable/disable behavior
  - route expectations for old deterministic artifact links
  - shared copy consistency
- Done looks like:
  - a first-time operator cannot find a deterministic placeholder lane inside previz because it is gone, not merely demoted

#### Task 2 — Shrink the previz contract and AI artifact references

- Files:
  - `src/cine_forge/services/previz_adoption.py`
  - `src/cine_forge/schemas/render.py`
  - `ui/src/lib/types.ts`
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  - `tests/unit/test_previz_adoption_service.py`
  - `tests/unit/test_render_adapter_module.py`
- Change:
  - remove deterministic lane status from the adoption contract if possible
  - remove `previz_baseline_ref` if it no longer communicates anything useful
  - keep AI-previz metadata focused on the real lane only
- Could break:
  - API typing between backend and UI
  - artifact-detail assumptions in old viewers/tests
- Done looks like:
  - no active API/UI contract still encodes a deleted deterministic previz lane

#### Task 3 — Audit or delete residual deterministic substrate

- Files:
  - `src/cine_forge/modules/visualization/animatic_v1/main.py`
  - `src/cine_forge/modules/visualization/keyframe_v1/main.py`
  - `configs/recipes/recipe-animatics-generation.yaml`
  - `src/cine_forge/pipeline/scene_actions.py`
- Change:
  - decide whether animatic generation survives as a non-previz artifact with a clear owner/consumer, or gets removed
  - if it survives, remove previz naming and operator surfacing; if not, delete the dead path
  - ensure keyframe lineage and scene actions no longer quietly assume animatic-backed previz still exists
- Could break:
  - keyframe derivation
  - old scene-action menus
  - recipe references or tests that still assume animatics are part of previz
- Done looks like:
  - no orphaned `Deterministic Baseline` feature remains in product or contract surfaces

#### Task 4 — Verification

- Required checks after implementation:
  - backend if touched: `.venv/bin/python -m pytest tests/unit/test_previz_adoption_service.py tests/unit/test_render_adapter_module.py -q`
  - backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - UI: `pnpm --dir ui run lint`
  - UI: `cd ui && npx tsc -b`
  - UI: `pnpm --dir ui run build`
- Browser verification plan:
  - desktop: open Scene Workspace `Previz` for a representative AI-previz-ready scene and verify only the AI lane appears
  - mobile: repeat the same route after viewport resize and confirm no deterministic CTA/viewer survives
  - artifact detail: open one `ai_previz_video` artifact and confirm there is no baseline cross-link implying a live two-lane model
  - if animatic artifacts survive outside previz, verify they no longer masquerade as previz
- Done looks like:
  - the real reachable product route matches the AI-only shipped-previz contract rather than the old dual-lane model

### Risks / Approval Blockers

- No new dependency, migration, or external approval blocker is known.
- Main implementation risk is half-removal: the UI disappears but the backend contract and substrate keep pretending the lane exists.
- Secondary risk is accidentally breaking keyframe or render flows if they still rely on animatic artifacts more than current evidence suggests.

### Definition Of Done For This Build

- Scene Workspace shows AI previz as the only shipped previz lane.
- No operator-facing deterministic baseline generate/review/viewer flow remains under previz.
- Any remaining animatic/keyframe substrate has a concrete non-previz justification, or it is deleted.
- AI previz no longer carries baseline cross-links/contract fields that imply a live two-lane product.
- Required checks and representative browser verification pass, or a concrete blocker is recorded.

## Work Log

20260404-2245 — story creation: captured the new previz-speed gap as a separate `Draft` story instead of reopening Story 148, because the subsystem is still previz but the success surface changed from scoped execution / honest prerequisites to operator-loop latency. Evidence: the user’s live workflow report said AI previz “took a LONG time,” and Story 143’s validated registry entry still shows the useful AI lanes at roughly 32-39 seconds with Sora much slower. Drafted this as a fast-lane / latency-budget story rather than a vague “make rendering faster” note, because a few-second target likely requires a separate quick-previz path or hybrid strategy instead of minor tuning to the existing provider-backed call. Next step: compile methodology surfaces so the new story appears in generated planning views.
20260407-1742 — exploration: Story 149 is substrate-verified and buildable, but narrower than the original draft now that Stories 143, 144, and 148 have already landed the `ai_previz_generation` recipe, scene-scoped previz actions, media-validation trust for `ai_previz_video`, the shared previz adoption service, and the side-by-side `Previz` workspace surface. The real remaining gap is a first-class fast-lane contract: measured deterministic-lane latency, explicit fast-vs-slower-lane semantics, and visible upgrade flow from fast deterministic previz to slower AI previz. Evidence checked: `docs/spec.md` (`spec:5.3`, `spec:5.5`, `spec:6.3`, `spec:7.1`, `spec:10.3`), ADR-002, ADR-003, Stories 143/144/148, `src/cine_forge/services/previz_adoption.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `configs/recipes/recipe-ai-previz-generation.yaml`, `benchmarks/tasks/previz-usefulness.yaml`, and `make check-size`. Risks found: `PrevizPanel.tsx` and `SceneWorkspacePage.tsx` are already large, and this worktree currently has no `.venv`, so `/discover-models`, repo-local tests, and benchmark reruns will need environment repair or an alternate project Python before implementation can be verified cleanly. Next step: use the narrowed plan above as the implementation gate and promote to `Pending` only when coding begins.
20260408-0736 — implementation: repaired the local environment first by recreating `.venv` with Python `3.12` and installing the repo in editable dev mode, then ran `.venv/bin/python scripts/discover-models.py --summary` and `.venv/bin/python scripts/check-compromises.py` to re-ground the build against the live model catalog and current compromise state. Implemented the winning two-lane policy instead of chasing placebo AI-video speedups: the shared previz contract now exposes deterministic `Fast Previz` as the default lane, `AI Previz` as the slower richer upgrade lane, a `<= 6000 ms` fast-lane budget, and explicit latency/fidelity/upgrade metadata across backend and UI. Updated the benchmark/report surface to measure deterministic lanes honestly instead of using placeholder zeroes, then generated a new report from measured deterministic data plus the latest validated AI eval result. Evidence: annotated fast previz measured `606 ms` average / `635 ms` median on the fixed fixture pack, symbolic measured `476 ms` average, and the new report recommends `keep_fast_default` because `Veo 3.1 Lite Previz` still leads AI quality at `0.828` overall but remains around `39273 ms`. Verification: `make test-unit PYTHON=.venv/bin/python` (`665 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all completed successfully; UI lint still reports existing non-blocking warnings outside the touched previz flow. Browser verification covered desktop and mobile Scene Workspace plus animatic and AI-previz artifact detail with clean console output and screenshots for the updated routes. Next step: run `/validate` against Story 149 before any `/mark-story-done` closeout.
20260408-0922 — correction: user feedback invalidated the seeded browser-fixture evidence as product verification. The fixture had manually injected artifacts and produced an impossible UI state: disabled previz actions sitting beside already-ready previz outputs. Re-ran testing through the normal API path instead: created fresh project `story-149-real-ui`, uploaded the same sample screenplay, ran `mvp_ingest`, confirmed both previz preflights moved to honest `warn` status, then ran `creative_direction` to provide real `look_and_feel` / `rhythm_and_flow` / `sound_and_music` inputs before re-testing previz. Browser verification on the real route now shows an active prerequisite run instead of fake “ready but disabled” controls. New runtime finding: scene-scoped `animatics_generation` run `story149-real-animatic` spent about `455s` in `shot_planning`, then another `110s+` in `storyboards`, and still had not reached an `animatic` artifact when this note was written; process sampling shows the backend waiting on provider SSL reads, so representative previz validation is currently blocked by live runtime latency, not by the old seeded fixture. Also updated `AGENTS.md`, `/build-story`, and `/validate` to forbid counting hand-seeded or impossible project states as UX/product evidence. Decision correction: deterministic animatic should no longer be treated as the settled shipped fast-previz lane; next falsifiable step is a fastest-real-AI-previz eval across reachable engine-pack/settings combinations, grounded in the refreshed `/discover-models` inventory and the current real runtime blocker.
20260408-0955 — unblock pass: fixed the real animatic failure by making `animatic_v1` ignore non-file `sound_and_music.reference_audio_assets` entries during muxing instead of treating descriptive strings as project-relative audio files. Added unit coverage in `tests/unit/test_animatic_module.py`, reran the animatic-specific unit suite, and retried the failed honest run through `/api/runs/{run_id}/retry-failed-stage`. Evidence: retry run `story149-real-animatic-retry-ccad` completed in `62.5s` total (`animatics=61.7s`, `keyframes=0.8s`, `total_cost_usd=0.0`), and `/output/story-149-real-ui/artifacts/animatic/scene_001/v1.json` now carries `audio_refs=[]` instead of the bogus descriptive path that previously broke FFmpeg. Next step: rerun fresh AI previz on a normal project to measure whether the upstream model-routing fix materially changes time to first real AI previz artifact.
20260408-0955 — representative rerun: created fresh project `story-149-real-ui-rerun` through the API, uploaded the screenplay normally, reran `mvp_ingest` (`17.9s`) and `creative_direction` (`101.9s`), then launched scene-scoped `ai_previz_generation` for `scene_001`. Pinned both previz recipes’ `shot_planning` stage to `claude-haiku-4-5-20251001` / `claude-haiku-4-5-20251001` / `claude-opus-4-6` so previz no longer inherits video-facing defaults for upstream planning. Evidence: fresh run `run-6305b0b5` used Haiku for `shot_planning`, improved that stage from the earlier `455.2s` honest baseline to `230.3s`, then spent `63.3s` in `ai_previz` and `5.2s` in `validate_media` for a `299.0s` end-to-end time to first real `ai_previz_video`. That is materially better than the earlier path but still far outside the intended interactive budget, so Story 149 is now honestly `Blocked` on real runtime rather than on fixture validity. Next step: create/run a fastest-real-AI-previz eval or redesign upstream previz substrate so `shot_planning` no longer dominates the path.
20260408-1136 — validation: corrected the misleading fast-vs-AI copy before closeout instead of leaving the PR to imply that AI previz is simply “better except slower.” The shared policy and UI now describe AI previz as an optional generated motion pass that trades latency, cost, and determinism for a low-fidelity clip, and the Scene Workspace action labels now say `Generate` / `Regenerate` instead of ambiguous `Run` / `Refresh`. Fresh checks rerun in this validation pass: targeted previz pytest (`tests/unit/test_previz_adoption_service.py`, `tests/unit/test_animatic_module.py`, `tests/unit/test_previz_usefulness_report.py`), `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `./scripts/sync-agent-skills.sh --check`, and `pnpm methodology:check`. Browser verification was rerun after restarting the non-reloading API process so the UI reflected the final policy text: local Chromium Playwright passed on desktop Scene Workspace previz (`story-149-real-ui`), mobile Scene Workspace previz (`story-149-real-ui-rerun`), and AI previz detail (`story-149-real-ui-rerun`) with clean console output and screenshots saved under `/tmp/story149-*-final.png`. Outcome: implementation quality is validated, but the story remains correctly `Blocked` because the named runtime blocker still stands. Next step: follow the recorded unblock condition rather than trying to mark Story 149 done.
20260409-0935 — product-truth-realignment: user feedback hardened the product requirement: deterministic previz is not a shipped answer, only fallback/control substrate. Updated the shared previz contract, UI labels, and methodology/spec/story surfaces so AI previz is treated as the intended primary lane even while it remains runtime-blocked, and deterministic annotated animatic is labeled as `Deterministic Baseline` instead of `Fast Previz`. Evidence: `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/schemas/render.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `benchmarks/scripts/previz_usefulness_report.py`, and `docs/spec.md`. Next step: rerun full checks plus browser verification, then keep Story 149 blocked until a measured AI lane clears the fast-previz target.
20260409-0946 — validation-after-realignment: reran the changed-scope validation suite after the AI-primary / deterministic-fallback correction and verified the same live previz route through a local Playwright fallback when the MCP browser transport stayed unavailable. Evidence: `.venv/bin/python -m pytest tests/unit/test_previz_adoption_service.py tests/unit/test_previz_usefulness_report.py -q` (pass), `make test-unit PYTHON=.venv/bin/python` (`675 passed, 158 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass), `pnpm --dir ui run lint` (0 errors, existing warnings only), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), `pnpm methodology:compile && pnpm methodology:check` (pass), and browser artifacts `output/browser-verification/previz-desktop.png` plus `output/browser-verification/previz-mobile.png` with zero console/page errors in both viewports. DOM follow-up confirmed the current UI no longer renders `Generate/Regenerate Fast Previz`; the one remaining `Fast Previz complete` string comes from historical run/chat text, not the patched lane labels. Outcome: the copy/policy correction is validated, and Story 149 remains blocked only on real AI-previz runtime.
20260409-1408 — user-clarification-reopen: user clarified that the `<= 6000 ms` detector is a climb goal, not a blocker, and that “proper previz” means an actual AI-generated clip rather than the programmatically created placeholder video. Updated Story 149 from `Blocked` to `Pending`, re-scoped the remaining acceptance/tasks around removing or explicitly re-homing the deterministic placeholder, and treated Story 153's runtime/usefulness split as supporting evidence rather than a gate. Next step: build the operator-facing AI-previz-only product slice and validate it on the normal Scene Workspace / Artifact Detail path.
20260409-1418 — build-story exploration: confirmed Story 149 is buildable as a narrow operator-surface correction, not a new benchmarking or provider-selection story. Evidence checked: ADR-002, ADR-003, Stories 028/143/144/148/153, `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/api/routers/previz.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/previz-panel-support.ts`, `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, `src/cine_forge/pipeline/scene_actions.py`, and `make check-size`. Key finding: the backend policy already says AI previz is primary, but the panel still gives deterministic baseline equal visual weight and first-viewer placement, while shared run/stage labels still make the placeholder feel like a peer product lane. Risks: `ui/src/components/PrevizPanel.tsx` is `617` lines, `src/cine_forge/services/previz_adoption.py` is `423` lines, and `PrevizAdoptionService.build_status` already exceeds `100` lines, so implementation should extract helpers before adding logic. Next step: use the rewritten plan above as the human gate before implementation.
20260409-1425 — implementation-start: moved Story 149 to `In Progress` after the human gate approved the rewritten plan. Next step: compile methodology surfaces so generated planning views reflect the active build, then implement the Scene Workspace hierarchy change before deciding whether any backend contract change is truly needed.
20260409-1402 — implementation: rewired the operator-facing previz surface so AI previz is now the obvious primary generate/review path and deterministic baseline is visibly secondary fallback/control only. Evidence: `ui/src/components/PrevizPanel.tsx` now renders the AI card first, gives it the stronger primary badges and CTA, and renders the AI viewer before the deterministic viewer; `ui/src/components/AiPrevizViewer.tsx` and `ui/src/components/AnimaticViewer.tsx` now use the correct cross-lane upgrade copy instead of swapped messages; `ui/src/components/previz-panel-support.ts`, `ui/src/components/preview-provenance.ts`, `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and `src/cine_forge/pipeline/scene_actions.py` now describe deterministic output as fallback/control substrate instead of peer previz. Verification: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`680 passed, 158 deselected, 1 warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with existing warnings only), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), and `pnpm methodology:check` (pass). Representative browser verification used the worktree backend plus Vite dev server on a fresh API-created project `story-149-ui-verify-20260409` from `samples/sample-screenplay.fountain`; desktop and mobile screenshots on the real route confirmed AI-first lane ordering, explicit deterministic fallback framing, and zero browser console errors. Environment note: this worktree had no local `.venv` or `ui/node_modules`, so validation reused the main repo virtualenv and UI dependencies instead of pretending the local toolchain existed. Next step: hand off for `/validate` or user review; leave story status `In Progress` until formal close-out.
20260409-1413 — scope-correction: user explicitly rejected the deterministic baseline as useless for both the user and the pipeline, so Story 149 now treats deletion of that lane as the requirement instead of merely demoting it to fallback/control. Updated the goal, acceptance criteria, task list, architectural fit, and plan accordingly, and reopened the `Build complete` gate because the prior implementation only re-homed the placeholder rather than deleting it. Evidence checked while making the correction: `docs/spec.md` (`spec:6.3.5`), `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/visualization/keyframe_v1/main.py`, and the current Story 149 plan/work-log history. Next step: implement the hard-removal slice and re-verify the real previz route.
20260409-1445 — hard-removal implementation: deleted the shipped deterministic previz lane instead of merely demoting it. Evidence: `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/previz-panel-support.ts`, `ui/src/lib/types.ts`, `src/cine_forge/schemas/render.py`, `src/cine_forge/services/previz_adoption.py`, and `src/cine_forge/modules/generation/render_adapter_v1/main.py` now expose AI previz as the only shipped lane and remove baseline-link contract fields; `src/cine_forge/modules/visualization/keyframe_v1/main.py` plus `src/cine_forge/modules/visualization/keyframe_v1/module.yaml` now re-home keyframes to storyboard/render support without animatic dependency; `src/cine_forge/modules/timeline/track_system_v1/main.py`, `src/cine_forge/pipeline/graph.py`, `src/cine_forge/pipeline/scene_actions.py`, and the deleted `configs/recipes/recipe-animatics-generation.yaml` remove deterministic previz from pipeline fallback, the shipped recipe list, and normal scene-action workflow. Historical deterministic code remains only as non-shipped benchmark/evidence substrate. Validation: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`679 passed, 158 deselected, 1 warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with the existing 6 warnings), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass with the existing chunk-size warning). Runtime evidence: `curl http://127.0.0.1:8000/api/recipes` no longer returns `animatics_generation`; `POST /api/projects/story-149-previz-test-20260409/scene-actions/preflight` with `recipe_id=animatics_generation` now returns a `soft_block` explaining the deterministic baseline was removed; Playwright verification on `http://localhost:5174/story-149-previz-test-20260409/scenes/scene_001?tab=previz` confirmed desktop and mobile AI-only previz surfaces, no deterministic buttons/links, and clean console output aside from the standard React DevTools info log. Next step: hand off for `/validate`; keep Story 149 `In Progress` until formal close-out.
20260409-1456 — validation: the shipped previz workflow validates as AI-only, but Story 149 is not honestly closable yet because repo-level animatic substrate still survives outside the Scene Workspace previz path. Fresh evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`679 passed, 158 deselected, 1 warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with the existing 6 warnings), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass with the existing chunk-size warning), and `pnpm methodology:check` (pass). Runtime/API evidence: `curl http://127.0.0.1:8000/api/health` returned `{"status":"ok","version":"2026.04.09-03"}`; `curl http://127.0.0.1:8000/api/recipes` still excludes `animatics_generation`; `POST /api/projects/story-149-previz-test-20260409/scene-actions/preflight` with `recipe_id=animatics_generation` returns the expected removal `soft_block`; and fresh desktop/mobile Playwright checks on `http://localhost:5174/story-149-previz-test-20260409/scenes/scene_001?tab=previz` confirmed AI-only previz with no deterministic CTA and clean console output apart from the standard React DevTools info log. Remaining same-scope gap: `ui/src/pages/ArtifactDetail.tsx` still renders `animatic` and `previz_reel`, `src/cine_forge/driver/schema_registry.py` still registers both artifact types, and `animatic_v1` still survives in module, benchmark, and unit-test substrate (`src/cine_forge/modules/visualization/animatic_v1/*`, `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `tests/unit/test_animatic_module.py`). Environment note: this worktree still has no local `.venv`, so the fresh backend validation pass again used `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`. Next step: delete or explicitly re-home the remaining animatic / `previz_reel` substrate, then rerun `/validate`; keep Story 149 `In Progress`.
20260409-1514 — cleanup: finished deleting the remaining repo-level deterministic previz substrate instead of leaving dead registry, viewer, fixture, or module ownership behind. Evidence: `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/artifact-meta.ts`, and `ui/src/lib/constants.ts` no longer expose `animatic` or `previz_reel`; `src/cine_forge/driver/schema_registry.py`, `src/cine_forge/schemas/preview.py`, `src/cine_forge/schemas/__init__.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/media_validation.py`, `src/cine_forge/schemas/track.py`, and `src/cine_forge/pipeline/scene_actions.py` remove the old artifact registrations/contracts and re-home live preview media + keyframe contracts under neutral schema/support names; `src/cine_forge/modules/visualization/keyframe_v1/support.py` now owns the surviving crop/placeholder helpers for live keyframe generation; and the deleted `src/cine_forge/modules/visualization/animatic_v1/*`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/PrevizReelViewer.tsx`, `tests/animatic_fixtures.py`, `tests/unit/test_animatic_module.py`, `tests/integration/test_animatic_integration.py`, and `tests/fixtures/media/*` remove the dead product/test substrate. Historical deterministic comparison evidence remains benchmark-only via `benchmarks/scripts/legacy_previz_support.py` and `benchmarks/scripts/generate_previz_usefulness_dataset.py`. Fresh verification: targeted pytest over schema/scene-action/track/render/media-validation/previz surfaces (pass), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`672 passed, 157 deselected, 1 warning`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass), `pnpm --dir ui run lint` (pass with the existing 6 warnings), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass with the existing chunk-size warning), and `pnpm methodology:check` (pass). Runtime evidence after restarting backend/UI: `curl http://127.0.0.1:8000/api/health` returned `{"status":"ok","version":"2026.04.09-03"}`, `curl http://127.0.0.1:8000/api/recipes` still excludes `animatics_generation`, `POST /api/projects/story-149-previz-test-20260409/scene-actions/preflight` with `recipe_id=animatics_generation` still returns the removal `soft_block`, and fresh desktop/mobile Playwright checks on `http://localhost:5174/story-149-previz-test-20260409/scenes/scene_001?tab=previz` confirmed AI-only previz with no deterministic CTA and clean console output apart from the standard React DevTools info log. Environment note: this worktree still has no local `.venv`, so backend verification again used `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`. Next step: Story 149 is ready for `/mark-story-done`.
20260409-1518 — completion: Story 149 is now formally closed because the shipped previz surface, runtime contracts, and repo substrate all agree on AI-only previz truth. Evidence: the latest cleanup/validation pass removed the remaining deterministic animatic / `previz_reel` ownership, reran the required targeted and full validation suite (`make test-unit`, Ruff, UI lint, `tsc -b`, UI build, methodology check), and re-verified the normal Scene Workspace previz route plus the removed animatics preflight through the live backend/UI. Methodology surfaces and changelog were refreshed as part of close-out. Next step: `/check-in-diff`.
