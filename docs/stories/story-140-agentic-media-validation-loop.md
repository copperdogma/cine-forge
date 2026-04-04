---
id: "140"
title: "Agentic Media Validation Loop"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness), R12 (radical transparency)"
spec_refs:
  - "spec:7"
  - "spec:8.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "027"
  - "028"
  - "030"
  - "127"
category_refs:
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 140 — Agentic Media Validation Loop

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness), R12 (radical transparency)
**Spec Refs**: spec:7 (Generation & Export), spec:8.2 (Quality Validation), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (goal-oriented navigation / preflight and run-detail visibility), ADR-003 (scene-workspace and origin-agnostic media inputs), `docs/design/principles.md` ("QA results are surfaced as health indicators")
**Depends On**: Story 027 (Animatics / Previz), Story 028 (Render Adapter), Story 030 (Generated Output QA), Story 127 (Artifact Health Semantics)

## Goal

Give CineForge a first-class validation loop for video-bearing outputs so agents and users can tell whether a generated clip is trustworthy without manually scrubbing every result or reading raw logs. The story should add a headless media-validation path for generated outputs, combine deterministic media probes with model-assisted semantic review where justified, persist typed validation artifacts with provenance, and surface the result through the existing Scene Workspace / Artifact Detail / health-badge flows.

## Acceptance Criteria

- [x] CineForge can run a headless validation pass against at least `generated_video` artifacts, producing a versioned validation artifact that records lineage to the validated media plus deterministic checks such as decode success, duration, stream presence, sample coverage, and other machine-verifiable media facts.
- [x] The validation pass supports a semantic review step that can use a configured multimodal model on sampled clip data or native-video input when available, and persists verdicts, cited evidence, confidence, and clear distinction between deterministic failures and model-judged concerns.
- [x] Validation results surface through existing user-facing trust channels: the relevant render/review UI shows health state plus a path to inspect the validation result, and actionable failures can land in chat/inbox rather than remaining buried in run logs.
- [x] The implementation keeps CLI/backend operation authoritative: the validation flow can run without the UI, and any UI affordance is a thin client over that same backend path.
- [x] Focused tests plus a measured baseline on real CineForge outputs distinguish the chosen approach from weaker alternatives; if model-facing validation prompts or judges are added/changed, `docs/evals/registry.yaml` is updated with the relevant runtime-validation eval entry or explicit follow-up.

## Out of Scope

- Automatic re-generation, self-healing, or prompt rewriting when validation fails
- Replacing Story 030's benchmark program or re-running the full video-understanding matrix unless the runtime path materially changes the judge/prompt surface
- Full human-equivalent artistic judgment of acting, taste, music, or editorial quality
- A broad project-wide media QA dashboard that tries to solve every artifact type at once
- Building an in-browser video-analysis engine or editor when the backend can own the truth

## Approach Evaluation

- **Simplification baseline**: first measure whether one frontier multimodal call on a real CineForge clip packet already produces trustworthy pass/fail guidance with cited defects. Story 030's `video-understanding` pilot reached `0.7923` for `GPT-5.4` on the 6-clip anchor subset, which is promising but still below the `0.80` pilot floor, and native-video provider paths are not yet the default benchmark path. Baseline measurement on real CineForge outputs is required before more scaffolding is added.
- **AI-only**: a single multimodal model judges the clip and emits defects, likely strongest for motion/audio semantics and weakest for exact structural facts. Simpler, but expensive and less trustworthy on deterministic checks.
- **Hybrid**: deterministic media probes own hard facts (decode, stream integrity, sample extraction, duration, waveform/clipping, simple continuity heuristics) while a model judges semantics such as motion readability, reveal clarity, lip-sync plausibility, or audio intent. Most plausible default because it matches CineForge's existing "structural + semantic" eval pattern.
- **Pure code**: valid only for structural checks and cheap heuristics. It cannot replace semantic judgment for directorial or motion-quality defects, so pure code is insufficient as the full answer.
- **Repo constraints / ADRs**: AGENTS requires headless operation. ADR-002 requires downstream trust surfaces to show diagnostics/preflight visibly, not hide them in logs. ADR-003 requires the solution to stay scene-workspace aware and origin-agnostic. Avoid bloating `render_adapter_v1/main.py` (1318), `SceneWorkspacePage.tsx` (758), or `ArtifactDetail.tsx` (630); use focused new modules/components instead.
- **Existing patterns to reuse**: `src/cine_forge/schemas/video_analysis.py`, Story 030's benchmark fixtures/prompts/scoring shape, `generated_video` and `animatic`/`previz_reel` artifact schemas, Story 127's artifact-health semantics, `ui/src/components/GeneratedVideoPanel.tsx`, and the existing chat/inbox notification patterns documented in `docs/design/decisions.md`.
- **Eval**: compare AI-only, hybrid, and deterministic-only validation on a fixed set of real CineForge outputs with seeded known defects or known-good clips. If the runtime semantic-review prompt materially diverges from Story 030's benchmark harness, add a dedicated runtime validation eval entry instead of pretending the benchmark already covers it.

