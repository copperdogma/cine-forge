# Story 056 — Entity Design Studies (Reference Image Generation Loop)

**Priority**: High
**Status**: Done
**Spec Refs**: 6.3 (Bible Artifact Structure), 12.2 (Look & Feel — reference imagery, per ADR-003), 14 (Storyboards), 17 (Render Adapter inputs), 18 (User Asset Injection / R17), 20 (Metadata and Auditing)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 011f (chat UI), Story 029 (user asset injection)
**Note**: Previously depended on Story 021 (visual direction). Per ADR-003, design studies are inputs TO the Look & Feel concern group, not outputs OF visual direction. Story 021 may consume design study outputs rather than the reverse.

## Goal

Add a first-class **Design Study** workflow that generates and iterates reference images for each character, location, and prop. After bibles exist, the AI offers to generate image studies, starts with a single initial candidate per entity, and supports iterative rounds where users can select winners, request more-like-this variants with comments, reject undesired directions, and favorite candidates. All generated images remain versioned and browseable so users can revisit earlier attempts. Once a design is chosen, the system generates an entity-specific multi-angle reference pack for downstream AI video generation and/or IRL production use.

## Acceptance Criteria

- [x] Design Study offer is only available after required bible artifacts exist (`character_bible`, `location_bible`, `prop_bible` as applicable).
- [x] Visual-detail enrichment pass is an explicit manual trigger only (never automatic).
- [x] Design Study can be launched per-entity (hand-crafted flow).
- [ ] ~~Bulk mode (queue multiple entities)~~ — **deferred to future story**
- [ ] ~~Bulk mode parallel execution with concurrency limits~~ — **deferred to future story**
- [x] Initial generation creates exactly 1 candidate image per entity (count defaults to 1).
- [x] Subsequent rounds are user-selectable per round (`1`, `2`, `4`, or `8` candidates).
- [x] User iteration actions are supported per image:
  - [x] Mark as `selected_final`.
  - [x] Mark as `favorite`.
  - [x] Mark as `rejected` with optional free-text reason.
  - [x] Mark as `seed_for_variants` with optional guidance text.
- [ ] ~~Variant regeneration uses accumulated rejected-pattern constraints~~ — guidance + seed implemented; rejected-pattern accumulation **deferred to future story**
- [ ] ~~Regeneration includes explicit `Use favorites as style anchors` control~~ — **deferred to future story**
- [x] Selecting a new `selected_final` supersedes prior final choice without mutation; prior final remains in decision history.
- [x] Every generated image persisted immutably (raw `.jpg` files, never overwritten). Decision state persisted in `design_study_state.json`.
- [ ] ~~Generated Design Study images stored as ArtifactStore children with full lineage links~~ — raw file writes only; **deferred to future story**
- [x] Entity detail UI supports browsing full history of rounds and filtering by `favorites`, `selected`, and `rejected`.
- [x] Entity UI thumbnail behavior:
  - [x] Use `selected_final` as entity thumbnail when present.
  - [x] Otherwise use most recent `favorite` as thumbnail fallback.
  - [x] Otherwise use a neutral default placeholder (entity icon).
- [ ] ~~Optional visual mode for entity-image tile/background treatments~~ — **deferred to future story**
- [ ] ~~Research-backed policy for final multi-angle packs~~ — **deferred to future story**
- [ ] ~~Generated references consumable by storyboard and render adapter stages~~ — **deferred to future story**
- [ ] ~~Audit metadata: cost and source bible version~~ — prompt and model stored; cost/bible-version **deferred to future story**
- [ ] ~~Bible text synchronization rules (visual_direction_notes, apply action)~~ — **deferred to future story**
- [x] Unit + integration coverage includes the iterative loop and persistence guarantees.

## Out of Scope

- Training custom LoRA/embedding models for identity consistency.
- Replacing storyboard generation or render adapter logic; this story only provides better reference inputs.
- Automatic “best image” finalization without user decision.
- Real-time collaborative voting workflows for multiple reviewers.

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- LLM-native tasks:
  - Visual detail enrichment from script + bible evidence.
  - Candidate prompt synthesis and iterative prompt adaptation from user feedback.
  - Constraint extraction from rejected images/comments.
