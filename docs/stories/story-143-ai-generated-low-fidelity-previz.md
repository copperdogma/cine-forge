# Story 143 — AI-Generated Low-Fidelity Previz

**Priority**: High
**Status**: Draft
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade motion assets), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:6.3 (Animatics / Previz Video), spec:6.3.2 (Characteristics), spec:6.3.3 (Previz Reel), spec:6.4 (Keyframes), spec:7.1 (Render Adapter Layer), spec:7.2 (User Asset Injection), spec:10.3 (Always-Playable Rule)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / concern-group inputs)
**Depends On**: Story 137 (Previz Fidelity Upgrade), Story 028 (Render Adapter), Story 029 (User Asset Injection), Story 030 (Generated Output QA), Story 056 (Entity Design Studies), Story 119 (Visual Reference Propagation), Story 140 (Agentic Media Validation Loop)

## Goal

Story 137 proved that CineForge's current annotated deterministic previz is more useful than the then-current shared-video path. This story revisits AI previz with a tighter question: can current cheap and fast video models produce a deliberately low-fidelity, non-final previz mode that improves camera-placement, blocking, motion, and pacing readability without encouraging users to obsess over final-render detail? The story should evaluate current AI-video candidates, define a consistent previz house style, and only adopt AI previz if it beats the annotated baseline inside a real cost/latency envelope.

## Acceptance Criteria

- [ ] A documented eval compares Story 137's `annotated_symbolic` baseline against at least two current AI-video previz candidates on the same fixed scene set, using low-resolution defaults and a rubric that scores camera placement, blocking clarity, motion readability, pacing usefulness, scene/prop/location legibility, character distinctness, style consistency, and cost/latency.
- [ ] One benchmarked candidate uses a current Google Veo 3.1 tier available as of 2026-04-03 rather than the repo's stale `veo-3.1-generate-preview` pack, and at least one non-Google fast lane already supported by the repo remains in the comparison so the story does not silently become vendor-locked.
- [ ] The chosen AI-previz path, if adopted, uses an explicit previz house style that is intentionally non-final: simplified, consistent, and blocking-first. The style contract makes clear how characters remain distinguishable, how locations and props stay readable enough for staging, what detail is intentionally suppressed, and whether consistency is achieved prompt-only or with optional reference inputs.
- [ ] Default AI-previz generation stays on the cheapest and lowest-resolution setting that still clears the usefulness bar for the winning engine pack. If a higher-cost tier or higher resolution is required, the measured reason is recorded in the eval and provenance surfaces.
- [ ] Scene Workspace, Artifact Detail, and stored artifacts make AI previz clearly distinct from final generated video, including engine pack/model, resolution, duration, cost/latency, intended use, and the consistency strategy that shaped the result, with reference inputs shown only when they were actually used.
- [ ] AI previz remains advisory and optional: `annotated_symbolic` fallback stays available, and CineForge never silently swaps final render for previz or previz for final render.
- [ ] If no AI-video lane clearly beats the annotated baseline inside the target cost/latency envelope, the story closes with measured evidence and no default-product switch.

## Out of Scope

- Photoreal or final-render-quality previz
- Training custom identity models, LoRAs, or other heavyweight consistency substrate
- Building a general-purpose 3D editor, DCC workflow, or virtual production toolchain inside CineForge
- Making AI previz mandatory before downstream render or export
- Treating AI previz as a disguised final render with extra polish or upscaling
- Solving full film-wide continuity or shot-to-shot identity perfection across arbitrarily long sequences
- Silent provider lock-in or assuming one vendor wins before measurement

## Approach Evaluation

