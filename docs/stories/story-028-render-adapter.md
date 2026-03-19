# Story 028: Render Adapter Module

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:7.1 (Render Adapter Layer), spec:7.1.1 (Two-Part Prompt Architecture), spec:7.1.2 (Engine Packs), spec:7.1.3 (Error Handling), spec:10.2 (Tracks — generated video track)
**Depends On**: Story 025 (shot planning — shot definitions), Story 027 (keyframes — optional generation constraints), Story 022 (Sound & Music — audio intent), Story 013 (track system — video track), Story 029 (real-world asset upload + upload UX — R17 origin-agnostic inputs)

---

## Goal

Implement the **Render Adapter** — a stateless module (not a role) that translates film artifacts into model-ready generation prompts for AI video generation engines. The render adapter has no creative agency — it's a prompt compiler that optimizes for the target model's strengths and limitations.

---

## Acceptance Criteria

### Two-Part Prompt Architecture (Spec 17.1)
- [x] **Part 1 — Generic meta-prompt**: expert at producing rich AI video generation prompts from film artifacts. Model-agnostic. Focuses on quality and completeness.
- [x] **Part 2 — Model-specific engine pack**: adapts the prompt to a specific model's strengths, limits, preferred language, and supported inputs.
- [x] **Synthesis**: a single AI call combines both parts with actual creative inputs into one cohesive, model-optimized prompt.
- [x] Synthesized prompt sent to target model API along with supported inputs (keyframes, audio, reference images).

### Engine Packs (Spec 17.2)
- [x] Per-generator tuning profiles (swappable configuration files):
  - [x] Known strengths and limitations.
  - [x] Supported inputs (number of keyframes, audio support, max duration).
  - [x] Preferred prompt language and structure.
  - [x] Retry and mitigation strategies.
- [x] At least two engine packs for initial release (targeting most capable models available).
- [x] Engine pack format designed for easy addition of new models.