## Tasks

- [x] Measure the simplification baseline on a small fixed set of real CineForge outputs: test whether a single frontier multimodal call on clip packets or native-video input already provides useful validation without additional orchestration. Evidence: `benchmarks/scripts/runtime_media_validation_eval.py`, `benchmarks/fixtures/runtime_media_validation_cases.json`, and `benchmarks/results/runtime-media-validation-gpt54-2026-03-20.{json,md}` now compare deterministic-only, AI-only, and hybrid validation on a fixed `generated_video` pilot pack, and `docs/evals/registry.yaml` records the baseline.
- [x] Define the runtime validation contract schema-first before wiring code across layers. Reuse shared video-analysis primitives only where they fit cleanly; if benchmark-specific models leak promptfoo assumptions, create a focused runtime `media_validation` schema/artifact instead of overloading benchmark types.
- [x] Keep the first implementation slice scoped to `generated_video` only. If exploration during implementation shows that `animatic` or `previz_reel` can reuse the exact same substrate with no material blast radius, record that as follow-up instead of silently expanding this story.
- [x] Implement a headless validation service/module for `generated_video` and chain it into `recipe-render-generation.yaml` as a downstream stage so the main render path lands validated output by default.
- [x] Persist validation artifacts with lineage, deterministic probe outputs, semantic findings, and enough provenance to explain which validator/model/config produced the result.
- [x] Overlay generated-video health from the latest matching validation artifact in the artifact browsing layer, while preserving higher-precedence graph health states (`stale`, impact-assessment results, and manual overrides).
- [x] Surface validation state in the existing review UX with a focused component path rather than growing oversized pages: at minimum cover the render/review entry point plus Artifact Detail inspection.
- [x] Gate impact-assessment-only UI controls by health `source_kind` so media-validation failures do not show structural-impact actions.
- [x] Add actionable notification wiring for failures that need user attention, using existing chat/inbox patterns instead of inventing a second alert system.
- [x] Add focused regression coverage for deterministic probes, artifact persistence, and the chosen UI summary path. Use representative fixture clips rather than synthetic dict-only tests wherever possible.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; no such files changed)
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (equivalent custom-harness investigation completed for the new runtime-media-validation eval. Result: hybrid cleared the 4-case pilot; deterministic-only and AI-only misses are approach-limited, not golden drift.)
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

