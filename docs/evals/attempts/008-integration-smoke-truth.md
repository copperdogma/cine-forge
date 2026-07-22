# Eval Attempt 008 - Integration and Smoke Fixture Truth

**Status:** Succeeded
**Eval:** repository-integration-smoke-harness
**Date:** 2026-07-21
**Worker Model:** GPT-5
**Subject Model(s):** N/A - deterministic fixture/runtime paths

## Mission

Repair the real integration and smoke failures exposed only after Package A
removed accidental collection traps. Preserve current production contracts and
update stale test fixtures or assumptions rather than weakening assertions.

## Baseline Reproduction

After the Package A collection repair, `make test` collected `1,100` tests and
completed the full suite for the first time in this audit:

- `1,090` passed.
- `4` skipped.
- `6` failed.

The failures group into three source-backed contracts:

1. `test_final_output_recipe_builds_partial_cut_from_preserved_render_batch_failure`
   starts directly at `render` without the now-required `render_clip_plan`
   artifacts, so it fails before reaching the synthetic second-scene render
   failure it claims to test.
2. Four mocked MVP recipe tests reach the current `script_bible` stage, but the
   fixture LLM dispatcher has no `ScriptBible` response. They fail with
   `Unsupported fixture response schema: ScriptBible` rather than exercising
   their cache/staleness/end-to-end contracts.
3. `test_story_004_ingest_normalize_smoke` accepts a completed normalization
   stage whose canonical `script_text` is empty. The failure is a useful
   semantic guard and must not be removed or relaxed.

The widened repair loop subsequently exposed four additional defects:

4. Scene breakdown ignored the runtime fixture model and could call its paid
   Haiku default. Script-normalization retries could likewise jump from `mock`
   to a hard-coded Opus model.
5. The new scene-action fixture contradicted its prompt by including
   dialogue-only characters and excluded incidental props.
6. Eight per-scene fixture calls were collapsed to one and labeled
   `mixed:fixture` even though only one model was used.
7. Live acceptance/continuity tests ran whenever credentials existed, and the
   storyboard integration requested mocked images while leaving shot planning
   on live Sonnet.

## Classification and Runtime Impact

- **Render integration:** test-assumption-wrong. The runtime's required
  `render_clip_plan` guard is intentional; the fixture/setup is stale.
- **Mocked MVP:** fixture-wrong. The fixture transport did not grow with the
  current recipe's `ScriptBible` schema.
- **Story 004 smoke:** production-wrong. Story 040's performance shortcut
  rejected prose despite the Ideal/spec/Story 004 contract that prose is a
  supported story input. This was runtime-blocking.
- **Model selection and live gating:** runtime/harness-wrong. Deterministic
  tests could escape into paid calls; this was test-safety blocking.
- **Scene-action fixture:** golden-wrong, non-runtime-blocking. The production
  extraction prompt remained authoritative.
- **Telemetry:** runtime-observability-wrong. Cost stayed zero for fixtures,
  but call count and model identity were false.
- **Storyboard setup:** test-assumption-wrong, with paid-call risk.

No model-wrong verdict applies because all six failures occur before a paid or
live subject-model judgment.

## Plan

1. Capture the actual recipe, fixture bundle, generated run state, and canonical
   artifact for each group before editing.
2. Update the render test setup to satisfy the current normal prerequisite path
   while preserving its intended partial-success assertion.
3. Add a source-linked `ScriptBible` fixture response using the real schema and
   keep the mocked MVP tests semantically meaningful.
4. Diagnose the empty normalization artifact; fix the real runtime/fixture
   assumption and retain the nonempty semantic assertion.
5. Rerun each focused group, then the full suite. Do not change production
   defaults or skip/xfail the failures.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Working-tree state: uncommitted, user has not authorized a commit.
- Integration/runtime contract bundle SHA-256:
  `9e133865116019918f63045230875ac36445cee752d2b89737bb66799ae842d3`.
  This hashes the sorted per-file hashes for the production selection,
  fixture-dispatch, telemetry, and affected test files listed by this attempt.
- Paid subject output: one diagnostic run escaped to the old live Haiku
  default before the routing defect was isolated, estimated at `$0.00748`.
  Every subsequent focused and full run used fixture/mock models or deliberately
  invalid provider credentials and recorded `$0.00` fixture cost.
- Baseline command: `make test PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
- Baseline result: `6 failed, 1090 passed, 4 skipped in 210.00s`.

## Final Evidence

- Render integration starts at the required clip-plan stage and preserves both
  successful scene-1 clips while classifying scene 2 as partial failure.
- Prose and other schema-valid story text now use assisted normalization;
  the unreachable Tier-3 rejection shortcut and empty artifact path were
  deleted. Deterministic conversion preserves exact prose anchors and records
  its heading invention and source-as-action assumption.
- Work, verification, and escalation models now honor stage/runtime settings;
  escalation is explicit and otherwise remains on the selected work model.
- Source-linked ScriptBible and scene-action responses are source-hash locked.
  All eight scenes have exact positive and negative entity assertions.
- Driver and scene breakdown telemetry report `8` fixture calls, model
  `fixture`, zero tokens, and `$0.00` for the sample screenplay.
- Live tests require `CINE_FORGE_LIVE_TESTS=1` in addition to credentials.
- Full offline command with deliberately invalid provider credentials:
  `1,128 passed, 5 skipped in 61.95s`.
- Honest unit gate: `1,051 passed in 25.32s`.

## Definition of Done Checklist

- [x] Full-suite baseline completed and failure groups recorded
- [x] Initial classification and runtime impact recorded
- [x] Render integration reaches and validates its intended failure boundary
- [x] MVP fixture covers the current ScriptBible schema with semantic content
- [x] Story 004 smoke produces nonempty canonical screenplay content
- [x] Focused tests pass without weakened assertions or skips
- [x] Full test suite passes
- [x] Story work log and audit ledger record final evidence
- [x] Final working-tree contract hashes are recorded
