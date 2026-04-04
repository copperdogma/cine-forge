# Story 144 — AI Previz Adoption Gate and Trust Guardrails

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness), R12 (transparency & control)
**Spec Refs**: spec:5.5 (Readiness Indicators), spec:6.3 (Animatics / Previz Video), spec:6.3.4 (Serendipity Preservation), spec:7.1 (Render Adapter Layer), spec:8.2 (Quality Validation), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / concern-group inputs)
**Depends On**: Story 032 (Cost Tracking and Budget Management), Story 140 (Agentic Media Validation Loop), Story 143 (AI-Generated Low-Fidelity Previz)

## Goal

Story 143 shipped AI previz as a real operator-facing lane, but the product still does not make an evidence-backed recommendation/default decision. The current Scene Workspace copy hard-codes AI previz as experimental and still shows `cost unverified`, while runtime trust semantics remain stronger for `generated_video` than for `ai_previz_video`. This story closes that gap by turning the current static label into a real adoption gate: verify actual runtime cost/latency for the leading AI-previz lane, extend trust/health surfacing where needed, and make the product's recommendation/default state flow from measured evidence instead of stale story-era copy.

## Acceptance Criteria

- [x] The AI-previz lane exposes verified runtime cost/latency or a deterministic estimated-cost method grounded in actual recipe/provider behavior. If cost still cannot be verified, the product surfaces the concrete blocker instead of a generic hard-coded `cost unverified` label.
- [x] `ai_previz_video` artifacts participate in a typed trust path that is at least as honest as the current `generated_video` path: runtime validation or an equivalent artifact-backed health signal is available headlessly and visible in Scene Workspace and Artifact Detail.
- [x] Recommendation/default state for AI previz is derived from shared measured evidence rather than hard-coded UI text. The product can represent at least these states cleanly: `default`, `recommended optional`, or `experimental/manual`, with explicit blocker reasons when not default.
- [x] Any fresh benchmark or runtime-validation evidence required for the adoption decision is recorded in `docs/evals/registry.yaml`, and all significant mismatches are classified as model-wrong, golden-wrong, or ambiguous with runtime-blocking vs non-runtime-blocking status.
- [x] Browser verification covers the Scene Workspace `Previz` tab and AI-previz artifact detail route, showing the new trust/recommendation state with no browser console errors.

## Out of Scope

- Re-running a broad multi-provider video sweep beyond the minimum candidate work needed to settle the current adoption gate
- Final-render quality improvements, photoreal polish, or cross-shot identity R&D beyond low-fidelity previz trust
- General cost-profile or project-budget UI work already owned by Story 138
- Reworking runtime media validation for every media artifact type if the existing substrate can be reused narrowly for `ai_previz_video`
- New collaboration, transcript, or memory features unrelated to previz trust and adoption

## Approach Evaluation

- **Simplification baseline**: first verify whether the current `previz-usefulness` evidence plus provider/runtime metadata already answers the product question without new AI behavior. Story 143 shows that is not true yet: the lane is still hard-coded as experimental and its cost state is not backed by measured runtime evidence.
- **AI-only**: let a model decide whether AI previz is good enough to recommend and summarize why. Weak fit. This would turn a trust surface into another opaque model judgment and would still leave deterministic cost/provenance unresolved.
- **Hybrid**: existing benchmark evidence plus deterministic cost/provenance plus runtime semantic validation where needed. Strongest likely fit because adoption depends on both semantic usefulness and deterministic operator trust.
- **Pure code**: plausible if current evals are already sufficient and the only missing work is centralizing the gate, surfacing verified runtime metadata, and reusing existing validation artifacts. This should be preferred if the runtime trust gap can be closed without adding a new model-facing step.
- **Repo constraints / ADRs**: ADR-002 requires honest preflight, warnings, and run-detail visibility rather than hidden backend magic. ADR-003 requires previz to remain distinct from final render and grounded in Scene Workspace review. AGENTS requires headless operation, schema-first cross-layer contracts, and avoiding further growth in already-large files.
- **Existing patterns to reuse**: Story 143's `PrevizPanel` / AI-previz artifact taxonomy, Story 140's `media_validation_v1` substrate and artifact-health overlay, Story 032's cost-tracking/provenance path, `configs/recipes/recipe-ai-previz-generation.yaml`, `docs/evals/registry.yaml`, and the existing `previz-usefulness` benchmark/report path.
- **Eval**: `previz-usefulness` already exists as the usefulness/adoption detector, and `runtime-media-validation` exists as the trust baseline. This story should either reuse them directly or add the narrowest sibling measurement needed for `ai_previz_video` rather than inventing a second broad benchmark program.

