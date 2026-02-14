# Story 026: Storyboard Generation (Optional)

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 14 (Storyboards), 7.2 (Tracks — storyboard track), 7.3 (Always-Playable Rule)
**Depends On**: Story 025 (shot planning — storyboards derived from shot plan), Story 013 (track system — storyboard track slot)

---

## Goal

Generate **storyboard frames** from the shot plan. Each storyboard frame corresponds to one or more shots and provides a cheap visual representation of the scene — useful for blocking, eyeline verification, camera intent, and creative review.

Storyboards are optional. The pipeline can skip this stage entirely and go straight to animatics or generation.

---

## Acceptance Criteria

### Storyboard Generation
- [ ] Each storyboard frame derived from a shot definition (Story 025).
- [ ] Frame includes:
  - [ ] Visual representation of the shot (character positions, camera angle, composition).
  - [ ] Shot metadata overlay (shot ID, size, angle, movement).
  - [ ] Character labels and blocking indicators.
  - [ ] Camera position/movement indicator.
- [ ] Multiple frames per scene (one per key shot in the coverage plan).

### Storyboard Styles (Spec 14.2)
- [ ] Support for multiple visual styles:
  - [ ] Sketch (rough, fast, low-detail).
  - [ ] Clean line (clear outlines, minimal shading).
  - [ ] Animation-style (simplified but visually clear).
  - [ ] Abstract color-coded (shapes and colors representing elements).
  - [ ] Photoreal (discouraged, gated — requires explicit user opt-in due to cost).
- [ ] Style selection configurable per-project or per-run.

### Image Generation Integration
- [ ] Storyboard images generated via AI image generation API.
- [ ] Generation prompt constructed from:
  - [ ] Shot definition (framing, camera, content).
  - [ ] Visual direction (lighting, color palette, composition).
  - [ ] Character descriptions from bibles.
  - [ ] Location descriptions from bibles.
  - [ ] Continuity states for character/location appearance.
- [ ] Cost tracking per frame.
- [ ] Retry logic for generation failures.

### Track Integration
- [ ] Generated storyboard frames placed on the storyboard track (Story 013).
- [ ] Always-playable rule: storyboards serve as visual representation when no animatic or video exists.
- [ ] Stored as image files within the project artifact structure.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/visualization/storyboard_v1/`
- [ ] Reads shot plan, visual direction, character/location bibles, continuity states.
- [ ] Outputs storyboard image artifacts + storyboard index.

### Testing
- [ ] Unit tests for prompt construction from shot definitions (mocked AI).
- [ ] Unit tests for style selection.
- [ ] Unit tests for track integration.
- [ ] Integration test: shot plan → storyboard module → storyboard images + index.
- [ ] Schema validation on index artifacts.

---

## Design Notes

### Storyboards as Quick Feedback
Storyboards are the cheapest visual feedback in the pipeline. They let the user see "is this roughly what I imagined?" before committing to expensive animatics or video generation. The quality bar is low — correctness of composition and blocking matters more than visual fidelity.

### Photoreal Gating
Photoreal storyboards are expensive and often unnecessary. They should be gated behind explicit user opt-in and should carry a cost warning. The default should be sketch or clean line style.

### Character Consistency
Maintaining visual consistency for characters across storyboard frames is a known challenge with AI image generation. Consider using character reference images (from user asset injection, Story 029) or style-consistent generation techniques.

---

## Tasks

- [ ] Design storyboard prompt construction from shot definitions.
- [ ] Implement style selection and configuration.
- [ ] Create `storyboard_v1` module.
- [ ] Implement AI image generation integration.
- [ ] Implement storyboard index artifact.
- [ ] Implement track integration (storyboard track).
- [ ] Implement cost tracking and photoreal gating.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