- **Simplification baseline**: Story 137 already measured the then-current shared-video lane and it lost to `annotated_symbolic`, so the baseline is not hypothetical. The first question is whether current model inventory plus a deliberately low-detail house-style prompt changes that result enough to justify product work. If not, keep the deterministic default and stop.
- **AI-only**: Reuse the render adapter with a previz-specific prompt/compiler mode, short low-resolution clips, and current fast engine packs. Prompt-only house-style and character-description consistency is acceptable if it is measurably good enough for previz review. Pros: simplest path, best chance to feel like real motion instead of overlays. Cons: weak controllability, risk of pseudo-final imagery, and possible identity/style drift across shots.
- **Hybrid**: Compile a typed previz brief from shot plan, concern groups, keyframes, and optional design-study or injected references; then route that into selected engine packs with an explicit low-fidelity house style and provenance. Pros: strongest fit for controllability, transparency, and graceful model evolution as optional reference support improves. Cons: more orchestration work and more chances to bloat already-large render files if done carelessly.
- **Pure code**: `annotated_symbolic` remains the control arm and fallback. It is not the main answer to this story because the user-facing question is AI previz, but it is the benchmark every AI lane must beat.
- **Repo constraints / ADRs**: ADR-003 requires previz to stay grounded in Scene Workspace and concern-group artifacts, not isolated prompt hacking. ADR-002 requires visible diagnostics and preflight rather than backend magic. Story 137 already established the usefulness baseline. Story 028 owns the AI-video substrate. Current repo drift matters: local engine packs still point at `veo-3.1-generate-preview`, but Google's official docs updated on 2026-04-02 recommend `veo-3.1-generate-001` and `veo-3.1-fast-generate-001`, and introduced `veo-3.1-lite-generate-001`. Lite's lack of component/style reference images is therefore an eval consideration, not a product blocker by itself; it only matters if prompt-only consistency proves insufficient.
- **Existing patterns to reuse**: Story 137's `previz-usefulness` benchmark and `preview_provenance` surfaces; Story 028's render adapter and engine-pack structure; Story 029's injected assets; Story 056 and Story 119's design-study `visual_reference_image` propagation; Story 030 and Story 140's media-understanding and runtime validation substrate; the existing Scene Workspace / Artifact Detail review loop.
- **Eval**: extend the current previz-usefulness harness or add a tight sibling task so the same scenes compare `annotated_symbolic` against current AI lanes under low-cost, low-resolution defaults and explicit house-style prompts. The eval must classify significant misses as model-wrong, golden-wrong, or ambiguous, and record whether any remaining failures are runtime-blocking or non-runtime-blocking.

## Tasks

- [ ] Research and document a repo-fit AI-previz visual language informed by current previs practice: camera, blocking, motion, and staging first; detail deliberately suppressed. Turn that into an explicit previz style profile or prompt-compiler contract rather than ad hoc prompt strings.
- [ ] Refresh the video-engine candidate inventory before implementation: update Google Veo IDs/capabilities from retired preview IDs to current GA/preview surfaces, capture which tiers support prompt-only vs reference-assisted consistency, first/last frame, audio, and lowest output resolutions, and run `/discover-models` for any supporting compiler/judge model choices.
- [ ] Extend the previz-usefulness eval so it compares Story 137's `annotated_symbolic` baseline against at least two current AI-video lanes under low-cost, low-resolution defaults and house-style prompts; record fresh results in `docs/evals/registry.yaml`.
- [ ] If an AI lane wins, implement the thinnest end-to-end path in the same story: previz-specific prompt compilation/inputs, render-adapter integration, artifact provenance, Scene Workspace, Artifact Detail, and browser verification, without removing the annotated fallback.
- [ ] If no AI lane wins, close the story around the measured evidence, engine-pack refresh, and any follow-up needed instead of forcing a product switch.
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