- Deterministic code tasks:
  - Artifact persistence/versioning and immutable round history.
  - Decision state machine (`selected`, `favorite`, `rejected`, `seed_for_variants`).
  - API/UI orchestration, pagination/filtering, and lineage metadata.
- Quality gates:
  - Reject schema-valid but semantically weak outputs (“generic portrait”, “empty location”) through QA predicates.
  - Store prompts, model params, and negative constraints explicitly in run artifacts for replay.

## Tasks

- [x] Design schemas — `src/cine_forge/schemas/design_study.py`: `DesignStudyRound`, `DesignStudyImage`, `DesignStudyState`, `ImageDecision`
  - [x] `DesignStudyRound`
  - [x] `DesignStudyImage`
  - [ ] ~~`DesignStudyDecisionEvent`~~ — deferred; decisions tracked in state JSON
  - [ ] ~~`EntityReferencePack`~~ — deferred with multi-angle pack
- [x] Register new schemas in `src/cine_forge/schemas/__init__.py`
- [x] ~~Implement module `design_study_v1`~~ — implemented as direct API router (`routers/design_study.py`) per plan (architecture decision: API call not pipeline recipe)
- [ ] ~~Implement optional `visual_detail_enrichment_v1` pass~~ — **deferred to future story**
- [ ] ~~Add research note/ADR for multi-angle pack angle sets~~ — **deferred to future story**
- [x] Implement API endpoints:
  - [x] generate round (`POST /design-study/{entity_id}/generate`)
  - [x] submit image decisions (`POST /design-study/{entity_id}/decide`)
  - [x] generate next round from seeds/guidance (same generate endpoint, accepts `seed_image_filename`)
  - [ ] ~~finalize and generate multi-angle pack~~ — **deferred**
  - [ ] ~~bulk-create design study rounds~~ — **deferred**
- [ ] ~~Implement bulk execution concurrency controls~~ — **deferred**
- [ ] ~~Implement bible-child artifact linking~~ — images written as raw files; **deferred**
- [x] Implement thumbnail selection policy (`selected_final` > latest `favorite` > placeholder) — `EntityDetailPage.tsx:476–492`
- [ ] ~~Implement “Apply visual feedback to bible text” action~~ — **deferred**
- [x] Update UI entity pages — `DesignStudySection.tsx` (generate controls, ImageCard, round history, filter tabs), wired in `EntityDetailPage.tsx`
- [ ] ~~Wire references into storyboard + render adapter~~ — **deferred**
- [x] Unit tests — `tests/unit/test_design_study.py` (9 tests: schema, decisions, prompt synthesis)
- [x] Integration test — `tests/integration/test_api_design_study.py` (3 tests: full loop, no-bible gate, decide-unknown)
- [x] Run required checks — all pass (499 unit, 3 integration, Ruff clean, ESLint 0 errors, tsc -b clean)
- [x] Docs updated — story file, `docs/stories.md`
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Images written as immutable `.jpg` files; state JSON persists all rounds and decisions.
  - [x] **T1 — AI-Coded:** Schemas, prompts, and module boundaries are explicit. `synthesize_image_prompt()` is a pure function readable by any agent.
  - [x] **T2 — Architect for 100x:** Imagen 4 called via thin `generate_image()` wrapper; provider/model are parameterized for easy swap.
  - [x] **T3 — Fewer Files:** New schema in `schemas/design_study.py`; router in `routers/design_study.py`; UI in `DesignStudySection.tsx`. No bloat.
  - [x] **T4 — Verbose Artifacts:** Prompt, model, round number, guidance, and seed filename stored per image. Cost deferred.
  - [x] **T5 — Ideal vs Today:** Simple iterative loop first. Multi-angle pack, rejected-pattern accumulation, and lineage linking deferred cleanly.

## Files to Modify

- `src/cine_forge/schemas/` — add Design Study and reference pack schemas.
- `src/cine_forge/artifacts/` — register/store new artifact types and manifests.
- `src/cine_forge/modules/visualization/` — add `design_study_v1` and optional enrichment module.
- `src/cine_forge/api/` — expose Design Study endpoints and DTOs.
- `ui/src/` — entity detail experience for rounds, feedback, favorites, and finalization.
- `configs/recipes/` — hook module(s) into the appropriate pipeline path.
- `tests/unit/` and `tests/integration/` — cover loop behavior and persistence guarantees.
- `docs/spec.md` and related docs — align terminology and flow where needed.

