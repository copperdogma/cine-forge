# Story 017: Suggestion and Decision Tracking

**Status**: Done
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
- [x] Every suggestion is an immutable artifact with:
  - [x] **Source role**: who proposed it.
  - [x] **Related artifact**: scene, entity, or artifact the suggestion is about.
  - [x] **Proposal**: what is being suggested.
  - [x] **Confidence and rationale**: why, and how confident.
  - [x] **Lifecycle status**: proposed, accepted, rejected, deferred, superseded.
- [x] Suggestion lifecycle transitions:
  - [x] `proposed` → `accepted`: folded into canon, produces a new artifact version.
  - [x] `proposed` → `rejected`: declined, reason recorded.
  - [x] `proposed` → `deferred`: starred for later.
  - [x] `proposed`/`deferred` → `superseded`: a newer suggestion replaced this one.
  - [x] Each transition is recorded with who made the decision and why.

### Deferred Suggestion Resurfacing
- [x] Deferred suggestions are resurfaced when their related scene or entity comes up for revision.
- [x] Resurfacing is automatic: when a scene is re-extracted or a bible entry is updated, related deferred suggestions are flagged for review.

### Decision Artifacts (Spec 8.6)
- [x] Explicit decision artifacts recording:
  - [x] What was decided.
  - [x] By whom (role or human).
  - [x] Why (rationale).
  - [x] What alternatives were considered.
  - [x] What suggestions informed the decision.
  - [x] Links to affected artifacts.
- [x] Decisions are immutable and versioned.

### Suggestion Browsing
- [x] API to browse and search suggestions:
  - [x] Filter by role, artifact, status, confidence.
  - [x] Sort by recency, confidence, relevance.
  - [x] View suggestion history for a specific artifact.
- [x] Aggregate statistics: total suggestions, acceptance rate per role, deferred backlog size.

### Schema
- [x] `Suggestion` Pydantic schema:
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
- [x] `Decision` Pydantic schema.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for suggestion lifecycle transitions.
- [x] Unit tests for deferred suggestion resurfacing.
- [x] Unit tests for decision recording.
- [x] Unit tests for suggestion browsing and filtering.
- [x] Integration test: role generates suggestion → Director accepts → new artifact version created → decision recorded.
- [x] Schema validation on all outputs.

---

## Design Notes

### Suggestions as Creative Backlog
The suggestion system turns the pipeline from a one-shot process into an iterative creative conversation. Roles notice things — "this character's motivation is unclear", "this lighting would work better in warm tones", "consider a match cut here" — and these observations are captured even when they're not immediately actionable.

### Suggestion Volume
Suggestions will accumulate quickly. The browsing API needs to handle filtering efficiently. For MVP, in-memory filtering of JSON artifacts is fine. If volume becomes an issue, consider a lightweight database.

---

## Tasks

- [x] Design and implement `Suggestion`, `Decision` schemas.
- [x] Register schemas in schema registry.
- [x] Implement suggestion creation and lifecycle transition API.
- [x] Implement deferred suggestion resurfacing logic.
- [x] Implement decision recording.
- [x] Implement suggestion browsing and filtering API.
- [x] Implement aggregate statistics.
- [x] Wire suggestion creation into role invocation flow.
- [x] Write unit tests for all components.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*

20260220-1430 — implementation complete: added `Suggestion` and `Decision` schemas; implemented `SuggestionManager` for lifecycle management, resurfacing, and browsing; integrated suggestion creation into `RoleContext.invoke` so roles can emit suggestions in their JSON response; resurfaced deferred suggestions in `CanonGate` stage reviews; evidence=`src/cine_forge/schemas/suggestion.py`, `src/cine_forge/roles/suggestion.py`, `src/cine_forge/roles/runtime.py`, `src/cine_forge/roles/canon.py`.

20260220-1445 — verification complete: added unit tests for suggestion creation, transitions, querying, and aggregate stats; added integration test for full suggestion-to-decision lifecycle including automated resurfacing; verified all tests pass and lint is clean; evidence=`tests/unit/test_suggestion_system.py`, `tests/integration/test_suggestion_integration.py`.
