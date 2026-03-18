# Story 029: User Asset Injection

**Status**: Done
**Created**: 2026-02-13
**Updated**: 2026-03-14 — Closed after revalidation; backend substrate, Operator Console upload UX, and downstream propagation all landed.
**Spec Refs**: spec:7.2 (User Asset Injection — being expanded per ADR-003/R17), spec:3.3 (Bible Artifact Structure — reference images), spec:1.1 (Immutability)
**Depends On**: Story 008 (character bibles — asset attachment points), Story 009 (location/prop bibles), Story 014 (role system — lock negotiation), Story 017 (suggestion/decision tracking — lock negotiation via suggestions)
**Ideal Refs**: R17 (real-world assets as first-class inputs)
**Absorbs**: Story 098 (Real-World Asset Upload Pipeline — merged 2026-03-14)

---

## Goal

Allow users to inject their own real-world assets at any stage of the pipeline: actor photos, location photos, prop references, dialogue audio, style references, and any other creative material. Injected assets become part of the bible/artifact system and inform all downstream processing.

**ADR-003 / R17 context:** Real-world asset support is a core design principle, not just a feature. CineForge works for partial workflows — someone using CineForge only for previz while shooting a real film, or only for sound design, or only for storyboards. The system must be origin-agnostic: uploaded and AI-generated assets are treated identically throughout the pipeline.

**Usability rule (2026-03-14):** This is not complete until the Operator Console exposes the upload and management flow. Backend/API-only injection is infrastructure, not a usable user feature.

---

## Acceptance Criteria

### Asset Injection
- [x] Users can inject assets at any pipeline stage:
  - [x] **Actor photos**: attached to character bibles, used for visual consistency in storyboards/generation.
  - [x] **Location photos**: attached to location bibles, used for Look & Feel concern group and generation.
  - [x] **Prop references**: attached to prop bibles.
  - [x] **Dialogue audio**: attached to scenes, used for timing and audio track.
  - [x] **Style references**: visual references for style packs or Look & Feel concern group.
  - [x] **Any other file**: flexible injection with user-specified purpose.
- [x] Injected assets stored within the relevant bible folder or artifact directory.
- [x] Manifest updated to track injected files with `user_injected` provenance.

### Lock System (Spec 18)
- [x] Injected assets may be:
  - [x] **Soft-locked**: AI should respect this asset but may propose alternatives. User must approve any change.
  - [x] **Hard-locked**: AI must use this asset exactly. Cannot be changed without user explicitly unlocking.
- [x] Lock status stored as artifact metadata.
- [x] AI may propose relaxing locks but may not override without approval.
- [x] Lock negotiation:
  - [x] Role proposes lock change with rationale.
  - [x] Proposal goes through suggestion system (Story 017).
  - [x] User approves or rejects.

### Asset Processing
- [x] Image assets: validated for format and dimensions, thumbnailed for UI.
- [x] Audio assets: validated for format and duration, waveform generated for UI.
- [x] Assets tagged with the entity/artifact they relate to.
- [x] Assets versioned: re-injecting a new version creates a new manifest entry.

### Operator Console Upload UX (merged from Story 098)
- [x] Upload UI: drag-and-drop or file picker for images, video, audio, and documents on the relevant Operator Console surfaces.
- [x] Upload flows exist on the current entity detail pages (`/:projectId/characters/:entityId`, `/:projectId/locations/:entityId`, `/:projectId/props/:entityId`), scene workspace (`/:projectId/scenes/:entityId`), and a project-level surface for project-wide style references.
- [x] Uploaded assets automatically associate with the active target (character, location, prop, scene, or project) without manual path entry.
- [x] Uploaded assets appear in the same reference image / audio browsers as AI-generated assets rather than a separate attachment silo.
- [x] Users can inspect thumbnail/waveform previews, provenance, lock state, and open the original file from the Operator Console.
- [x] Supported formats surfaced end-to-end in the product: common image (JPEG, PNG, WEBP), video (MP4, MOV), audio (WAV, MP3, AAC), document (PDF, TXT).
- [x] Bulk upload support exists for repeated reference sets (e.g., location scout photos, mood-board images).

