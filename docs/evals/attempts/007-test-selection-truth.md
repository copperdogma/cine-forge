# Eval Attempt 007 - Test Selection Truth

**Status:** Succeeded
**Eval:** repository-test-harness
**Date:** 2026-07-21
**Worker Model:** GPT-5
**Subject Model(s):** N/A - deterministic repository harness

## Mission

Make CineForge's advertised test commands select exactly the suites they claim
to validate, fail on future selection drift, and avoid collecting fixture
utilities that write repository-relative files or report failure only through
printed text.

This is the first dependency of Story 208's repository-wide truth audit. No
golden, scorer, rubric, prompt, historical score, or production default may be
reinterpreted until the gate used to validate those repairs is honest.

## Baseline Reproduction

At base commit `a5b5c88`, using the repository virtual environment and
`PYTHONPATH=src`:

- `pytest tests/unit --collect-only` collected `1,019` tests.
- `pytest tests/unit -m unit --collect-only` selected `917` and deselected
  `102` tests physically owned by `tests/unit`.
- The omissions came from seven modules: `test_api.py` (`28` of `34`),
  `test_character_naming_regression.py` (`14`), `test_env.py` (`7`),
  `test_methodology_graph.py` (`15`),
  `test_module_entity_discovery_v1.py` (`30`),
  `test_post_rollout_breakdown_eval.py` (`3`), and
  `test_previz_adoption_service.py` (`5`).
- `make test-unit` reported `917 passed, 186 deselected, 1 warning`; 84 of the
  deselections were outside `tests/unit`, proving the command collected the
  entire repository before filtering.
- Full collection found `1,103` tests, including three files under
  `tests/fixtures/round_trip/` that were intended as utilities.
- Running only `test_fdx_round_trip.py` failed at setup because `fdx_path` was
  interpreted as a nonexistent pytest fixture.
- The other two accidental tests were not executed: each writes a PDF below
  repository-relative `tmp/research/` and contains no assertion that would turn
  its printed `FAIL` message into a failing test.
- Collection emitted `PytestUnknownMarkWarning` for the unregistered
  `acceptance` marker.

## Classification and Runtime Impact

- **Classification:** harness-wrong. This is outside the model-output mismatch
  taxonomy; no model-wrong, golden-wrong, or ambiguous model verdict is
  implied.
- **Historical impact:** prior `make test-unit` green reports are incomplete,
  including the Story 208 adoption validation. They remain useful evidence for
  the 917 selected tests but are not proof that the full owned unit suite ran.
- **Runtime impact:** non-runtime-blocking. Production behavior is unchanged,
  but future implementation/eval closure is blocked until the harness is fixed.

## Plan

1. Scope `make test-unit` to `tests/unit` while retaining the explicit `unit`
   marker contract.
2. Mark every currently omitted unit test and add a collection hook that fails
   if any future test under `tests/unit` lacks `pytest.mark.unit`.
3. Register the `acceptance` marker in the canonical pytest configuration.
4. Remove the unconditional placeholder test.
5. Convert, relocate, or remove the three fixture utilities so collection is
   side-effect free and all retained tests use `tmp_path` plus assertions.
6. Prove full collection, unit selection, focused replacements, Ruff, and
   `git diff --check` before closing this attempt.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Working-tree state: uncommitted, user has not authorized a commit.
- Package A selection-contract bundle SHA-256: `3d3758af35f298f9c971c827c55f927d27ced883877258f2435b336c1a1933aa`.
  This is the SHA-256 of the sorted per-file SHA-256 lines for the Makefile,
  pytest config/hook, seven repaired unit modules, and the retained PDF
  round-trip test named in this attempt.
- Paid subject output: none.
- Quality/latency/cost: not applicable; the measured contract is collected and
  selected test counts plus exit status.

## Work Log

- 2026-07-21: Reproduced the baseline twice, including an independent agent
  pass. No repository-relative writer was executed.
- 2026-07-21: Began isolated Package A edits. Semantic eval artifacts remain
  untouched behind the Package A stop/go gate.
- 2026-07-21: Scoped `make test-unit` to `tests/unit`, registered the
  acceptance marker, marked all seven omitted modules, and added a collection
  failure for any future unmarked unit item.
- 2026-07-21: Deleted the placeholder and three print-only/repository-writing
  fixture utilities. Added a `tmp_path` PDF render/re-ingest test with semantic
  title, heading, and dialogue assertions.
- 2026-07-21: Proved the collection hook with a temporary unmarked sentinel;
  collection failed with the exact node ID before the sentinel was removed.
- 2026-07-21: Final checkpoint: full collection `1,133`; unit collection and
  `-m unit` selection both `1,051`; `make test-unit` reported `1,051 passed in
  25.32s`. The full offline suite reported `1,128 passed, 5 skipped in 61.95s`.

## Definition of Done Checklist

- [x] Baseline failure reproduced before repair
- [x] Affected historical validation scope classified
- [x] Every test under `tests/unit` is selected by `make test-unit`
- [x] Future unmarked unit tests fail collection
- [x] Full collection has no fixture-utility tests or collection warnings
- [x] Retained round-trip/export behavior uses assertions and temporary paths
- [x] Focused and full Package A validation passes
- [x] Story work log and truth-audit ledger record final evidence
- [x] Registry attempt summary is not applicable; this harness is not a registry eval
- [x] Final working-tree contract hashes are recorded