### Prompt Construction (ADR-003 concern groups)
- [x] Prompt compiled from upstream concern group artifacts:
  - [x] Shot definition (framing, camera, content, blocking).
  - [x] **Look & Feel** (lighting, color, composition, camera personality, costume, set design, visual motifs).
  - [x] **Sound & Music** (ambient, emotional soundscape, silence, music intent, audio motifs).
  - [x] **Character & Performance** (character emotional states, physical notes, blocking — from concern group artifacts or character bibles if formal artifacts don't exist).
  - [x] **Rhythm & Flow** (pacing, transition intent, coverage approach — from editorial direction).
  - [x] Character bible state snapshots (current appearance).
  - [x] Location bible state snapshots (current appearance).
  - [x] Keyframes (if locked, as generation constraints).
  - [x] User-injected assets / real-world assets (reference images, audio — R17).
- [x] Prompt quality verified before submission (completeness check).

### Error Handling (Spec 17.3)
- [x] Reports errors when requests exceed model capabilities:
  - [x] Duration exceeds model max.
  - [x] Required inputs not supported by target model.
  - [x] Resolution/quality beyond model capability.
- [x] Errors bubble up to pipeline — adapter does not negotiate or make creative decisions.
- [x] Cannot change creative intent.
- [x] Retry strategy per engine pack (transient failures, rate limits).

### Prompt Transparency (Ideal R12, ADR-003 Decision #4)
- [x] The synthesized generation prompt is stored as a first-class artifact alongside the generated video.
- [x] Users can view the exact prompt that produced any generated output (read-only — "the prompt is a window, not a door").
- [x] Prompts are NOT directly editable. Changes go upstream (via chat or direct artifact edit), and the prompt recompiles automatically from upstream artifacts.
- [x] "Chat about this" affordance: user can highlight any part of the displayed prompt and drop it into chat with the appropriate AI role pre-tagged for discussion.
- [x] Prompt versions are tracked — upstream changes that trigger prompt recompilation create a new version of both the prompt and the output.
- [x] Generated video and compiled prompt are reviewable from existing operator surfaces (Scene Workspace + Artifact Detail) without relying on raw JSON inspection.

### Output
- [x] Generated video segments stored as artifacts with full metadata.
- [x] Placed on generated video track in timeline (Story 013).
- [x] Cost tracking per generation (model, tokens/compute, estimated cost).
- [x] Generation parameters recorded for reproducibility.
- [x] Recipe and pipeline graph surfaces align on `generated_video` terminology rather than the legacy `render_output` placeholder.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/generation/render_adapter_v1/`
- [x] Not a role — no system prompt, no hierarchy position, no style pack.
- [x] Reads shot plans, concern group artifacts, bibles, keyframes.
- [x] Outputs generated video artifacts.

### Testing
- [x] Unit tests for prompt construction from shot definitions.
- [x] Unit tests for engine pack loading and validation.
- [x] Unit tests for capability checking (duration limits, input support).
- [x] Unit tests for error handling (capability exceeded, transient failures).
- [x] Integration test: shot plan → render adapter → prompt generation (mocked model API).
- [x] Schema validation on all outputs.

---

## Design Notes

### Not a Role
The spec is explicit: the Render Adapter is not a role. It has no opinions, no hierarchy position, and no review gates. It's a stateless prompt compiler. It doesn't decide what to generate — it decides how to ask the model to generate what the creative roles decided.

### Engine Pack Longevity
AI video generation models evolve rapidly. Engine packs are designed to be swappable so that when a new model launches, adding support is just a new configuration file + any model-specific API integration.

### Keyframe Constraints
When keyframes are locked (Story 027), they become hard constraints for the render adapter. The generation prompt must instruct the model to match the keyframe at the specified point. How well the model respects this varies by engine — the engine pack should document this.

---

## Tasks

- [x] Design generic meta-prompt (Part 1) for video generation.
- [x] Design engine pack format and schema.
- [x] Create at least two engine packs for current leading models.
- [x] Implement prompt synthesis (Part 1 + Part 2 + creative inputs).
- [x] Create `render_adapter_v1` module.
- [x] Implement model API integration layer.
- [x] Implement capability checking and error reporting.
- [x] Implement retry strategy per engine pack.
- [x] Implement video artifact storage and track placement.
- [x] Implement cost tracking per generation.
- [x] Create render recipe and align pipeline graph / fix-recipe mapping with `generated_video`.
- [x] Add generated video + compiled prompt review surfaces in Scene Workspace / Artifact Detail.
- [x] Write unit tests.
- [x] Write integration test (mocked model API).
- [x] Run required validation checks (`make` equivalent because `.venv` is absent in this worktree).
- [x] Update AGENTS.md with any lessons learned.

---

## Tenet Verification

- [x] **T0 — Data Safety:** `render_prompt` and `generated_video` stay immutable; prompt edits are blocked at the UI, API, and chat proposal boundaries, and recompilation creates new versions instead of mutating existing artifacts.
- [x] **T1 — AI-Coded:** Prompt synthesis stays AI-first while capability checks, provider payload shaping, retries, cost tracking, and lineage remain schema-backed deterministic substrate.
- [x] **T2 — Architect for 100x:** Engine packs isolate provider churn from user-facing creative artifacts, and the prompt remains compiled from upstream concern-group artifacts instead of becoming a new manual-editing surface.
- [x] **T3 — Fewer Files:** Video transport, edit policy, render viewers, and render module logic live in focused new files instead of expanding `ai/image.py`, `ArtifactViewers.tsx`, or `track_system_v1`.
- [x] **T4 — Verbose Artifacts:** The compiled prompt, generated video metadata, cost/provenance fields, validation evidence, and work log make the render path inspectable end to end.
- [x] **T5 — Ideal vs Today:** This story lands the minimal operator-visible render loop now, while leaving output-quality QA and richer previz/render fidelity follow-ons to Stories 030 and 137 instead of pretending the first cut is complete.

---

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Tenet verification complete
- [x] Doc updates complete
- [x] Story marked done via `/mark-story-done`

---

## Plan

### Scope Adjustment

- Fold two small but necessary deltas into this story:
  - align the production graph and recipe surfaces with the repo's existing `generated_video` track terminology instead of leaving the legacy `render_output` placeholder in place
  - ship the minimal operator review surfaces needed to satisfy prompt transparency; a backend-only render adapter would technically produce artifacts but still fail the story's read-only prompt-window requirement
- Do not absorb the broader stale-recipe cleanup in `ui/src/pages/ProjectRun.tsx`. Its fallback list is already behind multiple recent stories and is a repo-wide polish task, not render-specific blocking scope.

### Ideal Alignment and Eval-First Gate

- This story closes a direct Ideal gap instead of speculative infrastructure. `docs/ideal.md` requires fast `generate -> react -> refine` loops, reviewable production artifacts, and origin-agnostic creative inputs. `docs/build-map.md` still marks `spec:7` Generation & Export as `partial` and `climb`, with Story 028 as the main missing substrate.
- The prerequisite substrate now exists:
  - Story 025 landed scene-level shot plans from concern groups.
  - Story 027 landed animatics + lockable keyframes that can become hard render constraints.
  - Story 013 already reserves `generated_video` in track fallback order.
  - Story 029 landed origin-agnostic injected assets and upload UX.
- Detection/eval status:
  - there is still no dedicated registry-backed deletion or convergence eval for the render-adapter compromise
  - this story should therefore use code-level acceptance tests plus provider capability smoke evidence, while Story 030 remains the correct place for output-quality QA and agentic media inspection
- Minimal baseline on current code: `0/6` render-adapter substrate checks pass. There is no render schema, no render module, no render recipe, no registered generated-video artifact type, no prompt artifact type, and no operator review surface for generated outputs/prompts. Existing support is partial substrate only: track reservation, keyframe constraints, and upstream concern-group artifacts.
- Candidate approaches considered:
  - AI-only: one LLM call synthesizes the final prompt and the module trusts the provider to reject unsupported requests.
  - Hybrid: one LLM call synthesizes the creative prompt, while deterministic code loads engine packs, validates capabilities, assembles provider payloads, retries transient failures, stores immutable artifacts, and updates tracks.
  - Pure code: deterministic string-template prompt compilation per engine pack.
- Simplest-first probe:
  - a live single-call probe with `gpt-5.4-mini` compiled a complete render prompt from a real shot-planning fixture in one pass with no missing input categories, which confirms prompt synthesis itself does not need elaborate orchestration to work
  - live provider checks confirmed `sora-2` is accessible from the configured OpenAI key, and the configured Gemini key currently exposes `veo-2.0-generate-001`, `veo-3.0-generate-001`, `veo-3.0-fast-generate-001`, `veo-3.1-generate-preview`, and `veo-3.1-fast-generate-preview`
  - current official docs also support the initial pack choice: OpenAI's video-generation guide supports image references via `input_reference`, while Google's Veo 3.1 docs support text/image/video generation, native audio, up to three reference images, first/last-frame control, and 720p/1080p/4k variants
- Chosen approach: **hybrid**.
  - Keep creative prompt synthesis in one AI call because that already works on the first probe.
  - Keep capability checks, provider-request shaping, retry policy, artifact persistence, provenance, and track placement deterministic because those are correctness and reproducibility concerns, not creative ones.
  - Reject pure code because hard-coded render templates would freeze provider-specific lore into brittle logic and move away from the Ideal's AI-first direction.

### Repo-Fit and Optimality Evidence

- ADR and story evidence:
  - `docs/decisions/adr-003-film-elements/adr.md`: render consumes concern-group artifacts directly; prompts are a read-only window; real-world assets are first-class inputs.
  - `docs/stories/story-025-shot-planning.md`: shot planning now emits the exact per-scene / per-shot framing substrate render needs.
  - `docs/stories/story-027-animatics-previz.md`: locked keyframes are explicitly intended to become downstream render constraints.
  - `docs/stories/story-022-sound-designer.md`: silence is first-class and any engine-specific silence limitations belong in engine packs, not creative artifacts.
  - `docs/stories/story-013-track-system.md`: `generated_video` already exists as the preferred playback track when present.
  - `docs/stories/story-029-user-asset-injection.md`: injected assets must remain origin-agnostic.
- Existing implementation patterns to follow:
  - `src/cine_forge/modules/visualization/storyboard_v1/` already shows the right compile-then-provider-dispatch pattern for media generation and cost recording.
  - `src/cine_forge/modules/visualization/keyframe_v1/main.py` already shows the correct module-owned track-manifest update pattern; render should follow that instead of pushing logic into `track_system_v1`.
  - `src/cine_forge/ai/image.py` proves the repo can integrate provider APIs with thin HTTP transports and no heavyweight SDK dependency.
  - `ui/src/components/AnimaticsPanel.tsx` and existing artifact detail viewers show the correct operator loop for run -> inspect -> drill into artifact detail.
- Initial engine-pack choice for this repo:
  - implement OpenAI Sora 2 and Google Veo 3.1 first because both are live, officially documented, and currently reachable from the configured local credentials
  - do not make Runway or other providers part of the required initial scope; no Runway key is configured here, and the story acceptance criteria are already satisfied by two current leading engines
- Main alternatives rejected:
  - backend-only render adapter with later UI follow-up: violates the story's own prompt-transparency acceptance criteria and repeats the repo's historical "artifact exists but nobody can review it" failure mode
  - extending `src/cine_forge/ai/image.py` for video generation: wrong file boundary; video generation deserves a sibling transport module, not a bigger 500+ line image client
  - moving generated-video track logic into `track_system_v1`: unnecessary enlargement of an already-large module when the repo already favors producer-owned track updates

### Structural Health Check

- Current planned touch points and line counts:
  - `src/cine_forge/schemas/__init__.py` — 258 lines
  - `src/cine_forge/driver/schema_registry.py` — 102 lines
  - `src/cine_forge/pipeline/graph.py` — 708 lines, already large; keep changes surgical
  - `src/cine_forge/ai/image.py` — 509 lines, already large; do not add video logic here
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` — 599 lines, already large; do not add render-specific behavior there
  - `ui/src/pages/SceneWorkspacePage.tsx` — 734 lines, already large; only wire a focused render panel/tab into the existing structure
  - `ui/src/pages/ArtifactDetail.tsx` — 617 lines, already large; keep changes to routing / metadata / viewer selection only
  - `ui/src/components/ArtifactViewers.tsx` — 1187 lines, heavily oversized; do not add generated-video or render-prompt viewers there
  - `ui/src/lib/constants.ts` — 169 lines
  - `ui/src/lib/chat-messages.ts` — 215 lines
- Architecture constraints for the implementation:
  - add schema-first contracts before wiring module, API, or UI code; render will introduce new cross-layer artifact payloads
  - prefer new focused files such as `src/cine_forge/schemas/render.py`, `src/cine_forge/ai/video.py`, and dedicated UI viewers/components rather than growing already-large existing files
  - no new event schema is currently required
  - if any existing >100-line method needs non-trivial render logic, first task is extraction rather than in-place growth

### Task Plan

1. **Schema and engine-pack contract**
   - Files:
     - new `src/cine_forge/schemas/render.py`
     - `src/cine_forge/schemas/__init__.py`
     - `src/cine_forge/driver/schema_registry.py`
   - Change:
     - define the persisted artifact contracts for at least:
       - compiled render prompt artifact (prompt text, engine-pack id/version, upstream refs, completeness status, provider request summary)
       - generated video artifact (media file refs, duration/resolution, engine/model metadata, params, cost, provenance, linked prompt ref)
     - define or validate the pack-loader contract so engine packs can be schema-validated before use
   - Risk:
     - weak schema boundaries would leak ad hoc dict parsing into the module or UI
   - Done when:
     - artifact registry recognizes the new types and schema tests prove round-trip validation

2. **Provider client and engine packs**
   - Files:
     - new `src/cine_forge/ai/video.py`
     - new `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/` pack files
     - small helper files in `src/cine_forge/modules/generation/render_adapter_v1/` as needed
   - Change:
     - add thin provider transports for OpenAI video generation and Gemini Veo requests, following the repo's existing HTTP-wrapper style
     - create at least two engine packs for Sora 2 and Veo 3.1 with capabilities, supported inputs, duration/resolution limits, prompt-style guidance, and retry/mitigation policy
     - keep provider-specific request shaping outside the core prompt compiler
   - Risk:
     - provider APIs evolve quickly; isolating request mapping from the core module reduces future churn
   - Done when:
     - pack validation tests pass and mocked provider calls can produce normalized request/response payloads for both initial engines

3. **Render adapter module**
   - Files:
     - new `src/cine_forge/modules/generation/render_adapter_v1/main.py`
     - new `src/cine_forge/modules/generation/render_adapter_v1/module.yaml`
   - Change:
     - consume shot plans, concern groups, character/location state, locked keyframes, injected assets, and track manifest inputs
     - run one AI prompt-synthesis call per render unit using the chosen meta-prompt + engine pack + creative inputs
     - run deterministic completeness and capability checks before provider submission
     - persist both the compiled prompt artifact and generated-video artifact, then emit updated `track_manifest` entries on the `generated_video` track
   - Risk:
     - scene-level vs shot-level generation is still a judgment point from Story 025; implementation should keep the render unit explicit in config rather than baking in a hidden assumption
   - Done when:
     - a mocked integration fixture proves upstream film artifacts become immutable prompt + generated-video artifacts plus track updates

4. **Recipe, pipeline graph, and terminology alignment**
   - Files:
     - new `configs/recipes/recipe-render-generation.yaml`
     - `src/cine_forge/pipeline/graph.py`
     - affected pipeline graph tests
   - Change:
     - wire the new stage into a first-class recipe
     - add the node fix recipe mapping for the production node
     - replace the legacy `render_output` artifact placeholder with `generated_video` so the graph, recipe, schema, and track system all speak the same language
   - Risk:
     - leaving the placeholder terminology in place would create immediate drift across graph status, artifacts, and operator UI
   - Done when:
     - graph tests pass and the production node can correctly point the operator at the new recipe

5. **Operator review UI and prompt transparency**
   - Files:
     - new focused UI components for generated-video and render-prompt review
     - `ui/src/pages/SceneWorkspacePage.tsx`
     - `ui/src/pages/ArtifactDetail.tsx`
     - `ui/src/lib/artifact-meta.ts`
     - `ui/src/lib/constants.ts`
     - `ui/src/lib/chat-messages.ts`
     - `ui/src/lib/types.ts` only if a new shared payload type is required
   - Change:
     - add a render/generated-video scene surface that mirrors the existing storyboard/animatics operator loop
     - add dedicated artifact detail viewers for generated video and compiled render prompts
     - expose the prompt as read-only with chat handoff affordance, not raw JSON editing
   - Risk:
     - touching large UI files without focused components will worsen maintainability; keep new display logic in dedicated components
   - Done when:
     - a user can run render generation from the scene workflow, inspect the produced video, and inspect the exact compiled prompt from the app without leaving the normal review surfaces

6. **Verification, smoke, and cleanup**
   - Files:
     - new and existing test files around render schemas/module/graph/UI types
   - Change:
     - add unit tests for prompt compilation, pack loading, capability rejection, retry handling, and track placement
     - add mocked integration coverage for the end-to-end render path
     - run backend + UI static checks and perform a browser-based smoke pass on the render workflow
     - remove or rename any obsolete `render_output` references that remain after the new path lands
   - Risk:
     - because live video generation is paid and slow, CI-safe tests should stay mocked; any paid smoke should be minimal and deliberate
   - Done when:
     - static checks pass, mocked integration coverage is green, and the app can be exercised through the render UI path without console/API errors

### Impact Analysis and Break Risk

- Backend risks:
  - artifact registry drift if new render artifact types are added without consistent registration/export wiring
  - graph drift if `render_output` remains anywhere after the new artifact type lands
  - provider/client drift if engine-pack capability rules and request mapping are not isolated cleanly
- UI risks:
  - prompt transparency could regress into raw JSON editing if no focused render-prompt viewer is added
  - large page files could worsen quickly if new display logic is embedded directly instead of extracted
- Test impact:
  - pipeline graph unit tests will need updates
  - new schema and module unit tests are required
  - a new mocked integration fixture should cover the render path end to end

### Redundancy Plan

- Remove or rename legacy `render_output` placeholder terminology as part of this story rather than carrying both names.
- Keep video-provider transport code out of `src/cine_forge/ai/image.py`; create a sibling video client instead of a multipurpose media god file.
- Keep generated-video track updates inside the render module; do not duplicate logic inside `track_system_v1`.
- Keep new render viewers in dedicated UI files; do not expand `ui/src/components/ArtifactViewers.tsx`.

### UI Verification Plan

- Use browser tooling to verify:
  - Scene Workspace route for a seeded scene with render-capable upstream artifacts
  - generated-video playback plus prompt inspection in Artifact Detail
  - run-start / completion copy for the new recipe and stage labels
- Golden path:
  - open a project with shot plans + keyframes
  - trigger the render recipe from the scene workflow
  - confirm the generated video appears on the scene review surface
  - open the compiled prompt artifact and verify it is read-only and chat-addressable
- If browser tooling is unavailable, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

### Human-Approval Blockers / Assumptions

- No new third-party SDKs are planned. The implementation should prefer thin HTTP clients plus existing asset-store patterns.
- Initial provider scope is OpenAI + Google only. Expanding the first cut to Runway or other providers should be treated as a follow-on scope increase, not a silent addition.
- Live paid generation smoke should stay minimal and optional; mocked provider integration remains the default validation path unless you explicitly want real paid render calls exercised during implementation.

---

## Work Log

*(append-only)*

- 20260319-0910 — implementation-started: plan approved. Promoted the story to `In Progress` and started with the schema / engine-pack contract slice so new render artifacts, provider capability checks, and prompt transparency can stabilize before module wiring or UI work. Evidence: approved plan in this story, current registry gap in `src/cine_forge/driver/schema_registry.py`, and no existing render implementation under `src/cine_forge/modules/generation/`. Next step: add render schemas plus registry exports, then build the thin video-provider client and pack loader against those contracts.
- 20260319-0859 — exploration: confirmed Story 028 is `Pending` and still directly aligned to `spec:7` / build-map `climb`; inspected the render placeholder, track substrate, storyboard/animatic/keyframe producers, and current operator review surfaces; found no render schema/module/recipe/UI yet, the production graph still uses legacy `render_output`, and prompt transparency requires folding minimal Scene Workspace + Artifact Detail review into this story. Evidence: read `docs/ideal.md`, `docs/build-map.md`, `docs/spec.md`, ADR-003, Stories 013/022/025/027/029; inspected `src/cine_forge/pipeline/graph.py`, `src/cine_forge/schemas/animatic.py`, `src/cine_forge/modules/visualization/{storyboard_v1,keyframe_v1}`, `src/cine_forge/modules/timeline/track_system_v1/main.py`, `ui/src/pages/{SceneWorkspacePage,ArtifactDetail}.tsx`, `ui/src/lib/{constants,chat-messages,artifact-meta}.ts`; ran `make check-size`; live provider checks confirmed OpenAI `sora-2` access and Gemini `veo-3.1-*` availability; a single-call `gpt-5.4-mini` probe produced a complete render prompt from a real shot fixture. Next step: get plan approval, then implement schema-first render artifacts, engine packs, module wiring, and review UI.
- 20260319-1146 — implementation-complete: landed schema-first render artifacts, thin OpenAI/Google video transport, `render_adapter_v1`, two engine packs (`openai_sora2`, `google_veo31`), the `render_generation` recipe, `generated_video` graph alignment, and focused operator review surfaces for generated video + compiled prompts. Added selection-aware prompt discussion buttons and locked `render_prompt` Artifact Detail into review-only mode so prompt changes must flow upstream. Evidence: new render files under `src/cine_forge/{schemas,ai,modules/generation/render_adapter_v1}`, new recipe `configs/recipes/recipe-render-generation.yaml`, UI viewers/panel under `ui/src/components/`, and AGENTS backend-smoke fallback note.
- 20260319-1146 — verification: backend checks are green and runtime smoke succeeded on a seeded local project. Evidence: `PYTHONPATH=src pytest tests/unit/test_render_schema.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/unit/test_schema_registry.py tests/unit/test_pipeline_graph.py tests/integration/test_render_adapter_integration.py` → `50 passed`; `ruff check src/ tests/` → `All checks passed!`; `pnpm --dir ui run lint` → 0 errors with 5 pre-existing fast-refresh warnings in unrelated UI files; `pnpm --dir ui run build` → success; `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"2026.03.18-04"}`; Playwright smoke on `/render-smoke-028/scenes/scene_001` verified the new Render tab with prompt/video detail links, loaded `generated_video` + `render_prompt` artifacts with 200 API responses and no browser-console errors, and confirmed `/render-smoke-028/artifacts/render_prompt/scene_001/1` shows the compiled prompt as read-only with no `Edit` action. Next step: run `/validate` to audit the implementation against story requirements and residual risks.
- 20260319-1201 — validation: validation ran end-to-end and found two closure blockers. Evidence: required validate commands produced `make test-unit PYTHON=.venv/bin/python` → fail (`.venv/bin/python` missing), `.venv/bin/python -m ruff check src/ tests/` → fail for the same reason, story-targeted pytest suite → `50 passed in 0.67s`, `pnpm --dir ui run lint` → 0 errors / 5 pre-existing fast-refresh warnings, `cd ui && npx tsc -b` → success, `pnpm --dir ui run build` → success; Playwright verified `/render-smoke-028/scenes/scene_001` Render tab and `/render-smoke-028/artifacts/render_prompt/scene_001/1` with no console errors and no visible `Edit` action; backend runtime probe still accepted `POST /api/projects/render-smoke-028-edit-probe-validate/artifacts/render_prompt/scene_001/edit` and created `render_prompt` v2 with manual prompt text; live API reads also showed both `render_prompt/scene_001/v1` and `generated_video/scene_001/v1` immediately marked `stale`, triggered by `track_manifest:project:v2`. Recommended next step: keep the story open, block `render_prompt` edits in the backend/chat edit path, and remove `track_manifest` from render prompt/video invalidation lineage before `/mark-story-done`.
- 20260319-1212 — validation-remediation: closed both validation blockers and reran the affected checks. Added a shared artifact edit policy so backend edit routes and chat-side edit proposals now reject `render_prompt` overrides, and added artifact-specific lineage exclusions so fresh `render_prompt` / `generated_video` outputs no longer inherit `track_manifest` as a semantic upstream dependency. Evidence: `ruff check src/ tests/` → `All checks passed!`; targeted regression suite `PYTHONPATH=src pytest tests/unit/test_render_schema.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/unit/test_schema_registry.py tests/unit/test_pipeline_graph.py tests/integration/test_render_adapter_integration.py tests/unit/test_artifact_persister.py tests/unit/test_chat_artifact_edits.py` → `58 passed`; `pnpm --dir ui run lint` → 0 errors / same 5 pre-existing warnings, `cd ui && npx tsc -b` → success, `pnpm --dir ui run build` → success; direct `tests/unit/test_api.py -k edit_artifact` remained unavailable in this worktree because the active system pytest environment lacks `fastapi`, so the API path was rechecked live instead; a fresh mocked rerun on `output/render-smoke-028-fix-probe` produced `render_prompt/scene_001/v2` and `generated_video/scene_001/v2` with `health=valid`; `POST /api/projects/render-smoke-028-fix-probe/artifacts/render_prompt/scene_001/edit` now returns `422 artifact_read_only`; Playwright on `/render-smoke-028-fix-probe/artifacts/render_prompt/scene_001/2` showed `v2` as current/valid, no visible `Edit` action, and 0 browser-console errors. Next step: `/mark-story-done`.
- 20260319-1250 — closure: reran the full required close-out checks against the project virtualenv, updated the planning/docs surfaces, and marked Story 028 done. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `576 passed, 134 deselected` with one pre-existing `PytestUnknownMarkWarning` on `tests/acceptance/test_entity_discovery_verification.py`; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` → `All checks passed!`; `pnpm --dir ui run lint` → 0 errors / same 5 pre-existing fast-refresh warnings, `cd ui && npx tsc -b` → success, `pnpm --dir ui run build` → success; updated `docs/stories.md`, `docs/build-map.md`, and `CHANGELOG.md` so Story 028 is closed and `spec:7` reflects that render-adapter substrate now exists even though generated-output QA/export follow-ons remain. Next step: `/check-in-diff`.
