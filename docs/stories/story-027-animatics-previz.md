---
id: "027"
title: "Animatics, Keyframes, and Previz (Optional)"
status: "Done"
priority: "Unknown"
ideal_refs: []
spec_refs:
  - "spec:6.3"
  - "spec:6.4"
  - "spec:10.2"
  - "spec:10.3"
adr_refs: []
depends_on:
  - "013"
  - "025"
  - "026"
category_refs:
  - "spec:6"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 027: Animatics, Keyframes, and Previz (Optional)

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:6.3 (Animatics / Previz Video), spec:6.4 (Keyframes), spec:10.2 (Tracks — animatic/keyframe tracks), spec:10.3 (Always-Playable Rule)
**Depends On**: Story 025 (shot planning), Story 026 (storyboards — optional input), Story 013 (track system)

---

## Goal

Generate **animatics** (low-detail video with accurate timing and camera motion), **keyframes** (start/mid/end frames for constraining video generators), and **previz reels** (mixed storyboard + animatic timelines with temp audio). These are optional visualization stages between storyboards and final generation.

---

## Acceptance Criteria

### Animatics (Spec 15)
- [x] Scene-level `animatic` artifacts persist ordered shot segments with video refs, timing metadata, and lineage back to shot plans and any storyboard/audio inputs used.
- [x] MVP review slices are usable at the levels this story now owns:
  - [x] Per project via `previz_reel`.
  - [x] Per scene via scene-level `animatic`.
  - [x] Per shot via animatic segments and per-shot keyframes.
- [x] Animatic characteristics:
  - [x] Low detail (symbolic characters and sets is acceptable).
  - [x] Accurate timing (matches shot duration estimates).
  - [x] Accurate camera motion (reflects shot definitions).
- [x] Available storyboard frames are reused when present; missing storyboard coverage degrades gracefully instead of hard-failing the run.
- [x] Temp dialogue and sound are included when available from Sound & Music outputs or injected project/scene audio references.
- [x] Animatic artifacts populate the `animatics` track for always-playable resolution.

### Keyframes (Spec 16)
- [x] Scene-level keyframe artifacts persist start, mid, and end frames per shot with image refs, shot linkage, and lock metadata.
- [x] Keyframes are lockable by Director from a dedicated UI surface rather than only raw JSON editing.
- [x] Keyframes are derived from storyboards or animatics.
- [x] Locked keyframes preserve enough constraint metadata and lineage for Story 028 render adapter consumption.
- [x] Keyframe artifacts populate the `keyframes` track in the timeline manifest.

### Previz Reel (Spec 15.3)
- [x] Project-level `previz_reel` artifact assembles a project-wide playable review reel from scene animatics, with storyboard or placeholder fallback flowing through the animatic stage instead of UI-side guesswork.
- [x] Temp dialogue and sound are included when available.
- [x] Reel is usable for review and education, not only stored as loose files.
- [x] Assembly follows the always-playable rule and fills gaps with the best available representation via backend data, not UI-side guesswork.

### Advisory Behavior (Spec 15.4)
- [x] Previz is never mandatory.
- [x] This MVP keeps previz advisory and non-blocking. It does not make previz or keyframe locks a required upstream gate for downstream stages yet.

### UI Integration
- [x] Scene Workspace exposes animatics/keyframes as a first-class review surface, not only via generic artifact browsing.
- [x] The scene workspace surface supports the same operational loop as shot planning/storyboards:
  - [x] Empty state explains value and prerequisites.
  - [x] Run / refresh action launches the project-wide animatics recipe and resolves back to the current scene.
  - [x] In-progress state explains the project-wide scope while keeping the current scene usable.
  - [x] Success state shows inline playback and keyframe review for the current scene.
- [x] Inline review shows actual video/image assets loaded from project paths plus structured metadata (shot linkage, duration, audio availability, lock state, and provenance cues).
- [x] Artifact Detail renders animatic, keyframe, and previz artifacts with dedicated viewers rather than raw JSON.
- [x] New artifact types have proper artifact metadata and run labels/messages anywhere artifact types or recipes are surfaced in the UI.

