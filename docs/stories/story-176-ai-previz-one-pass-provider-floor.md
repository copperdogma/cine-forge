---
id: "176"
title: "AI Previz Provider Floor on Honest One-Pass Route"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
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
  - "151"
  - "153"
  - "174"
  - "175"
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
  - "provider-floor"
  - "one-pass"
  - "iteration-loop"
legacy_system: ""
---

# Story 176 - AI Previz Provider Floor on Honest One-Pass Route

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:8.2, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 151, Story 153, Story 174, Story 175

## Goal

Story 175 proved that the honest shipped AI-previz route should stay on the one-pass `mvp_ingest_only` boundary: first playable fell to `96821 ms`, prerequisites dropped to `44048 ms`, and the old full `scene_ready` chain is no longer the right default comparison. That closes the prerequisite-side ambiguity, but it does not answer the remaining product question: which already integrated provider is now the best floor for the shipped one-pass lane? Story 151 showed xAI/Grok Imagine as the fastest measured runtime on an older `mvp_ingest_only` boundary (`65552 ms` total / `21687 ms` isolated `ai_previz`), while the current usefulness harness still only scores Sora/Veo candidates. This story re-runs the provider-floor question on the current honest one-pass route, extends usefulness coverage where needed, and either ships a materially better lane or records that the provider/runtime floor is still the blocker.

## Acceptance Criteria

- [x] A bounded one-pass provider-floor comparison exists on the maintained honest route. At minimum it compares the shipped `google_veo31_lite` lane against `xai_grok_imagine_video` and one already integrated Google comparator on the same `mvp_ingest_only` boundary, with identical upstream substrate and persisted runtime/cost metadata.
- [x] The paired quality surface is honest. If `xai_grok_imagine_video` or any added candidate remains in scope, `previz-usefulness` is extended to score that candidate on the fixed clip pack instead of leaving it as runtime-only evidence; otherwise the story explicitly narrows the candidate set and explains why.
- [x] `docs/evals/registry.yaml` is updated in the same story with fresh `real-ai-previz-runtime` and `previz-usefulness` result paths, `git_sha`, dates, and mismatch classification (`model-wrong`, `golden-wrong`, `ambiguous`, plus `runtime-blocking` vs `non-runtime-blocking`).
- [x] The shipped one-pass AI-previz lane changes only if a candidate improves first playable or isolated `ai_previz` runtime by at least `15%` versus Story 175's shipped baseline while staying at or above the validated usefulness floor of `0.803`; otherwise the shipped lane stays unchanged and the blocker truth is sharpened.
- [x] Focused regression coverage exists for any changed engine-pack selection, usefulness-dataset wiring, prompt/provenance contract, or adoption policy. If UI/provenance copy changes, Scene Workspace previz and AI-previz Artifact Detail are browser-verified on desktop and mobile with clean console output.

## Out of Scope

- Re-running the same fixed-pack Veo-only comparison from Story 174 without a new one-pass hypothesis
- Another prerequisite-collapse story; Story 175 already answered that boundary
- New provider transport or broad provider integration beyond the already wired xAI / Google / OpenAI packs
- Final-render provider-floor or export-fidelity work
- Reintroducing deterministic placeholder previz as the product answer
- A broad Scene Workspace redesign outside previz/adoption/provenance touchpoints

## Approach Evaluation

