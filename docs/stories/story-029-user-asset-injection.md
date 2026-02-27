# Story 029: User Asset Injection

**Status**: To Do
**Created**: 2026-02-13
**Updated**: 2026-02-27 — ADR-003 elevates real-world assets to core design principle (R17).
**Spec Refs**: 18 (User Asset Injection — being expanded per ADR-003/R17), 6.3 (Bible Artifact Structure — reference images), 2.1 (Immutability)
**Depends On**: Story 008 (character bibles — asset attachment points), Story 009 (location/prop bibles), Story 014 (role system — lock negotiation), Story 017 (suggestion/decision tracking — lock negotiation via suggestions)
**Ideal Refs**: R17 (real-world assets as first-class inputs)

---

## Goal

Allow users to inject their own real-world assets at any stage of the pipeline: actor photos, location photos, prop references, dialogue audio, style references, and any other creative material. Injected assets become part of the bible/artifact system and inform all downstream processing.

**ADR-003 / R17 context:** Real-world asset support is a core design principle, not just a feature. CineForge works for partial workflows — someone using CineForge only for previz while shooting a real film, or only for sound design, or only for storyboards. The system must be origin-agnostic: uploaded and AI-generated assets are treated identically throughout the pipeline.

---

## Acceptance Criteria

### Asset Injection
- [ ] Users can inject assets at any pipeline stage:
  - [ ] **Actor photos**: attached to character bibles, used for visual consistency in storyboards/generation.
  - [ ] **Location photos**: attached to location bibles, used for Look & Feel concern group and generation.
  - [ ] **Prop references**: attached to prop bibles.
  - [ ] **Dialogue audio**: attached to scenes, used for timing and audio track.
  - [ ] **Style references**: visual references for style packs or Look & Feel concern group.
  - [ ] **Any other file**: flexible injection with user-specified purpose.
- [ ] Injected assets stored within the relevant bible folder or artifact directory.
- [ ] Manifest updated to track injected files with `user_injected` provenance.

### Lock System (Spec 18)
- [ ] Injected assets may be:
  - [ ] **Soft-locked**: AI should respect this asset but may propose alternatives. User must approve any change.
  - [ ] **Hard-locked**: AI must use this asset exactly. Cannot be changed without user explicitly unlocking.
- [ ] Lock status stored as artifact metadata.
- [ ] AI may propose relaxing locks but may not override without approval.
- [ ] Lock negotiation:
  - [ ] Role proposes lock change with rationale.
  - [ ] Proposal goes through suggestion system (Story 017).
  - [ ] User approves or rejects.

### Asset Processing
- [ ] Image assets: validated for format and dimensions, thumbnailed for UI.
- [ ] Audio assets: validated for format and duration, waveform generated for UI.
- [ ] Assets tagged with the entity/artifact they relate to.
- [ ] Assets versioned: re-injecting a new version creates a new manifest entry.

### Downstream Integration
- [ ] Injected character photos used as reference in:
  - [ ] Look & Feel concern group (character appearance consistency).
  - [ ] Storyboard generation (character likeness).
  - [ ] Video generation (character reference images).
- [ ] Injected location photos used in Look & Feel and generation.
- [ ] Injected audio used in Sound & Music concern group, timeline tracks, and render adapter.
- [ ] Injected style references usable to seed concern group generation (e.g., upload mood board → used as Look & Feel reference).
- [ ] Lock status respected by all downstream modules.
- [ ] **Origin-agnostic**: no part of the pipeline should distinguish between uploaded and AI-generated assets. Both follow the same reference image / audio / document paths.

### Schema
- [ ] `InjectedAsset` Pydantic schema:
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
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for asset injection into bible folders.
- [ ] Unit tests for lock status enforcement.
- [ ] Unit tests for lock negotiation flow.
- [ ] Unit tests for asset validation (format, dimensions).
- [ ] Integration test: inject asset → bible manifest updated → downstream module respects asset.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Assets as First-Class Artifacts
Injected assets are not second-class attachments — they're first-class artifacts tracked by the manifest, versioned, and respected by the dependency graph. When a character photo is injected, everything that depends on that character's appearance should be flagged for potential update.

### Lock Gradients
Soft locks are the default for injected assets. They tell the AI "I prefer this, but I'm open to suggestions." Hard locks are for when the user has a specific actor in mind and won't accept substitutions. The distinction matters for generation — a hard-locked actor photo means the render adapter must include it as a reference image constraint.

---

## Tasks

- [ ] Design and implement `InjectedAsset` schema.
- [ ] Register schema in schema registry.
- [ ] Implement asset injection API (file upload → bible folder → manifest update).
- [ ] Implement lock system (soft/hard lock, unlock).
- [ ] Implement lock negotiation via suggestion system.
- [ ] Implement asset validation (format, dimensions, duration).
- [ ] Implement downstream integration hooks (Look & Feel concern group, storyboard, generation).
- [ ] Wire asset injection into Operator Console API.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
