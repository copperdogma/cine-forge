# Story 095: Intent / Mood Layer

**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003, Synthesis §6 (Final Recommendation)
**Spec Refs**: 12.1 (Intent / Mood Layer)
**Ideal Refs**: R5 (full spectrum of involvement), R7 (iterative refinement), R11 (production readiness)
**Depends On**: Story 094 (concern group schemas), Story 014 (role system)

---

## Goal

Implement the **Intent / Mood layer** — the primary interaction surface where users describe what they want through emotion, references, and style presets. Changes in this layer auto-propagate suggested defaults to all five concern groups.

## Why (Ideal Alignment)

The Ideal says CineForge should feel like a creative conversation, not operating a pipeline. The Intent/Mood layer is how users enter that conversation. Non-filmmakers describe intent through emotion first ("tense," "dreamy"), references second ("like Blade Runner"), and sensory terms third ("dark," "grainy"). This layer speaks their language.

It also replaces the eliminated convergence step (Story 024). Cross-group coherence comes from the mood layer propagating consistent intent across all concern groups — not from a Director reviewing four separate artifacts.

Templates beat parameters (ADR-003 research finding). Style presets / "vibe" packages are the primary interaction pattern.

## Acceptance Criteria

- [x] Mood/tone selector: emotional descriptors that propagate to concern group defaults — mood chip selector with 16 quick suggestions, add/remove tags
- [x] Reference input: films, directors, aesthetic subcultures accepted as style references — tag input field for reference films
- [x] Style presets / "vibe" packages: named starting points that set coherent defaults across all five concern groups — 6 presets (Neo-Noir, Summer Indie, Documentary Realism, Gothic Horror, Ethereal Drama, Action Thriller) with per-group hints
- [x] Natural language input: "make this scene darker and tenser" parsed and routed to appropriate concern groups — textarea routed through Director during propagation
- [x] Auto-propagation: changing mood shows proposed adjustments in each concern group — Save & Propagate → expandable preview cards per concern group with field-level values and rationale
- [x] Per-scene overrides of project-wide intent — SceneIntentPanel in Direction tab shows inherited mood, Customize button, link to project intent
- [x] Works as the ONLY layer a user needs to touch for the 90/10 case — preset picker → propagate → draft artifacts created for all concern groups → readiness transitions
- [x] Warm invitation: when no intent is set but script bible exists, page shows script context (genre, tone, themes) and a one-click "Suggest a Vibe" that generates a suggested IntentMood from script analysis

## Tasks

- [x] **T1 — Style preset catalog**: 6 built-in presets as YAML files in `configs/style_presets/`. `StylePreset` model in `src/cine_forge/presets/models.py`. Loader with caching in `src/cine_forge/presets/loader.py`.
- [x] **T2 — Propagation service**: `src/cine_forge/services/intent_mood.py` — Director role prompt, `call_llm` with structured output → `PropagationResult` with per-group `PropagatedGroup` fields.
- [x] **T3 — Intent/Mood API endpoints**: 4 endpoints in `app.py` — GET/POST intent-mood, POST propagate, GET style-presets. Response models in `api/models.py`.
- [x] **T4 — Pipeline module**: `src/cine_forge/modules/creative_direction/intent_mood_v1/` — follows editorial_direction_v1 pattern, mock mode, structured LLM output.
- [x] **T5 — Project-level Intent/Mood UI page**: `ui/src/pages/IntentMoodPage.tsx` — preset picker, mood chips with suggestions, reference film tags, NL textarea, save/propagate, propagation preview cards. Route at `/:projectId/intent`, nav item in sidebar.
- [x] **T6 — Scene-level overrides**: `SceneIntentPanel` component in `DirectionTab.tsx` — shows inherited project mood, "Customize for this scene" button, links to project intent page.
- [x] **T7 — NL intent parsing**: Folded into T2 — Director receives `natural_language_intent` as part of propagation prompt context.
- [x] **T8 — Recipe + pipeline graph**: `intent_mood` stage added to `recipe-creative-direction.yaml`. `implemented=True` + `nav_route="/intent"` in graph.py. Added to `NODE_FIX_RECIPES`.
- [x] **T9 — Tests**: 17 unit tests in `tests/unit/test_intent_mood.py` — presets (7), propagation schemas (3), IntentMood schema (3), pipeline module mock mode (2), pipeline graph config (2). All 394 tests pass.
- [x] **T10 — Warm invitation UX**: Purple-accented card at top of IntentMoodPage showing script context (title, genre, tone, themes, logline) and "Suggest a Vibe" button. Appears only when no intent is set and script bible exists. User-initiated, not auto-generated.
- [x] **T11 — Suggest endpoint**: `GET /api/projects/{id}/script-context` returns ScriptContextResponse. `POST /api/projects/{id}/intent-mood/suggest` extracts mood words from tone (with stopword filtering), matches best preset by keyword overlap, returns IntentMoodSuggestion without saving. UI pre-fills form from suggestion.
- [x] **T12 — Tests for suggest flow**: 7 unit tests — ScriptContextResponse roundtrip (2), IntentMoodSuggestion roundtrip (2), mood extraction logic (1), preset matching by keyword overlap (1), no-match case (1). All 401 tests pass.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.