- **Simplification baseline**: Keep the shipped `google_veo31_lite` one-pass lane unchanged. Story 175 already proved that the one-pass route is the simplest honest architecture, so the first measurement here is provider floor on that route, not more orchestration work.
- **AI-only**: A different already integrated provider may materially improve the shipped one-pass lane with the current compiled previz contract. Plausible, but insufficient by itself because runtime/cost/path truth must still be measured deterministically.
- **Hybrid**: Strongest default. Keep provider-floor measurement deterministic via `real-ai-previz-runtime`, use the fixed clip-pack semantic judge in `previz-usefulness`, and change product wiring only if the runtime winner still clears the usefulness floor. If the pure quality leader differs, record that divergence explicitly instead of pretending the evidence is unanimous.
- **Pure code**: Choosing the winner from engine-pack metadata or older boundary results alone is wrong. Story 153 answered `scene_ready`, Story 174 answered fixed-pack prompt compaction on that same old boundary, and Story 175 changed the shipped route.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced truth and rejects silent fallback. ADR-003 keeps previz as a planning surface, not a disguised final-render lane. `spec:6` stays in `climb` specifically because fast useful AI previz is still unfinished, while Story 175 already proved the prerequisite-side simplification answer. The AGENTS live-model rule also applies: model choice must use fresh discovery rather than stale assumptions.
- **Existing patterns to reuse**: Story 151's xAI runtime probe, Story 153's provider-floor harness and decision-summary pattern, Story 174's fixed-pack usefulness/runtime pairing, Story 175's one-pass route truth, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `benchmarks/tasks/previz-usefulness.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/*.yaml`, `src/cine_forge/services/previz_adoption.py`, and `ui/src/components/preview-provenance.ts`.
- **Eval**: Reuse the maintained `real-ai-previz-runtime` and `previz-usefulness` surfaces rather than inventing a third detector. If xAI stays in the candidate set, the usefulness harness must be extended in the same story; shipping a runtime-only winner would be a regression in evaluation honesty.

## Tasks

