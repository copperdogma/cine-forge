---
id: "143"
title: "AI-Generated Low-Fidelity Previz"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine), R8 (professional-grade motion assets), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)"
spec_refs:
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.3"
  - "spec:6.4"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "028"
  - "029"
  - "030"
  - "056"
  - "119"
  - "137"
  - "140"
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

# Story 143 — AI-Generated Low-Fidelity Previz

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade motion assets), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:6.4 (Keyframes), spec:7.1 (Render Adapter Layer), spec:7.2 (User Asset Injection), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / concern-group inputs)
**Depends On**: Story 137 (Previz Fidelity Upgrade), Story 028 (Render Adapter), Story 029 (User Asset Injection), Story 030 (Generated Output QA), Story 056 (Entity Design Studies), Story 119 (Visual Reference Propagation), Story 140 (Agentic Media Validation Loop)

## Goal

Story 137 proved that CineForge's current annotated deterministic previz is more useful than the then-current shared-video path. Story 143's substrate work then showed that current AI-video candidates can be materially better than that old shared-video lane, with Veo Lite currently strongest on usefulness. That is still not enough by itself: AI previz is an operator-facing capability, so CineForge needs a visible Scene Workspace / Artifact Detail path for it rather than benchmark folders and backend-only plumbing. This story now covers both sides of the problem: evaluate current cheap and fast AI-video candidates, define a consistent low-fidelity previz house style, and ship an explicit AI-previz review flow that stays clearly separate from final render. The benchmark should decide which lane is recommended or default, not whether the capability gets a UI at all.

## Acceptance Criteria

- [x] A documented eval compares Story 137's `annotated_symbolic` baseline against at least two current AI-video previz candidates on the same fixed scene set, using low-resolution defaults and a rubric that scores camera placement, blocking clarity, motion readability, pacing usefulness, scene/prop/location legibility, character distinctness, style consistency, and cost/latency.
- [x] One benchmarked candidate uses a current Google Veo 3.1 tier available as of 2026-04-03 rather than the repo's stale `veo-3.1-generate-preview` pack, and at least one non-Google fast lane already supported by the repo remains in the comparison so the story does not silently become vendor-locked.
- [x] The AI-previz contract now uses an explicit previz house style that is intentionally non-final: simplified, consistent, and blocking-first. The style contract makes clear how characters remain distinguishable, how locations and props stay readable enough for staging, what detail is intentionally suppressed, and whether consistency is achieved prompt-only or with optional reference inputs.
- [x] Benchmarked AI-previz generation uses the cheapest and lowest-resolution settings exposed by each candidate lane that still allow a fair usefulness comparison, and the measured blocker that prevented adoption is recorded when cost evidence or quality is insufficient.
- [x] Scene Workspace exposes previz as a single operator-facing surface instead of splitting it between deterministic animatics, benchmark scripts, and final-render UI. The surface presents deterministic and AI-previz lanes side by side, makes the current recommendation/default explicit, and lets the operator intentionally generate or refresh AI previz.
- [x] The Scene Workspace previz surface includes preflight and disclosure: candidate pack/model, resolution, estimated cost/latency or `cost unverified`, consistency strategy, intended use, and a clear non-final warning so users understand this is for camera/blocking/motion review rather than polish.
- [x] Artifact Detail exposes AI previz in a route/view distinct from final render, with links back to the deterministic baseline and any project-level previz reel or comparison affordance. No operator path should require browsing benchmark folders or raw artifact JSON.
- [x] User-facing provenance and artifact taxonomy remove stale `shared_video` language and stop conflating AI previz with `generated_video` final renders. If a dedicated artifact or recipe path is needed, it is implemented directly rather than hidden behind old naming.
- [x] AI previz remains advisory and optional: `annotated_symbolic` fallback stays available, final render remains separate, and benchmark results decide the default/recommended lane rather than whether the UI exists.
- [x] If no AI-video lane clears the default-adoption gate, CineForge still ships an explicit experimental/manual AI-previz path with warnings; `annotated_symbolic` remains the default until the gate is cleared.

## Out of Scope

- Photoreal or final-render-quality previz
- Training custom identity models, LoRAs, or other heavyweight consistency substrate
- Building a general-purpose 3D editor, DCC workflow, or virtual production toolchain inside CineForge
- Making AI previz mandatory before downstream render or export
- Treating AI previz as a disguised final render with extra polish or upscaling
- Solving full film-wide continuity or shot-to-shot identity perfection across arbitrarily long sequences
- Silent provider lock-in or assuming one vendor wins before measurement
- Benchmark-only or CLI-only AI previz access with no operator-facing UI path

## Approach Evaluation

