# Story 032: Cost Tracking and Budget Management

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 2.7 (Cost Transparency), 20 (Metadata & Auditing — cost data in artifacts)
**Depends On**: Story 002 (pipeline foundation — cost recording hooks), Story 014 (role system — per-role cost attribution)

---

## Goal

Build the full cost tracking and budget management system on top of the per-call cost hooks from Story 002. This includes cost dashboards, per-stage and per-run summaries, cost-quality tradeoff controls, and budget caps.

---

## Acceptance Criteria

### Cost Dashboard
- [ ] Per-run cost summary:
  - [ ] Total cost.
  - [ ] Breakdown by stage.
  - [ ] Breakdown by model (which AI models were used and their individual costs).
  - [ ] Breakdown by role (which roles incurred what cost).
- [ ] Per-project cost summary:
  - [ ] Historical run costs.
  - [ ] Cumulative project cost.
  - [ ] Cost trends over time (are runs getting more or less expensive?).
- [ ] Per-scene cost (how much did it cost to process each scene through the pipeline?).

### Budget Caps (Spec 2.7)
- [ ] Budget caps configurable:
  - [ ] Per-project budget limit.
  - [ ] Per-run budget limit.
  - [ ] Per-stage budget limit (optional).
- [ ] When budget is approached:
  - [ ] Warning at configurable threshold (e.g., 80%).
  - [ ] Pipeline pauses at budget limit with clear message.
  - [ ] User can increase budget and resume, or stop.
- [ ] Budget enforcement does not corrupt state — pipeline stops cleanly between stages.

### Cost-Quality Tradeoffs (Spec 2.7)
- [ ] Support for model selection based on cost:
  - [ ] Cheaper models for initial passes (drafts, rough extraction).
  - [ ] Stronger models for refinement (final direction, critical reviews).
- [ ] Cost-quality profiles configurable per-stage or per-role.
- [ ] Cost comparison: show what the run would cost with different model choices.

### Cost Data in Artifacts
- [ ] Every AI-produced artifact includes cost data in its metadata (already hooked from Story 002).
- [ ] Cost data includes: model used, input tokens, output tokens, estimated cost USD.
- [ ] Cost data is auditable and queryable.

### Cost Reporting
- [ ] Generate cost report artifact per run.
- [ ] Export cost data (CSV/JSON) for external analysis.
- [ ] Cost data available through Operator Console API.

### Schema
- [ ] `CostSummary` Pydantic schema:
  ```python
  class StageCost(BaseModel):
      stage_id: str
      model: str
      input_tokens: int
      output_tokens: int
      estimated_cost_usd: float
      call_count: int

  class RunCostSummary(BaseModel):
      run_id: str
      total_cost_usd: float
      stages: list[StageCost]
      by_model: dict[str, float]
      by_role: dict[str, float]
      budget_limit_usd: float | None
      budget_remaining_usd: float | None
  ```
- [ ] `BudgetConfig` schema.
- [ ] Schemas registered in schema registry.

### Testing
- [ ] Unit tests for cost aggregation (per-stage, per-model, per-role).
- [ ] Unit tests for budget cap enforcement (warning, pause, resume).
- [ ] Unit tests for cost-quality profile selection.
- [ ] Unit tests for cost report generation.
- [ ] Integration test: run pipeline with budget cap → pipeline pauses at limit.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Cost Transparency as Trust
For a personal project with real API costs, cost transparency is critical. The user needs to know before clicking "run" approximately what it will cost, and they need clear controls to prevent runaway spending. Budget caps are a safety net, not a feature.

### Model Selection
Different stages have different cost-quality needs. Scene extraction might work fine with a cheaper model, but the Director's creative review might need the best model available. The cost-quality profile system lets the user (or the system defaults) make these tradeoffs explicit.

---

## Tasks

- [ ] Design and implement `RunCostSummary`, `StageCost`, `BudgetConfig` schemas.
- [ ] Register schemas in schema registry.
- [ ] Implement cost aggregation from existing per-call hooks.
- [ ] Implement per-run cost summary generation.
- [ ] Implement per-project cost tracking (historical).
- [ ] Implement budget cap configuration.
- [ ] Implement budget enforcement (warning, pause, resume).
- [ ] Implement cost-quality profile selection.
- [ ] Implement cost report artifact generation.
- [ ] Implement cost export (CSV/JSON).
- [ ] Wire into Operator Console API.
- [ ] Write unit tests.
- [ ] Write integration test.
- [ ] Run `make test-unit` and `make lint`.
- [ ] Update AGENTS.md with any lessons learned.

---

## Work Log

*(append-only)*