- **Owning class/module**: a new focused backend owner should handle validation orchestration, either `src/cine_forge/modules/qa/media_validation_v1/` or a similarly scoped service/module. `render_adapter_v1` and the animatic pipeline should emit/consume refs but should not absorb the validation logic.
- **Data contracts**: validation crosses module -> artifact store -> API -> UI boundaries, so it needs a typed schema first. Existing benchmark types in `src/cine_forge/schemas/video_analysis.py` are useful reference material, but runtime validation likely needs a sibling artifact contract rather than promptfoo-shaped reuse by default.
- **Health ownership**: validation evidence should be exposed through the existing health-badge path, but it should not mutate the dependency graph as if it were structural invalidation. The better repo fit is to let the runtime validation artifact remain the source of truth and synthesize `source_kind=media_validation` health for `generated_video` in the artifact browsing layer, with graph-driven stale/impact/manual states taking precedence.
- **File sizes**: current likely touch points include `src/cine_forge/schemas/render.py` (165), `src/cine_forge/schemas/video_analysis.py` (221), `src/cine_forge/schemas/__init__.py` (376), `src/cine_forge/driver/schema_registry.py` (120), `src/cine_forge/api/artifact_manager.py` (448), `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1318, oversized), `ui/src/components/GeneratedVideoPanel.tsx` (263), `ui/src/components/ImpactAssessmentCard.tsx` (481), `ui/src/pages/ArtifactDetail.tsx` (630, oversized), `ui/src/pages/SceneWorkspacePage.tsx` (758, oversized), and `docs/evals/registry.yaml` (1610, large but expected). `build-story` should avoid adding logic to the oversized render and scene pages when a new focused component or module will do.
- **Decision context**: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-002, ADR-003, `docs/design/principles.md`, Story 030, Story 127, Story 137, and the current generated-video / animatic UI surfaces. No ADR currently settles the runtime media-validation implementation, so the story must stay aligned with the existing transparency and scene-workspace decisions instead of inventing a parallel review model.

## Files to Modify

- `src/cine_forge/schemas/media_validation.py` — new runtime validation artifact contract and summary models (new)
- `src/cine_forge/schemas/__init__.py` — export the new runtime validation models through the shared schema surface (376)
- `src/cine_forge/schemas/video_analysis.py` — reuse or extract shared primitives only if they help without coupling runtime artifacts to promptfoo-specific fields (221)
- `src/cine_forge/driver/schema_registry.py` — register the new runtime validation artifact type (120)
- `src/cine_forge/modules/qa/media_validation_v1/` — new headless validation orchestration path and deterministic probe helpers (`module.yaml`, `main.py`, optional `support.py`) (new)
- `configs/recipes/recipe-render-generation.yaml` — append the downstream validation stage instead of expanding `render_adapter_v1` itself (25)
- `src/cine_forge/api/artifact_manager.py` — synthesize validation-backed health details for `generated_video` without bypassing graph precedence (448)
- `ui/src/components/MediaValidationViewer.tsx` — new focused summary/detail renderer for review surfaces (new)
- `ui/src/components/GeneratedVideoPanel.tsx` — surface validation summary and deep-link for generated video review (263)
- `ui/src/components/ImpactAssessmentCard.tsx` — ignore `source_kind=media_validation` so validation failures do not show impact-assessment controls (481)
- `ui/src/pages/ArtifactDetail.tsx` — render the dedicated validation viewer via a thin new artifact-type branch (630)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only for surfacing the validation group into `GeneratedVideoPanel`; avoid growing the oversized page directly (758)
- `ui/src/lib/artifact-meta.ts` — add display metadata for the new `media_validation` artifact type (61)
- `ui/src/lib/constants.ts` — add a human-readable artifact label for run summaries/notifications if the new artifact type surfaces there (181)
- `docs/evals/registry.yaml` — add or update runtime validation eval tracking if model-facing validation logic changes or is added (1610)
- `tests/unit/` and `tests/integration/` — focused media-validation coverage using checked-in clip fixtures and artifact persistence paths (new or narrow additions)

## Redundancy / Removal Targets

- Any ad hoc "guess from logs / framegrabs" review guidance that remains the only runtime validation path once a real validation artifact exists
- Any duplicate UI-only validation state that bypasses the shared artifact-health semantics
- Any one-off runtime frame-sampling helpers duplicated from Story 030 if the runtime and benchmark paths can safely share them

## Notes

This story exists because no current story owns runtime inspection of generated media. Story 030 gives benchmark evidence, but not the product surface. Story 137 already notes that richer previz work needs better validation substrate. Exploration confirmed that `generated_video` is the only coherent first slice that closes the current trust gap without turning this into a broader media-review rewrite; animatic/previz expansion should be captured as follow-up after the shared validation substrate lands.

## Plan

### Repo-Fit Decision

- **Chosen approach**: a **hybrid** downstream validation stage: deterministic probes own machine-verifiable media facts, while an optional multimodal semantic review evaluates motion/audio/readability concerns. The validator emits its own immutable `media_validation` artifact, and the artifact browsing layer overlays that result onto `generated_video` health when graph health is otherwise clear.
- **Why this is the best fit here**:
  - `docs/ideal.md` and `spec:7`/`spec:10.3` require generated media to stay playable and inspectable, not just present.
  - ADR-002 requires visible downstream diagnostics; a stored validation artifact plus health overlay satisfies that better than buried run logs.
  - ADR-003 requires the review surface to stay scene-workspace aware and origin-agnostic; a validation artifact linked to the exact `generated_video` ref preserves that.
  - The repo already has generation transport (`src/cine_forge/ai/video.py`), render schemas (`src/cine_forge/schemas/render.py`), and render UI review surfaces, but `rg -n "media_validation|runtime-media-validation|validate_media" src/cine_forge configs tests ui/src docs/evals/registry.yaml` returned no hits, so the runtime validation product surface is currently zero.
  - `make check-size` confirmed that `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1318), `ui/src/pages/SceneWorkspacePage.tsx` (758), and `ui/src/pages/ArtifactDetail.tsx` (630) are already oversized. A downstream module plus focused viewer component is safer than packing more logic into those files.
- **Alternatives rejected**:
  - **AI-only**: too weak on deterministic facts like decode success, stream presence, and sample extraction. Story 030's best current semantic prior (`GPT-5.4` at `0.7923` on the 2026-03-19 anchor subset) is promising, but still below the `0.80` pilot floor and does not remove the need for hard media checks.
  - **Pure code**: covers structural facts only, but this story explicitly needs semantic review where justified.
  - **Embed validation inside `render_adapter_v1`**: wrong ownership and wrong file target. It would grow the largest file in the lane and make validation harder to reuse for later media-bearing artifacts.
  - **Use `video_analysis_*` benchmark schemas directly**: they are shaped around promptfoo clip-packet scoring, not runtime artifact lineage and operational provenance.
  - **Store validation state only in the dependency graph**: validation is runtime evidence, not upstream invalidation. Overloading the graph would blur Story 127 semantics and would surface the wrong UI affordances.