- **Simplification baseline**: Story 137 already measured the then-current shared-video lane and it lost to `annotated_symbolic`, so the baseline is not hypothetical. The first question is whether current model inventory plus a deliberately low-detail house-style prompt changes that result enough to justify a recommendation/default change. If not, keep the deterministic default, but the current story still needs a visible AI-previz lane if AI previz remains an operator-facing capability.
- **AI-only**: Reuse the render adapter with a previz-specific prompt/compiler mode, short low-resolution clips, and current fast engine packs. Prompt-only house-style and character-description consistency is acceptable if it is measurably good enough for previz review. Pros: simplest path, best chance to feel like real motion instead of overlays. Cons: weak controllability, risk of pseudo-final imagery, and possible identity/style drift across shots.
- **Hybrid**: Compile a typed previz brief from shot plan, concern groups, keyframes, and optional design-study or injected references; then route that into selected engine packs with an explicit low-fidelity house style and provenance. Pros: strongest fit for controllability, transparency, and graceful model evolution as optional reference support improves. Cons: more orchestration work and more chances to bloat already-large render files if done carelessly.
- **Pure code**: `annotated_symbolic` remains the control arm and fallback. It is not the main answer to this story because the user-facing question is AI previz, but it is the benchmark every AI lane must beat.
- **Repo constraints / ADRs**: ADR-003 requires previz to stay grounded in Scene Workspace and concern-group artifacts, not isolated prompt hacking. ADR-002 requires visible diagnostics and preflight rather than backend magic. Story 137 already established the usefulness baseline. Story 028 owns the AI-video substrate. Current repo drift matters: local engine packs still point at `veo-3.1-generate-preview`, but Google's official docs updated on 2026-04-02 recommend `veo-3.1-generate-001` and `veo-3.1-fast-generate-001`, and introduced `veo-3.1-lite-generate-001`. Lite's lack of component/style reference images is therefore an eval consideration, not a product blocker by itself; it only matters if prompt-only consistency proves insufficient.
- **Existing patterns to reuse**: Story 137's `previz-usefulness` benchmark and `preview_provenance` surfaces; Story 028's render adapter and engine-pack structure; Story 029's injected assets; Story 056 and Story 119's design-study `visual_reference_image` propagation; Story 030 and Story 140's media-understanding and runtime validation substrate; the existing Scene Workspace / Artifact Detail review loop.
- **Eval**: extend the current previz-usefulness harness or add a tight sibling task so the same scenes compare `annotated_symbolic` against current AI lanes under low-cost, low-resolution defaults and explicit house-style prompts. The eval must classify significant misses as model-wrong, golden-wrong, or ambiguous, and record whether any remaining failures are runtime-blocking or non-runtime-blocking.

## Tasks