- [x] Re-run `/discover-models` and freeze the candidate set for this story to already integrated one-pass previz packs. Default expectation: shipped `google_veo31_lite`, `google_veo31_fast`, and `xai_grok_imagine_video`; include `google_veo31` or `openai_sora2` only if build finds a concrete one-pass reason they still belong.
- [x] Extend the `real-ai-previz-runtime` fixture manifest and harness only as needed to compare provider floor on the honest `mvp_ingest_only` boundary rather than the older `scene_ready` boundary.
- [x] Extend `generate_previz_usefulness_dataset.py`, `previz-usefulness.yaml`, and `previz_usefulness_report.py` so xAI or any newly included candidate can be scored on the same fixed clip pack; if that is not honestly buildable, narrow the candidate set explicitly instead of comparing unlike surfaces.
- [x] Run the paired runtime and usefulness comparisons, classify every significant mismatch, and update `docs/evals/registry.yaml` with the verified result paths, `git_sha`, dates, and blocker classification.
- [x] If a candidate materially wins, wire it into `recipe-ai-previz-generation.yaml`, engine-pack defaults, and adoption/provenance copy in the same story. If no candidate wins, keep the shipped lane unchanged and record the sharper provider-floor blocker truth.
- [x] Add or extend focused regression coverage for changed runtime-harness case handling, xAI usefulness dataset generation, prompt/provenance fields, adoption policy, and any changed provider request shaping.
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
  - [x] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: The provider-floor question belongs first in the benchmark/runtime seams: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/generate_previz_usefulness_dataset.py`, and the engine-pack definitions under `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/`. Product wiring should stay limited to `recipe-ai-previz-generation.yaml`, `src/cine_forge/services/previz_adoption.py`, and the small previz UI surfaces if a new winner actually ships.
- **Data contracts**: Reuse the existing render/provenance schemas and the benchmark result models in `real_ai_previz_runtime_support.py` / `real_ai_previz_runtime_decision.py`. If a new provider-floor or prompt-profile field crosses the backend/UI boundary, define it schema-first in the render schema layer before service/UI code consumes it.
- **File sizes**: `make check-size` currently flags the likely watchpoints: `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`560`, LARGE), `benchmarks/scripts/generate_previz_usefulness_dataset.py` (`660`, LARGE), `benchmarks/scripts/previz_usefulness_report.py` (`506`, LARGE), `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` (`695`, LARGE), `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1823`, LARGE), `src/cine_forge/ai/video.py` (`550`, LARGE), `ui/src/components/PrevizPanel.tsx` (`419`, LARGE), and `tests/unit/test_render_adapter_module.py` (`948`, test file). Smaller likely owners are `benchmarks/scripts/real_ai_previz_runtime_support.py` (`308`), `benchmarks/scripts/real_ai_previz_runtime_decision.py` (`229`), `src/cine_forge/services/previz_adoption.py` (`341`), `ui/src/components/AiPrevizViewer.tsx` (`338`), `ui/src/components/preview-provenance.ts` (`137`), `tests/unit/test_previz_adoption_service.py` (`267`), `tests/unit/test_previz_prompting.py` (`170`), and `tests/unit/test_video_client.py` (`301`). Build should prefer these smaller seams over widening the oversized owners.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/evals/registry.yaml`, `docs/runbooks/promptfoo.md`, ADR-002, ADR-003, and Stories 149 / 151 / 153 / 174 / 175. I did not find a newer decision document in `docs/design/` that changes previz ownership beyond ADR-002 / ADR-003.

## Files to Modify

- `docs/stories/story-176-ai-previz-one-pass-provider-floor.md` - keep the story current during build, validation, and close-out (`122`)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` - add or reshape one-pass provider-floor cases on the maintained boundary (`169`)
- `benchmarks/scripts/real_ai_previz_runtime_eval.py` - compare provider floor on the one-pass route and persist the right metrics (`560`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` - extend shared result and summary support only if the new boundary needs more metadata (`308`)
- `benchmarks/scripts/real_ai_previz_runtime_decision.py` - keep the runtime/usefulness decision summary honest if the candidate matrix changes (`229`)
- `benchmarks/scripts/generate_previz_usefulness_dataset.py` - add xAI or other included candidate dataset generation on the fixed clip pack (`660`)
- `benchmarks/tasks/previz-usefulness.yaml` - add any new candidate rows to the maintained usefulness harness (`145`)
- `benchmarks/scripts/previz_usefulness_report.py` - report the updated candidate ranking and blocker decision (`506`)
- `configs/recipes/recipe-ai-previz-generation.yaml` - change the shipped one-pass lane only if a measured winner exists (`80`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-lite.yaml` - current shipped one-pass comparator settings (`41`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-fast.yaml` - Google comparator settings (`47`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/grok-imagine-video.yaml` - xAI comparator settings (`44`)
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` - fallback-only if a candidate needs bounded provider-specific prompt shaping or budgeting (`695`)
- `src/cine_forge/ai/video.py` - fallback-only if provider request shaping changes for the winning lane (`550`)
- `src/cine_forge/services/previz_adoption.py` - update recommendation/provisional truth if the shipped answer changes (`341`)
- `ui/src/components/PrevizPanel.tsx` - update operator-facing disclosure only if the shipped lane or blocker wording changes (`419`)
- `ui/src/components/AiPrevizViewer.tsx` - viewer disclosure for any changed lane/provenance fields (`338`)
- `ui/src/components/preview-provenance.ts` - provenance wording for any new provider-floor or blocker metadata (`137`)
- `tests/unit/test_previz_adoption_service.py` - lock the changed adoption recommendation/provisional truth if needed (`267`)
- `tests/unit/test_previz_prompting.py` - prompt contract or provider-budget coverage if `previz_prompting.py` changes (`170`)
- `tests/unit/test_video_client.py` - provider request-shaping coverage if `ai/video.py` changes (`301`)
- `tests/unit/test_render_adapter_module.py` - fallback-only touchpoint if pack defaults or provenance fields change (`948`)
- `docs/evals/registry.yaml` - record the fresh one-pass runtime/usefulness evidence, `git_sha`, dates, and mismatch classification (`2575`)

## Redundancy / Removal Targets

- Stale notes that still treat Story 153's `scene_ready` provider-floor result as the current answer after Story 175 changed the shipped boundary
- Any runtime-only xAI recommendation that skips usefulness comparison and would let a quality-unknown lane look shipped-ready
- Adoption/provenance copy that implies the current one-pass Veo Lite lane is already the settled provider-floor answer

## Notes

- This is a new story, not a reopen of Story 174 or Story 175. Anti-fragmentation check: Story 174 exhausted fixed-pack prompt/profile attempts on the old `scene_ready` boundary, and Story 175 answered the prerequisite-collapse question on the current route. The remaining question is a different validation surface: provider floor on the shipped one-pass lane.
- Current honest shipped baseline from Story 175: `96821 ms` to first playable, `44048 ms` prerequisites, `52773 ms` isolated `ai_previz`, and `105702 ms` full completion on the one-pass `mvp_ingest_only` route.
- Current xAI context from Story 151: `xai_4_480p_mvp_ingest_only` reached `65552 ms` total / `21687 ms` isolated `ai_previz` on an older one-pass-shaped boundary, which is strong enough to justify a re-test on the current shipped route instead of dismissing xAI as exhausted.
- Story 176 widened the maintained usefulness harness to include `xai_grok_imagine_video_previz`. Current fixed-pack report: `google_veo31_fast` leads pure usefulness at `0.9063`, `google_veo31_lite` follows at `0.8853`, and xAI/Grok Imagine clears the validated usefulness floor at `0.8413`.
- Live discovery on 2026-04-19 found `72` models across `3` providers with `28` untested. That is enough freshness to avoid stale model assumptions, but it does not by itself add a new already integrated video provider beyond the current OpenAI / Google / xAI set.

## Plan

1. Freeze the candidate set on the honest one-pass boundary before changing any product wiring.
   Files: `benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, fallback-only `benchmarks/scripts/real_ai_previz_runtime_decision.py`
   Change: reuse the existing `mvp_ingest_only` runtime cases that already cover `google_veo31_lite`, `google_veo31_fast`, and `xai_4_480p`; only touch the harness if the result bundle or decision summary needs extra metadata for the narrowed one-pass comparison. Do not reopen the old `scene_ready` boundary.
   Impact / risk: `real_ai_previz_runtime_eval.py` is already `560` lines, so widen the fixture or support seam first and only touch the main script when the existing case plumbing cannot express the comparison cleanly.
   Repo-fit evidence: Story 175 already established that the one-pass route is the current shipped truth, and Story 151 already proved xAI belongs in the candidate set on that same shaped boundary.
   Done looks like: one runtime artifact compares only the honest one-pass lanes with identical upstream substrate and persisted timing metadata.

2. Close the current usefulness-harness blind spot before allowing xAI to compete as a ship candidate.
   Files: `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `benchmarks/tasks/previz-usefulness.yaml`, `benchmarks/scripts/previz_usefulness_report.py`
   Change: extend the fixed clip-pack dataset, task rows, and report variant list so `xai_grok_imagine_video` is scored on the same surface as the Veo and Sora lanes. If exploration during build proves the xAI clip cannot be produced or scored honestly on that same surface, narrow the candidate set explicitly and keep xAI out of the ship decision instead of comparing unlike evidence.
   Impact / risk: this is the main new work. `generate_previz_usefulness_dataset.py` (`660`) and `previz_usefulness_report.py` (`506`) are already oversized, so add the smallest possible candidate wiring and avoid unrelated refactors. If a new cross-layer field becomes necessary, make it schema-first instead of smuggling stringly metadata.
   Repo-fit evidence: Story 174 and the current registry already use `previz-usefulness` as the semantic gate; ADR-002 rejects silent truth gaps, so a runtime-only xAI win is not enough to change the shipped lane.
   Done looks like: the provider-floor decision compares like with like, not runtime-only evidence versus runtime-plus-usefulness evidence.

3. Run the paired runtime and usefulness comparisons, then update the canonical eval truth.
   Files: benchmark scripts above plus `docs/evals/registry.yaml`
   Change: run `real-ai-previz-runtime` on the one-pass boundary and `previz-usefulness` on the matching candidate set, classify significant mismatches as `model-wrong`, `golden-wrong`, or `ambiguous`, record runtime impact, and update the registry with fresh dates, `git_sha`, and result paths.
   Impact / risk: this story cannot close on raw scores alone. If the usefulness extension exposes scorer or golden defects, that classification work is part of the story rather than optional cleanup.
   Repo-fit evidence: the repo already treats `docs/evals/registry.yaml` as the single maintained truth surface, and the story acceptance criteria explicitly require blocker classification instead of benchmark theater.
   Done looks like: the repo has one current, classified answer for the one-pass provider-floor question.

4. Ship a new provider only if it clears the runtime bar without dropping below the usefulness floor; otherwise preserve the current lane and sharpen the blocker truth.
   Files: `configs/recipes/recipe-ai-previz-generation.yaml`, winning engine-pack file(s), `src/cine_forge/services/previz_adoption.py`, fallback-only `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/components/preview-provenance.ts`, and small focused tests
   Change: if a candidate beats the Story 175 shipped baseline by at least `15%` while staying at or above usefulness `0.803`, update the shipped route and any adoption/provenance copy that describes it, even if a different candidate still leads pure fixed-pack quality. If no candidate clears both bars, leave the shipped lane on `google_veo31_lite` and record that the provider floor remains the blocker.
   Impact / risk: `previz_adoption.py` currently has no xAI label mapping, so it only needs touching if xAI actually wins. UI work should stay disclosure-only; if nothing ships, do not churn the interface.
   Repo-fit evidence: ADR-003 keeps previz as a planning surface with honest provenance, not a hidden provider roulette. The smallest correct product change is to touch recipe/adoption/provenance only after the eval surfaces agree.
   Done looks like: either the shipped one-pass lane changes coherently across recipe, provenance, and adoption surfaces, or the repo keeps the current lane and documents the sharper blocker without extra churn.

Human approval blocker: implementation should proceed only with the explicit understanding that extending `previz-usefulness` for xAI is part of the story if xAI remains in scope; otherwise the candidate set must be narrowed before any runtime run is treated as ship-relevant evidence.

## Work Log

20260419-1104 - story-created: triage after Story 175 confirmed the active `spec:6` / `spec:7` lane still lacks a post-one-pass owner, so I created Story 176 as a new `Pending` story rather than reopening Story 174 or 175. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/evals/registry.yaml`, ADR-002, ADR-003, Stories 149 / 151 / 153 / 174 / 175, ran fresh `scripts/discover-models.py --summary`, and confirmed the anti-fragmentation boundary change: Story 174 exhausted fixed-pack work on `scene_ready`, Story 175 closed prerequisite collapse, and the remaining question is provider floor on the shipped one-pass route. Next step: run `/build-story 176`.
20260419-1128 - exploration-notes: traced the current provider-floor path before implementation and confirmed the boundary split is real. Files likely to change are the runtime harness (`benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, fallback-only `real_ai_previz_runtime_decision.py`), the usefulness harness (`benchmarks/scripts/generate_previz_usefulness_dataset.py`, `benchmarks/tasks/previz-usefulness.yaml`, `benchmarks/scripts/previz_usefulness_report.py`), the eval registry, and only if a winner ships, the recipe/adoption/provenance surfaces (`configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/services/previz_adoption.py`, small UI disclosure files, and focused tests). Files at risk of breakage are the oversized benchmark scripts, `previz_adoption.py` label matching, and any provider-specific request shaping in `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` or `src/cine_forge/ai/video.py` if the winning lane needs special handling. Consulted decisions and context: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/evals/registry.yaml`, `docs/runbooks/promptfoo.md`, ADR-002, ADR-003, Stories 151 / 153 / 174 / 175, and fresh `scripts/discover-models.py --summary`. Patterns to follow: Story 175's one-pass runtime truth, Story 174's paired runtime/usefulness evaluation, existing engine-pack comparator wiring, and registry-first eval recording. Redundancy targets: stale language that still treats the old `scene_ready` provider floor as current, and any runtime-only xAI recommendation that bypasses usefulness evidence. Surprise / risk: the runtime harness already contains `xai_4_480p_mvp_ingest_only`, but the usefulness dataset/report and adoption label mapping still assume Google/OpenAI variants, so xAI cannot honestly win the shipped lane without extending those seams in the same story. Next step: present the plan and get approval before changing code.
20260419-1759 - implementation: widened the maintained usefulness harness to include `xai_grok_imagine_video`, made the runtime summary honest for one-pass-only runs, reran the live provider-floor comparison, and switched the shipped recipe/adoption truth to xAI because it cleared the story bar. Evidence: `benchmarks/results/real-ai-previz-runtime-story-176-one-pass-provider-floor-2026-04-19.{json,md}` shows xAI at `61387 ms` to first playable (`43708 ms` prerequisites + `17679 ms` isolated `ai_previz`; `67856 ms` full completion) versus shipped Lite at `96588 ms` / `52880 ms` and Veo Fast at `96698 ms` / `52990 ms`; `benchmarks/results/previz-usefulness-story-176-one-pass-provider-floor-2026-04-19-report.{json,md}` shows Veo Fast leading fixed-pack quality at `0.9063`, Lite at `0.8853`, and xAI still clearing the validated usefulness floor at `0.8413`. Classification: runtime harness had no model-wrong / golden-wrong / ambiguous mismatches; usefulness rerun had no model-wrong or golden-wrong mismatches and only three ambiguous deterministic-control mismatches (`Symbolic Animatic / quiet_bedside_vigil`, `Symbolic Animatic / radio_hold_tracking`, `Annotated Animatic / radio_hold_tracking`), all non-runtime-blocking. Product decision: ship xAI because it improves Story 175's shipped baseline by `36.4%` to first playable and `66.6%` inside `ai_previz` while staying `0.0383` above the `0.803` usefulness floor, even though Veo Fast remains the pure fixed-pack quality leader. Checks: targeted pytest/ruff slices passed, `make test-unit PYTHON=.venv/bin/python` passed (`757 passed, 173 deselected`), and `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` passed. Next step: run `/validate 176`.
20260419-1816 - validation: reran Story 176 validation end to end on the fresh local diff. Evidence: `make test-unit PYTHON=.venv/bin/python` passed (`757 passed, 173 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` passed, `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b` passed, `pnpm methodology:check` stayed clean apart from the pre-existing `api_service_and_operator_console` architecture-audit warning, `benchmarks/results/real-ai-previz-runtime-story-176-one-pass-provider-floor-2026-04-19.{json,md}` reran with xAI still winning at `65514 ms` first playable (`47865 ms` prerequisites + `17649 ms` isolated `ai_previz`; `82137 ms` full completion), and `benchmarks/results/previz-usefulness-story-176-one-pass-provider-floor-2026-04-19-report.{json,md}` reran with Lite leading fixed-pack quality at `0.8980`, xAI still above the `0.803` floor at `0.8420`, and one new ambiguous xAI scorer mismatch on `radio_hold_tracking` plus the three existing ambiguous deterministic-control mismatches, all non-runtime-blocking. Validation finding: the shipped recipe/adoption truth moved to xAI, but `src/cine_forge/modules/generation/render_adapter_v1/main.py` still leaves the internal `ai_previz` `default_engine_pack_id` on `google_veo31_lite`, so the story's engine-pack-defaults ship-through remains incomplete and untested. Next step: keep Story 176 open, update the render-adapter `ai_previz` default plus focused regression coverage, then rerun `/validate 176`.
20260419-1824 - validation-fix: updated the render adapter's internal `ai_previz` fallback from `google_veo31_lite` to `xai_grok_imagine_video` and added focused boundary coverage in `tests/unit/test_render_adapter_module.py` so the no-`engine_pack_id` path now matches the shipped recipe/adoption truth. Evidence: `PYTHON=.venv/bin/python .venv/bin/python -m pytest tests/unit/test_render_adapter_module.py -q` passed (`14 passed`), `make test-unit PYTHON=.venv/bin/python` passed (`758 passed, 173 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` passed, `pnpm --dir ui run lint` passed, and `cd ui && npx tsc -b` passed. I did not rerun the provider-backed runtime/usefulness evals after this fix because the patch only changes the non-recipe `ai_previz` default path; the fresh Story 176 eval artifacts from the immediately prior validation pass still describe the shipped recipe lane and remain the current classified evidence. Next step: Story 176 is implementation-complete; proceed to `/mark-story-done`.
20260419-1832 - completion: marked Story 176 done after confirming the shipped xAI one-pass previz lane, registry truth, render-adapter default, and focused regression coverage are aligned. Evidence: workflow gates are closed, `CHANGELOG.md` now records Story 176, `pnpm methodology:compile` refreshed generated planning surfaces after the status change, and the latest required checks remain green (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`). Next step: `/check-in-diff`.