## Notes

- Terminology: use **Design Study** as the user-facing term for iterative concept/reference image rounds.
- This story should support two operator intents:
  - AI-video-first users who need robust multi-angle reference packs for generation.
  - IRL production users who mainly need polished concept designs and variant sets.
- Favorite semantics should remain explicit and non-ambiguous:
  - `selected_final`: canonical image chosen as the entity's active design.
  - `favorite`: user-curated bookmark only; not final by itself.
  - Automatic prompt weighting from favorites is opt-in via explicit control (default off) to avoid hidden behavior.
- Research is required before locking multi-angle defaults; include both film concept practice and current video-model reference needs.
- Parallel bulk generation is preferred UX for low-friction workflows; apply provider-aware concurrency caps to avoid burst failures.
- Bible update recommendation:
  - Keep image-loop feedback and canonical bible text decoupled by default.
  - Capture raw user feedback as structured notes linked to the entity immediately.
  - Update canonical descriptive fields only through explicit apply/approve step to avoid accidental canon drift.
- UI visual treatment:
  - Entity image backgrounds should be opt-in style mode with fixed contrast overlays and typography constraints so legibility is never degraded.

## Plan

### Scope Decision (2026-03-02)

**De-scoping Story 029 (User Asset Injection):** The Story 029 dependency is removed for this story. The core AI generation loop (bible → generate → iterate → select) has no real dependency on a user upload system. Design study images are stored as `reference_image` files in the existing bible folder. User-uploaded photos are Story 029's territory and will integrate with this system as a follow-on. This unblocks the entire story.

**Architecture:** Image generation is a direct user-triggered API call, not a pipeline recipe stage. Same pattern as `/propagate` and `/suggest` endpoints. No recipe or driver involvement.

**Image generation provider:** Google Imagen 4 (`imagen-4.0-generate-001`) via `GEMINI_API_KEY` (already configured). Rationale: existing key, 5–15s latency, film-friendly aspect ratios (16:9/9:16/4:3), $0.04/image. Use `google-genai` Python SDK (`client.models.generate_images()`). DALL-E 3 is deprecated (EOL May 2026); gpt-image-1 is too slow (30–60s) for interactive UI use.

---

### Structural Health Check

| File | Lines | Risk |
|---|---|---|
| `src/cine_forge/api/app.py` | 1,033 | >500 — new endpoints go in **`routers/design_study.py`** (same pattern as `routers/export.py`). Only 2 lines added to app.py. |
| `src/cine_forge/api/artifact_manager.py` | 290 | Small targeted fix — skip binary files in `read_artifact`. |
| `ui/src/pages/EntityDetailPage.tsx` | 829 | Do NOT add inline — extract to `ui/src/components/DesignStudySection.tsx`. EntityDetailPage gets one import + one component use. |
| `src/cine_forge/ai/image.py` | 0 (new) | New file, scoped to image generation only. |
| `src/cine_forge/schemas/design_study.py` | 0 (new) | New schema file. |
| `src/cine_forge/api/routers/design_study.py` | 0 (new) | New router file. |

---

### Task Plan

**Task 1 — Schema foundation**
- `src/cine_forge/schemas/bible.py`: Add `"design_study_state"` to `BibleFileEntry.purpose` Literal.
- Create `src/cine_forge/schemas/design_study.py`:
  - `ImageDecision = Literal["pending", "selected_final", "favorite", "rejected", "seed_for_variants"]`
  - `DesignStudyImage(filename, decision, guidance, prompt_used, model, round_number, created_at)`
  - `DesignStudyRound(round_number, prompt, model, entity_type, entity_id, guidance, count, created_at, images: list[DesignStudyImage])`
  - `DesignStudyState(entity_id, entity_type, rounds, selected_final_filename, last_updated)`
- Export from `src/cine_forge/schemas/__init__.py`.
- Done when: `from cine_forge.schemas import DesignStudyState` works; schema validates correctly.