- [x] Research and document a repo-fit AI-previz visual language informed by current previs practice: camera, blocking, motion, and staging first; detail deliberately suppressed. Turn that into an explicit previz style profile or prompt-compiler contract rather than ad hoc prompt strings.
- [x] Refresh the video-engine candidate inventory before implementation: update Google Veo IDs/capabilities from retired preview IDs to current GA/preview surfaces, capture which tiers support prompt-only vs reference-assisted consistency, first/last frame, audio, and lowest output resolutions, and run `/discover-models` for any supporting compiler/judge model choices.
- [x] Extend the previz-usefulness eval so it compares Story 137's `annotated_symbolic` baseline against at least two current AI-video lanes under low-cost, low-resolution defaults and house-style prompts; record fresh results in `docs/evals/registry.yaml`.
- [x] Implement the schema-first substrate needed for AI previz regardless of the eventual default decision: previz-specific prompt compilation/inputs, engine-pack refresh, low-fidelity house-style provenance, benchmark harness, and recorded evidence.
- [x] Replace the current `Animatics`-only review surface with a repo-fit `Previz` surface or equivalent focused refactor that presents deterministic and AI-previz lanes side by side without bloating `SceneWorkspacePage.tsx`.
- [x] Add a dedicated AI-previz operator action and recipe path (`ai_previz_generation` or equivalent) so users can intentionally generate or refresh AI previz without going through final-render actions.
- [x] Add a dedicated AI-previz artifact/detail surface distinct from final render, with clear cross-links to the annotated animatic baseline and any previz reel/comparison affordance.
- [x] Refactor stale previz taxonomy and vocabulary (`shared_video`, misleading labels, any generated-video reuse that obscures intent) wherever user-facing or cross-layer contracts require it.
- [x] If no AI lane wins the default-adoption gate, keep AI previz as an explicit experimental/manual lane with warnings instead of hiding it or pretending it is final render.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` not needed; agent tooling was untouched
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
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

- **Owning class/module**: Actual AI generation stays under `src/cine_forge/modules/generation/render_adapter_v1/`, but the operator-facing surface belongs under previz, not render. The right UI shape is a refactored `Previz` surface in Scene Workspace backed by small components, with Scene Workspace and Artifact Detail remaining thin consumers. Do not move core logic into `animatic_v1/support.py`, and do not smuggle AI previz through `GeneratedVideoPanel` as if it were final render.
- **Data contracts**: Reuse and extend typed contracts such as `PreviewProvenance`, `CompiledRenderPrompt`, and animatic/previz schemas where clean, but prefer a direct dedicated AI-previz artifact + recipe path over overloading `generated_video` if that is what removes operator confusion. If the story needs `previz_style_profile`, `consistency_strategy`, `ai_previz_video`, or stronger intended-use metadata, define it schema-first before wiring module, API, or UI code.
- **File sizes**: `make check-size` currently flags the likely touch points: `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1374), `src/cine_forge/ai/video.py` (411), `src/cine_forge/pipeline/graph.py` (711), `src/cine_forge/api/artifact_manager.py` (528), `ui/src/pages/SceneWorkspacePage.tsx` (758), and `ui/src/pages/ArtifactDetail.tsx` (634). Smaller likely touch points are `src/cine_forge/schemas/track.py` (51), `src/cine_forge/schemas/render.py` (169), `src/cine_forge/schemas/animatic.py` (154), `ui/src/components/AnimaticsPanel.tsx` (251), `ui/src/components/GeneratedVideoPanel.tsx` (305), `ui/src/components/GeneratedVideoViewer.tsx` (182), `ui/src/components/AnimaticViewer.tsx` (254), `ui/src/lib/constants.ts` (182), and `ui/src/lib/artifact-meta.ts` (62). `/build-story` must bias toward new focused files/components instead of growing the oversized ones.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/build-map.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:7.1`, `spec:7.2`, `spec:10.3`), ADR-002, ADR-003, Story 137, Story 028, Story 029, Story 030, Story 119, Story 140, current render engine packs, and official Google Cloud docs/blog updates dated 2026-04-02 through 2026-04-03 covering Veo 3.1 Fast/Lite, capabilities, and pricing.

## Files to Modify

- `benchmarks/tasks/previz-usefulness.yaml` — extend candidate coverage and rubric for AI-previz house-style comparison
- `benchmarks/prompts/` — refine the judging prompt so it scores low-fidelity readability rather than raw cinematic impressiveness
- `benchmarks/scripts/generate_previz_usefulness_dataset.py` — update dataset generation if new AI-previz candidates or style-profile inputs need fresh fixtures
- `benchmarks/scripts/previz_usefulness_report.py` — surface cost/latency and style-consistency findings clearly
- `docs/evals/registry.yaml` — record fresh AI-previz benchmark results and mismatch classification
- `configs/recipes/recipe-ai-previz-generation.yaml` — dedicated run path for operator-triggered AI previz instead of piggybacking on final render
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/` — refresh Google Veo packs and add any missing current fast/lite candidate packs if justified
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — thin orchestration only; avoid adding more packed logic to the 1374-line file
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` or a new focused sibling helper — previz-specific house-style prompt compilation and intent shaping
- `src/cine_forge/ai/video.py` — provider request shaping if updated model IDs/features require it (411)
- `src/cine_forge/schemas/render.py` — provenance and consistency-strategy extensions if needed (169)
- `src/cine_forge/schemas/animatic.py` — shared previz-mode metadata and removal of stale `shared_video` vocabulary (154)
- `src/cine_forge/schemas/track.py` — if AI previz becomes a real track/artifact, reflect it directly in fallback ordering (51)
- `src/cine_forge/pipeline/graph.py` — register the new AI-previz generation path in the goal graph instead of treating it as render (711)
- `src/cine_forge/api/artifact_manager.py` — support any dedicated AI-previz artifact or validation lookup path cleanly (528)
- `ui/src/components/PrevizPanel.tsx` or equivalent focused replacement for `AnimaticsPanel.tsx` — host deterministic and AI-previz lanes without page bloat
- `ui/src/components/AiPrevizViewer.tsx` or equivalent focused viewer — distinct artifact detail surface for AI previz
- `ui/src/components/AnimaticViewer.tsx` — surface the comparison/fallback relationship between annotated and AI previz when relevant (254)
- `ui/src/components/PrevizReelViewer.tsx` — clarify project-level previz mode and review intent when AI clips exist (111)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only; do not grow the 758-line page
- `ui/src/pages/ArtifactDetail.tsx` — thin routing only; do not grow the 634-line page
- `ui/src/lib/constants.ts` — add run labels and messages for the dedicated AI-previz recipe (182)
- `ui/src/lib/artifact-meta.ts` — give AI previz its own user-facing label/icon instead of reusing generated video (62)

## Redundancy / Removal Targets

- The stale `veo-3.1-generate-preview` pack and any related docs/config if current GA packs supersede it
- Any prompt text or UI copy that implies AI previz is just a cheaper final render
- Any duplicated house-style strings or previz-mode labels spread across engine packs, UI, and benchmark prompts
- The old `AnimaticsPanel` framing if a broader `Previz` surface replaces it
- Any user-facing `shared_video` terminology or reuse of `render_generation` / `generated_video` that keeps AI previz visually coupled to final render

## Notes

- Traditional previs exists to plan and communicate shots, not to perfect surface detail. This story should treat generative video as a faster visualization substrate, not as an excuse to skip previs discipline.
- An operator-facing capability without an operator-facing UI is not complete in this repo. Benchmark outputs and raw artifact files are useful evidence, not a substitute for product access.
- Current Google docs materially changed after Story 137's benchmark. As of 2026-04-02, Google introduced `Veo 3.1 Lite`, positioned it as the most cost-effective tier, and documented `Veo 3.1`, `Fast`, and `Lite` as separate options. The same docs also say Lite does not support component/style reference images, while full and fast do. That makes Lite an explicit eval candidate, not something to reject or accept on capability assumptions alone.
- Current Google docs also say the preview IDs `veo-3.1-generate-preview` and `veo-3.1-fast-generate-preview` are deprecated as of 2026-04-02 in favor of GA IDs. The repo should not build further product logic on retired preview names.
- The right visual target is not an arbitrary branded style reference such as "South Park-style." That would confuse aesthetic imitation with previs purpose. The better target is a production-readable schematic house style: clear silhouette separation, deliberate simplification, stable color/blocking cues, restrained texture/detail, and labels only if identity cannot stay readable otherwise.
- Reference images should be treated as optional consistency accelerants, not a baseline requirement. If prompt-only character/style descriptions are consistent enough for previs review, that is a valid win. The architecture should keep optional reference slots available so future model upgrades can improve consistency without redefining the previz contract.
- Native audio is useful for pacing, but it should not dominate the winner selection. Camera, motion, blocking, and staging readability remain the primary bar.
- Current render substrate is scene-level by default. If the eval shows AI previz requires shot-level generation or assembly to stay controllable, that must be surfaced explicitly during `/build-story` instead of being absorbed silently.
- External references reviewed while drafting:
  - Google Cloud blog: "Introducing Veo 3.1 Lite and a new Veo upscaling capability on Vertex AI" (2026-04-03)
  - Google Cloud docs: Veo 3.1 model page, last updated 2026-04-02
  - Google Cloud pricing page for Vertex AI generative video
  - Autodesk whitepaper on virtual moviemaking / previs as an iterative planning and communication surface

## Plan

### Baseline / Eval Gate

- Current baseline was re-run on the current branch before planning:
  - Command: `source ~/.nvm/nvm.sh && nvm use 24 >/dev/null 2>&1 && cd benchmarks && ../.venv/bin/python scripts/generate_previz_usefulness_dataset.py && PROMPTFOO_PYTHON=../.venv/bin/python promptfoo eval -c tasks/previz-usefulness.yaml --no-cache -j 1 --output results/previz-usefulness-build-story-2026-04-03.json`
  - Report: `benchmarks/results/previz-usefulness-build-story-2026-04-03-report.md`
  - Result: `annotated_symbolic` `0.808`, `shared_video` `0.603`, `symbolic` `0.658`
- Candidate-specific reruns completed later in the story and changed the quality picture:
  - `benchmarks/results/previz-usefulness-story-143-2026-04-03-report.md` ranked `Veo 3.1 Lite Previz` `0.9027`, `Annotated Animatic` `0.8130`, `Veo 3.1 Fast Previz` `0.8003`, `Symbolic Animatic` `0.6787`, `Sora 2 Previz` `0.6598`
  - `benchmarks/results/previz-usefulness-validation-story-143-2026-04-03-report.md` re-validated the same strategic result: `Veo 3.1 Lite Previz` `0.9303`, `Annotated Animatic` `0.8563`, `Veo 3.1 Fast Previz` `0.8230`, `Symbolic Animatic` `0.6863`, `Sora 2 Previz` `0.6340`
- Repo-fit conclusion now: Story 143 should still not default-switch blindly, but it also cannot close as benchmark-only substrate. The remaining gap is product access. The benchmark gate governs recommendation/default status and warning language, not whether AI previz exists in Scene Workspace and Artifact Detail.
- Live provider check completed during planning:
  - OpenAI API currently exposes `sora-2` and `sora-2-pro`
  - Google API currently exposes `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, and `veo-3.1-lite-generate-preview` as of 2026-04-03