## Tasks

- [x] Measure the current AI-previz runtime baseline on a seeded project: generate the leading lane, record actual runtime cost/latency/provenance, and determine whether provider-reported or deterministic estimated cost should be the source of truth for adoption decisions.
- [x] Implement the narrowest typed trust path for `ai_previz_video`: reuse `media_validation_v1` directly if that fits cleanly, or add a focused ai-previz-specific adapter without duplicating the generated-video substrate.
- [x] Centralize AI-previz recommendation/default/blocker logic in a shared backend or helper seam so UI surfaces stop hard-coding `experimental` vs `default` status.
- [x] Update Scene Workspace `Previz` and AI-previz Artifact Detail to render verified cost, trust health, and recommendation state from shared data rather than static text.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; no agent tooling or project instruction files changed)
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (equivalent mismatch investigation completed via `runtime-media-validation` rerun; remaining comparator misses were reclassified ambiguous and non-runtime-blocking, and the registry was updated)
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

- **Owning class/module**: keep AI-previz generation under `render_adapter_v1`, but do not add more adoption/trust branching inside its 1532-line `main.py`. The better fit is a small focused recommendation helper/service plus narrow reuse of `media_validation_v1`, with `PrevizPanel` and `AiPrevizViewer` staying thin consumers.
- **Data contracts**: reuse or extend typed contracts in `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/animatic.py`, and `src/cine_forge/schemas/media_validation.py`. If adoption-state or verified-cost data crosses backend -> API -> UI boundaries, define the schema first instead of smuggling strings through UI copy.
- **File sizes**: `make check-size` confirms the main risk files are already large: `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1532), `src/cine_forge/api/artifact_manager.py` (528), `src/cine_forge/pipeline/graph.py` (722), `ui/src/pages/SceneWorkspacePage.tsx` (766), and `ui/src/pages/ArtifactDetail.tsx` (639). Reusable but smaller seams include `src/cine_forge/modules/qa/media_validation_v1/main.py` (222), `src/cine_forge/modules/qa/media_validation_v1/probe.py` (427), `src/cine_forge/modules/qa/media_validation_v1/semantic_review.py` (452), `src/cine_forge/ai/video.py` (411), `src/cine_forge/schemas/animatic.py` (160), `src/cine_forge/schemas/render.py` (200), `ui/src/components/PrevizPanel.tsx` (363), `ui/src/components/AiPrevizViewer.tsx` (234), `ui/src/components/AnimaticViewer.tsx` (254), `ui/src/components/PrevizReelViewer.tsx` (111), `ui/src/lib/artifact-meta.ts` (64), and `ui/src/lib/constants.ts` (194).
- **Decision context**: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Story 032, Story 140, and Story 143. No newer CineForge-local ADR governs the remaining AI-previz adoption/default decision, so this story is the right home for that choice.

## Files to Modify

- `configs/recipes/recipe-ai-previz-generation.yaml` — thread any validation or adoption-gate runtime params into the dedicated AI-previz path (`33`)
- `src/cine_forge/services/previz_adoption.py` — centralize recommendation/default/blocker logic so UI copy stops hard-coding policy (`new`)
- `src/cine_forge/modules/qa/media_validation_v1/main.py` — extend the existing runtime validation owner only if `ai_previz_video` can reuse it cleanly (`222`)
- `src/cine_forge/modules/qa/media_validation_v1/probe.py` — narrow deterministic probe changes only if ai-previz clips need them (`427`)
- `src/cine_forge/modules/qa/media_validation_v1/semantic_review.py` — ai-previz-specific semantic-review shaping only if reuse is insufficient (`452`)
- `src/cine_forge/ai/video.py` — surface verified provider cost/latency/provenance if the current video client still leaves AI-previz cost unresolved (`411`)
- `src/cine_forge/schemas/render.py` — typed adoption/provenance additions if needed (`200`)
- `src/cine_forge/schemas/animatic.py` — typed previz-mode metadata if recommendation/health state belongs here (`160`)
- `src/cine_forge/api/artifact_manager.py` — synthesize AI-previz trust/recommendation details for artifact browsing surfaces (`528`)
- `src/cine_forge/pipeline/graph.py` — only if AI-previz validation or readiness status needs explicit graph wiring (`722`)
- `ui/src/components/PrevizPanel.tsx` — render shared recommendation/default/blocker and verified cost state instead of static experimental copy (`363`)
- `ui/src/components/AiPrevizViewer.tsx` — expose AI-previz trust and verified-cost detail in Artifact Detail (`234`)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin wiring only; do not grow the 766-line page (`766`)
- `ui/src/pages/ArtifactDetail.tsx` — thin wiring only; do not grow the 639-line page (`639`)
- `ui/src/lib/artifact-meta.ts` — label any new trust artifact surfaced to the operator (`64`)
- `ui/src/lib/constants.ts` — shared run/recommendation copy only if the centralized gate needs it (`194`)
- `benchmarks/tasks/previz-usefulness.yaml` — rerun or tighten the adoption gate only if the candidate/rubric changes materially (`129`)
- `benchmarks/scripts/runtime_media_validation_eval.py` — extend or clone only if `ai_previz_video` needs its own runtime fixture path (`332`)
- `benchmarks/scripts/previz_usefulness_report.py` — surface adoption-gate inputs clearly if report output changes (`401`)

## Redundancy / Removal Targets

- Hard-coded `AI lane: experimental` / deterministic-default copy in `ui/src/components/PrevizPanel.tsx`
- Any static `cost unverified` string that survives without a measured blocker or deterministic estimate path behind it
- Split adoption logic spread across benchmark reports, engine-pack defaults, and UI labels instead of one shared gate
- Any AI-previz trust caveats in the UI that become redundant once artifact-backed validation / health is surfaced directly

## Notes

- This story exists to move toward the Ideal, not to entrench a workaround. If the simplest honest implementation is “keep AI previz experimental because the measured gate still fails,” that is a valid outcome. What is not valid is leaving the product in a half-static state where recommendation/default copy drifts away from current evidence.
- Existing eval evidence already says the lane is close, not ready by assumption: `previz-usefulness` shows `Veo 3.1 Lite Previz` ahead on usefulness but still inside the default-switch guardrail and with unresolved cost verification on the latest validated reruns.
- Existing trust substrate is asymmetric today: Story 140 gives `generated_video` a real runtime validation artifact, while AI previz currently relies more on story-era disclosure than on the same artifact-backed trust path.
- If build-story finds that the current provider response cannot yield reliable AI-previz cost verification, the smallest coherent fallback is a deterministic duration/resolution-based estimate anchored to documented provider pricing, not more manual UI copy.

## Plan

### Baseline / Eval Gate

- Existing measured evidence is already enough to drive the first product decision; this story is mostly plumbing and policy, not a new benchmark program.
- Current adoption baseline from `docs/evals/registry.yaml`:
  - `previz-usefulness` (`2026-04-03`, git `d6ac336`): `Veo 3.1 Lite Previz` scores `0.828` overall vs `Annotated Animatic` at `0.803`, with `39273 ms` generation latency and `cost_usd: null`. The registry note explicitly says the lane remains on hold because Lite cost is still unverified and the lead over annotated stays inside the `0.03` default-switch guardrail.
  - `runtime-media-validation` (`2026-03-20`, git `28dac8f`): `Hybrid (GPT-5.4)` scores `1.0` overall on the pilot pack, which is already the repo-fit trust substrate for generated scene video.
- Repo-fit conclusion:
  - No new broad eval is needed before implementation because the quality/default detector already exists and the trust detector already exists.
  - The missing work is to reuse those signals in the product and to stop hard-coding stale UI copy.
  - If implementation changes either detector materially, rerun the narrow affected eval only and update `docs/evals/registry.yaml`.

### Repo-Fit / Why This Approach

- The current repo already has the right substrate:
  - `ai_previz_video` reuses the same `GeneratedVideoArtifact` contract as `generated_video`.
  - `media_validation_v1` already validates `GeneratedVideoArtifact` payloads headlessly and persists typed `media_validation` artifacts.
  - `artifact_manager.py` already overlays validation verdicts onto `generated_video`; the current trust gap exists because that overlay is artificially limited to one artifact type.
  - Story 143 already proved the product problem is a stale adoption/default surface, not missing generation capability.
- Chosen approach:
  - Reuse `media_validation_v1` for `ai_previz_video` through recipe wiring plus a small target-artifact-type parameter, rather than duplicating a second validation module.
  - Add one focused backend adoption service that reads the current recipe + engine pack + eval registry and emits a typed AI-previz status object for the UI.
  - Keep `PrevizPanel`, `AiPrevizViewer`, and `ArtifactDetail.tsx` thin consumers over that shared status and existing health artifacts.
- Rejected alternatives:
  - More logic inside `render_adapter_v1/main.py`: wrong ownership, already oversized, and the adoption gap is not generation logic.
  - Pure UI constants or report-file parsing in React: violates schema-first cross-layer contracts and repeats the current drift problem.
  - A second ai-previz-only validation artifact type: unnecessary because `MediaValidationArtifact` already models the trust signal we need.

### Structural Health Check

- `make check-size` was already run while drafting the story. Current likely touch points:
  - `src/cine_forge/api/artifact_manager.py` — `528` lines, oversized; keep changes surgical.
  - `src/cine_forge/modules/qa/media_validation_v1/main.py` — `222` lines.
  - `src/cine_forge/schemas/render.py` — `200` lines.
  - `src/cine_forge/schemas/__init__.py` — `413` lines.
  - `src/cine_forge/api/app.py` — `724` lines, oversized; router include only.
  - `configs/recipes/recipe-ai-previz-generation.yaml` — `33` lines.
  - `ui/src/components/PrevizPanel.tsx` — `363` lines.
  - `ui/src/components/AiPrevizViewer.tsx` — `234` lines.
  - `ui/src/pages/ArtifactDetail.tsx` — `639` lines, oversized; keep to prop wiring only.
  - `ui/src/lib/types.ts` — `608` lines, oversized; add only the new endpoint type.
  - `ui/src/lib/api/artifacts.ts` — `84` lines.
  - `ui/src/lib/hooks/artifacts.ts` — `198` lines.
- Method-size risk:
  - `media_validation_v1.run_module` is the main touched function. The plan is a narrow parameterization, not another branch-heavy feature. If the diff starts pushing more ownership into it, stop and extract helper logic first.
- Schema-first requirement:
  - The new adoption payload crossing backend -> API -> UI must be defined as a Pydantic schema before route or React wiring.
  - No new event type is planned.

### Scope Refinement

- Small coupled scope expansion folded into this story:
  - Add a focused API route for previz adoption status instead of trying to smuggle policy through artifact-group responses. This is an `S` delta and keeps the existing artifact payloads honest.
- Small scope reduction discovered during exploration:
  - Do not touch `src/cine_forge/ai/video.py`, `src/cine_forge/pipeline/graph.py`, or the benchmark scripts unless verification later proves the current cost-blocker reasoning is wrong. The first coherent slice does not need them.

### Task Plan

#### Task 1 — Add a typed previz adoption service

- Files:
  - `src/cine_forge/schemas/render.py`
  - `src/cine_forge/schemas/__init__.py`
  - `src/cine_forge/services/previz_adoption.py`
  - `src/cine_forge/services/__init__.py`
  - `src/cine_forge/api/routers/previz.py`
  - `src/cine_forge/api/app.py`
- Change:
  - Define a typed `PrevizAdoptionStatus` / lane-status contract in the schema layer.
  - Build a focused backend service that reads:
    - `configs/recipes/recipe-ai-previz-generation.yaml`
    - the selected engine-pack config
    - `docs/evals/registry.yaml`
  - Compute:
    - current default lane
    - AI-previz state (`default`, `recommended_optional`, or `experimental_manual`)
    - explicit blocker reasons
    - current tested config (pack/model/resolution/duration/consistency)
    - latency evidence from the active eval entry
    - cost evidence as `verified`, `estimated`, or `blocked`
  - Expose it through a small API router.
- Could break:
  - nothing in the artifact store directly; the main risk is bad registry/recipe parsing.
- Done looks like:
  - one backend source of truth decides whether AI previz is default, optional, or experimental, and why.

#### Task 2 — Reuse media validation for `ai_previz_video`

- Files:
  - `configs/recipes/recipe-ai-previz-generation.yaml`
  - `src/cine_forge/modules/qa/media_validation_v1/main.py`
  - `src/cine_forge/modules/qa/media_validation_v1/module.yaml`
  - `src/cine_forge/api/artifact_manager.py`
- Change:
  - Add a `validate_media` stage to the AI-previz recipe by mapping the module input key `generated_video` to stored artifact type `ai_previz_video`.
  - Parameterize `media_validation_v1` with a narrow `target_artifact_type` override so the persisted `MediaValidationArtifact.target_ref` points to `ai_previz_video` when used on the previz lane.
  - Extend `artifact_manager.py` validation overlay from only `generated_video` to both `generated_video` and `ai_previz_video`, still preserving higher-precedence graph states.
- Could break:
  - render validation if the target-artifact-type default changes incorrectly
  - validation lookup when both render and AI-previz validations exist for the same scene
- Done looks like:
  - a fresh AI-previz run lands a `media_validation` artifact headlessly and the Scene Workspace / Artifact Detail health badge can resolve it correctly for `ai_previz_video`.

#### Task 3 — Switch previz UI surfaces to the shared policy and trust path

- Files:
  - `ui/src/lib/types.ts`
  - `ui/src/lib/api.ts`
  - `ui/src/lib/api/artifacts.ts`
  - `ui/src/lib/hooks.ts`
  - `ui/src/lib/hooks/artifacts.ts`
  - `ui/src/components/PrevizPanel.tsx`
  - `ui/src/components/AiPrevizViewer.tsx`
  - `ui/src/pages/ArtifactDetail.tsx`
- Change:
  - Add a typed frontend query for the new previz-adoption endpoint.
  - Replace hard-coded `Default: Annotated Animatic`, `AI lane: experimental`, `Best quality candidate: Veo Lite`, and generic `Cost unverified` copy with shared backend status.
  - On the Scene Workspace previz surface:
    - show the current default lane honestly
    - show the AI-previz adoption state and blocker reasons
    - show measured latency and cost status from shared data
    - show `MediaValidationViewer` compactly when `ai_previz_video` has a validation artifact, matching the render panel pattern
  - On the AI-previz artifact detail viewer:
    - show the same adoption/default state and cost blocker or estimate from shared data instead of a static `Experimental lane` badge.
  - Keep `ArtifactDetail.tsx` changes thin by only passing the existing props needed for the dedicated viewer.
- Could break:
  - React type contracts and route rendering if the new query shape drifts
  - AI-previz detail if the viewer assumes the new status is always present
- Done looks like:
  - both Scene Workspace and AI-previz Artifact Detail read the same backend policy instead of local strings.

#### Task 4 — Verification, docs, and cleanup

- Checks:
  - Focused backend tests for the new service, media-validation target override, and artifact-manager overlay
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Browser verification plan:
  - Start backend + UI locally.
  - Exercise `/{projectId}/scenes/{sceneId}` -> `Previz`.
  - Verify the AI lane shows shared adoption state, measured latency/cost blocker, and validation detail when present.
  - Exercise `/{projectId}/artifacts/ai_previz_video/{sceneId}/{version}`.
  - Confirm the page header health badge plus viewer-level adoption state render cleanly with no console errors.
- Docs / redundancy:
  - Update the story work log and any touched docs.
  - Remove the remaining hard-coded AI-previz policy strings from the UI instead of leaving dead fallback copy behind.

### Human Gate / Implementation Note

- The plan is now concrete and the required scope expansion is only the small new previz-status API route. Because the user already explicitly said to go ahead with the recommended action and then to continue, implementation can proceed on that approval without another stop.

## Work Log

20260403-2315 — story-created: captured the missing follow-on to Story 143 after `/triage` identified AI-previz adoption/trust as the highest-leverage live climb gap with no real backlog home. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-002, ADR-003, Story 032, Story 140, Story 143, `make check-size`, `docs/evals/registry.yaml`, `configs/recipes/recipe-ai-previz-generation.yaml`, and the current `PrevizPanel` / AI-previz artifact surfaces. Next step: `/build-story 144`.
20260404-0002 — exploration: traced the current AI-previz gap to three concrete seams instead of a broad render refactor. Evidence: `ui/src/components/PrevizPanel.tsx` and `ui/src/components/AiPrevizViewer.tsx` hard-code adoption and cost copy; `src/cine_forge/api/artifact_manager.py` already overlays `media_validation` health but only for `generated_video`; `src/cine_forge/modules/qa/media_validation_v1/main.py` already validates `GeneratedVideoArtifact` payloads headlessly and only needs a narrow target-artifact-type override to cover `ai_previz_video`; `docs/evals/registry.yaml` already contains the active adoption detector (`previz-usefulness`: Lite `0.828` vs Annotated `0.803`, cost unresolved) and trust detector (`runtime-media-validation`: hybrid `1.0`). Scope adjustment folded in: add one small previz-status API route so Scene Workspace and Artifact Detail can consume a shared policy object instead of trying to infer it from artifact lists. Scope reduction: no first-slice changes needed in `render_adapter_v1/main.py`, `src/cine_forge/ai/video.py`, `src/cine_forge/pipeline/graph.py`, or the benchmark scripts. Next step: implement the backend adoption service, AI-previz validation recipe wiring, and artifact overlay reuse.
20260404-0010 — implementation-started: promoted Story 144 to `In Progress` and started with the backend ownership slice so the recipe/artifact trust path and shared adoption status exist before UI rewiring. First implementation targets: `PrevizAdoptionStatus` schema + service, AI-previz recipe validation stage, `media_validation_v1` target-artifact-type override, and `artifact_manager.py` validation overlay reuse. Next step: land the backend contract and regression tests, then switch the React surfaces to consume it.
20260404-0138 — implementation: landed the whole shared-policy + trust-path slice without expanding the oversized generation stack. Result: `src/cine_forge/services/previz_adoption.py` now emits a typed adoption/default/blocker status from the current recipe, engine-pack metadata, and `docs/evals/registry.yaml`; `src/cine_forge/api/routers/previz.py`, `src/cine_forge/api/app.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/__init__.py`, and `src/cine_forge/services/__init__.py` expose that contract cleanly to the UI; `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/modules/qa/media_validation_v1/main.py`, `src/cine_forge/modules/qa/media_validation_v1/module.yaml`, and `src/cine_forge/api/artifact_manager.py` now let `ai_previz_video` reuse `media_validation_v1` and receive the same artifact-backed health overlay as `generated_video`; `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/types.ts`, `ui/src/lib/api/artifacts.ts`, and `ui/src/lib/hooks/artifacts.ts` now consume the shared status instead of hard-coded `experimental` / `cost unverified` copy and surface `MediaValidationViewer` / validation links when present. Evidence: added focused regressions in `tests/unit/test_previz_adoption_service.py`, `tests/unit/test_media_validation_module.py`, and `tests/unit/test_artifact_manager_media_validation.py`; removed the stale local AI-previz constants from the React layer. Next step: run the full repo checks and live browser verification on a seeded AI-previz project.
20260404-0156 — verification: validated the story end to end with both headless checks and live browser proof. Evidence: focused pytest over the new backend seams passed (`10 passed`); `.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit` with the repo-safe override `PYTHON=.venv/bin/python` passed (`660 passed, 144 deselected, 1 existing unknown-mark warning`); `pnpm --dir ui run lint` passed with the repo's existing 5 fast-refresh warnings only; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed; local API smoke confirmed `/api/projects/story-144-ui-check/previz/adoption` returns `recommended_optional` plus explicit pricing and score-margin blockers while `/api/projects/story-144-ui-check/artifacts/ai_previz_video/scene_001/1` resolves `media_validation` health; browser verification used a seeded fixture cloned to `output/story-144-ui-check/`, generated a real `media_validation` artifact for `ai_previz_video`, opened `http://127.0.0.1:5174/story-144-ui-check/scenes/scene_001` -> `Previz`, then `http://127.0.0.1:5174/story-144-ui-check/artifacts/ai_previz_video/scene_001/1`, and confirmed the shared adoption state, blocker copy, and `Validation Detail` link render cleanly with zero console errors. Notes: the default `make test-unit` invocation still points at system `python3`, which lacks `pytest` in this environment, so the `.venv` override is still the correct repo command. Next step: hand off to `/validate` with Story 144 still `In Progress`.
20260404-0209 — validation: reran the full validation pass and found no closure-blocking implementation gaps. Fresh evidence: `make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected, 1 existing unknown-mark warning`); focused story pytest (`12 passed`); `.venv/bin/python -m ruff check src/ tests/`; `pnpm --dir ui run lint` (5 existing fast-refresh warnings only); `cd ui && npx tsc -b`; `pnpm --dir ui run build`; `PYTHONPATH=src .venv/bin/python benchmarks/scripts/runtime_media_validation_eval.py --model gpt-5.4 --output-prefix benchmarks/results/runtime-media-validation-story-144-validate` (Hybrid stayed `1.0` overall, comparator misses remained classified as ambiguous and non-runtime-blocking, and `docs/evals/registry.yaml` was updated to the new `2026-04-04` / `9598304` result); browser verification rechecked `http://127.0.0.1:5174/story-144-ui-check/scenes/scene_001` -> `Previz` and `http://127.0.0.1:5174/story-144-ui-check/artifacts/ai_previz_video/scene_001/1` with fresh screenshots and zero console errors. Next step: `/mark-story-done 144`.
20260404-0231 — done: closed Story 144 after validation confirmed the implementation and evidence trail were complete. Evidence: story checklist updated to reflect the conditional `skills-check` non-applicability, the runtime-media-validation mismatch investigation + registry refresh, and final closure; `docs/stories.md` moved Story 144 from the ready lane to `Done`; `CHANGELOG.md` now records the shipped adoption-gate/trust-guardrail slice. Next step: `/check-in-diff`.