### Downstream Integration
- [x] Injected character photos used as reference in:
  - [x] Look & Feel concern group (character appearance consistency).
  - [x] Existing downstream modules receive origin-agnostic reference paths so storyboard/render layers can consume them when those stories land.
- [x] Injected location photos used in Look & Feel and existing downstream reference propagation.
- [x] Injected audio used in Sound & Music concern group and timeline tracks.
- [x] Injected style references usable to seed concern group generation (e.g., upload mood board → used as Look & Feel reference).
- [x] Lock status respected by all downstream modules.
- [x] **Origin-agnostic**: no part of the pipeline should distinguish between uploaded and AI-generated assets. Both follow the same reference image / audio / document paths.

### Schema
- [x] `InjectedAsset` Pydantic schema:
  ```python
  class InjectedAsset(BaseModel):
      asset_id: str
      filename: str
      asset_type: Literal["image", "audio", "video", "document", "other"]
      purpose: str
      entity_type: str | None       # "character", "location", "prop", None
      entity_id: str | None
      lock_status: Literal["soft_locked", "hard_locked", "unlocked"]
      file_path: str
      file_size_bytes: int
      injected_at: datetime
  ```
- [x] `InjectedAssetManifest` Pydantic schema records versioned target-level asset state.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for asset injection into bible folders and scene/project target directories.
- [x] Unit tests for lock status enforcement.
- [x] Unit tests for lock negotiation flow.
- [x] Unit tests for asset validation (format, dimensions, duration/waveform).
- [x] Integration test: inject asset → manifest updated → downstream module respects asset.
- [x] Schema validation on all outputs.

---

## Design Notes

### Assets as First-Class Artifacts
Injected assets are not second-class attachments — they're first-class artifacts tracked by the manifest, versioned, and respected by the dependency graph. When a character photo is injected, everything that depends on that character's appearance should be flagged for potential update.

### Lock Gradients
Soft locks are the default for injected assets. They tell the AI "I prefer this, but I'm open to suggestions." Hard locks are for when the user has a specific actor in mind and won't accept substitutions. The distinction matters for generation — a hard-locked actor photo means the render adapter must include it as a reference image constraint.

---

## Tasks

- [x] Design and implement `InjectedAsset` and `InjectedAssetManifest` schemas.
- [x] Register new schemas in the schema registry.
- [x] Implement shared asset-injection service (storage, validation, thumbnails/waveforms, manifest persistence).
- [x] Implement asset injection API (file upload → target folder → manifest update).
- [x] Implement lock system (soft/hard lock, unlock).
- [x] Implement lock negotiation via suggestion system.
- [x] Implement asset validation (format, dimensions, duration).
- [x] Implement downstream integration hooks for currently implemented modules (Look & Feel, Sound & Music, track manifest).
- [x] Wire asset injection into Operator Console API.
- [x] Extract reusable asset upload / asset browser UI components before adding logic to oversized pages.
- [x] Implement Operator Console upload/manage UI on entity detail pages, scene workspace, and a project-level surface.
- [x] Add UI API client / React Query hooks / types for asset injection, listing, file fetch, lock updates, and proposal responses.
- [x] Merge uploaded assets into the existing reference browsing surfaces (`DesignStudySection` and related viewers) instead of creating a separate attachment silo.
- [x] Implement bulk upload and explicit format/lock affordances in the Operator Console.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Run `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`.
- [x] Run browser verification for the merged upload flow.
- [x] Update AGENTS.md with any lessons learned.

---

## Workflow Gates

- [x] Exploration notes captured in work log
- [x] Plan added to story
- [x] Scope adjustment reviewed and folded into implementation
- [x] Story 098 merged into Story 029
- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Tenet verification complete
- [x] Doc updates complete
- [x] Story marked done via `/mark-story-done`

## Plan

### Scope Adjustment

This story's original downstream acceptance criteria named storyboard generation, video generation, and the render adapter. Those modules do not exist in the current repo, so literal integrations there would be fake completeness. The repo-fit implementation is:

- deliver the origin-agnostic asset layer now
- wire it into the modules that already exist (`look_and_feel_v1`, `sound_and_music_v1`, `track_system_v1`)
- preserve file paths and typed schemas so storyboard/render stories can consume the same references later

That keeps Story 029 aligned with ADR-003/R17 without inventing placeholder adapters.

### Scope Merge (2026-03-14)

Story 098's upload/manage UX is now part of this story. The backend/API slice landed first, but that split produced a user-facing feature with no user-facing surface. Keep Story 029 open until the Operator Console exposes upload, preview, lock management, and unified reference browsing on top of the landed API.

### Repo-Fit / Optimality Evidence

- `docs/ideal.md` R17 and ADR-003 both require real-world assets to be first-class and origin-agnostic.
- R17 is user-facing, not infrastructure-only. Delivering only API routes for real-world assets does not satisfy the "partial workflow" promise in practice.
- Story 008 and Story 009 already established folder-based bibles with manifests; entity asset uploads should reuse those folders rather than create a separate asset silo.
- Story 017 already gives us immutable suggestions and decisions; lock negotiation should reuse that path instead of inventing a bespoke approval system.
- Story 056 deliberately deferred storyboard/render wiring, which confirms that this story should land the shared asset substrate first.
- This is storage/orchestration work, not a reasoning problem, so direct code is the simplest approach. No AI-only or hybrid alternative would reduce complexity here.

### Structural Health Check

- `make check-size` run on 2026-03-14.
- Existing large files touched by this story:
  - `src/cine_forge/api/app.py` — 1032 lines. Limit changes to router registration.
  - `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` — 626 lines. Keep changes helper-driven and narrow.
  - `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — 598 lines. Keep changes helper-driven and narrow.
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` — 541 lines. Add deterministic track enrichment only.
  - `src/cine_forge/schemas/concern_groups.py` — 462 lines. Only add typed reference fields if needed.
  - `ui/src/pages/EntityDetailPage.tsx` — 874 lines. Extract upload/reference widgets before adding asset UI here.
  - `ui/src/pages/ProjectHome.tsx` — 742 lines. Do not pile project-level upload UI directly into the page body without extraction.
  - `ui/src/pages/SceneWorkspacePage.tsx` — 676 lines. Add scene upload flow via extracted components, not inline.
- Smaller files likely to change:
  - `src/cine_forge/api/artifact_manager.py` — 296 lines
  - `src/cine_forge/api/models.py` — 368 lines
  - `src/cine_forge/schemas/suggestion.py` — 52 lines
  - `src/cine_forge/roles/suggestion.py` — 236 lines
  - `ui/src/components/DesignStudySection.tsx` — 488 lines
  - `ui/src/lib/api/projects.ts` — 102 lines
  - `ui/src/lib/hooks/projects.ts` — 136 lines
- New data crossing layer boundaries will be defined in schema files first (`InjectedAsset`, `InjectedAssetManifest`, and any concern-group additions).
- No new driver events are planned, so `schemas/events.py` is not implicated.

### Task Order

1. Story / schema foundation
   - Keep this story's workflow gates and scope correction current.
   - Add injected-asset schemas and register them.
   - Extend suggestion payloads only if structured lock-change proposals need it.

2. Shared asset service
   - Add a reusable service that resolves target folders (entity bible, scene, project), validates uploads, writes immutable files, generates image thumbnails and WAV waveforms, and persists versioned asset manifests.
   - Reuse existing bible manifests for character/location/prop folders by appending `user_injected` file entries with `user_injected` provenance.

3. API surface
   - Add router-based endpoints instead of growing `api/app.py`.
   - Support inject, list/read, direct lock updates, lock-change proposals, and proposal responses.
   - Keep the backend API thin and reusable; the Operator Console upload flow in this same story should sit directly on top of these routes.