- Recommended scope adjustment folded into the plan: reopen the story around operator-facing UI, direct artifact/recipe taxonomy, and stale naming cleanup. The candidate-specific benchmark work is already done; the remaining delta is the product surface. Relative effort: `M`.

### Repo-Fit / Why This Approach

- This repo already has the right substrate for a real operator-facing AI-previz path:
  - Story 137 supplies the deterministic control arm (`annotated_symbolic`) plus current `preview_provenance` UI surfaces.
  - Story 028 supplies render-adapter orchestration, engine-pack registry, and provider request shaping.
  - Story 029 / Story 056 / Story 119 already propagate optional reference imagery, so AI previz can stay reference-optional without inventing new asset plumbing.
  - Story 030 / Story 140 already provide media-understanding and validation substrate for judging generated clips.
  - ADR-002 requires visible preflight, warnings, and goal-aware navigation rather than hidden backend magic.
  - ADR-003 says previz belongs in Scene Workspace as part of a director-readable control surface, not as a disguised render mode.
- The chosen approach for this repo is hybrid and UI-first:
  - keep `annotated_symbolic` as the default control and fallback
  - reuse render-adapter generation for AI lanes
  - keep the candidate-specific benchmark as the recommendation/default detector
  - add a dedicated AI-previz product path so the operator can generate and inspect it in the same workspace as deterministic previz
- Why not hide AI previz under `Render`: that would violate the product semantics. Previz is a planning surface, final render is a delivery surface, and mixing them causes exactly the “obsess over details” failure mode the story is trying to avoid.
- Why not ship a debug-only or benchmark-only path: that would still fail the operator-access rule and would under-test the real user flow.
- Why not adopt Veo Lite by assumption: cost alone is not enough. Lite is attractive, but prompt-only identity/style consistency, motion readability, and blocking clarity still need to beat the annotated baseline under the same rubric.

### Recommended UI Shape

- Replace or refactor the current Scene Workspace `Animatics` tab into a broader `Previz` surface. `Animatic` becomes one lane inside previz, not the name of the whole surface.
- The `Previz` surface should have one shared explainer card at the top:
  - what previz is for: camera placement, blocking, motion, pacing
  - current recommendation/default lane
  - explicit note that final render lives in the separate `Render` tab
- The `Previz` surface should then show two peer lanes:
  - `Annotated Animatic`: current deterministic baseline, clearly labeled as the default until AI clears the adoption gate
  - `AI Previz`: explicit experimental/manual lane with candidate pack/model, resolution, consistency strategy, cost/latency or `cost unverified`, and a generate/refresh action
- The AI lane should include preflight and disclosure before generation, not after:
  - low-resolution / low-cost defaults
  - current recommendation vs experimental status
  - any unresolved blocker such as `cost unverified`
  - intended use badges such as `blocking-first` and `non-final`
- Artifact Detail should get a dedicated AI-previz viewer or route, not reuse final-render framing. The viewer should show:
  - prominent non-final warning
  - pack/model, resolution, cost/latency, and consistency strategy
  - link back to the annotated baseline for the same scene
  - link to the project-level previz reel if that reel incorporates AI previz
- Do not add a separate hidden “labs” page. The right place is the existing Scene Workspace, because that is where directors already review shot planning and previz.

### Structural Health Check

