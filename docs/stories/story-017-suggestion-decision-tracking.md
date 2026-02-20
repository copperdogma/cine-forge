# Story 017: Suggestion and Decision Tracking

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 8.5 (Suggestion System), 8.6 (Inter-Role Communication — decisions), 2.6 (Explanation Mandatory), 20 (Metadata & Auditing)
**Depends On**: Story 014 (role system foundation), Story 015 (Director and Canon Guardians — decision authority)

---

## Goal

Implement the suggestion and decision tracking system. Roles continuously generate insights and proposals. Not all are acted on immediately. The system captures, tracks, and surfaces suggestions as a creative backlog — and records all decisions with full audit metadata.

---


NOTE: We need to retain ALL agent proposals, even if they are not accepted. This is for debugging and learning purposes as well as giving the user to ability to go revisit a past decision or an idea they remember being suggested.


## Acceptance Criteria

### Suggestion Artifacts (Spec 8.5)
- [ ] Every suggestion is an immutable artifact with:
  - [ ] **Source role**: who proposed it.
  - [ ] **Related artifact**: scene, entity, or artifact the suggestion is about.
  - [ ] **Proposal**: what is being suggested.
  - [ ] **Confidence and rationale**: why, and how confident.
  - [ ] **Lifecycle status**: proposed, accepted, rejected, deferred, superseded.
- [ ] Suggestion lifecycle transitions:
  - [ ] `proposed` → `accepted`: folded into canon, produces a new artifact version.
  - [ ] `proposed` → `rejected`: declined, reason recorded.
  - [ ] `proposed` → `deferred`: starred for later.
  - [ ] `proposed`/`deferred` → `superseded`: a newer suggestion replaced this one.
  - [ ] Each transition is recorded with who made the decision and why.

### Deferred Suggestion Resurfacing
- [ ] Deferred suggestions are resurfaced when their related scene or entity comes up for revision.
- [ ] Resurfacing is automatic: when a scene is re-extracted or a bible entry is updated, related deferred suggestions are flagged for review.

### Decision Artifacts (Spec 8.6)
- [ ] Explicit decision artifacts recording:
  - [ ] What was decided.
  - [ ] By whom (role or human).
  - [ ] Why (rationale).
  - [ ] What alternatives were considered.
  - [ ] What suggestions informed the decision.
  - [ ] Links to affected artifacts.
- [ ] Decisions are immutable and versioned.

### Suggestion Browsing
- [ ] API to browse and search suggestions:
  - [ ] Filter by role, artifact, status, confidence.
  - [ ] Sort by recency, confidence, relevance.
  - [ ] View suggestion history for a specific artifact.
- [ ] Aggregate statistics: total suggestions, acceptance rate per role, deferred backlog size.

### Schema
- [ ] `Suggestion` Pydantic schema:
  ```python
  class Suggestion(BaseModel):
      suggestion_id: str
      source_role: str
      related_artifact_ref: ArtifactRef | None
      related_scene_id: str | None
      related_entity_id: str | None
      proposal: str
      rationale: str
      confidence: float
      status: Literal["proposed", "accepted", "rejected", "deferred", "superseded"]
      status_reason: str | None
      decided_by: str | None        # Role or "human"
      decided_at: datetime | None
      superseded_by: str | None     # suggestion_id of replacement
      created_at: datetime
  ```
- [ ] `Decision` Pydantic schema.
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for suggestion lifecycle transitions.
- [ ] Unit tests for deferred suggestion resurfacing.
- [ ] Unit tests for decision recording.
- [ ] Unit tests for suggestion browsing and filtering.
- [ ] Integration test: role generates suggestion → Director accepts → new artifact version created → decision recorded.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Suggestions as Creative Backlog
The suggestion system turns the pipeline from a one-shot process into an iterative creative conversation. Roles notice things — "this character's motivation is unclear", "this lighting would work better in warm tones", "consider a match cut here" — and these observations are captured even when they're not immediately actionable.

### Suggestion Volume
Suggestions will accumulate quickly. The browsing API needs to handle filtering efficiently. For MVP, in-memory filtering of JSON artifacts is fine. If volume becomes an issue, consider a lightweight database.

---

## Tasks

- [ ] Design and implement `Suggestion`, `Decision` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement suggestion creation and lifecycle transition API.
- [ ] Implement deferred suggestion resurfacing logic.
- [ ] Implement decision recording.
- [ ] Implement suggestion browsing and filtering API.
- [ ] Implement aggregate statistics.
- [ ] Wire suggestion creation into role invocation flow.
- [ ] Write unit tests for all components.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
