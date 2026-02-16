# Story 038 — Apply Model Selections to Production

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: To Do
**Depends on**: Story 037 (Multi-Provider Transport), Story 036 (Model Selection)

## Goal

Apply Story 036's task-specific model selections to production code and recipe configs. Also build any remaining eval types (normalization, scene enrichment) that were deferred from Story 036.

## Context

Story 036 benchmarked 5 eval types across 12 models and produced task-specific try-validate-escalate triads. Story 037 unblocks using non-OpenAI models in production. This story wires the selections into actual module configs and fills in the remaining eval gaps.

## Acceptance Criteria

- [ ] Model defaults in `src/cine_forge/schemas/models.py` reflect Story 036 task-specific triads
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

- [ ] Update `ModelConfig` defaults per task in `src/cine_forge/schemas/models.py`
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