### Module Manifests
- [x] Module: `src/cine_forge/modules/visualization/animatic_v1/`
- [x] Module: `src/cine_forge/modules/visualization/keyframe_v1/`
- [x] Reads shot plans, storyboards (if available), Sound & Music concern group artifacts, and scene/project audio references when available.
- [x] Outputs scene-level animatic and keyframe artifacts plus project-level previz reel assembly.

### Schema
- [x] `AnimaticSegment` schema (video reference, timing, shot linkage).
- [x] `Animatic` schema (scene-level ordered segments, timing summary, audio refs, and provenance).
- [x] `Keyframe` schema (image reference, shot position, lock status).
- [x] `PrevizReel` schema (project review reel with temp audio and scene-level lineage).
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for deterministic animatic composition logic, including missing-storyboard fallback and temp-audio handling.
- [x] Unit tests for keyframe extraction from storyboards/animatics.
- [x] Unit tests for keyframe locking behavior.
- [x] Unit tests for previz reel assembly and always-playable fallback selection.
- [x] Integration test: shot plan → animatic/keyframe generation → track population → previz reel assembly.
- [x] Schema validation on all outputs.
- [x] UI checks: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, plus browser verification.

---

## Design Notes

### Animatics vs. Storyboards
Storyboards are static images. Animatics add time and motion — they're essentially very rough video. The value of animatics is timing verification: does the scene feel too fast? Too slow? Does the camera movement work? Storyboards can't answer these questions.

### Keyframes as Generation Constraints
Keyframes are the bridge between previz and final generation. When a keyframe is locked by the Director, it becomes a constraint for the render adapter (Story 028) — the generated video must match the keyframe at that point. This gives the user creative control over the final look while letting AI handle the in-between frames.

### Cost Considerations
Animatics and keyframes involve either AI video generation (expensive) or 3D rendering (complex setup). For MVP, consider simple approaches: panning over storyboard images with camera motion simulation, or using lightweight AI video generation at very low quality/resolution.

### Deterministic MVP Composition
This repo already has storyboard frames, shot timing estimates, audio-reference plumbing, project-relative asset serving, and immutable artifact persistence. The first animatic implementation should exploit that substrate instead of jumping straight to AI-video generation. A deterministic compositor over storyboard stills, timing, and optional temp audio closes the user-facing previz gap with far less blast radius, while leaving Story 028 to own actual generative video constraints.

---

## Tasks

