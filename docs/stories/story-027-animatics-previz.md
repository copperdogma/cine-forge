# Story 027: Animatics, Keyframes, and Previz (Optional)

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 15 (Animatics / Previz Video), 16 (Keyframes), 7.2 (Tracks — animatic/keyframe tracks), 7.3 (Always-Playable Rule)
**Depends On**: Story 025 (shot planning), Story 026 (storyboards — optional input), Story 013 (track system)

---

## Goal

Generate **animatics** (low-detail video with accurate timing and camera motion), **keyframes** (start/mid/end frames for constraining video generators), and **previz reels** (mixed storyboard + animatic timelines with temp audio). These are optional visualization stages between storyboards and final generation.

---

## Acceptance Criteria

### Animatics (Spec 15)
- [ ] Animatics at configurable granularity:
  - [ ] Per project, per act, per scene, or per shot.
- [ ] Animatic characteristics:
  - [ ] Low detail (symbolic characters and sets).
  - [ ] Accurate timing (matches shot duration estimates).
  - [ ] Accurate camera motion (reflects shot definitions).
- [ ] Placed on animatics track in timeline.
- [ ] Temp dialogue and sound included when available.

### Keyframes (Spec 16)
- [ ] Start, mid, and end frames per shot.
- [ ] Lockable by Director (once locked, keyframes constrain video generation).
- [ ] Derived from storyboards or animatics.
- [ ] Used as generation constraints for render adapter (Story 028).
- [ ] Placed on keyframes track in timeline.

### Previz Reel (Spec 15.3)
- [ ] Mixed storyboard + animatic timeline.
- [ ] Temp dialogue and sound.
- [ ] Used for review and education.
- [ ] Follows always-playable rule: fills gaps with best available representation.

### Serendipity Preservation (Spec 15.4)
- [ ] Previz is never mandatory.
- [ ] Director policy controls rigidity of previz adherence.
- [ ] Divergence from previz is explicitly allowed — previz is a guide, not a constraint.

### Module Manifests
- [ ] Module: `src/cine_forge/modules/visualization/animatic_v1/`
- [ ] Module: `src/cine_forge/modules/visualization/keyframe_v1/`
- [ ] Reads shot plan, storyboards (if available), Sound & Music concern group artifacts.
- [ ] Outputs animatic video segments and/or keyframe images.

### Schema
- [ ] `AnimaticSegment` schema (video reference, timing, shot linkage).
- [ ] `Keyframe` schema (image reference, shot position, lock status).
- [ ] `PrevizReel` schema (mixed timeline of storyboards + animatics + temp audio).
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for animatic generation logic (mocked video generation).
- [ ] Unit tests for keyframe extraction from storyboards.
- [ ] Unit tests for keyframe locking behavior.
- [ ] Unit tests for previz reel assembly.
- [ ] Integration test: shot plan → animatic/keyframe generation → track population.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Animatics vs. Storyboards
Storyboards are static images. Animatics add time and motion — they're essentially very rough video. The value of animatics is timing verification: does the scene feel too fast? Too slow? Does the camera movement work? Storyboards can't answer these questions.

### Keyframes as Generation Constraints
Keyframes are the bridge between previz and final generation. When a keyframe is locked by the Director, it becomes a constraint for the render adapter (Story 028) — the generated video must match the keyframe at that point. This gives the user creative control over the final look while letting AI handle the in-between frames.

### Cost Considerations
Animatics and keyframes involve either AI video generation (expensive) or 3D rendering (complex setup). For MVP, consider simple approaches: panning over storyboard images with camera motion simulation, or using lightweight AI video generation at very low quality/resolution.

---

## Tasks

- [ ] Design and implement `AnimaticSegment`, `Keyframe`, `PrevizReel` schemas.
- [ ] Register schemas in schema registry.
- [ ] Create `animatic_v1` module.
- [ ] Create `keyframe_v1` module.
- [ ] Implement animatic generation from shot plans.
- [ ] Implement keyframe extraction and locking.
- [ ] Implement previz reel assembly.
- [ ] Implement track integration (animatic and keyframe tracks).
- [ ] Implement serendipity controls (Director policy for previz rigidity).
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