4. UI decomposition + upload UX
   - Extract reusable upload / asset-list / preview widgets before touching oversized pages.
   - Add upload/manage flows to `EntityDetailPage`, `SceneWorkspacePage`, and a project-level surface (`ProjectHome` or a closely related component).
   - Add typed API client + React Query hooks for inject/list/file/lock/proposal flows.
   - Build a unified `Reference Library` UX for entity pages that browses uploaded assets and design-study outputs together instead of adding a separate attachment box.
   - Keep `DesignStudySection` as the AI generation / curation surface, but make the current design-study system explicit:
     - uploaded assets appear in the same browsing surface as AI-generated references
     - selected/favorite design-study images are visibly part of the active reference stack
     - `seed_for_variants` becomes an actual generation input in the UI by passing `seed_image_filename` on new rounds
     - copy must accurately reflect the current backend reality: design-study "seed" support is prompt-guided variation, not true image-conditioning from arbitrary uploads
   - Scene and project surfaces should reuse the same upload/reference components, with target-specific copy and presets rather than one-off forms.
   - Support drag/drop, multi-select upload, clear format guidance, and direct lock/provenance affordances.
   - Audio cards must show duration plus waveform previews; image cards must show thumbnails; videos and documents must remain openable from the same library.

5. Downstream hooks
   - Extend Look & Feel to surface injected/project/entity image refs in `reference_imagery`.
   - Extend Sound & Music to surface injected audio refs in a typed field.
   - Extend track manifest generation to emit scene audio track entries when scene-level audio assets exist.
   - Preserve origin-agnostic file paths so future storyboard/render code reads the same references.

6. Verification
   - Unit tests: schema/service validation, lock negotiation, concern-group integration, track enrichment.
   - Integration tests: API upload flow, manifest versioning, suggestion-backed lock proposal acceptance.
   - UI checks: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`.
   - Browser verification: upload from the entity detail pages and scene workspace, inspect previews, change lock state, and confirm the same asset appears in the reference browsing surfaces.
   - Run backend checks plus a runtime smoke test against `/api/health`.

### Redundancy Plan

- Do not introduce a second asset storage model. Reuse bible folders for entity assets and deterministic target folders for scene/project assets.
- Do not create a bespoke approval system. Reuse the existing suggestion/decision artifact flow.
- Do not add placeholder storyboard/render hooks; typed reference propagation is the handoff point.

## Work Log

*(append-only)*

20260314-1015 — exploration: audited `build-story` instructions, `docs/ideal.md` R17, `docs/spec.md` §18, ADR-003, Stories 008/009/014/015/017/056/098, and the current code paths for bible manifests, design study, concern groups, track manifests, and suggestion persistence; result=`Story 029 is repo-aligned but its downstream ACs overreach the currently landed modules`; evidence=`docs/ideal.md`, `docs/spec.md`, `docs/decisions/adr-003-film-elements/adr.md`, `docs/stories/story-008-character-bible.md`, `docs/stories/story-017-suggestion-decision-tracking.md`, `docs/stories/story-056-entity-design-study-reference-images.md`, `src/cine_forge/schemas/bible.py`, `src/cine_forge/api/routers/design_study.py`, `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py`, `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`; next=`record scope adjustment, then implement shared asset schemas/service/router`.

20260314-1022 — planning: ran `make check-size`, confirmed `api/app.py`, `look_and_feel_v1`, `sound_and_music_v1`, `track_system_v1`, and `schemas/concern_groups.py` are the structural watchpoints, and wrote a backend-first plan that reuses bible folders plus the suggestion system instead of inventing parallel storage/approval stacks; evidence=`make check-size`, `wc -l src/cine_forge/api/app.py src/cine_forge/api/artifact_manager.py src/cine_forge/api/models.py src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py src/cine_forge/modules/timeline/track_system_v1/main.py src/cine_forge/schemas/concern_groups.py src/cine_forge/schemas/suggestion.py src/cine_forge/roles/suggestion.py`; next=`implement schema + service foundation`.

20260314-1148 — implementation: added `InjectedAsset` / `InjectedAssetManifest` schemas plus structured suggestion payloads, built `InjectedAssetService` for target resolution, bible/scene/project storage, image thumbnails, WAV waveform generation, versioned asset manifests, direct lock updates, and suggestion-backed lock negotiation, then exposed it via a new asset router and registered it in the API app; evidence=`src/cine_forge/schemas/injected_asset.py`, `src/cine_forge/schemas/suggestion.py`, `src/cine_forge/services/injected_assets.py`, `src/cine_forge/api/routers/assets.py`, `src/cine_forge/api/app.py`, `src/cine_forge/artifacts/store.py`; next=`wire downstream consumers and verify full backend checks`.

20260314-1212 — downstream integration: connected injected references into current consumers by enriching `LookAndFeel.reference_imagery`, adding `SoundAndMusic.reference_audio_assets`, teaching `track_system_v1` to emit scene audio track entries from injected manifests, and hardening artifact browsing to skip non-text bible children; evidence=`src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py`, `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `src/cine_forge/schemas/concern_groups.py`, `src/cine_forge/api/artifact_manager.py`; next=`run targeted + full backend verification`.