20260227-1430 — **Exploration Notes**

**What already exists (from 094):**
- `IntentMood` schema: `src/cine_forge/schemas/concern_groups.py` — fields: mood_descriptors, reference_films, style_preset_id, natural_language_intent, user_approved, scope, scene_id
- Pipeline node: `src/cine_forge/pipeline/graph.py` line ~183 — `intent_mood`, `implemented=False`, deps: scene_extraction
- Readiness: `src/cine_forge/schemas/readiness.py` — yellow threshold on mood_descriptors, style_preset_id, natural_language_intent
- Schema registration: `src/cine_forge/driver/engine.py`
- UI artifact-meta: `ui/src/lib/artifact-meta.ts` — Compass icon, purple-400, label "Intent & Mood"
- Direction UI: `ui/src/components/DirectionAnnotation.tsx` (generic renderer), `ui/src/components/DirectionTab.tsx` (concern group tab host — only rhythm_and_flow active, others commented out)
- Role system: Director (canon_authority), Editorial Architect, Visual Architect, Sound Designer, Story Editor — all with style packs
- Style pack infra: `src/cine_forge/roles/style_packs/` — folder-based, loaded via RoleCatalog, injected into system prompts

**Reference implementation to follow:**
- `src/cine_forge/modules/editorial_direction_v1/` — only concern group module currently implemented
- `configs/recipes/recipe-creative-direction.yaml` — recipe that runs editorial direction

**Key design decisions for 095:**
1. **Propagation = AI-generated suggestions, not artifact creation.** The propagation service returns suggested field values for each concern group. Full artifacts are created by the individual concern group modules (021, 022, etc.) or by user acceptance. This avoids 095 owning artifacts for all five groups.
2. **Style presets are NOT per-role style packs.** Presets are higher-level "vibe packages" that map to concern group defaults. They're a separate concept from the role-specific style packs in `src/cine_forge/roles/style_packs/`.
3. **Director role drives propagation.** The Director (canon_authority) is the right role to reason about cross-group coherence. It receives the IntentMood input + script bible context and produces concern group suggestions.
4. **NL parsing is a special case of propagation.** "Make this darker" → parse into mood descriptors + affected groups → propagate. Same AI pathway, different input format.

