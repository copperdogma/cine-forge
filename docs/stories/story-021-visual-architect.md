# Story 021: Look & Feel — Visual Direction

**Status**: Done
**Created**: 2026-02-13
**Reshaped**: 2026-02-27 — ADR-003 reorganizes direction types into concern groups. Visual direction → Look & Feel concern group.
**Spec Refs**: 9.2 (Visual Architect), 12.2 (Look & Feel)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews direction), Story 008 (character bibles), Story 009 (location/prop bibles), Story 011 (continuity states)
**Ideal Refs**: R7 (iterative refinement), R11 (production readiness), R12 (transparency)

---

## Goal

Implement the **Look & Feel** concern group — everything that shapes what the audience sees. This is one of five concern groups in the ADR-003 three-layer architecture.

The Visual Architect role produces Look & Feel artifacts per scene, informed by the Intent/Mood layer (project-wide style/mood settings) and constrained by entity bibles and continuity states. Look & Feel is the visual world: lighting, color, composition, camera, costume, set design, and visual motifs.

---

## ADR-003 Context

**Before (old architecture):** Visual direction was one of four role-produced direction types (editorial, visual, sound, performance) that fed into a convergence step (Story 024) before shot planning.

**After (new architecture):** Look & Feel is one of five concern groups in the Creative Concerns layer. There is no convergence step — the Intent/Mood layer provides cross-group coherence. The Visual Architect role still produces this output, but it's organized by creative concern (what the audience sees) rather than by professional role (what the Visual Architect does).

**Key changes from the original story:**
- Spec ref 12.5 (convergence) removed — Story 024 is cancelled
- Output is a "Look & Feel" artifact, not a "Visual Direction" artifact
- The artifact is informed by project-wide Intent/Mood settings (from the Intent/Mood layer)
- Visual motifs are now annotations at any scope (character, location, world-level) — not just per-scene notes

---

## Acceptance Criteria

### Look & Feel Artifacts (per scene)
- [x] Per-scene Look & Feel specification including:
  - [x] **Lighting concept**: key light direction, quality (hard/soft), motivated vs. stylized, practical sources.
  - [x] **Color palette**: dominant colors, temperature (warm/cool), saturation, contrast.
  - [x] **Composition philosophy**: symmetry, negative space, depth of field intention, framing style.
  - [x] **Camera personality**: static/controlled vs. handheld/chaotic, observational vs. intimate.
  - [x] **Reference imagery**: visual references from style pack, user-injected (R17), or AI-suggested.
  - [x] **Costume and production design notes**: what characters and environment look like, referencing bible states.
  - [x] **Visual motifs**: recurring visual elements connecting to larger themes (may reference world-level, character-level, or scene-level motif annotations).
  - [x] **Aspect ratio and format**: if scene-specific override of project-wide setting.
- [x] Artifacts informed by project-wide Intent/Mood settings (style presets, mood descriptors, reference films).
- [x] Artifacts reference continuity states from Story 011 for character/location appearance.
- [x] All artifacts immutable, versioned, with audit metadata.
- [x] Reviewed by Director.

### Visual Architect Role
- [x] Role definition with system prompt embodying visual storytelling.
- [x] Tier: structural_advisor.
- [x] Style pack slot (accepts visual personality packs — e.g., "Roger Deakins").
- [x] Capability: `text`, `image` (for reference image evaluation).

### Progressive Disclosure (ADR-003 Decision #2)
- [x] AI generates Look & Feel for any scene on demand ("let AI fill this").
- [ ] User can specify any subset of fields; AI fills the rest. *(Deferred → Story 099 Scene Workspace)*
- [ ] Readiness indicator: red (no specification), yellow (partial), green (fully specified and reviewed). *(Deferred → Story 099 Scene Workspace)*

### Testing
- [x] Unit tests for Look & Feel generation referencing bible states and Intent/Mood settings.
- [x] Integration test: scenes + bibles + Intent/Mood → Look & Feel artifacts. *(Manual end-to-end: run-6016a14f, 14 artifacts)*
- [x] Schema validation on all outputs.

---

## Design Notes

### Global Coherence via Intent/Mood
The old architecture used a convergence step (Story 024) to ensure cross-direction consistency. The new architecture achieves this through the Intent/Mood layer — project-wide mood/style settings automatically propagate as constraints to all concern groups. Look & Feel generation should read and respect these settings.