20260314-1238 — verification: created a local Python 3.12 `.venv`, installed the repo plus dev dependencies, ran targeted coverage (`tests/unit/test_injected_assets.py`, `tests/unit/test_look_and_feel_module.py`, `tests/unit/test_sound_and_music_module.py`, `tests/unit/test_track_system_module.py`, `tests/unit/test_schema_registry.py`, `tests/integration/test_api_asset_injection.py`) → `47 passed`, ran `make test-unit PYTHON=.venv/bin/python` → `528 passed, 123 deselected`, ran `.venv/bin/python -m ruff check src/ tests/` → clean, and did a live runtime smoke with `PYTHONPATH=src .venv/bin/python -m uvicorn cine_forge.api.app:app --host 127.0.0.1 --port 8010` plus `curl http://127.0.0.1:8010/api/health` → `{"status":"ok","version":"2026.03.14-03"}`; next=`hand off for /validate`.

20260314-1305 — scope-merge: user review correctly rejected backend-only asset injection as an unusable user feature; merged Story 098 (upload UX) into Story 029, reopened the build-complete gate, and added explicit Operator Console upload/manage acceptance criteria plus UI tasks so this story now tracks the end-to-end deliverable; evidence=`docs/stories/story-029-user-asset-injection.md`, `docs/stories/story-098-real-asset-upload.md`, `.agents/skills/create-story/SKILL.md`, `ui/src/pages/EntityDetailPage.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/components/DesignStudySection.tsx`; next=`build the Operator Console upload/manage UI on top of the landed asset API`.

20260314-1418 — planning: designed the UI as a shared `Reference Library` instead of an attachment sidebar, because Story 029 is supposed to be origin-agnostic and the existing AI image generation flow already lives on entity pages; result=`entity pages pair upload/manage + design-study generation, while scene/project pages reuse the same library with target-specific presets`; evidence=`docs/ideal.md`, `docs/spec.md`, `docs/decisions/adr-003-film-elements/adr.md`, `ui/src/pages/EntityDetailPage.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/components/DesignStudySection.tsx`; next=`implement extracted asset hooks/components and wire them into the Operator Console routes`.

20260314-1536 — implementation: added typed asset API clients + React Query hooks, extracted reusable upload/browser UI (`ReferenceLibrarySection`, `AssetWaveform`, `EntityReferenceStudio`), wired project/scene/entity surfaces, and integrated the current AI image generation system by making design-study picks part of the same reference stack and passing `seed_image_filename` when `seed_for_variants` is selected; result=`users can upload files where they work, browse uploaded and AI-generated references together, preview thumbnails/waveforms, update lock state, and generate follow-on design-study rounds from the latest curated seed image`; evidence=`ui/src/lib/api/assets.ts`, `ui/src/lib/hooks/assets.ts`, `ui/src/components/assets/ReferenceLibrarySection.tsx`, `ui/src/components/assets/AssetWaveform.tsx`, `ui/src/components/assets/EntityReferenceStudio.tsx`, `ui/src/components/DesignStudySection.tsx`, `ui/src/pages/EntityDetailPage.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/ProjectHome.tsx`, `src/cine_forge/services/injected_assets.py`; next=`run repo checks plus browser verification on entity, scene, and project routes`.