- [x] Design schema-first animatic, keyframe, and previz artifacts.
- [x] Register schemas in schema registry and exports.
- [x] Create `animatic_v1` module.
- [x] Create `keyframe_v1` module.
- [x] Implement deterministic animatic composition from shot plans plus optional storyboard/audio inputs.
- [x] Implement keyframe extraction, display metadata, and Director lock/unlock flow.
- [x] Implement previz reel assembly.
- [x] Implement track integration (animatic and keyframe tracks) and any required pipeline-graph correction for optional storyboard input.
- [x] Keep previz advisory and non-blocking for MVP rather than inventing premature rigidity controls with no downstream consumer yet.
- [x] Design animatics/keyframes UI integration for Scene Workspace and Artifact Detail.
- [x] Implement dedicated viewers/panels for animatic, keyframe, and previz review.
- [x] Integrate recipe/run labels, stage copy, and artifact metadata into existing UI surfaces.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run backend checks (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`, `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`).
- [x] Run UI checks (`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`) and browser verification.
- [x] Search all docs and update any related to what we touched.
- [x] Review whether this work surfaced a reusable `AGENTS.md` lesson; no repo-wide update was warranted.

## Tenet Verification

- [x] **T0 — Data Safety:** New artifacts and keyframe lock changes are versioned immutably; no existing artifact versions are mutated in place.
- [x] **T1 — AI-Coded:** The implementation stays schema-first, uses focused modules/components, and records the operator-visible workflow directly in the story.
- [x] **T2 — Architect for 100x:** MVP uses deterministic composition instead of premature render-adapter or 3D-stack complexity; richer previz remains a follow-on story.
- [x] **T3 — Fewer Files:** New files were added only where they reduced pressure on already-large page/module files; large existing files were kept to thin wiring changes.
- [x] **T4 — Verbose Artifacts:** Work log, validation note, and smoke artifacts capture the implementation/verification history with concrete evidence.
- [x] **T5 — Ideal vs Today:** This lands the minimal always-playable previz step without pretending symbolic animatics solve richer previs; Story 137 captures that next climb explicitly.

---

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

---

## Plan

### Scope Adjustment

- Persist scene-level animatic and keyframe artifacts plus a project-level previz reel artifact, instead of treating animatics as loose media files with no structured review payload.
- Fold user-facing review surfaces into this story: Scene Workspace panel, Artifact Detail viewers, artifact metadata, and run-label/message updates. Splitting backend generation from UI here would recreate the exact "functionality ships, UI gets lost" failure mode.
- Prefer deterministic ffmpeg-based composition over AI-video generation for MVP animatics. Storyboards, shot timings, and optional temp audio already provide the substrate needed for cheap, reviewable previz, while Story 028 remains the correct place for true render-time generation constraints.
- Keyframe lock/unlock must be operable in-app. Reusing the existing immutable artifact-edit path under a dedicated UI control is acceptable; relying on raw JSON editing as the primary lock UX is not.

### Eval-First Baseline

- Minimal eval for this story is code-level rather than promptfoo: schema validation, unit tests for animatic segment assembly / keyframe derivation / lock round-tripping / previz reel assembly, and an integration fixture proving `shot_plan + optional storyboard + optional audio -> animatic/keyframe artifacts + track_manifest + previz_reel`.
- Baseline on current code:
  - No animatic, keyframe, or previz schemas/modules/recipes/tests exist.
  - `src/cine_forge/pipeline/graph.py` already defines an `animatics` node but leaves it `implemented=False`.
  - The UI has storyboard review surfaces, but no animatic/keyframe/previz viewers, metadata, recipe names, or stage copy.
- Candidate approaches considered:
  - AI-video-first animatics: rejected because it overlaps Story 028, would force premature provider/model selection, and is not required to satisfy the current previz goal.
  - Hybrid deterministic composition over storyboard stills + shot timing + optional temp audio: chosen because it matches existing immutable-artifact and asset-serving patterns while delivering a playable assembly now.
  - Pure text/slate-only previz with no media composition: rejected because it does not close the Ideal/spec gap of a watchable intermediate assembly.

### Repo-Fit Evidence

- The Ideal explicitly requires rapid `generate -> react -> refine` iteration and a playable assembly at every stage. Animatics and previz are the first time-based visualization layer after storyboards, so this story directly advances that gap.
- ADR-002 says downstream stages should be visible, diagnosable, and operable from the UI rather than hidden behind isolated buttons. A backend-only animatic producer would violate that navigation model.
- ADR-003 makes Scene Workspace the place where users review and refine scene-level creative artifacts. If animatics/keyframes are user-facing production artifacts, they belong there, not only in generic artifact JSON.
- Story 013 already defines `animatics` / `keyframes` track types and backend fallback precedence. The missing work is producers and review surfaces, not a new track architecture.
- Story 026 established the correct local pattern: scene-level visualization artifacts, project-wide recipe run, dedicated Scene Workspace panel, dedicated Artifact Detail viewer, and thin track-manifest updates inside the visualization module rather than in `track_system_v1`.
- Existing asset serving already handles project-relative image/audio/video files via `src/cine_forge/api/routers/assets.py`, so MVP animatic playback does not require a new media API.
- Rejected alternative: a backend-only Story 027 with a later UI follow-up would make validation misleading and contradict the user's explicit requirement that user-facing work ship with its UI.

### Structural Health

- Planned existing touch points and current line counts:
  - `src/cine_forge/driver/schema_registry.py` (96)
  - `src/cine_forge/schemas/__init__.py` (240)
  - `src/cine_forge/pipeline/graph.py` (697) — large; keep graph changes thin and local.
  - `ui/src/pages/SceneWorkspacePage.tsx` (706) — large; only wire a new panel/tab into the existing pattern.
  - `ui/src/pages/ArtifactDetail.tsx` (605) — large; add thin viewer routing only.
  - `ui/src/lib/types.ts` (419) — near threshold; keep new type additions focused.
  - `ui/src/lib/chat-messages.ts` (207)
  - `ui/src/lib/constants.ts` (155)
  - `ui/src/lib/artifact-meta.ts` (55)
- Existing large files to avoid growing with new logic:
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` (599) — reuse Story 026's module-owned track-update pattern instead of adding animatic logic here.
  - `ui/src/components/StoryboardViewer.tsx` (427) — do not turn it into a generic media viewer; add dedicated animatic/keyframe/previz components instead.
- New cross-layer contract must be schema-first: add animatic/keyframe/previz schemas before module, API, or UI code consumes their payloads.
- No new event type is currently planned.
- `ffmpeg` is present locally and the repo already tolerates optional ffmpeg usage in injected-asset handling, so composition should use a thin helper/subprocess wrapper instead of introducing a new heavyweight video library by default.

### Task Plan

1. Schema and contract
   - Files: new `src/cine_forge/schemas/animatic.py`, plus `src/cine_forge/schemas/__init__.py` and `src/cine_forge/driver/schema_registry.py`.
   - Change: define the persisted animatic/keyframe/previz models, including file refs, segment timing, audio provenance, Director lock metadata, and the minimal constraint fields Story 028 will need later.
   - Risk: weak schema boundaries would force frontend-only parsing hacks or ad hoc track metadata.
   - Done when: schema validation passes in unit tests and the artifact registry recognizes all new types.

2. Backend composition modules
   - Files: new `src/cine_forge/modules/visualization/animatic_v1/main.py`, new `src/cine_forge/modules/visualization/animatic_v1/module.yaml`, new `src/cine_forge/modules/visualization/keyframe_v1/main.py`, new `src/cine_forge/modules/visualization/keyframe_v1/module.yaml`, plus any small helper files in those module directories needed to keep methods below the size threshold.
   - Change: compose scene-level animatics from shot timing plus optional storyboard/audio inputs, derive keyframes, persist media files, assemble the project-level previz reel, and emit updated track-manifest entries for `animatics` and `keyframes`.
   - Risk: missing storyboard or audio inputs, ffmpeg failures, and lock metadata not round-tripping cleanly through versioned artifacts.
   - Done when: unit tests prove deterministic composition, graceful fallback behavior, keyframe derivation, and immutable lock updates.

3. Recipe and pipeline integration
   - Files: new `configs/recipes/recipe-animatics-generation.yaml` and `src/cine_forge/pipeline/graph.py`.
   - Change: wire the modules into a project-wide recipe, mark animatics as implemented in the pipeline graph, and correct graph dependencies if storyboards remain an optional enhancement rather than a hard prerequisite.
   - Risk: preserving a false graph dependency would mislead ADR-002 goal guidance and UI availability states.
   - Done when: an integration fixture proves `best_for_scene` selects `animatics` when animatic artifacts exist and `storyboards` when they do not.

4. Scene Workspace and Artifact Detail UI
   - Files: new dedicated UI components for animatic/keyframe/previz review, plus `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/lib/types.ts`, and `ui/src/lib/artifact-meta.ts`.
   - Change: add an Animatics scene tab that mirrors the storyboard operational loop, inline media playback for the current scene, a keyframe review/control surface with lock visibility, and dedicated artifact-detail viewers for animatic/keyframe/previz artifacts.
   - Risk: widening already-large page files or leaving lock control discoverable only through raw artifact editing.
   - Done when: a user can run, inspect, and manage animatics/keyframes from the scene workspace and inspect all three artifact types in Artifact Detail without raw JSON.

5. Shared UI language and operator feedback
   - Files: `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and any minimal call sites that surface recipe or stage names.
   - Change: add recipe names, run-start/completion copy, and stage descriptions so the new flow speaks in operator-facing language rather than raw recipe IDs.
   - Risk: shipping a usable feature with opaque copy like `animatics_generation` or missing stage messages.
   - Done when: run toasts, status labels, and stage chat updates all render clean user-facing text.

6. Verification and docs
   - Files: new/updated tests under `tests/unit/` and `tests/integration/`, this story file, and any touched docs discovered during implementation.
   - Change: add backend coverage, run static checks, run browser verification, and update documentation/work log evidence.
   - Risk: validating schema shape only while missing real playback or UI regressions.
   - Done when: required backend/UI checks pass, browser verification is recorded, and the work log is ready for `/validate`.

### Redundancy Plan

- Do not add a new media-serving endpoint if `assets/file` already serves the generated video/image/audio assets correctly.
- Do not push animatic generation logic into `storyboard_v1` or `track_system_v1`; keep the module boundaries clean and parallel to Story 026.
- Do not invent a frontend-only media schema separate from the backend artifact payloads.
- Do not rely on raw JSON edit mode as the only keyframe-lock workflow once keyframes become user-facing.
- Do not add AI-video-provider plumbing in this story unless the deterministic composition path proves insufficient under the planned tests.

### UI Verification

- Primary browser path:
  - Open Scene Workspace for a seeded scene with shot plans and storyboard artifacts.
  - Verify the new Animatics surface appears, explains prerequisites when empty, and makes the project-wide run scope explicit.
  - Start or refresh the animatics recipe, confirm the running state is understandable, then verify inline playback, keyframe review, audio-availability cues, and artifact-detail links once the run completes.
  - Toggle a keyframe lock/unlock action and confirm the UI reflects the new versioned artifact state.
- Secondary browser path:
  - Open animatic, keyframe, and previz artifacts directly in Artifact Detail and confirm they render dedicated viewers rather than raw JSON.
- Browser tools to use:
  - Screenshot for visual verification.
  - Console inspection for media/network errors.
  - Network inspection if video/audio/image asset paths fail.
- Fallback if browser automation is unavailable:
  - Run the UI lint/type/build checks, inspect the dev server manually, and record the blocker in the work log.

### Human Approval Blockers

- Scope folded into this story:
  - Scene Workspace + Artifact Detail UI for animatics/keyframes/previz.
  - Keyframe lock/unlock controls in-app.
  - Run-label / stage-copy / artifact-metadata updates.
  - Pipeline-graph dependency correction if storyboards remain optional input.
- Approach decision proposed:
  - Implement MVP animatics via deterministic ffmpeg-based composition over storyboard stills, structured timing, and available temp audio instead of AI-video generation.
- Scope increase: `M`, but still tightly coupled enough that splitting it would make validation dishonest.
- No new Python dependency is planned. If implementation later proves that a new dependency is required beyond the repo's current ffmpeg usage, pause and re-approve before adding it.

---

## Work Log

*(append-only)*

20260318-1358 — exploration + planning: confirmed Story 027 advances the Ideal's fast `generate -> react -> refine` loop and `playable assembly at every stage` requirement; consulted `docs/ideal.md`, `docs/spec.md` refs `spec:6.3`, `spec:6.4`, `spec:10.2`, and `spec:10.3`, plus `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/decisions/adr-003-film-elements/adr.md`, and dependency stories 013/025/026. Traced `src/cine_forge/pipeline/graph.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `src/cine_forge/modules/visualization/storyboard_v1/main.py`, `src/cine_forge/schemas/storyboard.py`, `src/cine_forge/api/routers/assets.py`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `ui/src/components/StoryboardPanel.tsx`, `ui/src/components/StoryboardViewer.tsx`, `ui/src/lib/artifact-meta.ts`, `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, and `ui/src/lib/types.ts`. Key findings: the repo already has a strong storyboard pattern to clone; `animatics` exists as a reserved track type and a not-yet-implemented pipeline node; asset serving already supports image/audio/video playback; and Story 027 as written would currently let backend generation land without its required UI. Scope correction folded into this story: scene-level animatic/keyframe artifacts, project-level previz reel, Scene Workspace + Artifact Detail review surfaces, and run-label/message updates. Main risk files are already large (`src/cine_forge/pipeline/graph.py` 697, `ui/src/pages/SceneWorkspacePage.tsx` 706, `ui/src/pages/ArtifactDetail.tsx` 605), so implementation should stay schema-first and add dedicated components/modules instead of inflating existing ones. Proposed approach: deterministic ffmpeg-based composition over storyboard stills, shot timing, and available temp audio, with keyframe locks versioned through immutable artifacts. Next step: get approval on the plan and scope corrections, then start implementation.
20260318-1518 — backend implementation: added schema-first animatic contracts in `src/cine_forge/schemas/animatic.py`, registered them in `src/cine_forge/{schemas/__init__.py,driver/schema_registry.py}`, and built new modules/recipe at `src/cine_forge/modules/visualization/{animatic_v1,keyframe_v1}/` plus `configs/recipes/recipe-animatics-generation.yaml`. `src/cine_forge/pipeline/graph.py` now marks `animatics` as implemented, adds `keyframes`, and treats storyboard input as optional entity-scoped enrichment instead of a project-scoped blocker. Implementation detail that changed during build: the first ffmpeg motion pass (`zoompan` over looped stills) was too slow for short shots, so the module switched to deterministic start/mid/end crops rendered as a slideshow-style segment clip. Evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_animatic_module.py tests/integration/test_animatic_integration.py -q` passed; direct smoke run of `recipe-animatics-generation.yaml` produced scene-level `animatic`, `keyframe`, and project-level `previz_reel` artifacts.
20260318-1638 — UI implementation: added dedicated viewers/panels at `ui/src/components/{AnimaticViewer.tsx,KeyframeViewer.tsx,PrevizReelViewer.tsx,AnimaticsPanel.tsx}` and wired them into `ui/src/pages/{SceneWorkspacePage.tsx,ArtifactDetail.tsx}` plus `ui/src/lib/{artifact-meta.ts,constants.ts,chat-messages.ts}`. Live browser work exposed a real usability bug: `ui/src/lib/hooks/artifacts.ts` only invalidated version-specific keys after artifact edits, so keyframe lock/unlock created a new immutable version without refreshing the Scene Workspace "latest version" links. Fixed by invalidating the full project artifact query family (and project/pipeline graph) after edits. Scope note recorded here for honesty: Story 027's MVP now owns project/scene/shot review surfaces and advisory previz behavior; explicit per-act review slices and policy-driven rigidity controls are deferred until a downstream consumer exists.
20260318-1716 — verification and handoff prep: static checks passed with the shared repo venv and freshly installed UI dependencies: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `565 passed, 132 deselected, 1 pre-existing acceptance-mark warning`; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` -> clean; `pnpm --dir ui run lint` -> 0 errors with 5 pre-existing `react-refresh/only-export-components` warnings in unrelated files; `cd ui && npx tsc -b` -> clean; `pnpm --dir ui run build` -> clean with the existing Vite chunk-size warning. Browser verification used a seeded project at `output/story-027-smoke`: started backend on `http://127.0.0.1:8000` and Vite on `http://127.0.0.1:5174`, opened `http://127.0.0.1:5174/story-027-smoke/scenes/scene_001`, switched to the Animatics tab, confirmed inline video playback and artifact-detail links, toggled the first keyframe lock/unlock control, and observed the keyframe detail href advance from `/story-027-smoke/artifacts/keyframe/scene_001/2` to `/story-027-smoke/artifacts/keyframe/scene_001/3`, proving immutable versioned edits now refresh correctly. Then opened `/story-027-smoke/artifacts/keyframe/scene_001/3` and `/story-027-smoke/artifacts/previz_reel/project/1`, confirming dedicated viewers and media playback with no browser console errors. Verification screenshots: `output/story-027-smoke/verification/{scene-animatics.png,keyframe-detail.png,previz-detail.png}`. Residual note: the seeded smoke project triggered an unrelated backend chat-role validation exception in server logs during automatic welcome-message activity, but the animatic/keyframe/previz surfaces themselves stayed functional and the browser smoke remained clean. Next step: `/validate`.
20260318-1807 — media-quality correction after manual review: inspected generated media directly instead of trusting the UI alone by extracting representative frames from `output/story-027-smoke/artifacts/animatic_media/scene_001/v1/scene_animatic.mp4` and probing the audio streams with `ffprobe` / `ffmpeg -af volumedetect`. Root causes were concrete: the compositor's `resize_cover()` path was center-cropping sparse storyboard frames into near-solid-color output, and the seeded verification asset in `tests/animatic_fixtures.py` intentionally injected a silent WAV, so the mux path was correct but the smoke project was misleading. Fixed by switching the motion-frame builder in `src/cine_forge/modules/visualization/animatic_v1/support.py` to contain-fit scaling with only modest motion/zoom, preserving the full storyboard frame, and by updating `tests/animatic_fixtures.py` to generate visually distinct seed frames plus an audible tone instead of silence. Rebuilt `output/story-027-smoke`; extracted frame inspection now shows the full seed storyboard composition instead of a flat blue field, and `ffmpeg -af volumedetect` on the rebuilt `scene_animatic.mp4` reports `mean_volume: -13.3 dB` / `max_volume: -6.0 dB`, confirming audible temp audio in the verification project. Validation rerun after the fix: targeted animatic suite `6 passed`; full unit suite unchanged-green at `565 passed, 132 deselected, 1 pre-existing acceptance-mark warning`; Ruff clean. Next step: ask the user to hard-refresh the running `story-027-smoke` route and confirm the rebuilt media behaves as expected.
20260318-1835 — follow-up quality pass after user review: replaced the remaining stepped-motion implementation with true per-frame motion generation in `src/cine_forge/modules/visualization/animatic_v1/support.py` instead of a 3-frame slideshow, so long shots are now rendered as continuous movement across the full output frame. Also replaced the synthetic test tone with a real public-domain guitar clip vendored at `tests/fixtures/media/clean_tapping_sample.ogg` (source + license recorded in `tests/fixtures/media/README.md`) and taught `tests/animatic_fixtures.py` to transcode that fixture locally before injection. Rebuilt `output/story-027-smoke`; current smoke asset name is `clean_tapping_sample.wav`, not the old fake `temp_music.wav`. Validation after the swap: Ruff clean, targeted animatic suite green, full unit suite still `565 passed, 132 deselected, 1 pre-existing acceptance-mark warning`. Next step: have the user hard-refresh the live smoke route and verify the smoother motion path and real sample clip.
20260318-1839 — fixture hardening + metadata fix: while verifying the new real sample clip, discovered that the first transcode path (`ffmpeg ... -f wav pipe:1`) produced a stream-style WAV header that Python's `wave` reader interpreted as `1073741823` frames, inflating injected-audio duration metadata to ~24,348 seconds even though `ffprobe` reported ~12.78 seconds. Fixed this in two places: `src/cine_forge/services/injected_assets.py` now rejects impossible WAV frame counts and falls back to ffmpeg decoding, and `tests/animatic_fixtures.py` now transcodes the vendored clip to a real temporary WAV file before reading bytes so the smoke fixture itself stays sane. Added a regression in `tests/unit/test_injected_assets.py` for streamed-WAV input. Next step: rerun injected-asset and animatic checks, rebuild `output/story-027-smoke`, and confirm the live artifact metadata now reports the correct sample duration.
20260318-2306 — validation: `/validate` reran the full required suite on the current diff and the story passed cleanly. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `566 passed, 132 deselected, 1 pre-existing acceptance-mark warning`; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` -> clean; targeted tests `tests/unit/test_animatic_module.py tests/integration/test_animatic_integration.py tests/unit/test_injected_assets.py tests/unit/test_pipeline_graph.py tests/unit/test_schema_registry.py` -> `54 passed`; `pnpm --dir ui run lint` -> 0 errors with 5 pre-existing react-refresh warnings in unrelated files; `cd ui && npx tsc -b` -> clean; `pnpm --dir ui run build` -> clean with the existing Vite chunk-size warning. Browser verification via Python Playwright against the running smoke project confirmed `http://127.0.0.1:5174/story-027-smoke/scenes/scene_001` renders the Animatics tab with no browser console/page errors, the first keyframe lock advances the immutable detail href from `/artifacts/keyframe/scene_001/1` to `/2`, and direct artifact pages for `/artifacts/keyframe/scene_001/2` and `/artifacts/previz_reel/project/1` render dedicated viewers. Media probe on `output/story-027-smoke/artifacts/animatic_media/scene_001/v1/scene_animatic.mp4` confirms a `10.0s` H.264/AAC file with audible stereo audio (`mean_volume: -28.5 dB`, `max_volume: -11.7 dB`). Validation judgment: the output remains intentionally symbolic and not yet rich previz, but that is within the story's accepted MVP scope; Story 137 now captures the future usefulness upgrade. Next step: `/mark-story-done`.
20260318-2312 — close-out: marked Story 027 done after validation and backlog capture of the richer-previz follow-on in Story 137. Updated the story index, unblocked Story 028 in the backlog, and prepared the changelog entry for landing. Evidence remains the validation suite and browser/media probes recorded above. Next step: `/check-in-diff`.