- `make check-size` was run during planning. Files likely to be touched and current size:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1374`
  - `src/cine_forge/ai/video.py` — `411`
  - `src/cine_forge/pipeline/graph.py` — `711`
  - `src/cine_forge/api/artifact_manager.py` — `528`
  - `ui/src/pages/SceneWorkspacePage.tsx` — `758`
  - `ui/src/pages/ArtifactDetail.tsx` — `634`
  - `ui/src/components/GeneratedVideoPanel.tsx` — `305`
  - `ui/src/components/GeneratedVideoViewer.tsx` — `182`
  - `ui/src/components/AnimaticsPanel.tsx` — `251`
  - `ui/src/components/AnimaticViewer.tsx` — `254`
  - `ui/src/components/PrevizReelViewer.tsx` — `111`
  - `ui/src/lib/constants.ts` — `182`
  - `ui/src/lib/artifact-meta.ts` — `62`
  - `src/cine_forge/schemas/render.py` — `169`
  - `src/cine_forge/schemas/animatic.py` — `154`
- Plan risk: `render_adapter_v1/main.py`, `pipeline/graph.py`, `artifact_manager.py`, `SceneWorkspacePage.tsx`, and `ArtifactDetail.tsx` are already oversized. New logic should land in focused helpers / schemas / smaller UI components first, with those large files used only as thin integration points.
- Schema-first requirement: if the story introduces `ai_previz_video`, stronger `consistency_strategy`, `previz_style_profile`, or new preview-mode distinctions across backend/API/UI, add them to schema files before wiring call sites.
- Event requirement: no new event type is planned right now. If implementation adds one, it must be added to `src/cine_forge/schemas/events.py` first.

### Task Plan

#### Task 1 — Lock the previz taxonomy and dedicated AI-previz path

- Files:
  - `src/cine_forge/schemas/animatic.py`
  - `src/cine_forge/schemas/render.py`
  - `src/cine_forge/schemas/track.py`
  - `src/cine_forge/pipeline/graph.py`
  - `src/cine_forge/api/artifact_manager.py`
  - `configs/recipes/recipe-ai-previz-generation.yaml`
  - `ui/src/lib/constants.ts`
  - `ui/src/lib/artifact-meta.ts`
- Change:
  - remove stale `shared_video` naming from user-facing previz taxonomy
  - introduce a dedicated AI-previz recipe/run identity instead of piggybacking on `render_generation`
  - if needed, introduce a dedicated AI-previz artifact type instead of overloading `generated_video`
  - register the new path in graph, artifact metadata, and any fallback ordering the product uses
- Could break:
  - artifact grouping and readiness calculations
  - run labels, chat activity labels, and artifact detail dispatch
- Done looks like:
  - operators can see AI previz as its own product concept instead of a mislabeled render
  - final render and previz no longer share misleading recipe or artifact names

#### Task 2 — Keep the substrate current and emit AI-previz artifacts through the new path

- Files:
  - `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/`
  - `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` or a new sibling helper under that module
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  - `src/cine_forge/ai/video.py`
  - unit tests under `tests/unit/`
- Change:
  - preserve the existing low-fidelity AI-previz compiler and candidate packs
  - emit artifacts and provenance through the new AI-previz path rather than leaving the capability benchmark-only
  - keep final-render prompt behavior unchanged
- Could break:
  - render-adapter tests that assume only final-render generation artifacts
  - provider request shaping or artifact payload contracts
- Done looks like:
  - the existing substrate remains valid
  - AI previz generation now materializes product-consumable artifacts, not just benchmark outputs

#### Task 3 — Refactor Scene Workspace from `Animatics` to `Previz`

- Files:
  - `ui/src/components/PrevizPanel.tsx` or equivalent focused replacement
  - `ui/src/components/AnimaticViewer.tsx`
  - `ui/src/components/PrevizReelViewer.tsx`
  - `ui/src/pages/SceneWorkspacePage.tsx`
- Change:
  - replace the current `Animatics`-only framing with a broader previz surface
  - show deterministic and AI-previz lanes as peers
  - keep the `Render` tab reserved for final render
  - add preflight/disclosure, recommendation/default copy, and explicit action buttons for the AI lane
- Could break:
  - scene workspace tab labels, run-state copy, and detail links
  - existing seeded browser-check routes and screenshots
- Done looks like:
  - Scene Workspace is honest about what previz modes exist and what each is for
  - AI previz is accessible without leaving the main creative loop

#### Task 4 — Add a dedicated AI-previz artifact detail surface

- Files:
  - `ui/src/components/AiPrevizViewer.tsx` or equivalent focused viewer
  - `ui/src/components/AnimaticViewer.tsx`
  - `ui/src/components/PrevizReelViewer.tsx`
  - `ui/src/pages/ArtifactDetail.tsx`
- Change:
  - route AI previz to its own detail viewer rather than final-render framing
  - show model/pack, resolution, cost/latency, intended use, consistency strategy, and a prominent non-final warning
  - add links back to the annotated baseline and any previz reel/comparison surface
- Could break:
  - existing artifact detail rendering assumptions
  - preview-mode labels in shared viewer components
- Done looks like:
  - operators can open an AI previz artifact and immediately understand that it is a planning asset, not final footage
  - annotated fallback still works and is clearly distinct

#### Task 5 — Re-verify the benchmark decision and lock UI language around it

- Files:
  - `benchmarks/tasks/previz-usefulness.yaml`
  - `benchmarks/scripts/generate_previz_usefulness_dataset.py`
  - `benchmarks/scripts/previz_usefulness_report.py`
  - `docs/evals/registry.yaml`
  - story file
  - any UI copy/docs touched along the way
- Change:
  - rerun the benchmark if generation behavior changed materially
  - keep the UI recommendation/default aligned to verified results
  - if Lite still lacks verified pricing, expose AI previz as experimental/manual with warnings while keeping deterministic previz as default
- Could break:
  - docs or UI copy can drift from measured results if not updated together
- Done looks like:
  - the app has a visible AI-previz path
  - the benchmark-backed default/recommendation is honest
  - the story can close without pretending UI and product access are optional

### Tests / Verification Plan

- Backend checks after meaningful changes:
  - `.venv/bin/python -m pytest -m unit`
  - `.venv/bin/python -m ruff check src/ tests/`
  - targeted unit tests for render-adapter, prompt compilation, and any schema changes
- Eval checks:
  - rerun the previz-usefulness dataset and promptfoo task from scratch
  - classify all significant mismatches as `model-wrong`, `golden-wrong`, or `ambiguous`
  - update `docs/evals/registry.yaml` with date, `git_sha`, and verified scores
- UI checks:
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Runtime / browser verification:
  - open Scene Workspace on a seeded scene and click the `Previz` tab
  - inspect the top explainer/recommendation card plus both previz lanes
  - confirm the AI lane shows pack/model, resolution, cost/latency or `cost unverified`, consistency strategy, and non-final intent before generation
  - open the AI previz detail page and confirm the non-final warning plus links back to the annotated baseline
  - open the final render route and confirm it remains render-only
  - if browser tooling is blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker

### Redundancy Plan

- Remove or replace stale Google pack definitions and pack labels that imply the old shared-video lane is still the only AI comparator.
- Remove any duplicated previz house-style text if it ends up copied across prompts, engine packs, and UI labels.
- Remove the old `Animatics`-only framing if the broader `Previz` surface supersedes it.
- Remove any reuse of `render_generation` / `generated_video` that keeps AI previz visually coupled to final render.
- Do not leave behind half-wired toggles or dead comparison helpers once the new previz surface is in place.

### Human-Approval Blockers

- No major blocker on dependencies or public APIs is known yet.
- The key architectural choice in this rescope is deliberate: prefer a dedicated AI-previz artifact + recipe path over overloading final-render types. That is a larger but cleaner refactor and matches the greenfield rule better than preserving misleading names.
- If Google's live API/model naming conflicts with the docs during implementation, prefer the live API for runtime truth and record the discrepancy in the work log rather than forcing doc-era names into code.

### Recommended Execution Order

1. Lock the AI-previz artifact/recipe taxonomy and remove stale `shared_video` / render-coupled naming.
2. Emit AI-previz artifacts through the dedicated path while keeping the current substrate intact.
3. Refactor Scene Workspace into a real `Previz` surface with deterministic and AI lanes.
4. Add the dedicated AI-previz artifact detail viewer and cross-links back to annotated baseline.
5. Re-run checks, browser verification, and the benchmark if generation behavior changed, then lock the default/recommendation copy.

### Build Outcome Target

- Best case: a specific low-cost AI lane beats `annotated_symbolic`, lands as an explicit AI-previz mode inside the new `Previz` surface, and becomes the recommended/default lane while remaining clearly non-final.
- Acceptable case: AI previz lands as an explicit experimental/manual lane in the same `Previz` surface, deterministic previz stays default, final render remains separate, and the UI warns honestly about the blocker instead of hiding the capability.

## Work Log

20260403-1048 — story created: user requested a next-step story for gen-AI previz after Story 137. Evidence reviewed while drafting: `docs/ideal.md`, `docs/build-map.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:7.1`, `spec:7.2`, `spec:10.3`), ADR-002, ADR-003, Story 137, Story 028, Story 029, Story 030, Story 119, Story 140, local render engine packs, `scripts/discover-models.py --summary`, and current Google Cloud docs/blog updates dated 2026-04-02 through 2026-04-03. Key findings: no dedicated post-137 gen-AI previz story existed; the repo still points at a stale `veo-3.1-generate-preview` pack; Google now offers `Veo 3.1`, `Fast`, and `Lite`; Lite is attractive on cost but lacks component/style reference images; and Story 137's last measured shared-video lane still loses to `annotated_symbolic`. Next step: promote only when someone is ready to run the refreshed AI-previz benchmark and choose the winner with evidence.
20260403-1943 — build-story exploration: promoted the story from `Draft` to `Pending`, traced the render-adapter / animatic / benchmark paths, and wrote the implementation plan without starting code changes. Evidence reviewed: `docs/ideal.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:7.1`, `spec:7.2`, `spec:10.3`), `docs/build-map.md`, ADR-002, ADR-003, Story 137, Story 028, Story 029, Story 030, Story 056, Story 119, Story 140, `src/cine_forge/modules/generation/render_adapter_v1/`, `src/cine_forge/ai/video.py`, `src/cine_forge/services/injected_assets.py`, `src/cine_forge/schemas/render.py`, `src/cine_forge/schemas/animatic.py`, `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/PrevizReelViewer.tsx`, and `benchmarks/tasks/previz-usefulness.yaml`. Live checks: `make check-size`, `.venv/bin/python scripts/discover-models.py --summary`, direct OpenAI model-list probe (`sora-2`, `sora-2-pro`), direct Google model-list probe (`veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`), and a fresh baseline promptfoo rerun recorded in `benchmarks/results/previz-usefulness-build-story-2026-04-03-report.md` (`annotated_symbolic` `0.808`, `shared_video` `0.603`, `symbolic` `0.658`). Risks/surprises: the current shared-video lane is still clearly behind; the benchmark currently collapses all AI video into one bucket, so the story needed a small scope correction toward candidate-specific AI lanes; and the likely backend integration points are already oversized, so the plan explicitly biases toward focused helpers and schema-first changes. Next step: get human approval on the plan, then start implementation and set story status to `In Progress`.
20260403-2008 — implementation: added a schema-first AI-previz prompt contract in `src/cine_forge/schemas/render.py`, exported it from `src/cine_forge/schemas/__init__.py`, and added the focused helper `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` so low-fidelity house-style prompt compilation lives outside the already-oversized render adapter entrypoint. Refreshed candidate inventory by updating `engine_packs/sora-2.yaml`, `engine_packs/veo-3.1.yaml`, and adding `engine_packs/veo-3.1-fast.yaml` plus `engine_packs/veo-3.1-lite.yaml`. While smoke-testing live providers, found a real Google transport bug in `src/cine_forge/ai/video.py`: `durationSeconds` had to be numeric, not a string, for Veo 3.1 preview endpoints to accept the request. Evidence: real smoke clips landed under `output/story-143-smoke/`, with approximate generation latencies of 32144 ms for Veo 3.1 Fast, 42395 ms for Veo 3.1 Lite, and 107289 ms for Sora 2. The live API still exposed preview-era Veo IDs even though the docs had already shifted naming guidance, so the implementation followed runtime truth and recorded the discrepancy here instead of forcing doc-era names into code. Next step: rerun the benchmark with candidate-specific lanes and decide whether any AI path earns product integration.
20260403-2018 — benchmark + handoff: replaced the old shared-video comparator with candidate-specific AI lanes in `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `benchmarks/tasks/previz-usefulness.yaml`, and `benchmarks/scripts/previz_usefulness_report.py`, then generated a full five-lane dataset and promptfoo rerun recorded in `benchmarks/results/previz-usefulness-story-143-2026-04-03.json` plus the paired report files. Final ranking: `Veo 3.1 Lite Previz` `0.9027`, `Annotated Animatic` `0.8130`, `Veo 3.1 Fast Previz` `0.8003`, `Symbolic Animatic` `0.6787`, `Sora 2 Previz` `0.6598`. Decision: no product switch yet. Lite won on usefulness but public generation cost could not be verified from the current official pricing pages checked, so it did not clear the adoption gate. Fast trailed the deterministic default. Sora was far slower and more expensive while still underperforming. Mismatch classifications were recorded for the story and eval registry: `Sora 2 Previz` had three non-runtime-blocking ambiguous failures on `hard_constraints.evidence_timestamp_range`; `Veo 3.1 Fast Previz` had one non-runtime-blocking model-wrong miss on `radio_hold_tracking`; and `Symbolic Animatic` retained one non-runtime-blocking ambiguous simplification miss on the same clip. Checks run for touched scope: targeted unit tests for the new prompt helper / schema / video client / report path, `make test-unit PYTHON=.venv/bin/python` (`649 passed, 141 deselected, 1 warning`), and backend lint. UI checks and browser verification were intentionally skipped because no UI files changed and Task 4 never triggered. Next step: run `/validate` on this story.
20260403-2238 — validate: reran local delta inspection (`git status --short`, `git diff --stat`, `git diff`, `git ls-files --others --exclude-standard`), reviewed `docs/ideal.md`, ADR-002, ADR-003, and the Story 143 spec refs, then reran the full validation suite for this scope: `make test-unit PYTHON=.venv/bin/python` (`649 passed, 141 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`, targeted pytest for Story 143 (`13 passed` across prompt helper / report / video client / schema / engine-pack coverage), `pnpm --dir ui run lint` (`0 errors, 5 existing unrelated warnings`), and `cd ui && npx tsc -b` (pass). Fresh eval evidence was regenerated from scratch in this validation pass: `benchmarks/scripts/generate_previz_usefulness_dataset.py`, `promptfoo eval -c tasks/previz-usefulness.yaml --no-cache -j 1 --output results/previz-usefulness-validation-story-143-2026-04-03.json`, and `benchmarks/scripts/previz_usefulness_report.py`. Verified ranking changed numerically but not strategically: `Veo 3.1 Lite Previz` `0.9303`, `Annotated Animatic` `0.8563`, `Veo 3.1 Fast Previz` `0.8230`, `Symbolic Animatic` `0.6863`, `Sora 2 Previz` `0.6340`. Product decision remains the same: hold the deterministic default until Lite cost can be verified. Fresh mismatch classification from this pass: Sora 2 still has three non-runtime-blocking ambiguous failures driven by `hard_constraints.evidence_timestamp_range` while the rubric remains strong; Symbolic Animatic still has one non-runtime-blocking ambiguous miss on `radio_hold_tracking`; Veo Fast's earlier miss did not reproduce on the validation rerun. Browser verification remains not applicable because no UI files changed in this story. Recommended next step: `/mark-story-done`.
20260403-2354 — story rescope: user rejected the benchmark-only closure because AI previz is an operator-facing capability and this repo does not allow shipping UI-facing features without UI. Re-reviewed ADR-002, ADR-003, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/components/AnimaticsPanel.tsx`, `ui/src/components/GeneratedVideoPanel.tsx`, `ui/src/components/preview-provenance.ts`, `src/cine_forge/schemas/animatic.py`, `src/cine_forge/schemas/track.py`, `src/cine_forge/pipeline/graph.py`, `src/cine_forge/api/artifact_manager.py`, `ui/src/lib/constants.ts`, and `ui/src/lib/artifact-meta.ts`. Key findings: the current split between `Animatics` and `Render` forces AI previz into the wrong mental model; stale `shared_video` survives in user-facing mode labels; and overloading `render_generation` / `generated_video` would keep previz visually coupled to final footage. Updated the story to reopen build/validation gates, replace the old “close with evidence and no UI” acceptance criteria with UI-first criteria, and write a refactor-oriented plan centered on a real `Previz` surface, dedicated AI-previz artifact/recipe identity, and cleanup of obsolete naming. Next step: implement the UI-backed path before re-validating or closing the story.
20260404-0118 — implementation: finished the UI-backed AI-previz path and removed the obsolete `AnimaticsPanel` surface. Scene Workspace now routes through `ui/src/components/PrevizPanel.tsx`, which presents `Annotated Animatic` and `AI Previz` side by side, keeps the deterministic lane as the explicit default, and adds manual generate/refresh actions plus preflight disclosure for the AI lane (`google_veo31_lite`, `veo-3.1-lite-generate-preview`, `1280x720`, prompt-only consistency, `cost unverified`, and non-final warning). Artifact Detail now dispatches dedicated AI-previz routes through `ui/src/components/AiPrevizViewer.tsx` and treats `ai_previz_prompt` as a read-only compiled artifact via both UI and backend policy (`src/cine_forge/artifacts/edit_policy.py`, `tests/unit/test_api.py`, `tests/unit/test_chat_artifact_edits.py`). Backend taxonomy is now direct instead of overloaded: `ai_previz_prompt` / `ai_previz_video` are registered in `src/cine_forge/driver/schema_registry.py`, exposed in `src/cine_forge/modules/generation/render_adapter_v1/module.yaml`, routed in `src/cine_forge/pipeline/graph.py`, and threaded through `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/schemas/animatic.py`, `src/cine_forge/schemas/render.py`, and `src/cine_forge/schemas/track.py`. A real bug surfaced during focused pytest: AI previz still inherited final-render strictness for locked keyframes/audio, so `google_veo31_lite` hard-failed whenever a required reference existed. Fixed by allowing prompt-only fallback for required media in AI-previz mode only while preserving strict final-render behavior. Checks rerun after the fix: focused pytest over touched Story 143 surfaces (`61 passed`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass), `make test-unit PYTHON=.venv/bin/python` (`652 passed, 142 deselected, 1 warning`), `pnpm --dir ui run lint` (`0 errors, 5 existing unrelated warnings`), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass). Browser verification was completed with a seeded project at `output/story-143-ui-check/` plus shell-driven Playwright after the MCP browser context was unavailable; screenshots and console/page-error evidence are in `output/story-143-verification/scene-workspace-previz-tab.png`, `output/story-143-verification/ai-previz-detail.png`, `output/story-143-verification/ai-previz-prompt-detail.png`, and `output/story-143-verification/browser-log.json` (`0` console errors, `0` page errors). Related docs updated: this story file and `docs/stories.md`. Next step: run `/validate` on Story 143 against the new UI-backed implementation.
20260403-2255 — validate: finished the fresh validation pass for the UI-backed Story 143 implementation. Reran the required checks: `make test-unit PYTHON=.venv/bin/python` (`652 passed, 142 deselected, 1 warning`), `.venv/bin/python -m pytest tests/unit/test_previz_prompting.py tests/unit/test_previz_usefulness_report.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/unit/test_render_schema.py tests/unit/test_api.py tests/unit/test_chat_artifact_edits.py tests/unit/test_track_system_module.py tests/unit/test_schema_registry.py` (`68 passed`), `.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (`0 errors, 5 existing warnings`), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass). Browser MCP remained unavailable (`Target page, context or browser has been closed`), so validation followed `docs/runbooks/browser-automation-and-mcp.md` and used an isolated Playwright fallback against the seeded Story 143 routes. Fresh browser evidence is in `output/story-143-validation/scene-workspace-previz-tab.png`, `output/story-143-validation/ai-previz-detail.png`, `output/story-143-validation/ai-previz-prompt-detail.png`, and `output/story-143-validation/browser-log.json` (`3` routes covered, `0` console errors, `0` page errors). Fresh eval evidence was regenerated from scratch in this pass: the first dataset build attempt hit a transient `moderation_blocked` Sora response, but an immediate clean retry succeeded; promptfoo rerun `results/previz-usefulness-validation-story-143-ui-2026-04-03.json` and report `...-report.md` now rank `Veo 3.1 Lite Previz` `0.8280`, `Annotated Animatic` `0.8030`, `Veo 3.1 Fast Previz` `0.7780`, `Sora 2 Previz` `0.6590`, and `Symbolic Animatic` `0.6547`. Product decision remains unchanged: hold the deterministic default because Lite cost is still unverified and its lead stays below the 0.03 default-switch gate. Remaining eval mismatches are classified and non-runtime-blocking: `Veo 3.1 Fast Previz` on `dialogue_confession_push_in` is model-wrong, `Sora 2 Previz` retains three ambiguous `evidence_timestamp_range` hard-constraint misses, `Annotated Animatic` on `radio_hold_tracking` is ambiguous on tone/emotion, and `Symbolic Animatic` remains ambiguous on `quiet_bedside_vigil` plus `radio_hold_tracking` simplification. Recommended next step: `/mark-story-done`.
20260403-2312 — mark-story-done: reviewed the completed story against the fresh validation pass and closed it. Verified workflow gates, acceptance criteria, task checklist, mismatch classification, and registry updates all matched the landed slice. Close-out docs were brought back into alignment by updating `docs/stories.md`, `docs/build-map.md`, and `CHANGELOG.md` so the planning surfaces reflect that Story 143 is shipped as an explicit UI-backed AI-previz lane with a benchmark-backed `hold` default decision. Recommended next step: `/check-in-diff`.