### Bible State References
Look & Feel references continuity states, not master definitions. If a character has a black eye in scene 15 (from Story 011), the Look & Feel for that scene should note it.

---

## Plan

### Architecture Summary

Follow the **editorial_direction_v1 module pattern** exactly. The Look & Feel module is a per-scene parallel analysis pipeline where the Visual Architect role processes each scene using a 3-scene sliding window, producing one `LookAndFeel` artifact per scene and one `LookAndFeelIndex` aggregate for the project.

**Key difference from Rhythm & Flow**: The Visual Architect needs richer inputs — character bibles (what characters look like), location bibles (what locations look like), and the project-level Intent/Mood artifact (to respect the director's global vision). These are loaded via `store_inputs` / `store_inputs_optional` in the recipe stage.

**Data flow**:
```
Intent/Mood (project)  ─┐
Character bibles       ─┤
Location bibles        ─┼──► Visual Architect per-scene LLM call → LookAndFeel artifact
Scene text (3-window)  ─┤
Scene metadata (tone)  ─┘
```

### What Already Exists (no changes needed)

- `LookAndFeel` schema in `concern_groups.py` — fully defined with all fields
- Schema registered in `engine.py` line 148 and exported from `__init__.py`
- `look_and_feel` pipeline node in `graph.py` with `implemented=True` and correct dependencies
- `look_and_feel` in UI `artifact-meta.ts` (Eye icon, sky-400)
- `DirectionTab.tsx` has a commented-out config entry for Look & Feel — just uncomment
- `DirectionAnnotation.tsx` already supports `look_and_feel` as a concern group type
- Visual Architect `role.yaml` exists with basic system prompt
- Intent/Mood propagation already produces `look_and_feel` field-level suggestions

### Files to Create

| File | Purpose |
|---|---|
| `src/cine_forge/modules/creative_direction/look_and_feel_v1/__init__.py` | Empty package marker |
| `src/cine_forge/modules/creative_direction/look_and_feel_v1/module.yaml` | Module manifest |
| `src/cine_forge/modules/creative_direction/look_and_feel_v1/main.py` | Per-scene parallel analysis module |
| `tests/unit/test_look_and_feel_module.py` | Unit tests (mirror editorial_direction tests) |

### Files to Modify

| File | Change |
|---|---|
| `src/cine_forge/schemas/concern_groups.py` | Add `LookAndFeelIndex` model |
| `src/cine_forge/schemas/__init__.py` | Export `LookAndFeelIndex` |
| `src/cine_forge/driver/engine.py` | Register `look_and_feel_index` schema; add `look_and_feel` to `REVIEWABLE_ARTIFACT_TYPES` |
| `src/cine_forge/pipeline/graph.py` | Add `look_and_feel_index` to node's `artifact_types`; add `look_and_feel` to `NODE_FIX_RECIPES`; add `nav_route` |
| `src/cine_forge/roles/visual_architect/role.yaml` | Enhance system prompt with rich Visual Architect persona |
| `configs/recipes/recipe-creative-direction.yaml` | Add `look_and_feel` stage with `store_inputs` for bibles + intent |
| `ui/src/components/DirectionTab.tsx` | Uncomment Look & Feel config entry |
| `ui/src/lib/artifact-meta.ts` | Add `look_and_feel_index` entry |

### Scope Boundaries

**In scope (Story 021):**
- Pipeline module: AI generates per-scene Look & Feel + project index via the driver
- Visual Architect persona enhancement
- Recipe stage wiring with bible + intent inputs
- DirectionTab integration (scene detail page shows Look & Feel annotations)
- Unit tests

**Out of scope (deferred to Story 099 — Scene Workspace):**
- Dedicated Look & Feel editing page (user edits fields directly)
- Per-scene readiness indicators (red/yellow/green)
- "Let AI fill this" per-field button
- Per-scene override UI

The readiness indicators and per-field generation buttons are Scene Workspace concerns (Story 099). Story 021 focuses on the generation engine and showing results in existing UI surfaces.

---

## Tasks

- [x] **T1**: Add `LookAndFeelIndex` schema to `concern_groups.py` — project-level visual identity aggregate (overall visual language, key motifs, color consistency, scenes with special needs)
- [x] **T2**: Register `LookAndFeelIndex` in `engine.py` and export from `__init__.py`
- [x] **T3**: Enhance Visual Architect `role.yaml` system prompt — rich persona covering lighting philosophy, color theory, camera language, composition, costume/production design, and visual storytelling
- [x] **T4**: Create `look_and_feel_v1` module directory with `module.yaml` manifest
- [x] **T5**: Implement `main.py` — per-scene parallel analysis following `editorial_direction_v1` pattern: 3-scene window, ThreadPoolExecutor, QA loop with escalation, announce callback, mock support. Key addition: inject bible summaries and Intent/Mood context into each scene prompt
- [x] **T6**: Add `look_and_feel` stage to `recipe-creative-direction.yaml` with `store_inputs` for bibles and `store_inputs_optional` for intent_mood
- [x] **T7**: Update `graph.py` — add `look_and_feel_index` to `artifact_types`, add `nav_route`, add to `NODE_FIX_RECIPES`
- [x] **T8**: Add `look_and_feel` to `REVIEWABLE_ARTIFACT_TYPES` in `engine.py`
- [x] **T9**: Uncomment Look & Feel entry in `DirectionTab.tsx` CONCERN_GROUPS array; add `look_and_feel_index` to `artifact-meta.ts`
- [x] **T10**: Write unit tests — mock validation, 3-scene window, full module run, missing inputs, empty scenes, announce callback, bible context injection
- [x] **T11**: Run backend checks (`make test-unit`, ruff) and UI checks (`pnpm lint`, `tsc -b`, `pnpm build`)

---

## Work Log

*(append-only)*

20260227 — Story reshaped per ADR-003. Visual direction → Look & Feel concern group. Convergence dependency (024) removed. Intent/Mood layer replaces convergence for cross-group coherence. Visual motifs expanded to any-scope annotations.

20260228 — **Exploration complete**. Studied editorial_direction_v1 module (the template), concern_groups.py schemas, Intent/Mood propagation, pipeline graph, recipe DSL, DirectionTab UI, and Visual Architect role definition. Key findings: LookAndFeel schema already exists with all fields; DirectionTab.tsx has commented-out Look & Feel entry ready to activate; pipeline node already exists with `implemented=True`. Missing: LookAndFeelIndex (project-level aggregate), the actual module, recipe stage, and test suite. Plan written above — 11 tasks following the established pattern exactly.

20260228 — **Implementation complete**. All 11 tasks done:
- T1-T2: `LookAndFeelIndex` schema added to `concern_groups.py`, registered in `engine.py`, exported from `__init__.py`
- T3: Visual Architect `role.yaml` enhanced with rich persona — lighting philosophy, colour theory, camera language, composition, costume/production design, visual storytelling
- T4-T5: `look_and_feel_v1` module created (`module.yaml` + `main.py`) — per-scene parallel analysis with 3-scene window, bible + Intent/Mood context injection, QA loop with escalation, mock support, announce callbacks
- T6: `look_and_feel` stage added to `recipe-creative-direction.yaml` with `store_inputs_optional` for intent_mood, character_bible, location_bible
- T7: `graph.py` updated — `look_and_feel_index` added to artifact_types, `look_and_feel` added to `NODE_FIX_RECIPES`
- T8: `look_and_feel` added to `REVIEWABLE_ARTIFACT_TYPES` in `engine.py`
- T9: Look & Feel entry activated in `DirectionTab.tsx`, `look_and_feel_index` added to `artifact-meta.ts`
- T10: 14 unit tests written and passing — mock validation, 3-scene window (first/mid/last), full module run, missing inputs, empty scenes, progressive disclosure, announce callbacks, bible context extraction, intent context extraction, enriched inputs
- T11: All checks green — 415/415 unit tests, ruff clean, tsc -b clean, UI build successful

Evidence: `pytest tests/unit/test_look_and_feel_module.py -v` → 14 passed. Full suite → 415 passed.

20260228 — **Runtime smoke test + bug fixes**. Browser-verified all changes:
- **Spinner refresh bug fix** (`chat-store.ts`): Added `resolveTaskProgress()` to `migrateMessages()` that flips `running`/`pending` task_progress items to `done` on reload. Verified: page refresh preserves green checkmarks on completed propagation cards.
- **Propagation summary message** (`IntentMoodPage.tsx`): Added `ai_status_done` message from Director after propagation completes, listing concern groups updated. Verified: message renders in chat with markdown formatting.
- **DirectionTab generalized** (`DirectionTab.tsx`): Fixed hardcoded Rhythm & Flow-only rendering to dynamically loop over all `CONCERN_GROUPS`. Now shows "Get Look & Feel Direction" button alongside Rhythm & Flow. Updated empty state text to be generic. Verified: both buttons render on Scene 001 Direction tab.
- No JS console errors from CineForge (only unrelated Chrome extension error).
- All checks green: `tsc -b` clean, `pnpm build` successful, `pnpm lint` 0 errors.

20260228 — **End-to-end pipeline integration + engine fixes**. Made direction buttons trigger real pipeline runs instead of chat messages. Fixed three issues discovered during testing:
- **DirectionTab pipeline trigger** (`DirectionTab.tsx`): Rewrote `handleGenerate()` from `askChatQuestion()` (chat message approach) to `startRun.mutateAsync()` with `recipe_id: 'creative_direction'` and `start_from: concernGroup`. Adds spinner, chat status messages, and post-run cache invalidation.
- **Recipe `needs` vs `after` fix** (`recipe-creative-direction.yaml`): Both `rhythm_and_flow` and `look_and_feel` had `needs: [intent_mood]` but their modules don't consume `intent_mood` as an input schema — they only need ordering. Changed both to `needs: []` + `after: [intent_mood]`. This avoids `_assert_schema_compatibility` failures where intent_mood's outputs don't match the downstream module's `input_schemas`.
- **Engine `start_from` wave scheduling fix** (`engine.py`): When `start_from` slices off upstream stages, `_compute_execution_waves` couldn't resolve `after` dependencies because skipped stages weren't in `already_satisfied`. Added `skipped_stages = set(execution_order) - set(ordered_stages)` to the `already_satisfied` set.
- **End-to-end verification**: Clicked "Get Look & Feel Direction" on scene_005 → pipeline run `run-6016a14f` completed successfully with 14 artifacts (13 scenes + 1 index). Direction tab renders full Look & Feel card with Camera Personality, Color Palette, Composition Philosophy, Costume Notes, Lighting Concept, Production Design Notes, Reference Imagery, and Visual Motifs. Verified on scene_001 and scene_005. "Regenerate Look & Feel" button variant renders when artifacts exist. "Review with Director" button appears. RolePresenceIndicators (blue eye icon) show on scene headers.
- No JS console errors from CineForge. All checks green: 415/415 tests, ruff clean, tsc -b clean, pnpm build OK.

20260228 — **UX polish + run tracking fix**. Addressed user feedback on direction buttons:
- **Button cursor-pointer** (`button.tsx`): Added `cursor-pointer` to the global shadcn/ui button cva base styles. All buttons now show hand cursor on hover.
- **DirectionTab run tracking** (`DirectionTab.tsx`): Rewrote `handleGenerate` to call `setActiveRun(projectId, run_id)` after starting a run. This activates the existing `useRunProgressChat` system in AppShell, which handles all chat messages (per-stage progress), the ProcessingView banner, and artifact invalidation on completion. Removed manual `ai_status` message management and local `generatingGroup` state — buttons now disable via `activeRunId` from the global chat store (stays disabled for the full duration of the run, not just the mutation call). Error-only chat message on failure.
- **Regeneration force flag** already in place from previous session (passes `force: isRegenerate` to bypass engine cache).
- Created Story 101 (Centralized Long-Running Action System) to address the systemic issue: build a `useLongRunningAction` hook so every future operation gets consistent 6-point feedback automatically.
- tsc -b clean.

20260228 — **Runtime smoke test of run tracking fix — PASS**. Browser-verified the `setActiveRun` wiring on Scene 005 Direction tab:
- Clicked "Regenerate Look & Feel" → buttons disabled with spinners ✓
- RunProgressCard appeared in chat with 3 stages (Intent Mood, Rhythm And Flow, Look And Feel) ✓
- ProcessingView banner on project home ✓
- Run completed (14 artifacts: 13 look & feel + 1 index) ✓
- Post-completion: buttons re-enabled with "Regenerate" text, no banner, chat shows green checkmarks, both direction cards render with full content ✓
- Zero JS console errors from CineForge ✓
- **Story marked Done**. All acceptance criteria met, all tasks complete, all checks green.
