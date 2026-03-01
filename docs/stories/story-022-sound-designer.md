# Story 022: Sound & Music — Sound Direction

**Status**: Done
**Created**: 2026-02-13
**Reshaped**: 2026-02-27 — ADR-003 reorganizes direction types into concern groups. Sound direction → Sound & Music concern group.
**Spec Refs**: 11 (Sound Design), 12.3 (Sound & Music)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews direction), Story 005 (scene extraction)
**Ideal Refs**: R7 (iterative refinement), R11 (production readiness), R12 (transparency)

---

## Goal

Implement the **Sound & Music** concern group — everything that shapes what the audience hears. This is one of five concern groups in the ADR-003 three-layer architecture.

The Sound Designer role produces Sound & Music artifacts per scene, informed by the Intent/Mood layer. Sound design begins before shot planning (spec 11.1) — it's a creative input to visual and editorial decisions, not an afterthought.

---

## ADR-003 Context

**Before:** Sound direction was one of four role-produced direction types feeding into convergence (Story 024).

**After:** Sound & Music is a concern group. No convergence step. The Intent/Mood layer provides cross-group coherence. The Sound Designer role still produces this, but organized by creative concern (what the audience hears).

**Key changes:**
- Convergence dependency removed (024 cancelled)
- Output is a "Sound & Music" artifact
- **Silence** is a first-class element (ADR-003 Decision #3): Sound roles must actively recommend silence as a creative tool, countering AI video gen's tendency toward constant output. This is a compromise — model limitations may prevent silence from being respected in generated video, but the artifact should specify it correctly.
- Sound & Music includes: ambient/room tone, diegetic SFX, music, Foley, silence (deliberate), mixing balance, audio motifs/leitmotifs

---

## Acceptance Criteria

### Sound & Music Artifacts (per scene)
- [x] Per-scene Sound & Music specification including:
  - [x] **Ambient environment**: baseline soundscape (city noise, wind, silence, machinery hum).
  - [x] **Emotional soundscape**: how sound supports the scene's emotional arc.
  - [x] **Silence placement**: intentional absence of sound and where it falls. The Sound Designer should actively consider and recommend silence — AI video gen defaults to constant noise.
  - [x] **Offscreen audio cues**: sounds from outside the frame that expand the world or foreshadow.
  - [x] **Sound-driven transitions**: audio bridges, stingers, motifs connecting to adjacent scenes.
  - [x] **Music intent**: score direction (tension, release, theme, absence of score).
  - [x] **Diegetic vs. non-diegetic**: what sounds exist in the story world vs. for the audience only.
  - [x] **Audio motifs/leitmotifs**: recurring sound elements with thematic meaning (may reference world-level annotations).
- [x] Artifacts informed by project-wide Intent/Mood settings.
- [x] All artifacts immutable, versioned, with audit metadata.
- [x] Reviewed by Director. (via REVIEWABLE_ARTIFACT_TYPES registration)

### Sound Designer Role
- [x] Role definition with system prompt embodying sonic storytelling.
- [x] Tier: structural_advisor.
- [x] Style pack slot (accepts sound personality packs — e.g., "David Lynch").
- [x] Capability: `text`, `audio+video` (when available for audio review).

### Cross-Scene Awareness
- [x] Sound transitions (bridges, stingers) require adjacent scene context.
- [x] Sound Designer sees adjacent scenes when proposing audio transitions. (3-scene sliding window)

### Progressive Disclosure (ADR-003 Decision #2)
- [x] AI generates Sound & Music for any scene on demand. (DirectionTab "Get Sound & Music Direction" button)
- [x] User can specify any subset; AI fills the rest. (all SoundAndMusic fields optional)
- [ ] Readiness indicator: red/yellow/green. → Deferred to Story 099 (Scene Workspace)

### Sound Asset List (Spec 11.2)
- [ ] Optional: generate IRL-ready sound asset lists for real-world production workflows (R17). → Deferred to Story 098

### Testing
- [x] Unit tests for Sound & Music generation. (13 tests)
- [x] Integration test: scenes + Intent/Mood → Sound & Music artifacts. (test_run_module_with_intent_input)
- [x] Schema validation on all outputs.

---

## Design Notes

### Sound Before Shots
Sound design begins before shot planning. A scene driven by offscreen audio cues needs different coverage than a visually driven scene.

### Silence as Compromise (ADR-003 Decision #3)
Silence is specified correctly in artifacts. Whether video gen models respect it is a model capability compromise. Engine packs (Story 028) handle model-specific workarounds.

---

## Plan

Following the Look & Feel (Story 021) pattern exactly. Most infrastructure already exists from 094/095/021 — the SoundAndMusic schema, engine registration, API propagation, UI constants, and DirectionAnnotation are all wired. This story adds the module, index schema, enhanced role, recipe stage, and UI activation.

### Already Exists (no changes needed)
- `SoundAndMusic` Pydantic schema (concern_groups.py:176–218)
- `sound_and_music` registered in engine.py (line 152), pipeline graph (implemented=True), API propagation, UI constants, DirectionAnnotation
- Sound Designer role.yaml placeholder + style packs (generic, lynch)

### Implementation Order
1. **T1**: Add `SoundAndMusicIndex` schema to `concern_groups.py` (sonic terminology: overall_sonic_language, dominant_soundscape, score_arc, scenes_with_intentional_silence)
2. **T2**: Export `SoundAndMusicIndex` from `schemas/__init__.py` + register in `engine.py`
3. **T3**: Enhance `roles/sound_designer/role.yaml` with rich Sound Designer persona (silence mandate, sonic-domain specificity)
4. **T4**: Create `modules/creative_direction/sound_and_music_v1/` — __init__.py, module.yaml, main.py mirroring look_and_feel_v1 pattern (3-scene window, ThreadPoolExecutor, QA loop, mock support)
5. **T5**: Add `sound_and_music` stage to `recipe-creative-direction.yaml` with `after: [intent_mood]` + `store_inputs_optional` for intent_mood
6. **T6**: Update `pipeline/graph.py` — add `sound_and_music_index` to artifact_types, add `sound_and_music: creative_direction` to NODE_FIX_RECIPES
7. **T7**: Add `sound_and_music` to REVIEWABLE_ARTIFACT_TYPES in `engine.py`
8. **T8**: Uncomment `sound_and_music` in DirectionTab.tsx CONCERN_GROUPS + add Volume2 import
9. **T9**: Add `sound_and_music_index` to `artifact-meta.ts`
10. **T10**: Write unit tests mirroring `test_look_and_feel_module.py` — mock validation, 3-scene window, full module run, empty scenes, enrichment inputs, announce callbacks, silence mandate
11. **T11**: Run all checks (pytest, ruff, tsc -b, pnpm build)

### Key Differences from Look & Feel
- **Silence mandate**: Prompt explicitly instructs AI to recommend silence as a creative tool (ADR-003 Decision #3). Mock direction populates silence_placement. Test asserts it.
- **No bible context**: Sound Designer doesn't need character/location bibles. No `_build_bible_context`. Intent/Mood only via `store_inputs_optional`.
- **Sonic terminology**: Index fields use audio-domain language, not visual.

---

## Tasks

- [x] T1: Add SoundAndMusicIndex schema
- [x] T2: Export + register SoundAndMusicIndex
- [x] T3: Enhance Sound Designer role.yaml
- [x] T4: Create sound_and_music_v1 module (main.py, module.yaml, __init__.py)
- [x] T5: Add recipe stage
- [x] T6: Update pipeline graph (artifact_types + NODE_FIX_RECIPES)
- [x] T7: Add to REVIEWABLE_ARTIFACT_TYPES
- [x] T8: Uncomment UI concern group in DirectionTab.tsx
- [x] T9: Add sound_and_music_index to artifact-meta.ts
- [x] T10: Write unit tests
- [x] T11: Run all checks (pytest, ruff, tsc -b, pnpm build)

---

## Work Log

*(append-only)*

20260227 — Story reshaped per ADR-003. Sound direction → Sound & Music concern group. Convergence dependency (024) removed. Silence elevated as first-class element per ADR-003 Decision #3. Audio motifs added.

20260228-1430 — Implementation complete. Followed Look & Feel (Story 021) pattern exactly.

**Files created:**
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/__init__.py` — package marker
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/module.yaml` — module manifest
- `src/cine_forge/modules/creative_direction/sound_and_music_v1/main.py` — per-scene parallel analysis with 3-scene window, ThreadPoolExecutor, QA loop with escalation, mock support, silence mandate in prompt
- `tests/unit/test_sound_and_music_module.py` — 13 unit tests

**Files modified:**
- `src/cine_forge/schemas/concern_groups.py` — added SoundAndMusicIndex (sonic terminology: overall_sonic_language, dominant_soundscape, score_arc, scenes_with_intentional_silence)
- `src/cine_forge/schemas/__init__.py` — export SoundAndMusicIndex
- `src/cine_forge/driver/engine.py` — import + register SoundAndMusicIndex, add sound_and_music to REVIEWABLE_ARTIFACT_TYPES
- `src/cine_forge/pipeline/graph.py` — add sound_and_music_index to node artifact_types, add sound_and_music to NODE_FIX_RECIPES
- `src/cine_forge/roles/sound_designer/role.yaml` — enhanced from thin placeholder to rich Sound Designer persona (ambient design, emotional soundscape, silence as tool, music philosophy, transitions, motifs, offscreen audio, diegetic vs. non-diegetic)
- `configs/recipes/recipe-creative-direction.yaml` — added sound_and_music stage with after: [intent_mood] + store_inputs_optional for intent_mood
- `ui/src/components/DirectionTab.tsx` — uncommented sound_and_music entry, added Volume2 import
- `ui/src/lib/artifact-meta.ts` — added sound_and_music_index entry

**Key design decisions:**
- No bible context (unlike Look & Feel): Sound Designer depends only on scene_extraction per pipeline graph. Intent/Mood via store_inputs_optional.
- Silence mandate: Prompt contains CRITICAL section requiring AI to evaluate every scene for silence. Mock direction populates silence_placement. Dedicated test (test_mock_direction_has_silence) enforces this.
- Sonic terminology in SoundAndMusicIndex: overall_sonic_language, dominant_soundscape, score_arc, scenes_with_intentional_silence (not visual terms).

**Checks:** 428/428 unit tests pass, ruff clean, tsc -b clean, pnpm build clean.

**Deferred:**
- Readiness indicators (red/yellow/green) → Story 099 (Scene Workspace)
- Sound asset lists for real-world production → Story 098

20260228-1530 — Runtime smoke test (browser, real LLM). Triggered Sound & Music generation from Direction tab on Scene 001 (the-mariner-50 project).

**Verified end-to-end:**
- "Get Sound & Music Direction" button (primary green) triggers creative_direction pipeline run
- Operation banner: "Working on Sound & Music..." appears globally
- Chat timeline: Sound Designer announces run, per-scene streaming progress, completion summary ("13 sound & music, 1 sound and music index")
- Button transitions from "Get" (primary) → "Regenerate" (outline) as artifacts land
- All buttons disabled during run (no double-trigger)
- Zero JS console errors (only unrelated Chrome extension error)

**Artifact verification (API):**
- 13 per-scene sound_and_music artifacts (scene_001–scene_013), all health=valid
- 1 sound_and_music_index artifact, health=valid
- 1 project-level sound_and_music aggregate, health=valid

**Content quality (Scene 001 — "EXT. CITY CENTRE - NIGHT"):**
- Ambient Environment: "collapsed urban hellscape at night" — wind, subsonic rumble, fire crackles, structural percussion
- Emotional Soundscape: Arc from "vast, cold desolation" to "intimate and sinister"
- Music Intent: Cello/bass clarinet "Collapse Theme", no percussion, score stops mid-phrase
- Silence Placement: "CRITICAL SILENCE MOMENT: Immediately before the OPENING TITLE card... pull all sound to near-total silence for approximately two seconds" — ADR-003 Decision #3 working
- Offscreen Audio Cues: 7 entries (gunshots, Doppler sirens, helicopter, structural collapse, dog barking, radio static)
- Sound Driven Transitions: Cross-scene bridge to scene_002 with "German-engineered thunk" stinger — 3-scene window working
- Audio Motifs: "The Collapse Theme", "Distant Sirens", "Barrel Fire Crackle", "The German Door Thunk"
- Diegetic/Non-Diegetic: Detailed breakdown (subsonic drone is non-diegetic emotional architecture, radio static occupies "interesting middle space")

**Content quality (Scene 007 — "INT. 12TH FLOOR STAIRWELL - CONTINUOUS"):**
- Completely scene-specific: "Concrete stairwell acoustics — hard, reverberant surfaces"
- Audio Motifs: "Concrete Impact", "Rose Leitmotif", "Stairwell Reverb", "The Door Slam"
- Diegetic analysis: gun cock echoes in reverberant space, sparse piano motif is non-diegetic

**Multi-scene verification:** Navigated to Scene 007, confirmed Direction tab renders Sound & Music card with scene-specific content. All 3 role presence indicator badges present on scene heading.
