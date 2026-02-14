# Story 013: Track System and Always-Playable Rule

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 7.2 (Tracks), 7.3 (Always-Playable Rule), 7.1 (Timeline Artifact — track integration)
**Depends On**: Story 012 (timeline artifact — provides base timeline structure)

---

## Goal

Implement the track system that layers different media types onto the timeline, and the always-playable rule that ensures the timeline is scrubbable at any stage of production — displaying the best available representation for each moment.

Tracks are the vertical axis of the timeline (what types of content exist), while the timeline entries from Story 012 are the horizontal axis (when things happen).

---

## Acceptance Criteria

### Track Types (Spec 7.2)
- [ ] Support for these track types (not all populated initially):
  - [ ] **Script**: screenplay text per scene/shot.
  - [ ] **Dialogue / Audio**: dialogue lines, temp audio references.
  - [ ] **Shots**: shot plan entries (populated by Story 025).
  - [ ] **Storyboards**: storyboard images (populated by Story 026).
  - [ ] **Animatics**: animatic video segments (populated by Story 027).
  - [ ] **Keyframes**: keyframe images (populated by Story 027).
  - [ ] **Generated Video**: final rendered video (populated by Story 028).
  - [ ] **Continuity Events**: state changes per scene (from Story 011).
  - [ ] **Music / SFX**: music cues, sound effects (populated by Story 022).
- [ ] Track type registry: new track types can be added without modifying core logic.
- [ ] Each track entry references an artifact and a time range within the timeline.

### Track Data Model
- [ ] Track entries are artifact references positioned on the timeline.
- [ ] Each track entry includes:
  - [ ] Track type.
  - [ ] Time range (start/end within timeline, in seconds or scene/shot references).
  - [ ] Artifact reference (what content to display).
  - [ ] Priority level (for the always-playable fallback hierarchy).
  - [ ] Status: available, pending, failed.

### Always-Playable Rule (Spec 7.3)
- [ ] The timeline is scrubbable at all times.
- [ ] For any moment, the system displays the best available representation:
  - [ ] Generated video if available.
  - [ ] Animatic if no video.
  - [ ] Storyboard if no animatic.
  - [ ] Script text if nothing else.
- [ ] Fallback priority is configurable but has sensible defaults.
- [ ] Mixed-fidelity playback: different scenes can be at different stages (scene 1 has video, scene 2 has storyboard, scene 3 has only script text).

### Track Operations
- [ ] Add content to a track (creates new timeline version).
- [ ] Query: "what's the best available content for scene X?" → returns highest-priority track entry.
- [ ] Query: "what tracks have content?" → returns track fill summary.
- [ ] Export track listing (for debugging/review).

### Schema
- [ ] `TrackEntry` Pydantic schema:
  ```python
  class TrackEntry(BaseModel):
      track_type: str
      scene_id: str
      shot_id: str | None
      artifact_ref: ArtifactRef
      start_time_seconds: float
      end_time_seconds: float
      priority: int               # Lower = higher priority for playback
      status: Literal["available", "pending", "failed"]
  ```
- [ ] `TrackManifest` schema listing all tracks and their fill status.
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for track type registry.
- [ ] Unit tests for always-playable fallback logic.
- [ ] Unit tests for mixed-fidelity scenarios.
- [ ] Unit tests for track operations (add, query).
- [ ] Integration test: timeline + track entries → playback resolution.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Track System as Extension Points
Most tracks will be empty after this story. Each downstream story populates its track:
- Story 022 → Music/SFX track
- Story 025 → Shots track
- Story 026 → Storyboards track
- Story 027 → Animatics/Keyframes tracks
- Story 028 → Generated Video track

The track system must be designed as an extension point — adding new track types should be trivial.

### Playback Is Not This Story
This story builds the data model and resolution logic. Actual visual playback (scrubbing a timeline in the UI) is part of Story 011b (Operator Console). This story ensures the data is ready for the UI to consume.

### Continuity Events Track
The continuity events track is a read-only reference layer. It shows state changes (from Story 011) on the timeline so users can see when a character's costume changes or a prop is picked up. This helps with visual continuity review.

---

## Tasks

- [ ] Design and implement `TrackEntry`, `TrackManifest` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement track type registry (extensible).
- [ ] Implement always-playable fallback resolution logic.
- [ ] Implement track operations (add content, query best available).
- [ ] Integrate track data into timeline artifact.
- [ ] Populate script track automatically from scene artifacts.
- [ ] Populate continuity events track from Story 011 data (if available).
- [ ] Write unit tests for all track operations and fallback logic.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