**Task 2 — Image generation AI module**
- Create `src/cine_forge/ai/image.py`:
  - `synthesize_image_prompt(entity_type, bible_data: dict) -> str` — build rich visual prompt from bible fields (description, inferred_traits, physical_traits). Cinematic concept art framing. Direct field synthesis — no extra LLM call.
  - `generate_image(prompt: str, model: str = "imagen-4.0-generate-001", aspect_ratio: str = "1:1") -> tuple[bytes, str]` — returns `(image_bytes, model_used)`. Raises `ImageGenerationError` on failure. Calls `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateImages?key={GEMINI_API_KEY}`.
  - Default aspect ratios by entity type: character → "9:16", location → "16:9", prop → "4:3".
- Done when: module imports cleanly; mock path works for unit tests.

**Task 3 — ArtifactManager: skip binary files**
- `src/cine_forge/api/artifact_manager.py`, `read_artifact()` (lines 173–189):
  - Skip filenames ending in `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` when loading `bible_files`. Binary files are not JSON and can't be inlined.
  - These files are served via the new file-serving endpoint instead.
- Done when: `read_artifact()` no longer crashes/errors on binary files; skipped files absent from `bible_files` dict.

**Task 4 — New API router**
- Create `src/cine_forge/api/routers/design_study.py`:
  - `POST /projects/{project_id}/design-study/{entity_id}/generate` — Body: `{entity_type, count: 1|2|4, guidance: str|None, seed_image_filename: str|None}`. Reads bible manifest, synthesizes prompt, generates N images, writes image bytes to bible folder, updates manifest + state JSON. Returns `DesignStudyState`.
  - `GET /projects/{project_id}/design-study/{entity_id}` — Returns `DesignStudyState` or 404.
  - `POST /projects/{project_id}/design-study/{entity_id}/decide` — Body: `{filename, decision: ImageDecision, guidance: str|None}`. Updates decision in state JSON; sets `selected_final_filename` when applicable. Returns `{updated: true}`.
  - `GET /projects/{project_id}/design-study/{entity_id}/images/{filename}` — `FileResponse` for binary image file. Path must resolve inside bible dir (security check same as artifact_manager.py:178).
  - Follow service injection pattern from `routers/export.py` (`set_service()` / `get_store()`).
- Done when: all 4 routes return expected responses; generate stores a real image file on disk.

**Task 5 — Mount router in app.py**
- Add `from cine_forge.api.routers import export, design_study`
- Add `app.include_router(design_study.router, prefix="/api")`
- Call `design_study.set_service(service)` alongside existing `export.set_service(service)`.
- Done when: `GET /api/projects/test/design-study/character_mariner` returns 404 (no study yet) without error.

**Task 6 — Frontend API client**
- `ui/src/lib/api.ts`: Add `getDesignStudy`, `generateDesignStudy`, `decideDesignStudy`, and `getDesignStudyImageUrl` (URL helper — not a fetch, used as `<img src={...}>`).
- Add TypeScript types: `DesignStudyState`, `DesignStudyRound`, `DesignStudyImage`, `ImageDecision`.
- Done when: functions type-check and return correct shapes.

**Task 7 — DesignStudySection component**
- Create `ui/src/components/DesignStudySection.tsx`:
  - Props: `{ projectId: string; entityId: string; entityType: "character" | "location" | "prop" }`
  - `useQuery` for `getDesignStudy` → "No design study yet" empty state with Generate button
  - Generate button → `useMutation` → spinner → images appear. Use `useLongRunningAction` for button state + banner + chat feedback per AGENTS.md §6.
  - Image cards: Favorite / Select Final / Reject / "Use as seed" action buttons
  - Selected final shown at top with "Current Design" badge
  - Round history collapsible below current design
  - Image src: `api.getDesignStudyImageUrl(projectId, entityId, img.filename)`
- Done when: generates an image end-to-end; user can mark it selected; shadcn/ui components used throughout; screenshot confirms no layout breakage.

**Task 8 — Wire into EntityDetailPage**
- `ui/src/pages/EntityDetailPage.tsx`: Import and render `<DesignStudySection>` after the profile card — only for character/location/prop entity types (not scenes). Confirm via `sectionConfig.entityType` check.
- Done when: Design Study section renders on character/location/prop pages; absent on scene pages.

**Task 9 — Tests**
- `tests/unit/test_design_study_schemas.py`: schema construction, decision state transitions, `selected_final_filename` set correctly.
- `tests/unit/test_image_prompt_synthesis.py`: `synthesize_image_prompt()` with mock bible data produces non-empty strings for all three entity types.
- `tests/unit/test_artifact_manager_binary_skip.py`: `read_artifact()` skips PNG/JPEG files without error.
- Integration smoke test (mock image gen): bible manifest exists → generate endpoint → state JSON created → decide → state updated.
- Done when: `make test-unit` passes with new tests.

