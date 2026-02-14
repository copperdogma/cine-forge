# Story 031: Change Propagation (Semantic Impact Layer)

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 2.3 (Revision and Change Propagation — Layer 2), 2.8 (QA — AI assessment)
**Depends On**: Story 002 (pipeline foundation — Layer 1 structural invalidation), Story 014 (role system — AI assessment roles), Story 010 (entity graph — dependency understanding)

---

## Goal

Implement **Layer 2 — Semantic Impact Assessment**: the AI-powered analysis that examines stale artifacts (flagged by Layer 1 structural invalidation from Story 002) and triages them. Each stale artifact is assessed: does it actually need revision given what changed, or is it still valid despite the upstream change?

Layer 1 (Story 002) is conservative — it marks everything downstream as stale. Layer 2 is intelligent — it understands what changed and evaluates whether each stale artifact is actually affected.

---

## Acceptance Criteria

### Semantic Impact Assessment
- [ ] AI-powered diff analysis:
  - [ ] Diffs the old and new versions of the changed artifact.
  - [ ] Examines each stale downstream artifact.
  - [ ] Triages each stale artifact into:
    - [ ] `needs_revision` — confirmed affected, with notes on what needs to change.
    - [ ] `confirmed_valid` — still correct despite upstream change.
- [ ] Assessment produces "needs work" annotations with:
  - [ ] Rationale (why does it need work?).
  - [ ] What specifically changed upstream.
  - [ ] Which role flagged it.
  - [ ] Suggested revision approach.
- [ ] Assessment is on-demand (not automatic) — user or Director triggers it.

### Health Status Transitions
- [ ] Artifact health now fully functional:
  - [ ] `valid` → `stale` (Layer 1, automatic).
  - [ ] `stale` → `needs_revision` (Layer 2, AI assessment).
  - [ ] `stale` → `confirmed_valid` (Layer 2, AI assessment).
  - [ ] `needs_revision` → `valid` (after revision and re-validation).
  - [ ] `confirmed_valid` → `valid` (acknowledged by user/Director).
- [ ] Manual override: user or Director can manually set status without AI assessment.

### Impact Scope Analysis
- [ ] Before running full assessment, provide a quick scope preview:
  - [ ] How many artifacts are stale?
  - [ ] What types of artifacts are affected?
  - [ ] Estimated cost of running the assessment.
- [ ] User can choose to assess all, assess selectively, or skip assessment and manually triage.

### Assessment Module
- [ ] Module/utility for running semantic impact assessment.
- [ ] Configurable: which AI model to use, cost budget for assessment.
- [ ] Can run on a subset of stale artifacts (selective assessment).

### Schema
- [ ] `ImpactAssessment` Pydantic schema:
  ```python
  class ArtifactImpact(BaseModel):
      artifact_ref: ArtifactRef
      previous_health: Literal["stale"]
      assessed_health: Literal["needs_revision", "confirmed_valid"]
      rationale: str
      upstream_change_summary: str
      suggested_revision: str | None
      confidence: float
      assessing_role: str

  class ImpactAssessment(BaseModel):
      trigger_artifact_ref: ArtifactRef      # The artifact that changed
      trigger_diff_summary: str               # What changed
      assessments: list[ArtifactImpact]
      total_stale: int
      total_needs_revision: int
      total_confirmed_valid: int
      assessment_cost: CostRecord
  ```
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for semantic impact assessment logic (mocked AI).
- [ ] Unit tests for health status transitions.
- [ ] Unit tests for scope preview.
- [ ] Unit tests for selective assessment.
- [ ] Integration test: change artifact → Layer 1 staleness → Layer 2 assessment → triaged health statuses.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Layer 1 vs. Layer 2
Layer 1 is instant, free, and conservative: "something upstream changed, everything downstream might be affected." Layer 2 is slow, costs money, and intelligent: "I looked at what changed, and only these 3 of 15 stale artifacts actually need revision."

Most of the time, Layer 1 is sufficient — the user sees stale artifacts and manually decides what to re-run. Layer 2 is valuable when the change is small and the downstream graph is large (e.g., a minor script edit that affects 50+ downstream artifacts).

### Assessment Cost
Running Layer 2 on a large project could be expensive — every stale artifact gets an AI call. The scope preview and selective assessment features let the user control costs. Budget caps from Story 032 should also apply.

---

## Tasks

- [ ] Design and implement `ImpactAssessment`, `ArtifactImpact` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement semantic impact assessment logic.
- [ ] Implement health status transition management.
- [ ] Implement scope preview (count, types, estimated cost).
- [ ] Implement selective assessment (assess subset of stale artifacts).
- [ ] Implement manual override for health status.
- [ ] Wire into artifact store health tracking.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
