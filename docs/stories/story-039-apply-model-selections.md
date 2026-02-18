# Story 039 — Apply Model Selections to Production

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: To Do
**Depends on**: Story 038 (Multi-Provider Transport), Story 036 (Model Selection)

## Goal

Apply Story 036's task-specific model selections to production code and recipe configs. Also build any remaining eval types (normalization, scene enrichment) that were deferred from Story 036.

## Context

Story 036 benchmarked 5 eval types across 12 models and produced task-specific try-validate-escalate triads. Story 047 added Sonnet 4.6 to all evals and updated winners.

**Already applied (Story 047, 2026-02-17)**: Sonnet 4.5 → 4.6 defaults updated in character_bible, prop_bible, script_normalize, and ai/chat.py. Location_bible intentionally kept at Sonnet 4.5 (it scores better there: 0.895 vs 0.870). `ModelStrategy` defaults in `models.py` are correct (work=sonnet-4-6, verify=haiku-4-5, escalate=opus-4-6).

**Stale defaults discovered (2026-02-18)**: Audit found 4 modules with outdated hardcoded defaults that Story 047 missed: `scene_extract_v1` (Haiku instead of Sonnet 4.6), `location_bible_v1` (dated suffix), `continuity_tracking_v1` (gpt-4o-mini), `project_config_v1` (gpt-4o escalation).

**Remaining work**: Fix stale module defaults, update recipe configs, build deferred evals, end-to-end smoke test.

## Acceptance Criteria

- [ ] Model defaults in pipeline modules reflect Story 036/047 task-specific triads (4 stale modules remain — see Tasks)
- [ ] Recipe configs reference new model defaults
- [ ] All pipeline modules work end-to-end with their assigned models
- [ ] Build normalization eval (text-comparison scorer pattern — deferred from Story 036)
- [ ] Build scene enrichment eval (scene-level input fixtures — deferred from Story 036)
- [ ] Build QA pass eval (seeded good/bad pairs — deferred from Story 036)
- [ ] Run deferred evals across full model matrix, update task-specific triads if results differ
- [ ] Recalibrated config detection eval re-run with fixed golden reference

## Non-Goals

- Changing the try-validate-escalate architecture itself
- Building a model switching UI
- Cost optimization (Story 032)

## Tasks

- [x] Update module-level model defaults (Story 047: Sonnet 4.5 → 4.6 in character_bible, prop_bible, script_normalize, chat)
- [ ] Fix remaining stale module defaults missed by Story 047:
  - [ ] `scene_extract_v1/main.py`: default `work_model` is `claude-haiku-4-5` — should be `claude-sonnet-4-6` (benchmark winner, 0.815)
  - [ ] `location_bible_v1/main.py`: default `work_model` uses stale dated string `claude-sonnet-4-5-20250929` — normalize to `claude-sonnet-4-5`
  - [ ] `continuity_tracking_v1/main.py`: default `work_model` is `gpt-4o-mini` — update to benchmarked model (no eval yet, but at minimum use `claude-sonnet-4-6`)
  - [ ] `project_config_v1/main.py:301`: hardcodes `"gpt-4o"` as escalation model in ProjectConfig artifact — should be `claude-opus-4-6`
- [ ] Update recipe YAML configs with provider-prefixed model strings
- [ ] Build normalization eval: text-comparison scorer (Fountain structural validity + content preservation)
- [ ] Build scene enrichment eval: scene-level golden references from The Mariner
- [ ] Build QA pass eval: seeded known-good and known-bad inputs
- [ ] Run normalization, scene enrichment, and QA evals across 12 models
- [ ] Re-run config detection eval with calibrated golden reference
- [ ] Analyze all results and finalize task-specific triads
- [ ] End-to-end pipeline smoke test with new model assignments
- [ ] Update Story 036 with final comprehensive results

## Work Log

### 20260217-2100 — Partial completion via Story 047

Model defaults updated for 5 modules where Sonnet 4.6 benchmarks justify the change. Location_bible intentionally kept at Sonnet 4.5 (better score: 0.895 vs 0.870). Remaining work: recipe configs, deferred evals, end-to-end smoke test, multi-provider transport (Story 038).