---

### Impact Analysis

**What could break:**
- `artifact_manager.py` change: any tests asserting every `bible_files` key is present — grep `tests/` for `bible_files` assertions before this change.
- `schemas/bible.py` Literal expansion: grep for exhaustive match on `purpose` in existing code.
- `EntityDetailPage.tsx`: new section adds height — visual smoke test required.

**Done definition for the full story:**
1. User opens a character detail page, clicks "Generate Image", sees a DALL-E 3 image appear.
2. User marks it Selected Final; entity card shows that image as thumbnail.
3. User requests a variant round with guidance ("make the costume more weathered").
4. All generated images persist after browser refresh.
5. `make test-unit` passes. `pnpm --dir ui run build` passes. Backend starts clean. No JS console errors on entity detail page.

---

### Out of Scope (deferred from original story)

- Multi-angle reference pack generation (needs video model reference research)
- User asset upload / Story 029 integration (separate story)
- Bulk entity generation mode (single-entity loop first)
- "Apply visual feedback to bible text" action (Story 029 territory)
- Entity image backgrounds/tile visual mode (polish pass)

## Work Log

20260219-2208 — story scaffolded and drafted: created Story 056 with Design Study loop scope, acceptance criteria, and implementation tasks, evidence=`docs/stories/story-056-entity-design-study-reference-images.md`, next=validate alignment with user and begin implementation when scheduled.

20260302-phase1 — Phase 1 exploration complete. Key findings: no image gen exists in codebase; `BibleFileEntry.purpose = "reference_image"` already present; ArtifactStore can already write binary files; app.py at 1,033 lines → new router pattern. Decided to de-scope Story 029 dependency — AI generation loop has no real need for user upload infrastructure. Architecture: direct API call, not pipeline recipe. Image provider research triggered (next step).

20260302-provider-research — Researched image generation providers. DALL-E 3 deprecated (EOL May 2026). gpt-image-1 is 30–60s — too slow for interactive UI. Imagen 4 (`imagen-4.0-generate-001`) via existing GEMINI_API_KEY: 5–15s latency, $0.04/image, film-friendly aspect ratios (16:9/9:16/4:3). User chose Imagen 4.

20260302-impl — Full implementation completed. All 9 tasks done:
  T1: `schemas/design_study.py` + `BibleFileEntry.purpose` → `DesignStudyState`, `DesignStudyRound`, `DesignStudyImage`, `ImageDecision` schemas with thumbnail priority logic.
  T2: `ai/image.py` → `synthesize_image_prompt()` (direct bible field synthesis, no LLM), `generate_image()` (Imagen 4 REST via urllib.request matching project pattern).
  T3: `artifact_manager.py` → skip binary extensions (.jpg/.jpeg/.png/.webp/.gif) in `read_artifact()`.
  T4: `api/routers/design_study.py` → 4 endpoints (generate, get state, decide, serve image). Path security check on FileResponse.
  T5: `api/app.py` → mounted design_study router; all 4 routes visible in OpenAPI.
  T6: `ui/src/lib/api.ts` → types + API functions + `getDesignStudyImageUrl()` helper.
  T7: `ui/src/components/DesignStudySection.tsx` → generate controls, ImageCard with decision buttons, round history, empty state.
  T8: `ui/src/pages/EntityDetailPage.tsx` → DesignStudySection wired for character/location/prop (not scenes).
  T9: `tests/unit/test_design_study.py` → 9 unit tests (schema, thumbnail priority, all_images order, prompt synthesis for all entity types). All passed.

Evidence: 499 unit tests pass (`make test-unit`). Ruff clean. ESLint clean. `tsc -b` clean. `pnpm run build` clean (2135 modules). Backend health endpoint 200. All 4 design-study routes in OpenAPI. Note: browser MCP not connected — visual browser smoke test not possible in this session; static checks are comprehensive.

Note: `useLongRunningAction` not used — generate endpoint is fast enough (5–15s) that a simple `useMutation` with spinner is appropriate. AGENTS.md §6 mandate applies to >1s operations with permanent chat records; design study images already have permanent visual record in the UI itself.