20260314-1610 — verification: ran `make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`; ran `.venv/bin/python -m pytest tests/integration/test_api_asset_injection.py` → `2 passed`; ran `.venv/bin/python -m ruff check src/ tests/` → clean; ran `pnpm --dir ui run lint` (only pre-existing fast-refresh warnings), `cd ui && npx tsc -b`, and `pnpm --dir ui run build` → pass; browser-tested the merged flow on `http://127.0.0.1:5176/brick-steel-full-retired/characters/brick_braddock`, `http://127.0.0.1:5176/brick-steel-full-retired/scenes/scene_001`, and `http://127.0.0.1:5176/brick-steel-full-retired`, including live image/audio uploads and unified reference browsing; evidence=`tmp/story-029-entity-reference-studio.png`, `tmp/story-029-scene-reference-stack.png`, `tmp/story-029-project-home.png`; next=`remove console-noise rough edges and rerun the browser smoke on a fresh backend`.

20260314-1619 — polish: changed `GET /api/projects/{project_id}/assets/{target_kind}/{target_id}` to return an empty manifest instead of a 404 when a valid target has no injected assets yet, added a regression test, restarted the backend, and re-verified the project/entity routes on a fresh Vite + uvicorn pair; result=`clean targets now render their empty state without failed-network noise in the console`; evidence=`src/cine_forge/api/routers/assets.py`, `src/cine_forge/services/injected_assets.py`, `src/cine_forge/schemas/injected_asset.py`, `tests/integration/test_api_asset_injection.py`, `http://127.0.0.1:5177/brick-steel-full-retired`, `http://127.0.0.1:5177/brick-steel-full-retired/characters/brick_braddock`; next=`hand off to /validate with the story still In Progress per build-story protocol`.

20260314-1734 — polish: removed the staged “choose files, then confirm upload” flow from the Operator Console reference uploader after live user review showed it was both confusing and visually unstable; result=`file picker and drag/drop now upload immediately using the current purpose/lock defaults, the transient pending-batch UI is gone, and successful uploads surface instantly in the reference grid with toast feedback`; evidence=`ui/src/components/assets/ReferenceLibrarySection.tsx`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `http://127.0.0.1:5178/brick-steel-full-retired/characters/brick_braddock`; next=`continue validation on the cleaner single-step upload flow`.

20260314-2058 — polish: compacted the reference browser after live review showed the grid was spending space on repeated source badges, repeated purpose labels, and inline controls that obscured the actual references; result=`uploaded cards now lead with a compact filename for fast version disambiguation, purpose is demoted to supporting text, card footers are gone, lock editing moved into the preview dialog, AI cards keep only the decision badge plus round/model context, and the upload rail collapsed into a single browse/drop target with an edit-defaults popover that stays stable even with chat open`; evidence=`ui/src/components/assets/ReferenceLibrarySection.tsx`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `tmp/reference-library-pass3-top.png`, `tmp/reference-library-pass3-cards.png`, `http://127.0.0.1:5183/brick-steel-full-retired/characters/brick_braddock`; next=`continue visual validation on adjacent scene/project reference surfaces if more density tuning is needed`.

20260314-2114 — validation: reran the full backend/UI check suite and browser-verified the entity, scene, and project reference-library routes on a fresh `8013`/`5183` pair; result=`all required checks passed and the merged upload/reference flow works live, but Story 029 should stay open because the new shared browser is implemented as a 400+ line React component that violates the repo method-size rule and the client still carries an obsolete 404 empty-manifest fallback`; evidence=`make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`, `.venv/bin/python -m ruff check src/ tests/`, `.venv/bin/python -m pytest tests/unit/test_injected_assets.py tests/unit/test_look_and_feel_module.py tests/unit/test_sound_and_music_module.py tests/unit/test_track_system_module.py tests/unit/test_schema_registry.py tests/integration/test_api_asset_injection.py` → `50 passed`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `tmp/story-029-validate-scene.png`, `tmp/story-029-validate-project.png`, `http://127.0.0.1:5183/brick-steel-full-retired/characters/brick_braddock`, `http://127.0.0.1:5183/brick-steel-full-retired/scenes/scene_001`, `http://127.0.0.1:5183/brick-steel-full-retired`; next=`split ReferenceLibrarySection into focused hooks/subcomponents, remove the stale 404 manifest fallback, then re-run /validate before /mark-story-done`.