### Eval-First Baseline

1. **Baseline today**
   - Runtime validation product surface: `0`. The repo has no `media_validation` artifact, module, recipe stage, or runtime eval entry yet.
   - Best available semantic prior: Story 030's `video-understanding` rerun on 2026-03-19 shows `GPT-5.4` leading the frame-packet harness at `0.7923`, with corrected Gemini runs trailing (`Gemini 2.5 Flash` `0.6523`, `Gemini 3.1 Pro Preview` `0.6342`).
   - Live model discovery was refreshed on **2026-03-21 00:02 UTC** via `scripts/discover-models.py --summary`: `gpt-5.4` is still the newest SOTA OpenAI entry in the local catalog, `claude-sonnet-4-6` is the newest tested strong mid-tier entry, and the registry still shows multiple untested frontier candidates. That is enough to avoid stale model assumptions while this story chooses an initial runtime comparison.
2. **Eval to create/use**
   - Build an XS runtime-validation fixture pack from checked-in Story 030 clips wrapped behind `generated_video` artifact fixtures, plus at least one seeded broken case (missing file, corrupt decode, or missing audio stream). This keeps the comparison headless and reproducible without live provider generation.
   - Compare three paths on the same fixture set before hardening the implementation:
     - deterministic-only probe output
     - AI-only semantic review on sampled clip packets
     - hybrid probe + semantic review
3. **Success measure**
   - The chosen runtime path must correctly separate hard failures from valid clips on the fixture set, produce operator-useful reasons, and prove that the hybrid path is meaningfully better here than either pure code or AI-only.
   - If the runtime semantic-review prompt materially diverges from Story 030's benchmark prompt, add a dedicated `runtime-media-validation` eval entry in `docs/evals/registry.yaml`; if that cannot be finished inside this story, record the explicit follow-up instead of pretending Story 030 already covers it.

### Implementation Order

1. **Schema-first validation contract**
   - Files: `src/cine_forge/schemas/media_validation.py`, `src/cine_forge/schemas/__init__.py`, `src/cine_forge/driver/schema_registry.py`
   - Define a runtime artifact that records:
     - the exact validated `target_ref`
     - validator provenance (`validator_id`, probe tool/model, sampling policy, config hash)
     - deterministic findings (decode success, stream presence, duration, extracted sample refs, warnings/errors)
     - semantic findings (verdict, cited evidence, confidence, model used, distinction between blocking failures and softer concerns)
     - a recommended health state for the target artifact (`valid`, `needs_review`, or `needs_revision`)
   - Keep benchmark-only constructs in `video_analysis.py` unless a primitive is obviously shared verbatim.
   - Done looks like: the new artifact validates through the shared schema registry and can cross module -> store -> API -> UI boundaries without ad hoc dict contracts.
2. **Headless validator module and recipe wiring**
   - Files: `src/cine_forge/modules/qa/media_validation_v1/`, `configs/recipes/recipe-render-generation.yaml`
   - Create a dedicated validation module that consumes `generated_video` artifacts from the store, runs deterministic probes with PATH-gated `ffprobe`/`ffmpeg`, optionally prepares sampled frames/audio summaries for a semantic review call, and emits one `media_validation` artifact per scene/video target.
   - Append a downstream `validate_media` stage to `recipe-render-generation.yaml` instead of modifying `render_adapter_v1/main.py`. This keeps the main UX on the existing render button while preserving a headless rerun path via `--start-from validate_media`.
   - Do **not** pull `animatic` or `previz_reel` into the first implementation slice. Record that extension as follow-up unless the exact same substrate lands with no extra blast radius.
   - Done looks like: a render-generation run produces validation artifacts automatically, and the validation stage can be invoked headlessly against existing stored outputs.