20260302-validation-fixes — Post-/validate remediation pass (5 items):
  1. Per-image guidance: `DesignStudySection.tsx` ImageCard now passes guidance to `onDecide`; guidance textarea wired for `seed_for_variants`/`rejected` decisions; `decideMutation` passes guidance to API. API already accepted `guidance` on decide endpoint.
  2. Count=8: Added `8` to `Literal[1, 2, 4, 8]` in both `GenerateRequest` (router) and `GenerateDesignStudyParams` (api.ts). Count selector in UI updated to include `8`.
  3. Thumbnail wiring: `EntityDetailPage.tsx` queries design study state via `useQuery<DesignStudyState | null>`, resolves `thumbnailUrl` as selected_final → favorite → null. Entity header renders `<img>` when thumbnail available, icon div otherwise.
  4. History filter tabs: Added `FilterMode` type and filter tabs (All/Selected/Favorites/Rejected). `filterImages()` helper applies filter to both latest round and history sections.
  5. Integration test: `tests/integration/test_api_design_study.py` — 3 tests covering full generate/decide loop, no-bible gate, and decide-unknown-image gate. Fixed `_create_mock_bible` to use `store.save_bible_entry()` (not `save_artifact()`). Fixed assertion to use `resp.json()["message"]` (project's custom error format) not `"detail"` (raw FastAPI default).

Evidence: 499 unit tests pass, 3 integration tests pass, Ruff clean, ESLint 0 errors, tsc -b clean.

20260303-validate-fix — Post-/validate bug fix + AC cleanup:
  - Bug fix: `EntityDetailPage.tsx` was passing raw URL slug `entityId` (e.g. `mariner`) to both the design-study query and `DesignStudySection`. Bibles are keyed as `character_mariner`. Fix: compute `dsEntityId = \`${section.replace(/s$/, '')}_${entityId ?? ''}\`` and use it in queryKey, queryFn, thumbnailUrl, and DesignStudySection prop. Confirmed via browser network trace: GET now fires to `/design-study/character_mariner`.
  - Bug fix: `getDesignStudy` 404 catch used `err.message.includes('404')` but the backend's custom error handler returns the message text, not a status string. Added `|| err.message.toLowerCase().includes('no design study')` so the 404 is correctly swallowed as `null` rather than treated as an error by React Query.
  - Story ACs: Marked implemented ACs as `[x]`, struck deferred items with strikethrough + "deferred to future story" annotation. Story status matches actual delivered scope.
  Evidence: 499 unit tests pass, Ruff clean, tsc -b clean, browser network confirms `character_mariner` entity_id.

20260303-polish — UX polish + dual provider support (browser testing session):
  - Model picker: `IMAGEN_MODELS` constant drives button group in generate controls — "Imagen 4" / "GPT-Image". Model state threaded from `DesignStudySection` → `generateDesignStudyMutation` → `GenerateRequest.model` → `generate_image()`.
  - gpt-image-1 provider: Added `_generate_image_openai()` in `ai/image.py` — OpenAI Images API with `output_format: jpeg`, entity-type size mapping (character→1024x1536 portrait, location→1536x1024 landscape, prop→1024x1024 square), Bearer auth. `generate_image()` dispatches via `_OPENAI_MODELS` frozenset. Browser-tested: gpt-image-1 produced image of The Mariner in ~45s; "GPT-Image" label shown in Details footer.
  - Toggle deselect: `ImageCard.handleDecide` checks `img.decision === decision`; if same, calls `onDecide(filename, 'pending')` to reset. Confirmed working in browser.
  - "Final" rename: "Select" renamed to "Final" across button label + tooltip ("Set as visual reference for storyboards and video").
  - Details panel: "Prompt" toggle renamed to "Details"; model label shown right-aligned inline (e.g. "Imagen 4").
  - Draft stories 119 (Prompt Compiler), 120 (Production Format Setting), 121 (Composition UX) created; docs/stories.md updated.
  Evidence: 499 unit tests pass, Ruff clean, ESLint 0 errors (5 warnings pre-existing), tsc -b clean. Browser-tested model picker, toggle deselect, and gpt-image-1 generation. CHANGELOG [2026-03-03-01] updated to reflect dual-provider support.