**Files that will change:**
- NEW: `src/cine_forge/modules/intent_mood_v1/` (module)
- NEW: `src/cine_forge/services/propagation.py` (or similar — propagation logic)
- NEW: `configs/style_presets/` (preset definitions)
- NEW: `ui/src/pages/IntentMoodPage.tsx` (project-level UI)
- MODIFY: `src/cine_forge/api/app.py` (new endpoints)
- MODIFY: `src/cine_forge/pipeline/graph.py` (flip implemented=True)
- MODIFY: `configs/recipes/recipe-creative-direction.yaml` (add stage)
- MODIFY: `ui/src/components/DirectionTab.tsx` (scene-level overrides)
- MODIFY: `ui/src/App.tsx` or routing (new route)
- MODIFY: `src/cine_forge/roles/director/role.yaml` (add intent_mood to permissions)

**Files at risk of breaking:**
- `src/cine_forge/schemas/readiness.py` — if IntentMood schema fields change
- `ui/src/components/DirectionAnnotation.tsx` — if new concern group types added to ConcernGroupType
- `src/cine_forge/driver/engine.py` — schema registration order
- Tests in `tests/unit/` referencing concern group schemas

20260227-2340 — **Implementation complete**

**Backend (T1-T4, T8):**
- Created `src/cine_forge/presets/` package — StylePreset model, YAML loader with caching, 6 preset files
- Created `src/cine_forge/services/intent_mood.py` — PropagationResult/PropagatedGroup schemas, Director prompt, call_llm integration
- Added 4 API endpoints to `app.py` with response models in `api/models.py`
- Created `src/cine_forge/modules/creative_direction/intent_mood_v1/` pipeline module
- Updated `graph.py`: implemented=True, nav_route="/intent", NODE_FIX_RECIPES
- Updated `recipe-creative-direction.yaml`: intent_mood stage before rhythm_and_flow
- Fixed `load_artifact` return type handling (returns Artifact model, need `.data` for dict)

**Frontend (T5-T6):**
- Created `ui/src/pages/IntentMoodPage.tsx` — full page with preset picker, mood chips, film tags, NL textarea, save/propagate, propagation preview
- Added Intent nav item to AppShell sidebar + breadcrumb support
- Added route `/:projectId/intent` in App.tsx
- Added API functions to `ui/src/lib/api.ts`
- Added `SceneIntentPanel` component to `DirectionTab.tsx` — shows inherited project mood in scene detail

**Tests (T9):**
- 17 new tests in `tests/unit/test_intent_mood.py` — all passing
- Full suite: 394 passed, 0 failed

**Verification:**
- Static: tsc -b clean, ESLint 0 errors, Ruff clean, pnpm build passes
- Runtime: API health OK, style-presets returns 6 presets, intent-mood save/load round-trip works, scene detail Direction tab shows inherited intent panel
- Screenshots: Intent page renders correctly with all sections, scene detail shows inherited mood panel with "Customize for this scene" button
- Console: 0 app errors

20260227-2355 — **Story marked Done.** All 7 ACs met, 9 tasks complete. 394 unit tests passing. Ruff, ESLint, tsc -b all clean. Runtime smoke test verified: API endpoints, UI page, scene intent panel. No gaps.

20260228-0010 — **Reopened for T10-T12 (warm invitation UX)**

Design discussion: Intent & Mood is the gateway from story work to visual/film work. When no intent is set but a script bible exists, the empty state should show what the system already knows and invite the user to step through the door — not auto-generate.

**Backend (T11):**
- Added `ScriptContextResponse` + `IntentMoodSuggestion` models to `api/models.py`
- Added `GET /api/projects/{id}/script-context` — loads script_bible artifact, extracts title/logline/genre/tone/themes
- Added `POST /api/projects/{id}/intent-mood/suggest` — deterministic mapping: extracts mood words from tone (with stopword filtering), matches best preset by keyword overlap, returns suggestion without saving
- Fixed mood word extraction to filter common stopwords (with, moments, beneath, etc.)

**Frontend (T10):**
- Added `getScriptContext()` + `suggestIntentMood()` API functions to `api.ts`
- Added `scriptContext` query and `suggestMutation` to IntentMoodPage
- Purple-accented warm invitation card placed at top of page (after PageHeader, before Style Presets)
- Shows: title, genre, tone, themes, logline quote, "Suggest a Vibe" button
- "Suggest a Vibe" calls suggest endpoint → pre-fills mood tags, preset selection, and NL intent textarea
- Falls back to generic empty state when no script bible exists