3. **Health overlay and trust-surface integration**
   - Files: `src/cine_forge/api/artifact_manager.py`, `ui/src/components/MediaValidationViewer.tsx`, `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/components/ImpactAssessmentCard.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/lib/artifact-meta.ts`, `ui/src/lib/constants.ts`
   - Extend the artifact browsing layer so `generated_video` reads synthesize `source_kind=media_validation` health from the latest validation artifact that matches the exact `generated_video` ref, while graph-driven stale/impact/manual states remain higher precedence.
   - Health mapping for the first slice:
     - deterministic failure or high-confidence semantic failure -> `needs_revision`
     - inconclusive semantic concern -> `needs_review`
     - clean validation -> keep `valid`, but attach reason/source artifact provenance so the operator can inspect the evidence
   - Add a dedicated validation viewer component and reuse it:
     - compact summary in `GeneratedVideoPanel`
     - full artifact rendering in `ArtifactDetail`
   - Gate `ImpactAssessmentCard` by `source_kind` so a validation-derived `needs_revision` state does not expose impact-assessment controls.
   - Done looks like: the render review surface shows validation status immediately, the operator can open the exact validation artifact, and failure states show up through the existing artifact-health/inbox path instead of hiding in logs.
4. **Verification, docs, and redundancy**
   - Files: `tests/unit/`, `tests/integration/`, `docs/evals/registry.yaml`, related docs touched by the new runtime path
   - Add focused tests for:
     - schema validation
     - deterministic probe helpers against checked-in clip fixtures
     - module artifact persistence and lineage
     - health overlay precedence
     - UI summary rendering / impact-card gating
   - Required checks after implementation:
     - `make test-unit PYTHON=.venv/bin/python`
     - `.venv/bin/python -m ruff check src/ tests/`
     - `pnpm --dir ui run lint`
     - `cd ui && npx tsc -b`
     - `pnpm --dir ui run build`
   - Browser verification plan:
     - start backend + UI
     - open the Scene Workspace render tab for a scene with a validated `generated_video`
     - confirm the validation summary, detail link, and console cleanliness
     - open the validation artifact detail page and confirm the full viewer renders
   - Redundancy pass:
     - do not leave new ad hoc validation state in the UI if the artifact/health path already carries it
     - do not duplicate Story 030 provider helpers wholesale into runtime code unless the shared seam is explicit and safe
   - Done looks like: checks pass, the runtime path works end-to-end, docs match the new behavior, and any remaining eval or wider-media follow-up is written down explicitly.

### Structural Health Check

- `make check-size` was run during planning.
- Oversized files in the direct blast radius:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — 1318
  - `ui/src/pages/SceneWorkspacePage.tsx` — 758
  - `ui/src/pages/ArtifactDetail.tsx` — 630
  - `ui/src/components/ImpactAssessmentCard.tsx` — 481
  - `src/cine_forge/api/artifact_manager.py` — 448
- Planning guardrails:
  - Put new orchestration in a new module directory, not `render_adapter_v1`.
  - Keep Scene Workspace and Artifact Detail changes to thin wiring + a new viewer component.
  - Keep new cross-layer data in a Pydantic schema file before any module/API/UI code consumes it.
  - No new event type is planned; existing artifact persistence and run failure messaging should remain sufficient for this slice.

### Scope Adjustment And Human Gate

- **Recommended scope adjustment**: keep Story 140 to `generated_video` only. Extending the same substrate to `animatic` or `previz_reel` is a valid follow-up, but not part of the first build unless it falls out with effectively zero extra write scope.
- **No new external package dependencies are planned.** The deterministic path should reuse the repo's accepted media-tool pattern (`ffmpeg` already required by animatic workflows; local environment also has `ffprobe`).
- **Implementation blocker to call out now**: if the user wants native-video provider uploads in the first slice rather than sampled clip packets plus deterministic probes, that is a scope expansion from `S` to `M` and should be approved explicitly before implementation starts.

## Work Log