- **Owning class/module**: Actual AI generation should stay under `src/cine_forge/modules/generation/render_adapter_v1/`. If a previz-specific compiler is needed, add a focused sibling helper or prompt-compiler module rather than inflating `render_adapter_v1/main.py` further. Scene Workspace and Artifact Detail should remain thin consumers, not decision-makers. Do not move core logic into `animatic_v1/support.py`.
- **Data contracts**: Reuse and extend typed contracts such as `PreviewProvenance`, `CompiledRenderPrompt`, `GeneratedVideoArtifact`, and `animatic`/previz schemas where clean. If the story needs a `previz_style_profile`, `consistency_strategy`, or stronger intended-use metadata, define it schema-first before wiring module, API, or UI code.
- **File sizes**: `make check-size` currently flags the likely touch points: `src/cine_forge/modules/generation/render_adapter_v1/main.py` (1374), `src/cine_forge/services/injected_assets.py` (811), `src/cine_forge/ai/video.py` (411), `ui/src/pages/SceneWorkspacePage.tsx` (758), and `ui/src/pages/ArtifactDetail.tsx` (634). Smaller likely touch points are `src/cine_forge/schemas/render.py` (169), `src/cine_forge/schemas/animatic.py` (154), `ui/src/components/GeneratedVideoPanel.tsx` (305), `ui/src/components/AnimaticViewer.tsx` (254), and `ui/src/components/PrevizReelViewer.tsx` (111). `/build-story` must bias toward new focused files/components instead of growing the oversized ones.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/build-map.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:7.1`, `spec:7.2`, `spec:10.3`), ADR-002, ADR-003, Story 137, Story 028, Story 029, Story 030, Story 119, Story 140, current render engine packs, and official Google Cloud docs/blog updates dated 2026-04-02 through 2026-04-03 covering Veo 3.1 Fast/Lite, capabilities, and pricing.

## Files to Modify

- `benchmarks/tasks/previz-usefulness.yaml` — extend candidate coverage and rubric for AI-previz house-style comparison
- `benchmarks/prompts/` — refine the judging prompt so it scores low-fidelity readability rather than raw cinematic impressiveness
- `benchmarks/scripts/generate_previz_usefulness_dataset.py` — update dataset generation if new AI-previz candidates or style-profile inputs need fresh fixtures
- `benchmarks/scripts/previz_usefulness_report.py` — surface cost/latency and style-consistency findings clearly
- `docs/evals/registry.yaml` — record fresh AI-previz benchmark results and mismatch classification
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/` — refresh Google Veo packs and add any missing current fast/lite candidate packs if justified
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — thin orchestration only; avoid adding more packed logic to the 1374-line file
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` or a new focused sibling helper — previz-specific house-style prompt compilation and intent shaping
- `src/cine_forge/ai/video.py` — provider request shaping if updated model IDs/features require it (411)
- `src/cine_forge/services/injected_assets.py` — keep design-study and injected references available as optional consistency inputs rather than mandatory prerequisites (811)
- `src/cine_forge/schemas/render.py` — provenance and consistency-strategy extensions if needed (169)
- `src/cine_forge/schemas/animatic.py` — shared previz-mode metadata if AI previz becomes a first-class sibling mode (154)
- `ui/src/components/GeneratedVideoPanel.tsx` — show AI-previz intent, provenance, and non-final status more clearly (305)
- `ui/src/components/AnimaticViewer.tsx` — surface the comparison/fallback relationship between annotated and AI previz when relevant (254)
- `ui/src/components/PrevizReelViewer.tsx` — clarify project-level previz mode and review intent (111)
- `ui/src/pages/SceneWorkspacePage.tsx` — thin routing only; do not grow the 758-line page
- `ui/src/pages/ArtifactDetail.tsx` — thin routing only; do not grow the 634-line page

## Redundancy / Removal Targets

- The stale `veo-3.1-generate-preview` pack and any related docs/config if current GA packs supersede it
- Any prompt text or UI copy that implies AI previz is just a cheaper final render
- Any duplicated house-style strings or previz-mode labels spread across engine packs, UI, and benchmark prompts
- Any temporary shared-video comparison config left behind once the winning AI-previz path is explicit

## Notes

- Traditional previs exists to plan and communicate shots, not to perfect surface detail. This story should treat generative video as a faster visualization substrate, not as an excuse to skip previs discipline.
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

To be written during `/build-story`.

## Work Log

20260403-1048 — story created: user requested a next-step story for gen-AI previz after Story 137. Evidence reviewed while drafting: `docs/ideal.md`, `docs/build-map.md`, `docs/spec.md` (`spec:6.3`, `spec:6.4`, `spec:7.1`, `spec:7.2`, `spec:10.3`), ADR-002, ADR-003, Story 137, Story 028, Story 029, Story 030, Story 119, Story 140, local render engine packs, `scripts/discover-models.py --summary`, and current Google Cloud docs/blog updates dated 2026-04-02 through 2026-04-03. Key findings: no dedicated post-137 gen-AI previz story existed; the repo still points at a stale `veo-3.1-generate-preview` pack; Google now offers `Veo 3.1`, `Fast`, and `Lite`; Lite is attractive on cost but lacks component/style reference images; and Story 137's last measured shared-video lane still loses to `annotated_symbolic`. Next step: promote only when someone is ready to run the refreshed AI-previz benchmark and choose the winner with evidence.