**Tests (T12):**
- 7 new unit tests: model roundtrips, mood extraction logic, preset matching by overlap, no-match case
- Full suite: 401 passed, 0 failed

**Verification:**
- Static: tsc -b clean, ESLint 0 errors, Ruff clean, pnpm build passes
- Runtime: `GET /script-context` returns title/genre/tone/themes from script bible, `POST /intent-mood/suggest` returns mood descriptors + best preset match
- Screenshot: warm invitation card renders at top of Intent page with script context, "Suggest a Vibe" populates form correctly
- Console: 0 app errors

20260228-0015 — **Story marked Done (final).** All 8 ACs met, 12 tasks complete. 401 unit tests passing. All checks clean. Runtime verified end-to-end.

20260228-0100 — **Reopened for UX improvements (user feedback)**

Based on user testing session:
1. Reference film input too small → made full-width, separated tags from input
2. "Suggest a Vibe" didn't populate reference films → fixed
3. Deterministic suggest was wrong (Documentary Realism for action-drama) → replaced with LLM call (Haiku) using structured output + full preset catalog in prompt
4. "Save & Propagate" unclear → added explanatory text, descriptive loading state, chat activity messages
5. Deep breakdown prerequisite → added gate: Intent page shows amber card explaining why bibles are needed before creative direction, with "Run Deep Breakdown" button

**Deep breakdown gate:**
- Checks `artifactGroups` for `character_bible` or `entity_graph`
- When absent: shows gate card with explanation, script context, and "Run Deep Breakdown" button (triggers world_building recipe)
- When present: shows full Intent & Mood form
- Verified via Chrome MCP screenshot: gate renders correctly with all elements, 0 console errors

**All checks pass:** 401 unit tests, Ruff clean, ESLint 0 errors, tsc -b clean, pnpm build passes.

20260228-0200 — **Continued UX improvements (user testing feedback)**

Per-operation chat feedback:
- Created `TaskProgressCard` component (`ui/src/components/TaskProgressCard.tsx`) — compact multi-item progress card for chat, reusable for any grouped operation
- Added `task_progress` message type to `ChatMessageType`
- Propagation now shows a single card with per-group spinner→checkmark transitions (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World)
- Fixed stale closure issue with propagation IDs: thread msgId through mutation return value so onSuccess always gets its own ID
- Added propagation status banner at top of IntentMoodPage when mutation is pending

Recipe-aware processing banner:
- `ProcessingView` in ProjectHome.tsx now checks `runState.state.recipe_id` for appropriate default text ("Running Deep Breakdown..." for world_building, "Running Creative Direction..." for creative_direction)

Direction dropdown fix:
- Changed 5 concern group nodes in graph.py from `implemented=False` to `implemented=True` (look_and_feel, sound_and_music, character_and_performance, story_world, rhythm_and_flow)
- Added `rhythm_and_flow` to rhythm_and_flow node's artifact_types (was only `rhythm_and_flow_index`, but propagation saves as `rhythm_and_flow`)
- Updated 2 unit tests in `test_pipeline_graph.py` to reflect new node status

Durable directive:
- Added "User Feedback Contract for Long-Running Operations" section to AGENTS.md with rules, API examples, and reference table
- Added `TaskProgressCard` and `RunProgressCard` to UI Component Registry
- Added Known Pitfall about silent long-running operations

**All checks pass:** 401 unit tests, Ruff clean, ESLint 0 errors, tsc -b clean, pnpm build passes.

20260228-0210 — **Story marked Done (final).** All 8 ACs met, 12 tasks complete. 401 unit tests passing. All checks clean. Multiple rounds of user testing feedback addressed. UX feedback contract established as durable AGENTS.md directive.