20260320-1715 — triage: created from inbox item "Agentic video-validation loop". Existing homes checked: Story 030 covers benchmark evidence, Story 137 covers previz usefulness, and Story 130 covers export fidelity; none own runtime media inspection. Promoted directly to `Pending` because the first slice is concrete enough to build: schema-first validation artifacts, headless media checks, and review-surface integration for generated outputs. Next=`/build-story`.
20260320-1807 — exploration: traced the current render lane end-to-end and confirmed the repo already has provider transport (`src/cine_forge/ai/video.py`), render contracts (`src/cine_forge/schemas/render.py`), recipe wiring (`configs/recipes/recipe-render-generation.yaml`), and review surfaces (`ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`), but no runtime media-validation artifact, module, or eval surface (`rg -n "media_validation|runtime-media-validation|validate_media" src/cine_forge configs tests ui/src docs/evals/registry.yaml` returned no hits). Files that will change: new runtime schema/module + recipe stage + artifact-manager health overlay + focused viewer path. Files at risk of breaking: artifact browsing health summaries, render review UI, and impact-assessment controls if validation shares the same health states without `source_kind` gating. ADRs / design docs consulted: `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-002, ADR-003, and `docs/design/principles.md`. Patterns to follow: schema-first layer boundaries, headless recipe execution, artifact-health surfacing, and the repo's existing ffmpeg-based media tooling from `animatic_v1`. Surprises / risks: Story 140's original file list assumed a fresh render schema lane, but `GeneratedVideoArtifact` already lives in `src/cine_forge/schemas/render.py`; `render_adapter_v1/main.py` is already 1318 lines and should not absorb validation; `ArtifactDetail.tsx` (630) and `SceneWorkspacePage.tsx` (758) are already oversized; and `ImpactAssessmentCard.tsx` currently treats all `needs_revision` states as impact-assessment states, so media-validation health must be distinguished by `source_kind`. Next=write repo-fit implementation plan and keep the first slice to `generated_video` only.
20260320-1810 — planning: chose a hybrid downstream validator plus artifact-manager health overlay as the repo-fit approach. Evidence: Story 030 already gives the best current semantic prior (`GPT-5.4` at `0.7923` on the 2026-03-19 anchor subset), `scripts/discover-models.py --summary` refreshed the live model catalog on 2026-03-21 00:02 UTC, and `make check-size` confirmed the largest local risks are `render_adapter_v1/main.py` (1318), `SceneWorkspacePage.tsx` (758), and `ArtifactDetail.tsx` (630). Rejected alternatives: AI-only is too weak on hard media facts, pure code is too weak on semantics, direct `video_analysis_*` reuse would leak promptfoo assumptions into runtime contracts, and dependency-graph mutation would misuse structural health for runtime evidence. Planned first slice: new `media_validation` artifact + new `media_validation_v1` stage appended to `recipe-render-generation.yaml`, with `generated_video` health synthesized from the latest matching validation artifact and `ImpactAssessmentCard` gated away from `source_kind=media_validation`. Next=human approval on the plan before implementation.
20260320-1908 — implementation: landed the first runtime media-validation slice end to end. Evidence: added `src/cine_forge/schemas/media_validation.py` plus registry/export wiring so the contract crosses module -> store -> API -> UI cleanly; created `src/cine_forge/modules/qa/media_validation_v1/` with ffprobe/ffmpeg-backed deterministic probes, sampled-frame extraction, and optional multimodal semantic review model resolution; appended `validate_media` to `configs/recipes/recipe-render-generation.yaml`; marked `media_validation` artifacts read-only; overlaid generated-video health in `src/cine_forge/api/artifact_manager.py`; and added focused UI rendering via `ui/src/components/MediaValidationViewer.tsx`, `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/pages/ProjectInbox.tsx`, and `ui/src/components/ImpactAssessmentCard.tsx`. The first slice stayed intentionally scoped to `generated_video`; no animatic/previz expansion was absorbed. Next=run required checks plus browser verification.
20260320-1910 — verification: backend and UI checks passed after provisioning a local `.venv` and UI dependencies in this worktree. Evidence: targeted runtime-validation tests passed (`tests/unit/test_media_validation_schema.py`, `tests/unit/test_media_validation_module.py`, `tests/unit/test_artifact_manager_media_validation.py`, `tests/unit/test_schema_registry.py`, `tests/integration/test_render_adapter_integration.py`); `.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=.venv/bin/python` passed (`617 passed, 140 deselected, 1 existing warning`); `pnpm --dir ui run lint` exited clean with only pre-existing unrelated `react-refresh/only-export-components` warnings in shared UI files; `cd ui && npx tsc -b` passed; and `pnpm --dir ui run build` passed with an existing Vite chunk-size warning. Follow-up recorded in `docs/inbox.md`: create a dedicated runtime-media-validation eval/registry entry before hardening the semantic reviewer into a stricter default gate. Next=run browser smoke on a seeded project.
20260320-1911 — smoke: seeded `/tmp/cine-forge-story140-smoke/project` with a real fixture clip and persisted a `media_validation` artifact through the new module, then ran backend + UI locally for end-to-end verification. Evidence: `curl http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.03.20-06\"}`; Scene Workspace `/project/scenes/scene_001` -> `Render` showed `Needs Review`, a compact validation summary, and `Validation Detail`; `/project/artifacts/media_validation/scene_001/1` rendered the full viewer with deterministic status, sample thumbnails, and findings buckets; `/project/inbox` surfaced `scene_001 — Generated Video is needs review`, and its `View` action routed to the validation artifact; Playwright console reported `0` errors / `0` warnings; and a screenshot was captured at `/tmp/story-140-media-validation-detail.png`. The smoke pass also exposed bogus `20533d ago` inbox timestamps for items with no event time, so `ui/src/pages/ProjectInbox.tsx` now uses `health_details.updated_at` when available and falls back to `Recently` instead of lying. Redundancy outcome: validation state stays on the artifact/health path rather than adding a parallel alert model. Next=`/validate`.
20260320-1914 — polish: re-ran the UI validation suite after the inbox timestamp fix and re-verified the inbox surface. Evidence: `pnpm --dir ui run lint` still exits `0` with the same five pre-existing `react-refresh/only-export-components` warnings, `cd ui && npx tsc -b` passed again, and `pnpm --dir ui run build` passed again with the same existing Vite chunk-size warning. Browser confirmation: `/project/inbox` now shows `7m ago` for the validation-backed attention item (using `health_details.updated_at`) and `Recently` for review items that still have no reliable timestamp instead of the old epoch leak. Next=`/validate`.
20260320-1922 — validation: reran the full required suite and browser verification from scratch. Evidence: `make test-unit PYTHON=.venv/bin/python` passed again (`617 passed, 140 deselected, 1 existing warning`); `.venv/bin/python -m ruff check src/ tests/` passed; story-targeted pytest passed (`17 passed`); `pnpm --dir ui run lint` passed with the same five pre-existing `react-refresh/only-export-components` warnings; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed with the same existing Vite chunk-size warning; `curl http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.03.20-06\"}`; and browser re-verification confirmed `/project/scenes/scene_001` -> `Render`, `/project/artifacts/media_validation/scene_001/1`, and `/project/inbox` with a clean console plus screenshot `/tmp/story-140-validate-inbox-read.png`. Findings: `src/cine_forge/modules/qa/media_validation_v1/support.py` still false-fails clips when `ffprobe` is unavailable because the fallback path leaves `video_stream_present=False` and then emits `missing_video_stream`; the story's own simplification-baseline/eval requirement remains open (`docs/stories/story-140-agentic-media-validation-loop.md` still leaves the baseline task unchecked and `docs/evals/registry.yaml` still has no runtime validation entry); and Artifact Detail still shows the media-validation artifact's freshness health (`Current`) in the page chrome while the payload verdict can say `Needs Review`. Recommendation: keep the story open, fix the `ffprobe` fallback with regression coverage first, then either land the dedicated runtime-media-validation eval harness or explicitly rescope that remaining requirement before `/mark-story-done`.
20260320-2028 — remediation: fixed the two code issues from validation and uncovered one more semantic-review blocker while probing the live runtime path. Evidence: `src/cine_forge/modules/qa/media_validation_v1/support.py` now treats `ffprobe`-absent environments as degraded-but-usable by inferring `video_stream_present=True` from successful decode, skipping `missing_*_stream` findings unless stream metadata actually exists, and normalizing model severities like `high`, `blocking`, `medium`, and `minor` into the runtime schema's `error`/`warning` contract. `src/cine_forge/api/artifact_manager.py` now gives `media_validation` artifacts their own verdict-backed health payload instead of reusing freshness-only graph health, which fixes the Artifact Detail header and version-list badge inconsistency without UI-specific branching. Focused regression coverage added in `tests/unit/test_media_validation_module.py` and `tests/unit/test_artifact_manager_media_validation.py`; targeted suite passed (`19 passed`). Next=land the missing runtime eval harness and rerun the broader checks.
20260320-2039 — runtime-eval: landed the dedicated `runtime-media-validation` harness and recorded the first scored baseline. Evidence: added `benchmarks/fixtures/runtime_media_validation_cases.json` plus `benchmarks/scripts/runtime_media_validation_eval.py`; widened `tests/render_fixtures.py` so the harness can seed clip-aligned prompt context instead of the generic render-test prompt; ran `PYTHONPATH=src .venv/bin/python benchmarks/scripts/runtime_media_validation_eval.py --model gpt-5.4 --output-prefix benchmarks/results/runtime-media-validation-gpt54-2026-03-20`; and updated `docs/evals/registry.yaml` with the resulting pilot at git `28dac8f`. Outcome: `Hybrid (GPT-5.4)` scored `1.0` overall (`semantic_cases=1.0`, `structural_cases=1.0`, `2740 ms`, `$0.003688/case`), `Deterministic Only` scored `0.75`, and `AI-Only (GPT-5.4)` scored `0.5`. Mismatch classification: no hybrid mismatches on the 4-case pilot; deterministic-only's single miss on the prop-swap continuity clip is `ambiguous` and non-runtime-blocking because the comparator intentionally lacks semantic judgment; AI-only's misses on missing/corrupt media are `ambiguous` and non-runtime-blocking because no sample packet exists for structural failure states. Follow-up cleanup: removed the now-processed runtime-eval item from `docs/inbox.md` and updated `docs/stories.md` to reflect that Story 140 is back to needing `/validate`, not more open eval scaffolding. Next=rerun story-level checks and browser verification, then hand back for `/validate`.
20260320-2054 — verification: reran the full story-level checks after the remediation + eval-harness pass. Evidence: `make test-unit PYTHON=.venv/bin/python` passed (`620 passed, 140 deselected, 1 existing warning`); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/runtime_media_validation_eval.py` passed; the focused regression suite still passes (`19 passed`); `pnpm --dir ui run lint` passed with the same five pre-existing `react-refresh/only-export-components` warnings; `cd ui && npx tsc -b` passed; and `pnpm --dir ui run build` passed with the same existing Vite chunk-size warning. Browser smoke on `http://127.0.0.1:5175/project/artifacts/media_validation/scene_001/1` confirmed the Artifact Detail header badge and version-history badge now both show `Needs Review` for the seeded validation artifact instead of `Current`; console had `0` warnings / `0` errors; screenshot saved to `/tmp/story-140-media-validation-header.png`. Next=`/validate`.
20260320-2106 — validation: reran the required suite, browser smoke, and the dedicated runtime-media-validation harness for closure review. Evidence: `make test-unit PYTHON=.venv/bin/python` still passed (`620 passed, 140 deselected, 1 existing warning`); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/runtime_media_validation_eval.py` passed; the focused Story 140 pytest slice still passed (`19 passed`); UI lint, `tsc -b`, and build all passed with only the same pre-existing warnings; the runtime harness still measured `Hybrid (GPT-5.4)=1.0`, `Deterministic Only=0.75`, and `AI-Only=0.5`; and browser verification reconfirmed `/project/scenes/scene_001` -> `Render`, `/project/artifacts/media_validation/scene_001/1`, and `/project/inbox` with a clean console. Remaining finding: `src/cine_forge/modules/qa/media_validation_v1/support.py` has grown to 793 lines and still contains oversized methods (`run_deterministic_probe`, `_call_multimodal_reviewer`), which violates the repo's structural-health rules for touched files and leaves the validator substrate harder to extend safely. Recommendation: keep the story open, extract the deterministic probe and provider-call helpers into focused modules, then rerun `/validate`.
20260320-2144 — refactor: decomposed the oversized runtime-validator helper into focused backend modules and reran the story checks. Evidence: moved deterministic probing into `src/cine_forge/modules/qa/media_validation_v1/probe.py` (427 lines) and semantic-review transport/parsing into `src/cine_forge/modules/qa/media_validation_v1/semantic_review.py` (452 lines), shrinking `src/cine_forge/modules/qa/media_validation_v1/support.py` to shared utilities only (125 lines). Structural outcome: `run_deterministic_probe` and `_call_multimodal_reviewer` no longer live inside a 793-line catch-all file, and no function in the new modules exceeds the repo's 100-line method bar. Regression evidence: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/runtime_media_validation_eval.py` passed; the focused Story 140 pytest slice passed (`20 passed`); `make test-unit PYTHON=.venv/bin/python` passed (`620 passed, 140 deselected, 1 existing warning`); and the standard UI lint/`tsc -b`/build checks still passed with the same pre-existing warnings only. Next=`/validate`.
20260320-2208 — validation: reran the full required suite, the dedicated runtime-media-validation harness, and fresh browser smoke after the validator decomposition. Evidence: `make test-unit PYTHON=.venv/bin/python` passed again (`620 passed, 140 deselected, 1 existing warning`); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/runtime_media_validation_eval.py` passed; the focused Story 140 pytest slice passed (`20 passed`); `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed with only the same pre-existing warnings/chunk-size warning; `PYTHONPATH=src .venv/bin/python benchmarks/scripts/runtime_media_validation_eval.py --model gpt-5.4 --output-prefix benchmarks/results/runtime-media-validation-gpt54-2026-03-20` reproduced the same ranking with refreshed latency/cost metrics and `docs/evals/registry.yaml` was updated accordingly; and browser verification reconfirmed `/project/scenes/scene_001` -> `Render`, `/project/artifacts/media_validation/scene_001/1`, and `/project/inbox`, including inbox routing back to the validation artifact plus a clean console (`0` warnings / `0` errors). Outcome: no new findings; Story 140 is ready for `/mark-story-done`.
20260320-2222 — closure: marked Story 140 done after confirming all acceptance criteria and tasks are complete, workflow gates are satisfied, and the required close-out suite remains green (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/runtime_media_validation_eval.py`, targeted Story 140 pytest, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, runtime-media-validation harness rerun, and browser verification on the render/detail/inbox trust path). Alignment check: this work advances `docs/ideal.md` R7/R10/R11/R12 and the active `spec:7` climb lane in `docs/build-map.md` by making generated-video outputs inspectable and trustworthy through the existing artifact-health path instead of adding a parallel review system; it also supports `spec:8.2` and `spec:10.3` without changing their governing ADRs. Next step: `/check-in-diff`.