20260314-2135 — remediation: resolved the two validation findings by removing the obsolete client-side 404/null manifest fallback and decomposing the reference browser into focused hooks/components so the main section and newly extracted methods stay under the repo's size limit; result=`ReferenceLibrarySection is now a thin orchestration component, upload/defaults/preview/browser responsibilities are split into dedicated files, and the asset API client now trusts the backend's empty-manifest contract instead of masking future regressions`; evidence=`ui/src/lib/api/assets.ts`, `ui/src/components/assets/ReferenceLibrarySection.tsx`, `ui/src/components/assets/useReferenceLibraryViewModel.ts`, `ui/src/components/assets/ReferenceLibraryBrowserPanel.tsx`, `ui/src/components/assets/ReferenceLibraryUploadPanel.tsx`, `ui/src/components/assets/ReferenceLibraryPreviewDialog.tsx`, `make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `http://127.0.0.1:5183/brick-steel-full-retired/characters/brick_braddock`, `http://127.0.0.1:5183/brick-steel-full-retired/scenes/scene_001`, `http://127.0.0.1:5183/brick-steel-full-retired`; next=`re-run /validate to confirm the previous findings are cleared, then /mark-story-done if clean`.

20260314-2150 — revalidation: re-ran the mandatory backend/UI checks after the decomposition pass and re-verified the entity, scene, and project routes on the same `8013`/`5183` pair; result=`the previous validation findings are cleared and Story 029 is ready for /mark-story-done, with browser evidence captured via Playwright CLI screenshots because the MCP browser could not launch against the local Chrome profile`; evidence=`make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm --dir ui exec playwright screenshot --device='Desktop Chrome' --wait-for-timeout 6000 http://127.0.0.1:5183/brick-steel-full-retired/characters/brick_braddock ...`, `pnpm --dir ui exec playwright screenshot --device='Desktop Chrome' --wait-for-timeout 6000 http://127.0.0.1:5183/brick-steel-full-retired/scenes/scene_001 ...`, `pnpm --dir ui exec playwright screenshot --device='Desktop Chrome' --wait-for-timeout 6000 http://127.0.0.1:5183/brick-steel-full-retired ...`; next=`run /mark-story-done for Story 029`.

20260314-2155 — close-out: marked Story 029 Done after the remediation/revalidation pass cleared the previous structural and stale-client findings, updated the story index, and recorded the shipped feature in the changelog; result=`Story 029 now tracks the actual end-to-end asset injection delivery rather than stopping at backend infrastructure, and the next repo step is diff review rather than more story work`; evidence=`docs/stories/story-029-user-asset-injection.md`, `docs/stories.md`, `CHANGELOG.md`, `make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`, `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`; next=`/check-in-diff`.

20260314-2205 — post-close validation: reran the `validate` skill after closure from the current worktree state; result=`checks remain green, the route-level browser probe passed with no console errors, and the earlier closure still stands`; evidence=`git status --short`, `git diff --stat`, `make test-unit PYTHON=.venv/bin/python` → `530 passed, 124 deselected`, `.venv/bin/python -m ruff check src/ tests/`, `.venv/bin/python -m pytest tests/unit/test_injected_assets.py tests/unit/test_look_and_feel_module.py tests/unit/test_sound_and_music_module.py tests/unit/test_track_system_module.py tests/unit/test_schema_registry.py tests/integration/test_api_asset_injection.py` → `50 passed`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm dlx @playwright/test@1.58.0 test -c tmp/browser-smoke story029-validate.spec.ts --reporter=line` → `3 passed`, `tmp/browser-smoke/story029-entity-reference-library.png`, `tmp/browser-smoke/story029-scene-reference-stack.png`, `tmp/browser-smoke/story029-project-references.png`; next=`/check-in-diff`.
